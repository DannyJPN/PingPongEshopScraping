"""
Token and cost tracking for OpenAI API calls.

This module provides a singleton TokenTracker class that centrally tracks
all OpenAI API usage, including token counts and associated costs.
"""

import logging
import threading
from typing import Dict, List, Optional
from datetime import datetime


class TokenTracker:
    """
    Singleton class to track OpenAI API token usage and costs.
    Thread-safe for parallel execution.
    """

    _instance = None
    _lock = threading.Lock()

    # OpenAI pricing as of January 2025 (USD per 1M tokens)
    # Source: https://openai.com/api/pricing/
    PRICING = {
        'gpt-4o': {
            'input': 2.50,   # $2.50 per 1M input tokens
            'output': 10.00  # $10.00 per 1M output tokens
        },
        'gpt-4o-mini': {
            'input': 0.150,  # $0.15 per 1M input tokens
            'output': 0.600  # $0.60 per 1M output tokens
        },
        # Fine-tuned models use base model pricing
        'gpt-4o-2024-08-06': {
            'input': 2.50,
            'output': 10.00
        },
        # Default pricing for unknown models (use gpt-4o pricing as conservative estimate)
        'default': {
            'input': 2.50,
            'output': 10.00
        }
    }

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(TokenTracker, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the tracker (only once)."""
        if self._initialized:
            return

        self._initialized = True
        self.calls: List[Dict] = []
        self.lock = threading.Lock()
        logging.debug("TokenTracker initialized")

    def track_usage(self, model: str, prompt_tokens: int, completion_tokens: int,
                   total_tokens: int, task_type: str = 'general'):
        """
        Track a single API call's token usage.

        Args:
            model (str): Model name used for the API call
            prompt_tokens (int): Number of input tokens
            completion_tokens (int): Number of output tokens
            total_tokens (int): Total tokens (prompt + completion)
            task_type (str): Type of task (for categorization)
        """
        with self.lock:
            call_data = {
                'timestamp': datetime.now(),
                'model': model,
                'task_type': task_type,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'cost_usd': self._calculate_cost(model, prompt_tokens, completion_tokens)
            }
            self.calls.append(call_data)

            logging.debug(
                f"Token usage tracked - Model: {model}, "
                f"Prompt: {prompt_tokens}, Completion: {completion_tokens}, "
                f"Total: {total_tokens}, Cost: ${call_data['cost_usd']:.4f}"
            )

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate cost for a single API call.

        Args:
            model (str): Model name
            prompt_tokens (int): Number of input tokens
            completion_tokens (int): Number of output tokens

        Returns:
            float: Cost in USD
        """
        # Get pricing for the model, use default if not found
        pricing = self.PRICING.get(model, self.PRICING['default'])

        # If model is a fine-tuned model (contains 'ft:'), extract base model
        if model.startswith('ft:'):
            # Fine-tuned models have format: ft:base-model-id:org:custom-name:id
            # Extract base model (usually gpt-4o-mini or gpt-4o)
            if 'gpt-4o-mini' in model:
                pricing = self.PRICING['gpt-4o-mini']
            elif 'gpt-4o' in model:
                pricing = self.PRICING['gpt-4o']
            else:
                pricing = self.PRICING['default']

        # Calculate cost (pricing is per 1M tokens)
        input_cost = (prompt_tokens / 1_000_000) * pricing['input']
        output_cost = (completion_tokens / 1_000_000) * pricing['output']

        return input_cost + output_cost

    def get_statistics(self) -> Dict:
        """
        Get comprehensive statistics about API usage.

        Returns:
            Dict: Statistics including totals, breakdown by model, and costs
        """
        with self.lock:
            if not self.calls:
                return {
                    'total_calls': 0,
                    'total_tokens': 0,
                    'total_prompt_tokens': 0,
                    'total_completion_tokens': 0,
                    'total_cost_usd': 0.0,
                    'by_model': {},
                    'by_task_type': {}
                }

            # Calculate totals
            total_calls = len(self.calls)
            total_tokens = sum(call['total_tokens'] for call in self.calls)
            total_prompt_tokens = sum(call['prompt_tokens'] for call in self.calls)
            total_completion_tokens = sum(call['completion_tokens'] for call in self.calls)
            total_cost = sum(call['cost_usd'] for call in self.calls)

            # Breakdown by model
            by_model = {}
            for call in self.calls:
                model = call['model']
                if model not in by_model:
                    by_model[model] = {
                        'calls': 0,
                        'prompt_tokens': 0,
                        'completion_tokens': 0,
                        'total_tokens': 0,
                        'cost_usd': 0.0
                    }

                by_model[model]['calls'] += 1
                by_model[model]['prompt_tokens'] += call['prompt_tokens']
                by_model[model]['completion_tokens'] += call['completion_tokens']
                by_model[model]['total_tokens'] += call['total_tokens']
                by_model[model]['cost_usd'] += call['cost_usd']

            # Breakdown by task type
            by_task_type = {}
            for call in self.calls:
                task_type = call['task_type']
                if task_type not in by_task_type:
                    by_task_type[task_type] = {
                        'calls': 0,
                        'prompt_tokens': 0,
                        'completion_tokens': 0,
                        'total_tokens': 0,
                        'cost_usd': 0.0
                    }

                by_task_type[task_type]['calls'] += 1
                by_task_type[task_type]['prompt_tokens'] += call['prompt_tokens']
                by_task_type[task_type]['completion_tokens'] += call['completion_tokens']
                by_task_type[task_type]['total_tokens'] += call['total_tokens']
                by_task_type[task_type]['cost_usd'] += call['cost_usd']

            return {
                'total_calls': total_calls,
                'total_tokens': total_tokens,
                'total_prompt_tokens': total_prompt_tokens,
                'total_completion_tokens': total_completion_tokens,
                'total_cost_usd': total_cost,
                'avg_tokens_per_call': total_tokens / total_calls if total_calls > 0 else 0,
                'by_model': by_model,
                'by_task_type': by_task_type
            }

    def print_statistics(self):
        """
        Print formatted statistics to console and log.
        """
        stats = self.get_statistics()

        if stats['total_calls'] == 0:
            logging.info("=" * 80)
            logging.info("AI TOKEN AND COST STATISTICS")
            logging.info("=" * 80)
            logging.info("No AI API calls were made during this execution.")
            logging.info("=" * 80)
            return

        # Print header
        logging.info("=" * 80)
        logging.info("AI TOKEN AND COST STATISTICS")
        logging.info("=" * 80)

        # Overall statistics
        logging.info(f"Total API calls:        {stats['total_calls']:,}")
        logging.info(f"Total tokens:           {stats['total_tokens']:,}")
        logging.info(f"  - Prompt tokens:      {stats['total_prompt_tokens']:,}")
        logging.info(f"  - Completion tokens:  {stats['total_completion_tokens']:,}")
        logging.info(f"Average tokens/call:    {stats['avg_tokens_per_call']:,.1f}")
        logging.info(f"Total cost (USD):       ${stats['total_cost_usd']:.4f}")

        # Breakdown by model
        if stats['by_model']:
            logging.info("-" * 80)
            logging.info("BREAKDOWN BY MODEL:")
            for model, model_stats in sorted(stats['by_model'].items()):
                logging.info(f"  {model}:")
                logging.info(f"    Calls:              {model_stats['calls']:,}")
                logging.info(f"    Total tokens:       {model_stats['total_tokens']:,}")
                logging.info(f"    Prompt tokens:      {model_stats['prompt_tokens']:,}")
                logging.info(f"    Completion tokens:  {model_stats['completion_tokens']:,}")
                logging.info(f"    Cost (USD):         ${model_stats['cost_usd']:.4f}")

        # Breakdown by task type
        if stats['by_task_type']:
            logging.info("-" * 80)
            logging.info("BREAKDOWN BY TASK TYPE:")
            for task_type, task_stats in sorted(stats['by_task_type'].items(),
                                               key=lambda x: x[1]['cost_usd'],
                                               reverse=True):
                logging.info(f"  {task_type}:")
                logging.info(f"    Calls:              {task_stats['calls']:,}")
                logging.info(f"    Total tokens:       {task_stats['total_tokens']:,}")
                logging.info(f"    Cost (USD):         ${task_stats['cost_usd']:.4f}")

        logging.info("=" * 80)

    def reset(self):
        """Reset all tracked data (useful for testing)."""
        with self.lock:
            self.calls = []
            logging.debug("TokenTracker statistics reset")


def get_tracker() -> TokenTracker:
    """
    Get the global TokenTracker instance.

    Returns:
        TokenTracker: The singleton instance
    """
    return TokenTracker()
