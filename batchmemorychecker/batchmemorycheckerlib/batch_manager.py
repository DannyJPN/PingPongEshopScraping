"""Batch orchestration for memory validation."""
from __future__ import annotations

import csv
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

from shared.ai_module import Message, create_from_model_key
from tqdm import tqdm
from shared.config import get_config
from shared.file_operations import read_json, write_json, ensure_directory

from batchmemorycheckerlib.batch_prompts import build_memory_prompt
from batchmemorycheckerlib.batch_lock import BatchLock
from batchmemorycheckerlib.batch_state import BatchRegistry, BatchState
from batchmemorycheckerlib.constants import (
    DEFAULT_LANGUAGE,
    DEFAULT_BATCH_MAX_MB,
    DEFAULT_BATCH_MAX_RECORDS,
    DEFAULT_BATCH_POLL_INTERVAL,
    DEFAULT_MAX_POLL_ITERATIONS,
    DEFAULT_MODEL_KEY,
    DEFAULT_REGISTRY_WRITE_EVERY,
    DEFAULT_STATE_WRITE_EVERY,
    STATUS_COLLECTING,
    STATUS_READY,
    STATUS_SENT,
    STATUS_COMPLETED,
    STATUS_ERROR,
    BATCH_COST_LOG,
    BATCH_LOCK_FILE,
    VARIANT_NAME_PREFIX,
    VARIANT_VALUE_PREFIX,
    REPORTS_DIR
)
from batchmemorycheckerlib.memory_loader import list_memory_files, iter_memory_entries, get_memory_row_count
from batchmemorycheckerlib.result_loader import (
    build_latest_record_index,
    load_latest_result_records,
    get_latest_outputs_summary,
    normalize_key
)


def _create_batch_provider(model_key: str):
    config = get_config()
    provider, model = model_key.split("/", 1)
    model_config = config.get_ai_model_config(provider, model)
    if not model_config:
        raise RuntimeError("No valid AI model configuration found for batch mode.")

    kwargs = {}
    api_key = model_config.get("api_key")
    endpoint = model_config.get("endpoint")
    if api_key:
        kwargs["api_key"] = api_key
    if endpoint:
        kwargs["base_url"] = endpoint

    provider_instance = create_from_model_key(model_key, **kwargs)
    if not provider_instance.supports_batch():
        raise RuntimeError(f"Model does not support batch processing: {model_key}")
    return provider_instance


def _build_custom_id(memory_file: str, row_index: int, batch_id: str) -> str:
    base = os.path.basename(memory_file)
    stem = base.replace(".csv", "")
    return f"{stem}_{row_index}_{batch_id}"


def _build_record_id(memory_file: str, row_index: int) -> str:
    base = os.path.basename(memory_file)
    stem = base.replace(".csv", "")
    return os.path.join(stem, str(row_index))


def _estimate_request_size(prompt: str, custom_id: str, model_name: str) -> int:
    body = {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
    }
    payload = json.dumps(body, ensure_ascii=False)
    return len(payload.encode("utf-8")) + 1


def _serialize_reason(value: object) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]


def _parse_result_payload(text: str) -> Dict[str, object]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {
            "is_correct": "no",
            "correct_value": "",
            "reason": ["invalid_json"],
            "source": "provided_data"
        }

    if not isinstance(parsed, dict):
        return {
            "is_correct": "no",
            "correct_value": "",
            "reason": ["invalid_payload"],
            "source": "provided_data"
        }

    parsed["reason"] = _serialize_reason(parsed.get("reason"))
    return parsed


def _to_json_safe(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_json_safe(item) for item in value]
    return value


def _build_payload(memory_file: str, entry: Dict[str, object], product_context: Dict[str, object]) -> Dict[str, object]:
    safe_context = _to_json_safe(product_context)
    return {
        "memory_file": memory_file,
        "key": entry.get("key"),
        "value": entry.get("value"),
        "row_index": entry.get("row_index"),
        "product_context": safe_context
    }


def _build_messages(payload: Dict[str, object]) -> List[Message]:
    prompt = build_memory_prompt(payload)
    return [Message.user_text(prompt)]


def _is_variant_memory(memory_file: str) -> bool:
    base = os.path.basename(memory_file)
    return base.startswith(VARIANT_NAME_PREFIX) or base.startswith(VARIANT_VALUE_PREFIX)


