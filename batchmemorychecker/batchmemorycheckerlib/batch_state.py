"""Batch registry and per-batch state for memory checking."""
from __future__ import annotations

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
from uuid import uuid4

from batchmemorycheckerlib.constants import BATCH_REGISTRY_FILE, BATCH_STATE_DIR
from shared.file_operations import ensure_directory, read_json, write_json


def _utcnow_iso() -> str:
    return datetime.utcnow().isoformat()


def _normalize_path(path: str) -> str:
    return str(path).replace("\\", "/").strip()


class BatchRegistry:
    def __init__(self, registry_path: str = BATCH_REGISTRY_FILE, write_every: int = 1):
        self.registry_path = registry_path
        self._write_every = max(1, int(write_every))
        self._pending_writes = 0
        self.data = self._load_registry()

    def _load_registry(self) -> dict:
        data = read_json(self.registry_path, default={})
        data.setdefault("active_batches", {})
        data.setdefault("completed_batches", [])
        data.setdefault("file_registry", {})
        data.setdefault("memory_batches", {})
        return data

    def save(self, force: bool = False) -> None:
        self._pending_writes += 1
        if force or self._pending_writes >= self._write_every:
            write_json(self.registry_path, self.data)
            self._pending_writes = 0

    def flush(self) -> None:
        self.save(force=True)

    def create_batch(self, batch_type: str, batch_size_limit: int, memory_file: str) -> str:
        ensure_directory(BATCH_STATE_DIR)
        batch_id = f"batch_{uuid4().hex[:8]}"
        self.data["active_batches"][batch_id] = {
            "status": "collecting",
            "created_at": _utcnow_iso(),
            "batch_type": batch_type,
            "file_count": 0,
            "batch_size_limit": batch_size_limit,
            "openai_batch_id": None,
            "memory_file": memory_file
        }
        self.data.setdefault("memory_batches", {}).setdefault(memory_file, []).append(batch_id)
        self.save(force=True)
        return batch_id

    def get_active_batches(self, status: Optional[str] = None) -> Dict[str, dict]:
        batches = self.data.get("active_batches", {})
        if status is None:
            return batches
        return {bid: info for bid, info in batches.items() if info.get("status") == status}

    def set_batch_status(self, batch_id: str, status: str, **kwargs) -> None:
        batch = self.data["active_batches"].get(batch_id)
        if not batch:
            raise KeyError(f"Batch not found: {batch_id}")
        batch["status"] = status
        batch.update(kwargs)
        self.save(force=True)

    def increment_batch_file_count(self, batch_id: str) -> None:
        batch = self.data["active_batches"].get(batch_id)
        if not batch:
            raise KeyError(f"Batch not found: {batch_id}")
        batch["file_count"] = int(batch.get("file_count", 0)) + 1
        self.save()

    def register_record(self, record_id: str, batch_id: str) -> None:
        normalized = _normalize_path(record_id)
        existing = self.data.get("file_registry", {}).get(normalized)
        if existing and existing != batch_id:
            raise ValueError(f"Record already in active batch: {existing}")
        self.data["file_registry"][normalized] = batch_id
        self.save()

    def is_record_registered(self, record_id: str) -> bool:
        normalized = _normalize_path(record_id)
        return normalized in self.data.get("file_registry", {})

    def update_record_batch(self, record_id: str, batch_id: str) -> None:
        normalized = _normalize_path(record_id)
        self.data["file_registry"][normalized] = batch_id
        self.save()

    def unregister_records_for_batch(self, batch_id: str) -> None:
        registry = self.data.get("file_registry", {})
        to_remove = [path for path, bid in registry.items() if bid == batch_id]
        for path in to_remove:
            registry.pop(path, None)
        self.save()

    def complete_batch(self, batch_id: str) -> None:
        completed = {
            "batch_id": batch_id,
            "completed_at": _utcnow_iso()
        }
        self.data["completed_batches"].append(completed)
        self.data["active_batches"].pop(batch_id, None)
        self.unregister_records_for_batch(batch_id)
        self.save(force=True)

    def get_batch_dir(self, batch_id: str) -> str:
        return os.path.join(BATCH_STATE_DIR, "batches", batch_id)


class BatchState:
    def __init__(self, batch_id: str, batch_dir: str, write_every: int = 1):
        self.batch_id = batch_id
        self.batch_dir = batch_dir
        self._write_every = max(1, int(write_every))
        self._pending_writes = 0
        self.state_path = os.path.join(batch_dir, "state.json")
        self.results_path = os.path.join(batch_dir, "results.json")
        ensure_directory(batch_dir)
        self.state = self._load()

    def _load(self) -> dict:
        data = read_json(self.state_path, default={})
        if not data:
            data = {
                "batch_id": self.batch_id,
                "created_at": _utcnow_iso(),
                "records": []
            }
            write_json(self.state_path, data)
        return data

    def save(self, force: bool = False) -> None:
        self._pending_writes += 1
        if force or self._pending_writes >= self._write_every:
            write_json(self.state_path, self.state)
            self._save_results()
            self._pending_writes = 0

    def flush(self) -> None:
        self.save(force=True)

    def _save_results(self) -> None:
        results = {}
        for item in self.state.get("records", []):
            if item.get("result") is not None:
                results[item.get("custom_id")] = {
                    "record_id": item.get("record_id"),
                    "result": item.get("result")
                }
        write_json(self.results_path, results)

    def add_record(self, record_id: str, custom_id: str, payload: Dict[str, object],
                   status: str = "pending") -> None:
        if any(item["record_id"] == record_id for item in self.state["records"]):
            return
        entry = {
            "record_id": record_id,
            "custom_id": custom_id,
            "payload": payload,
            "status": status,
            "result": None,
            "error": None
        }
        self.state["records"].append(entry)
        self.save()

    def update_record(self, record_id: str, **kwargs) -> None:
        for item in self.state["records"]:
            if item["record_id"] == record_id:
                item.update(kwargs)
                break
        self.save()

    def update_record_by_custom_id(self, custom_id: str, **kwargs) -> None:
        for item in self.state["records"]:
            if item["custom_id"] == custom_id:
                item.update(kwargs)
                break
        self.save()

    def list_by_status(self, status: str) -> List[dict]:
        return [item for item in self.state.get("records", []) if item.get("status") == status]

    def all_records(self) -> List[dict]:
        return list(self.state.get("records", []))
