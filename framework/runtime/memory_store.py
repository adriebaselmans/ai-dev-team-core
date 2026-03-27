from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from spec_loader import repo_root


def memory_root() -> Path:
    return repo_root() / "framework" / "memory"


def logs_root() -> Path:
    path = memory_root() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def timestamp_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_memory_record(
    *,
    kind: str,
    phase: str,
    summary: str,
    payload: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    artifact_refs: list[str] | None = None,
    supersedes: str | None = None,
) -> Path:
    record = {
        "entry_id": uuid4().hex,
        "timestamp_utc": timestamp_utc(),
        "version": 1,
        "kind": kind,
        "phase": phase,
        "tags": tags or [],
        "summary": summary,
        "artifact_refs": artifact_refs or [],
        "payload": payload or {},
    }
    if supersedes:
        record["supersedes"] = supersedes
    file_name = f"{record['timestamp_utc'].replace(':', '').replace('-', '')}-{record['entry_id']}.json"
    path = logs_root() / file_name
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return path


def retrieve_memory(
    *,
    phase: str | None = None,
    kind: str | None = None,
    tags: set[str] | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in sorted(logs_root().glob("*.json"), reverse=True):
        entry = json.loads(path.read_text(encoding="utf-8"))
        if phase and entry.get("phase") != phase:
            continue
        if kind and entry.get("kind") != kind:
            continue
        if tags and not tags.issubset(set(entry.get("tags", []))):
            continue
        entries.append(entry)
        if len(entries) >= limit:
            break
    return entries


def latest_brief() -> dict[str, Any] | None:
    entries = retrieve_memory(kind="phase-brief", limit=1)
    return entries[0] if entries else None
