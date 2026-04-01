from __future__ import annotations

from typing import Any, Callable


class TraceLogger:
    def __init__(self, emit: Callable[[str], None] | None = None) -> None:
        self._emit = emit
        self.lines: list[str] = []

    def log(self, role: str, update: dict[str, Any]) -> str:
        line = format_trace_line(role, update)
        self.lines.append(line)
        if self._emit is not None:
            self._emit(line)
        return line


def format_trace_line(role: str, update: dict[str, Any]) -> str:
    label = role.upper()
    details: list[str] = []
    if "review" in update:
        review = update["review"]
        details.append(f"approved={review.get('approved')}")
        details.append(f"score={review.get('score')}")
    elif "test_results" in update:
        test_results = update["test_results"]
        details.append(f"passed={test_results.get('passed')}")
        errors = test_results.get("errors") or []
        if errors:
            details.append(f"errors={len(errors)}")
    elif "dod_review" in update:
        dod_review = update["dod_review"]
        details.append(f"approved={dod_review.get('approved')}")
        findings = dod_review.get("blocking_findings") or []
        if findings:
            details.append(f"findings={len(findings)}")
    elif "support_request" in update and update["support_request"]:
        request = update["support_request"]
        details.append(f"support={request.get('support_role')}")
        details.append(f"requester={request.get('requested_by')}")
    else:
        field_name, payload = next(iter(update.items()), ("status", {}))
        if isinstance(payload, dict):
            if "status" in payload:
                details.append(f"status={payload.get('status')}")
            if "ready" in payload:
                details.append(f"ready={payload.get('ready')}")
            if "revision" in payload:
                details.append(f"revision={payload.get('revision')}")
            if field_name == "coordination":
                details.append(f"mode={payload.get('repo_mode')}")
                details.append(f"parallel={payload.get('parallel_development')}")
        else:
            details.append(f"value={payload}")
    if not details:
        details.append("updated")
    return f"[{label}] {' '.join(details)}"