def _chunk_memory_entries(memory_file: str,
                          entries: Iterable[Dict[str, object]],
                          record_index: Dict[str, Dict[str, object]],
                          provider_model: str,
                          max_records: int,
                          max_bytes: int,
                          registry: BatchRegistry,
                          missing_keys: List[Dict[str, object]],
                          total_rows: int | None = None) -> List[Tuple[str, BatchState]]:
    batch_states: List[Tuple[str, BatchState]] = []

    batch_id = None
    batch_state = None
    current_count = 0
    current_bytes = 0
    batch_limit = max(1, max_records)

    is_variant_memory = _is_variant_memory(memory_file)
    total_seen = 0
    total_added = 0
    total_missing = 0

    progress_total = total_rows if total_rows and total_rows > 0 else None
    for entry in tqdm(entries, desc=f"Collecting {os.path.basename(memory_file)}", unit="rows", total=progress_total):
        total_seen += 1
        row_index = int(entry.get("row_index", 0))
        record_id = _build_record_id(memory_file, row_index)
        if registry.is_record_registered(record_id):
            continue

        key = str(entry.get("key", ""))
        if not key:
            logging.warning("Skipping empty key in %s row %d", memory_file, row_index)
            continue
        normalized_key = normalize_key(key)
        product_context = record_index.get(normalized_key)
        if not product_context and not is_variant_memory:
            total_missing += 1
            logging.warning("Missing result record for key '%s' (%s row %d)", key, memory_file, row_index)
            missing_keys.append({
                "memory_file": os.path.basename(memory_file),
                "row_index": row_index,
                "key": key
            })
            continue
        if not product_context:
            product_context = {}

        payload = _build_payload(memory_file, entry, product_context)

        if batch_state is None:
            batch_id = registry.create_batch("memory", batch_limit, memory_file)
            batch_state = BatchState(
                batch_id,
                registry.get_batch_dir(batch_id),
                write_every=DEFAULT_STATE_WRITE_EVERY
            )
            batch_states.append((batch_id, batch_state))
            current_count = 0
            current_bytes = 0

        custom_id = _build_custom_id(memory_file, row_index, batch_id)
        prompt = build_memory_prompt(payload)
        request_bytes = _estimate_request_size(prompt, custom_id, provider_model)

        if current_count > 0 and (current_count + 1 > max_records or current_bytes + request_bytes > max_bytes):
            registry.set_batch_status(batch_id, STATUS_READY)
            batch_state.flush()
            batch_id = registry.create_batch("memory", batch_limit, memory_file)
            batch_state = BatchState(
                batch_id,
                registry.get_batch_dir(batch_id),
                write_every=DEFAULT_STATE_WRITE_EVERY
            )
            batch_states.append((batch_id, batch_state))
            current_count = 0
            current_bytes = 0
            custom_id = _build_custom_id(memory_file, row_index, batch_id)

        batch_state.add_record(record_id, custom_id, payload, status=STATUS_COLLECTING)
        batch_state.update_record(record_id, status=STATUS_READY)
        registry.register_record(record_id, batch_id)
        registry.increment_batch_file_count(batch_id)

        current_count += 1
        current_bytes += request_bytes
        total_added += 1

    if batch_state:
        registry.set_batch_status(batch_id, STATUS_READY)
        batch_state.flush()

    logging.info(
        "Memory file summary: %s total=%d added=%d missing_result=%d",
        os.path.basename(memory_file),
        total_seen,
        total_added,
        total_missing
    )

    registry.flush()

    return batch_states


def _send_ready_batches(registry: BatchRegistry, model_key: str) -> None:
    provider = _create_batch_provider(model_key)
    ready_batches = list(registry.get_active_batches(status=STATUS_READY).items())
    if not ready_batches:
        logging.info("No ready batches to send")
        return

    for batch_id, info in tqdm(ready_batches, desc="Sending batches", unit="batch"):
        batch_state = BatchState(batch_id, registry.get_batch_dir(batch_id))
        records = batch_state.list_by_status(STATUS_READY)
        if not records:
            registry.set_batch_status(batch_id, STATUS_ERROR, error="empty_batch")
            continue

        messages_list = []
        custom_ids = []
        for record in records:
            payload = record.get("payload", {})
            messages_list.append(_build_messages(payload))
            custom_ids.append(record.get("custom_id"))

        try:
            batch_job = provider.create_batch_job(messages_list, custom_ids)
            registry.set_batch_status(
                batch_id,
                STATUS_SENT,
                openai_batch_id=batch_job.job_id,
                sent_at=datetime.utcnow().isoformat()
            )
            for record in records:
                batch_state.update_record(record.get("record_id"), status=STATUS_SENT)
            logging.info(
                "Batch sent: %s records=%d memory_file=%s openai_id=%s",
                batch_id,
                len(records),
                info.get("memory_file"),
                batch_job.job_id
            )
        except Exception as exc:
            logging.error("Failed to send batch %s: %s", batch_id, exc)
            registry.set_batch_status(batch_id, STATUS_ERROR, error=str(exc))


