from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re

from spec_loader import repo_root


@dataclass
class ValidationResult:
    valid: bool
    messages: list[str]


PLACEHOLDERS = {
    "TBD",
    "Pending first feature request.",
    "Not ready.",
    "Not reviewed yet.",
    "Not evaluated yet.",
    "No delivery yet.",
    "Nothing yet.",
    "No recommendation yet.",
    "No active feature yet.",
}


def _read(rel_path: str) -> str:
    return (repo_root() / rel_path).read_text(encoding="utf-8")


def _sections(markdown: str) -> dict[str, str]:
    parts = re.split(r"^##\s+", markdown, flags=re.MULTILINE)
    result: dict[str, str] = {}
    for part in parts[1:]:
        lines = part.splitlines()
        if not lines:
            continue
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        result[title] = body
    return result


def _is_populated(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    stripped = text.replace("- ", "").strip()
    return stripped not in PLACEHOLDERS


def validate_requirements() -> ValidationResult:
    sections = _sections(_read("docs/requirements/current.md"))
    required = [
        "Title",
        "User Need",
        "Goal",
        "In Scope",
        "Out of Scope",
        "Functional Requirements",
        "Acceptance Criteria",
        "Definition of Ready",
    ]
    messages = [name for name in required if not _is_populated(sections.get(name, ""))]
    dor = sections.get("Definition of Ready", "").lower()
    if "ready" not in dor or "not ready" in dor:
        messages.append("Definition of Ready does not indicate readiness.")
    return ValidationResult(not messages, messages or ["Requirements are ready."])


def validate_design() -> ValidationResult:
    sections = _sections(_read("docs/design/current.md"))
    required = [
        "Title",
        "Design Goal",
        "Architecture Approach",
        "Affected Areas",
        "Separation of Concerns",
        "Module Boundaries and Responsibilities",
        "Data Flow and State Handling",
        "Interfaces and Contracts",
        "Technology and Environment Considerations",
        "Non-Goals",
    ]
    messages = [name for name in required if not _is_populated(sections.get(name, ""))]
    return ValidationResult(not messages, messages or ["Design is implementation-safe."])


def validate_development() -> ValidationResult:
    src_dir = repo_root() / "src"
    files = [path for path in src_dir.rglob("*") if path.is_file() and path.name != ".gitkeep"]
    tests = [
        path
        for path in files
        if any(token in path.name.lower() for token in ("test", "spec"))
    ]
    messages: list[str] = []
    if not files:
        messages.append("No implementation files found in src/.")
    if not tests:
        messages.append("No obvious unit test files found in src/.")
    return ValidationResult(not messages, messages or ["Development outputs look present."])


def validate_review() -> ValidationResult:
    sections = _sections(_read("docs/review/current.md"))
    required = ["Decision", "Findings", "Recommendation"]
    messages = [name for name in required if not _is_populated(sections.get(name, ""))]
    decision = sections.get("Decision", "")
    if "Approved for testing" not in decision and "Rework required" not in decision:
        messages.append("Review decision must be 'Approved for testing' or 'Rework required'.")
    return ValidationResult(not messages, messages or ["Review artifact is complete."])


def validate_dod() -> ValidationResult:
    sections = _sections(_read("docs/dod/current.md"))
    required = [
        "Delivery Summary",
        "Requirements Coverage",
        "What Was Built",
        "What Was Verified",
        "Definition of Done Decision",
    ]
    messages = [name for name in required if not _is_populated(sections.get(name, ""))]
    decision = sections.get("Definition of Done Decision", "")
    if "Accepted for user review" not in decision and "Not accepted" not in decision:
        messages.append("DoD decision must be 'Accepted for user review' or 'Not accepted'.")
    return ValidationResult(not messages, messages or ["DoD artifact is complete."])


def validate_status_sync() -> ValidationResult:
    state = json.loads(_read("framework/runtime/state.json"))
    status = _sections(_read("framework/flows/current-status.md").replace("# Current Status", "## Current Status", 1))
    status_body = status.get("Current Status", "")
    messages: list[str] = []
    expected_pairs = {
        "Phase": state.get("phase"),
        "Owner": state.get("owner"),
        "State": state.get("state"),
        "Next action": state.get("next_action"),
    }
    for label, value in expected_pairs.items():
        needle = f"- {label}: {value}"
        if needle not in status_body:
            messages.append(f"Status markdown mismatch for {label}.")
    return ValidationResult(not messages, messages or ["Status markdown and runtime state are in sync."])


def validate_phase(phase: str) -> ValidationResult:
    if phase == "requirements":
        return validate_requirements()
    if phase == "architecture":
        return validate_design()
    if phase == "development":
        return validate_development()
    if phase == "review":
        return validate_review()
    if phase == "testing":
        return validate_dod()
    if phase in {"idle", "dod-review", "done"}:
        return ValidationResult(True, [f"No artifact validator required for phase '{phase}'."])
    return ValidationResult(False, [f"Unknown phase: {phase}"])
