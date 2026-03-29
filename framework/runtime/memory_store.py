from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from spec_loader import repo_root


MEMORY_SCHEMA_VERSION = 3
DEFAULT_SCOPE = "project"
DEFAULT_SOURCE = "runtime"
DEFAULT_CONFIDENCE = "medium"
DEFAULT_STATUS = "active"
VALID_RECORD_KINDS = {"fact", "decision", "question", "contradiction", "phase-brief"}
VALID_RECORD_STATUSES = {"active", "superseded", "resolved"}
VALID_CONFIDENCE_LEVELS = {"low", "medium", "high"}


@dataclass(frozen=True)
class MemoryRecord:
    entry_id: str
    timestamp_utc: str
    version: int
    kind: str
    phase: str
    scope: str
    subject: str | None
    source: str
    confidence: str
    status: str
    tags: list[str]
    summary: str
    artifact_refs: list[str]
    payload: dict[str, Any]
    supersedes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.supersedes is None:
            payload.pop("supersedes", None)
        if self.subject is None:
            payload.pop("subject", None)
        return payload


def memory_root() -> Path:
    return repo_root() / "framework" / "memory"


def records_root(*, create: bool = True) -> Path:
    path = memory_root() / "records"
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def legacy_records_root() -> Path:
    return memory_root() / "logs"