def _process_batch_results(batch_state: BatchState, results: List[object]) -> List[str]:
    missing = []
    completed_count = 0
    error_count = 0
    for response in results:
        custom_id = response.metadata.get("custom_id") if hasattr(response, "metadata") else None
        if not custom_id:
            error_count += 1
            continue
        try:
            payload = _parse_result_payload(response.content)
        except Exception as exc:
            batch_state.update_record_by_custom_id(custom_id, status=STATUS_ERROR, error=str(exc))
            error_count += 1
            continue
        batch_state.update_record_by_custom_id(custom_id, status=STATUS_COMPLETED, result=payload)
        completed_count += 1

    result_ids = {item.get("custom_id") for item in batch_state.list_by_status(STATUS_COMPLETED)}
    for item in batch_state.all_records():
        if item.get("status") == STATUS_SENT and item.get("custom_id") not in result_ids:
            batch_state.update_record(item.get("record_id"), status=STATUS_ERROR, error="missing_result")
            missing.append(item.get("custom_id"))
            error_count += 1
    logging.info(
        "Batch results processed: %s completed=%d errors=%d missing=%d",
        batch_state.batch_id,
        completed_count,
        error_count,
        len(missing)
    )
    return missing


def _retrieve_completed_batches(registry: BatchRegistry, model_key: str) -> None:
    provider = _create_batch_provider(model_key)
    sent_batches = list(registry.get_active_batches(status=STATUS_SENT).items())
    if not sent_batches:
        logging.info("No sent batches to check for completion")
        return

    batch_jobs: Dict[str, object] = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {}
        for batch_id, info in sent_batches:
            openai_batch_id = info.get("openai_batch_id")
            if not openai_batch_id:
                continue
            future_map[executor.submit(provider.get_batch_job, openai_batch_id)] = batch_id

        for future in tqdm(as_completed(future_map), total=len(future_map), desc="Retrieving batches", unit="batch"):
            batch_id = future_map[future]
            try:
                batch_jobs[batch_id] = future.result()
            except Exception as exc:
                logging.error("Failed to retrieve batch %s: %s", batch_id, exc)

    for batch_id, batch_job in batch_jobs.items():
        status = batch_job.status
        if status not in ["completed", "failed", "cancelled", "expired"]:
            continue
        if status != "completed":
            registry.set_batch_status(batch_id, STATUS_ERROR, error=status)
            continue
        batch_state = BatchState(batch_id, registry.get_batch_dir(batch_id))
        _process_batch_results(batch_state, batch_job.results or [])
        _log_batch_cost(batch_id, provider, batch_job)
        registry.complete_batch(batch_id)


def _log_batch_cost(batch_id: str, provider, batch_job) -> None:
    cost_log = read_json(BATCH_COST_LOG, default={})
    total_cost = 0.0
    for response in batch_job.results or []:
        usage = response.usage if hasattr(response, "usage") else {}
        if hasattr(provider, "estimate_cost"):
            total_cost += provider.estimate_cost(usage)
        elif hasattr(provider, "_calculate_cost"):
            total_cost += provider._calculate_cost(usage)
    entry = cost_log.get(batch_id, {})
    entry["total_cost"] = round(total_cost, 6)
    entry["model"] = getattr(provider, "model_name", "")
    entry["completed_at"] = datetime.utcnow().isoformat()
    cost_log[batch_id] = entry
    write_json(BATCH_COST_LOG, cost_log)


