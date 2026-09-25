"""
OpenAI API provider implementation.

Supports GPT models including GPT-4, GPT-4 Vision, GPT-3.5, and newer models.
Handles text, image, and multimodal inputs with batch processing.
"""

import json
import logging
import tempfile
from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .cloud_ai import CloudAIProvider
from .ai_provider import Message, AIResponse, BatchJob, ContentBlock, ContentType, MessageRole
from shared.file_operations import write_text, open_file_handle, delete_file


class OpenAIProvider(CloudAIProvider):
    """
    OpenAI API provider implementation.
    
    Supports:
    - GPT-4, GPT-4 Vision, GPT-3.5, GPT-4o models
    - Text and image inputs
    - Streaming responses
    - Batch processing
    - Function calling
    """
    
    def __init__(self, model_name: str = "gpt-4o", **kwargs):
        """
        Initialize OpenAI provider.
        
        Args:
            model_name: OpenAI model name
            **kwargs: Additional configuration
        """
        super().__init__(model_name, **kwargs)
        
        # OpenAI specific configuration
        self.organization = kwargs.get('organization')
        self.project = kwargs.get('project')
        
        # Model capabilities - Updated for 2025
        self._vision_models = {
            # GPT-5 Series (2025)
            'gpt-5', 'gpt-5-mini',
            # Legacy models with vision
            'gpt-4-vision-preview', 'gpt-4o', 'gpt-4o-mini', 
            'gpt-4-turbo', 'gpt-4-turbo-2024-04-09', 'gpt-4.1'
        }
        
        # Non-vision models (text-only)
        self._text_only_models = {
            'gpt-5-nano', 'gpt-4.1-nano', 'o3', 'o3-pro', 'o4-mini'
        }
        
        # Pricing (per 1K tokens, as of 2025) - Updated from web research
        self._pricing = {
            # GPT-5 Series
            'gpt-5': {'input': 1.25, 'output': 10.0},
            'gpt-5-mini': {'input': 0.01, 'output': 0.03},
            'gpt-5-nano': {'input': 0.005, 'output': 0.02},
            # GPT-4 Series  
            'gpt-4.1': {'input': 0.02, 'output': 0.06},
            'gpt-4.1-nano': {'input': 0.003, 'output': 0.01},
            'gpt-4o': {'input': 0.005, 'output': 0.015},
            'gpt-4o-mini': {'input': 0.0015, 'output': 0.0006},
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            # Reasoning models
            'o3': {'input': 0.05, 'output': 0.20},
            'o3-pro': {'input': 0.10, 'output': 0.40},
            'o4-mini': {'input': 0.02, 'output': 0.08},
            # Legacy
            'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
        }
        
        # Initialize client
        self._client = None
    
    def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            try:
                import openai
                client_kwargs = {
                    "api_key": self.api_key,
                    "organization": self.organization,
                    "base_url": self.base_url,
                    "timeout": self.timeout
                }
                if self.project:
                    client_kwargs["project"] = self.project
                try:
                    self._client = openai.OpenAI(**client_kwargs)
                except TypeError:
                    client_kwargs.pop("project", None)
                    self._client = openai.OpenAI(**client_kwargs)
            except ImportError:
                raise ImportError("OpenAI package not installed. Run: pip install openai")
        
        return self._client

    def _get_base_url(self) -> str:
        base = (self.base_url or "https://api.openai.com/v1").rstrip("/")
        if not base.endswith("/v1"):
            base = f"{base}/v1"
        return base

    def _http_request(self, method: str, path: str, payload: Optional[dict] = None) -> dict:
        url = f"{self._get_base_url()}{path}"
        data = None
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore") if exc.fp else ""
            logging.error("OpenAI HTTP error %s %s: %s", method, path, body)
            raise
        except URLError as exc:
            logging.error("OpenAI HTTP error %s %s: %s", method, path, exc)
            raise

    def _http_stream_lines(self, path: str) -> Iterator[str]:
        url = f"{self._get_base_url()}{path}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        req = Request(url, headers=headers, method="GET")
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                for raw_line in resp:
                    if not raw_line:
                        continue
                    line = raw_line.decode("utf-8", errors="ignore")
                    if line.strip():
                        yield line.strip()
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore") if exc.fp else ""
            logging.error("OpenAI HTTP error GET %s: %s", path, body)
            raise
        except URLError as exc:
            logging.error("OpenAI HTTP error GET %s: %s", path, exc)
            raise

    def _download_file_content(self, file_id: str) -> Iterator[str]:
        client = self._get_client()
        if hasattr(client, "files"):
            try:
                file_content = client.files.content(file_id)
                if hasattr(file_content, "iter_lines"):
                    for line in file_content.iter_lines():
                        yield line.decode("utf-8", errors="ignore") if isinstance(line, bytes) else line
                    return
                text = getattr(file_content, "text", "")
                for line in text.splitlines():
                    yield line
                return
            except AttributeError:
                pass

        for line in self._http_stream_lines(f"/files/{file_id}/content"):
            yield line

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert internal messages to OpenAI format."""
        openai_messages = []
        
        for msg in messages:
            openai_msg = {"role": msg.role.value}
            
            if isinstance(msg.content, str):
                openai_msg["content"] = msg.content
            else:
                # Handle multimodal content
                content_parts = []
                
                for block in msg.content:
                    if block.type == ContentType.TEXT:
                        content_parts.append({
                            "type": "text",
                            "text": block.content
                        })
                    elif block.type == ContentType.IMAGE_URL:
                        content_parts.append({
                            "type": "image_url",
                            "image_url": {
                                "url": block.content,
                                "detail": block.metadata.get("detail", "auto")
                            }
                        })
                    elif block.type == ContentType.IMAGE_BASE64:
                        mime_type = block.metadata.get("mime_type", "image/jpeg")
                        data_url = f"data:{mime_type};base64,{block.content}"
                        content_parts.append({
                            "type": "image_url",
                            "image_url": {
                                "url": data_url,
                                "detail": block.metadata.get("detail", "auto")
                            }
                        })
                
                openai_msg["content"] = content_parts
            
            openai_messages.append(openai_msg)
        
        return openai_messages
    
    def _make_request(self, messages: List[Message], **kwargs) -> AIResponse:
        """Make OpenAI API request."""
        client = self._get_client()
        openai_messages = self._convert_messages(messages)

        # Prepare request parameters
        request_params = {
            "model": self.model_name,
            "messages": openai_messages,
        }

        # Add optional parameters
        if 'temperature' in kwargs:
            request_params['temperature'] = kwargs['temperature']
        if 'max_tokens' in kwargs:
            request_params['max_tokens'] = kwargs['max_tokens']
        if 'top_p' in kwargs:
            request_params['top_p'] = kwargs['top_p']
        if 'frequency_penalty' in kwargs:
            request_params['frequency_penalty'] = kwargs['frequency_penalty']
        if 'presence_penalty' in kwargs:
            request_params['presence_penalty'] = kwargs['presence_penalty']
        if 'response_format' in kwargs:
            request_params['response_format'] = kwargs['response_format']

        # Debug logging: Log OpenAI-specific request details
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            import json
            logging.debug(f"OpenAI API Request:")
            logging.debug(f"  - Model: {request_params['model']}")
            logging.debug(f"  - Message count: {len(openai_messages)}")
            # Log first 500 chars of messages for debugging
            messages_str = json.dumps(openai_messages, ensure_ascii=False, indent=2)[:500]
            logging.debug(f"  - Messages preview: {messages_str}...")
            logging.debug(f"  - Request params: {', '.join([f'{k}={v}' for k, v in request_params.items() if k != 'messages'])}")

        try:
            response = client.chat.completions.create(**request_params)

            # Debug logging: Log OpenAI response details
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug(f"OpenAI API Response:")
                logging.debug(f"  - Response ID: {response.id}")
                logging.debug(f"  - Model: {response.model}")
                logging.debug(f"  - Created: {response.created}")
                logging.debug(f"  - Tokens: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}, total={response.usage.total_tokens}")
                logging.debug(f"  - Finish reason: {response.choices[0].finish_reason}")

            return AIResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                finish_reason=response.choices[0].finish_reason,
                metadata={
                    'id': response.id,
                    'created': response.created,
                    'system_fingerprint': getattr(response, 'system_fingerprint', None)
                }
            )

        except Exception as e:
            logging.error(f"OpenAI API request failed: {e}")
            # Debug logging: Log detailed error information
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                import traceback
                logging.debug(f"OpenAI Error Details:")
                logging.debug(f"  - Error type: {type(e).__name__}")
                logging.debug(f"  - Error message: {str(e)}")
                logging.debug(f"  - Traceback: {traceback.format_exc()}")
            raise
    
    def _make_stream_request(self, messages: List[Message], **kwargs) -> Iterator[str]:
        """Make streaming OpenAI API request."""
        client = self._get_client()
        openai_messages = self._convert_messages(messages)
        
        request_params = {
            "model": self.model_name,
            "messages": openai_messages,
            "stream": True
        }
        
        # Add optional parameters
        for key in ['temperature', 'max_tokens', 'top_p', 'frequency_penalty', 'presence_penalty']:
            if key in kwargs:
                request_params[key] = kwargs[key]
        
        try:
            stream = client.chat.completions.create(**request_params)
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logging.error(f"OpenAI streaming request failed: {e}")
            raise
    
    def create_batch_job(self, messages_list: List[List[Message]], 
                        custom_ids: List[str], **kwargs) -> BatchJob:
        """Create OpenAI batch job."""
        client = self._get_client()
        
        # Prepare batch requests
        batch_requests = []
        for i, (messages, custom_id) in enumerate(zip(messages_list, custom_ids)):
            openai_messages = self._convert_messages(messages)
            
            request = {
                "custom_id": custom_id,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": self.model_name,
                    "messages": openai_messages
                }
            }
            
            # Add optional parameters
            for key in ['temperature', 'max_tokens', 'top_p']:
                if key in kwargs:
                    request["body"][key] = kwargs[key]
            
            batch_requests.append(request)
        
        # Create batch file
        temp_fd, batch_file_path = tempfile.mkstemp(suffix='.jsonl')
        try:
            import os
            os.close(temp_fd)
        except Exception:
            pass
        write_text(batch_file_path, "\n".join(json.dumps(r) for r in batch_requests) + "\n")
        
        try:
            # Upload batch file
            with open_file_handle(batch_file_path, 'rb') as batch_file:
                file_response = client.files.create(
                    file=batch_file,
                    purpose="batch"
                )
            
            # Create batch job
            if hasattr(client, "batches"):
                batch_response = client.batches.create(
                    input_file_id=file_response.id,
                    endpoint="/v1/chat/completions",
                    completion_window="24h"
                )
            else:
                batch_response = self._http_request(
                    "POST",
                    "/batches",
                    {
                        "input_file_id": file_response.id,
                        "endpoint": "/v1/chat/completions",
                        "completion_window": "24h"
                    }
                )
            
            return BatchJob(
                job_id=getattr(batch_response, "id", None) or batch_response.get("id"),
                status=getattr(batch_response, "status", None) or batch_response.get("status"),
                messages_list=messages_list,
                custom_ids=custom_ids,
                created_at=datetime.fromtimestamp(
                    getattr(batch_response, "created_at", None) or batch_response.get("created_at", 0)
                ).isoformat(),
                metadata={
                    'input_file_id': file_response.id,
                    'endpoint': getattr(batch_response, "endpoint", None) or batch_response.get("endpoint"),
                    'completion_window': getattr(batch_response, "completion_window", None) or batch_response.get("completion_window")
                }
            )
            
        finally:
            # Clean up temporary file
            delete_file(batch_file_path)
    
    def get_batch_job(self, job_id: str) -> BatchJob:
        """Get batch job status and results."""
        client = self._get_client()
        
        try:
            if hasattr(client, "batches"):
                batch_response = client.batches.retrieve(job_id)
                status = batch_response.status
                output_file_id = batch_response.output_file_id
                input_file_id = batch_response.input_file_id
                error_file_id = batch_response.error_file_id
                request_counts = batch_response.request_counts.__dict__ if batch_response.request_counts else {}
                created_at = batch_response.created_at
                completed_at = batch_response.completed_at
            else:
                batch_response = self._http_request("GET", f"/batches/{job_id}")
                status = batch_response.get("status")
                output_file_id = batch_response.get("output_file_id")
                input_file_id = batch_response.get("input_file_id")
                error_file_id = batch_response.get("error_file_id")
                request_counts = batch_response.get("request_counts", {})
                created_at = batch_response.get("created_at", 0)
                completed_at = batch_response.get("completed_at")
            
            results = []
            if status == 'completed' and output_file_id:
                # Download and parse results
                for line in self._download_file_content(output_file_id):
                    if not line:
                        continue
                    if isinstance(line, bytes):
                        line = line.decode('utf-8', errors='ignore')
                    result = json.loads(line)
                    if result.get('response'):
                        choice = result['response']['body']['choices'][0]
                        response = AIResponse(
                            content=choice['message']['content'],
                            model=result['response']['body']['model'],
                            usage=result['response']['body'].get('usage', {}),
                            finish_reason=choice.get('finish_reason'),
                            metadata={'custom_id': result.get('custom_id')}
                        )
                        results.append(response)
            
            return BatchJob(
                job_id=job_id,
                status=status,
                messages_list=[],  # Not stored in response
                custom_ids=[],     # Not stored in response
                created_at=datetime.fromtimestamp(created_at or 0).isoformat(),
                completed_at=(
                    datetime.fromtimestamp(completed_at).isoformat() 
                    if completed_at else None
                ),
                results=results,
                metadata={
                    'input_file_id': input_file_id,
                    'output_file_id': output_file_id,
                    'error_file_id': error_file_id,
                    'request_counts': request_counts
                }
            )
            
        except Exception as e:
            logging.error(f"Failed to get batch job {job_id}: {e}")
            raise
    
    def cancel_batch_job(self, job_id: str) -> bool:
        """Cancel OpenAI batch job."""
        client = self._get_client()
        
        try:
            if hasattr(client, "batches"):
                client.batches.cancel(job_id)
            else:
                self._http_request("POST", f"/batches/{job_id}/cancel", payload={})
            return True
        except Exception as e:
            logging.error(f"Failed to cancel batch job {job_id}: {e}")
            return False
    
    def supports_images(self) -> bool:
        """Check if current model supports images."""
        model_name = self.model_name.lower()
        
        # Explicitly check text-only models first
        if model_name in self._text_only_models:
            return False
        
        # Check if it's in vision models
        if model_name in self._vision_models:
            return True
            
        # Default for unknown models - assume no vision to be safe
        return False
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """Calculate cost based on token usage."""
        if self.model_name not in self._pricing:
            return 0.0
        
        pricing = self._pricing[self.model_name]
        input_cost = usage.get('prompt_tokens', 0) * pricing['input'] / 1000
        output_cost = usage.get('completion_tokens', 0) * pricing['output'] / 1000
        
        return input_cost + output_cost