def timestamp_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def append_memory_record(
    *,
    kind: str,
    phase: str,
    summary: str,
    payload: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    artifact_refs: list[str] | None = None,
    supersedes: str | None = None,
    scope: str = DEFAULT_SCOPE,
    subject: str | None = None,
    source: str = DEFAULT_SOURCE,
    confidence: str = DEFAULT_CONFIDENCE,
    status: str = DEFAULT_STATUS,
) -> Path:
    record = _build_record(
        entry_id=uuid4().hex,
        timestamp=timestamp_utc(),
        kind=kind,
        phase=phase,
        scope=scope,
        subject=subject,
        source=source,
        confidence=confidence,
        status=status,
        tags=tags,
        summary=summary,
        artifact_refs=artifact_refs,
        payload=payload,
        supersedes=supersedes,
    )
    if record.supersedes:
        _ensure_supersedes_target_exists(record.supersedes)

    file_name = f"{record.timestamp_utc.replace(':', '').replace('-', '')}-{record.entry_id}.json"
    path = records_root() / file_name
    path.write_text(json.dumps(record.as_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def query_memory(
    *,
    phase: str | None = None,
    kind: str | Iterable[str] | None = None,
    scope: str | Iterable[str] | None = None,
    tags: Iterable[str] | None = None,
    subject: str | None = None,
    limit: int = 10,
    active_only: bool = True,
    include_superseded: bool = False,
    source: str | Iterable[str] | None = None,
    status: str | Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    if limit <= 0:
        return []

    entries = _load_records()
    kind_filter = _normalize_filter(kind)
    scope_filter = _normalize_filter(scope)
    tag_filter = _normalize_filter(tags)
    source_filter = _normalize_filter(source)
    status_filter = _normalize_filter(status)
    superseded_ids = _superseded_entry_ids(entries)

    results: list[dict[str, Any]] = []
    for entry in sorted(entries, key=_record_sort_key, reverse=True):
        if phase is not None and entry.get("phase") != phase:
            continue
        if kind_filter is not None and entry.get("kind") not in kind_filter:
            continue
        if scope_filter is not None and entry.get("scope") not in scope_filter:
            continue
        if subject is not None and entry.get("subject") != subject:
            continue
        if source_filter is not None and entry.get("source") not in source_filter:
            continue
        if status_filter is not None and entry.get("status") not in status_filter:
            continue
        if tag_filter is not None and not tag_filter.issubset(set(entry.get("tags", []))):
            continue
        if active_only and entry.get("status") != DEFAULT_STATUS:
            continue
        if not include_superseded and entry.get("status") == "superseded":
            continue
        if not include_superseded and _is_superseded(entry, superseded_ids):
            continue
        results.append(entry)
        if len(results) >= limit:
            break
    return results


def retrieve_memory(
    *,
    phase: str | None = None,
    kind: str | None = None,
    tags: set[str] | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    return query_memory(phase=phase, kind=kind, tags=tags, limit=limit)


def latest_brief(*, phase: str | None = None, subject: str | None = None, scope: str | None = None) -> dict[str, Any] | None:
    entries = query_memory(kind="phase-brief", phase=phase, subject=subject, scope=scope, limit=1)
    return entries[0] if entries else None


def _load_records() -> list[dict[str, Any]]:
    entries_by_id: dict[str, dict[str, Any]] = {}
    for path in _record_paths():
        record = _load_record(path)
        entries_by_id[record["entry_id"]] = record
    return list(entries_by_id.values())


def _record_paths() -> list[Path]:
    paths: list[Path] = []
    for root in (legacy_records_root(), records_root(create=False)):
        if not root.exists():
            continue
        paths.extend(sorted(root.glob("*.json")))
    return paths


def _load_record(path: Path) -> dict[str, Any]:
    try:
        entry = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid memory record {path}: {exc.msg}.") from exc
    if not isinstance(entry, dict):
        raise ValueError(f"Memory record {path} must contain a mapping.")
    return _normalize_loaded_record(entry, path).as_dict()


def _normalize_loaded_record(entry: dict[str, Any], path: Path) -> MemoryRecord:
    entry_id = _required_text(entry.get("entry_id"), f"Memory record {path} is missing 'entry_id'.")
    timestamp = _required_text(entry.get("timestamp_utc"), f"Memory record {path} is missing 'timestamp_utc'.")
    kind = _required_text(entry.get("kind"), f"Memory record {path} is missing 'kind'.")
    phase = _required_text(entry.get("phase"), f"Memory record {path} is missing 'phase'.")
    summary = _required_text(entry.get("summary"), f"Memory record {path} is missing 'summary'.")
    version = int(entry.get("version", 1))
    return _build_record(
        entry_id=entry_id,
        timestamp=timestamp,
        kind=kind,
        phase=phase,
        scope=_clean_optional_text(entry.get("scope")) or DEFAULT_SCOPE,
        subject=_clean_optional_text(entry.get("subject")),
        source=_clean_optional_text(entry.get("source")) or DEFAULT_SOURCE,
        confidence=_clean_optional_text(entry.get("confidence")) or DEFAULT_CONFIDENCE,
        status=_clean_optional_text(entry.get("status")) or DEFAULT_STATUS,
        tags=entry.get("tags"),
        summary=summary,
        artifact_refs=entry.get("artifact_refs"),
        payload=entry.get("payload"),
        supersedes=_clean_optional_text(entry.get("supersedes")),
        version=version,
    )


def _build_record(
    *,
    entry_id: str,
    timestamp: str,
    kind: str,
    phase: str,
    scope: str,
    subject: str | None,
    source: str,
    confidence: str,
    status: str,
    tags: Iterable[str] | None,
    summary: str,
    artifact_refs: Iterable[str] | None,
    payload: Any,
    supersedes: str | None,
    version: int = MEMORY_SCHEMA_VERSION,
) -> MemoryRecord:
    clean_kind = _required_text(kind, "Memory record kind must not be empty.")
    if clean_kind not in VALID_RECORD_KINDS:
        raise ValueError(f"Unsupported memory record kind '{clean_kind}'.")

    clean_phase = _required_text(phase, "Memory record phase must not be empty.")
    clean_summary = _required_text(summary, "Memory record summary must not be empty.")
    clean_scope = _required_text(scope, "Memory record scope must not be empty.")
    clean_source = _required_text(source, "Memory record source must not be empty.")
    clean_confidence = _required_text(confidence, "Memory record confidence must not be empty.")
    clean_status = _required_text(status, "Memory record status must not be empty.")
    if clean_confidence not in VALID_CONFIDENCE_LEVELS:
        raise ValueError(f"Unsupported memory confidence '{clean_confidence}'.")
    if clean_status not in VALID_RECORD_STATUSES:
        raise ValueError(f"Unsupported memory record status '{clean_status}'.")
    if payload is None:
        clean_payload: dict[str, Any] = {}
    elif isinstance(payload, dict):
        clean_payload = payload
    else:
        raise ValueError("Memory record payload must be a mapping.")

    return MemoryRecord(
        entry_id=_required_text(entry_id, "Memory record entry_id must not be empty."),
        timestamp_utc=_required_text(timestamp, "Memory record timestamp_utc must not be empty."),
        version=version,
        kind=clean_kind,
        phase=clean_phase,
        scope=clean_scope,
        subject=_clean_optional_text(subject),
        source=clean_source,
        confidence=clean_confidence,
        status=clean_status,
        tags=_clean_text_list(tags),
        summary=clean_summary,
        artifact_refs=_clean_text_list(artifact_refs),
        payload=clean_payload,
        supersedes=_clean_optional_text(supersedes),
    )


def _record_sort_key(entry: dict[str, Any]) -> tuple[str, str]:
    return (str(entry.get("timestamp_utc", "")), str(entry.get("entry_id", "")))


def _normalize_filter(value: str | Iterable[str] | None) -> set[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return {cleaned} if cleaned else set()
    cleaned_values = {str(item).strip() for item in value if str(item).strip()}
    return cleaned_values if cleaned_values else set()


def _clean_text_list(values: Iterable[str] | None) -> list[str]:
    if values is None:
        return []
    return [str(item).strip() for item in values if str(item).strip()]


def _clean_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned if cleaned else None


def _required_text(value: Any, message: str) -> str:
    cleaned = _clean_optional_text(value)
    if cleaned is None:
        raise ValueError(message)
    return cleaned


def _superseded_entry_ids(entries: list[dict[str, Any]]) -> set[str]:
    superseded_ids: set[str] = set()
    for entry in entries:
        supersedes = entry.get("supersedes")
        if isinstance(supersedes, str) and supersedes.strip():
            superseded_ids.add(supersedes.strip())
    return superseded_ids


def _is_superseded(entry: dict[str, Any], superseded_ids: set[str]) -> bool:
    entry_id = entry.get("entry_id")
    return isinstance(entry_id, str) and entry_id in superseded_ids


def _ensure_supersedes_target_exists(entry_id: str) -> None:
    if any(record.get("entry_id") == entry_id for record in _load_records()):
        return
    raise ValueError(f"Memory record supersedes unknown entry '{entry_id}'.")