def run_batch_mode(memory_dir: str,
                   results_dir: str,
                   language: str = DEFAULT_LANGUAGE,
                   model_key: str = DEFAULT_MODEL_KEY,
                   max_records: int = DEFAULT_BATCH_MAX_RECORDS,
                   max_batch_mb: int = DEFAULT_BATCH_MAX_MB,
                   poll_interval: int = DEFAULT_BATCH_POLL_INTERVAL,
                   wait_timeout: int = DEFAULT_MAX_POLL_ITERATIONS,
                   memory_files: Optional[List[str]] = None) -> None:
    with BatchLock(BATCH_LOCK_FILE):
        registry = BatchRegistry(write_every=DEFAULT_REGISTRY_WRITE_EVERY)

        records = load_latest_result_records(results_dir, memory_dir, language)
        record_index = build_latest_record_index(records)
        logging.info("Loaded result records: %d unique keys", len(record_index))

        outputs_summary = get_latest_outputs_summary(results_dir, memory_dir, language)
        _write_latest_outputs_report(outputs_summary)

        provider = _create_batch_provider(model_key)
        provider_model = provider.model_name

        memory_files = list_memory_files(memory_dir, allowed_files=memory_files)
        if not memory_files:
            logging.warning("No memory files found in %s", memory_dir)
            return

        logging.info("Memory files selected: %d", len(memory_files))

        max_bytes = max_batch_mb * 1024 * 1024
        missing_keys: List[Dict[str, object]] = []

        for memory_file in memory_files:
            entries = iter_memory_entries(memory_file)
            total_rows = get_memory_row_count(memory_file)
            _chunk_memory_entries(
                memory_file,
                entries,
                record_index,
                provider_model,
                max_records,
                max_bytes,
                registry,
                missing_keys,
                total_rows=total_rows
            )

        _write_missing_keys_report(missing_keys)

        _send_ready_batches(registry, model_key)
        _log_batch_status_summary(registry)

        if wait_timeout == 0:
            logging.info("Batch wait disabled")
            return

        poll_count = 0
        while True:
            sent_batches = registry.get_active_batches(status=STATUS_SENT)
            if not sent_batches:
                logging.info("All sent batches have been retrieved")
                break
            _retrieve_completed_batches(registry, model_key)
            _log_batch_status_summary(registry)
            _log_waiting_batches(registry)
            with tqdm(total=poll_interval, desc="Waiting for batch responses", unit="s") as wait_bar:
                time.sleep(poll_interval)
                wait_bar.update(poll_interval)
            poll_count += 1
            if poll_count >= wait_timeout:
                logging.warning("Max poll iterations reached (%d).", wait_timeout)
                break


def _log_batch_status_summary(registry: BatchRegistry) -> None:
    status_counts: Dict[str, int] = {}
    for info in registry.get_active_batches().values():
        status = info.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    if status_counts:
        summary = ", ".join(f"{key}={value}" for key, value in sorted(status_counts.items()))
        logging.info("Active batches: %s", summary)


def _log_waiting_batches(registry: BatchRegistry) -> None:
    sent_batches = registry.get_active_batches(status=STATUS_SENT)
    if not sent_batches:
        return
    now = datetime.utcnow()
    for batch_id, info in sent_batches.items():
        openai_batch_id = info.get("openai_batch_id")
        sent_at = info.get("sent_at")
        wait_desc = "unknown"
        if sent_at:
            try:
                sent_dt = datetime.fromisoformat(sent_at)
                wait_seconds = max(0, int((now - sent_dt).total_seconds()))
                wait_desc = f"{wait_seconds}s"
            except ValueError:
                wait_desc = "unknown"
        logging.info("Waiting on batch %s (openai_id=%s) for %s", batch_id, openai_batch_id, wait_desc)


def _write_latest_outputs_report(summary: List[Dict[str, object]]) -> None:
    ensure_directory(REPORTS_DIR)
    json_path = os.path.join(REPORTS_DIR, "latest_outputs_report.json")
    csv_path = os.path.join(REPORTS_DIR, "latest_outputs_report.csv")
    write_json(json_path, summary)
    _write_csv(csv_path, summary, ["eshop", "status", "latest_dir", "csv_path", "json_path", "source_date"])
    logging.info("Latest outputs report saved: %s", json_path)


def _write_missing_keys_report(missing_keys: List[Dict[str, object]]) -> None:
    if not missing_keys:
        logging.info("No missing keys detected")
        return
    ensure_directory(REPORTS_DIR)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(REPORTS_DIR, f"missing_keys_{timestamp}.csv")
    _write_csv(csv_path, missing_keys, ["memory_file", "row_index", "key"])
    logging.info("Missing keys report saved: %s", csv_path)


def _write_csv(path: str, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=",", quotechar='"')
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def check_batch_statuses() -> List[str]:
    registry = BatchRegistry()
    lines = []
    for batch_id, info in registry.get_active_batches().items():
        status = info.get("status", "unknown")
        openai_batch_id = info.get("openai_batch_id")
        if openai_batch_id:
            status = f"{status} (openai_id={openai_batch_id})"
        lines.append(f"{batch_id}: {status}")
    if not lines:
        lines.append("No active batches.")
    return lines
