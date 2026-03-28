from __future__ import annotations

from dataclasses import dataclass
import json

from artifacts import load_artifact, validate_artifact_data
from spec_loader import repo_root, transition_spec


@dataclass
class ValidationResult:
    valid: bool
    messages: list[str]


REPOSITORY_BRIEF_REQUIRED_SECTIONS = [
    "Repository Identity",
    "Purpose",
    "Stack and Tooling",
    "Top-Level Architecture",
    "Key Directories and Entry Points",
    "Important Flows for Current Work",
    "Conventions and Constraints",
    "Build, Test, and Run Commands",
    "Risks and Extension Points",
    "Open Questions",
]


REPOSITORY_FACTS_REQUIRED_KEYS = ["name", "source", "last_updated", "open_questions"]


def _sections(markdown: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    for line in markdown.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = ""
            continue
        if current is None:
            continue
        sections[current] += (line + "\n")
    return {key: value.strip() for key, value in sections.items()}


def _validation_result(messages: list[str], success_message: str) -> ValidationResult:
    return ValidationResult(not messages, messages or [success_message])


def validate_requirements() -> ValidationResult:
    messages = validate_artifact_data("requirements", load_artifact("requirements"))
    if load_artifact("requirements").get("definition_of_ready") != "Ready.":
        messages.append("Definition of Ready must be 'Ready.'.")
    return _validation_result(messages, "Requirements are ready.")


def validate_design() -> ValidationResult:
    messages = validate_artifact_data("design", load_artifact("design"))
    return _validation_result(messages, "Design is implementation-safe.")


def validate_development() -> ValidationResult:
    required_paths = [
        repo_root() / "framework" / "config" / "models.yaml",
        repo_root() / "framework" / "runtime" / "context_slices.yaml",
        repo_root() / "framework" / "runtime" / "execution.py",
        repo_root() / "framework" / "runtime" / "context_slicer.py",
        repo_root() / "framework" / "runtime" / "compaction.py",
        repo_root() / "framework" / "runtime" / "tests",
    ]
    messages = [f"Missing required development output: {path.relative_to(repo_root())}" for path in required_paths if not path.exists()]
    return _validation_result(messages, "Development outputs are present.")


def validate_review() -> ValidationResult:
    messages = validate_artifact_data("review", load_artifact("review"))
    decision = load_artifact("review").get("decision")
    if decision not in {"Approved for testing.", "Rework required.", "Not reviewed yet."}:
        messages.append("Review decision must be approved, rework required, or pending review.")
    return _validation_result(messages, "Review artifact is complete.")


def validate_dod() -> ValidationResult:
    messages = validate_artifact_data("dod", load_artifact("dod"))
    decision = load_artifact("dod").get("decision")
    if decision not in {"Accepted for user review.", "Not accepted."}:
        messages.append("Definition of Done decision must be accepted or not accepted.")
    return _validation_result(messages, "DoD artifact is complete.")


def validate_repository_knowledge_store() -> ValidationResult:
    base_dir = repo_root() / "framework" / "memory" / "repository-knowledge"
    messages: list[str] = []
    if not base_dir.exists():
        return ValidationResult(False, ["Repository knowledge store is missing."])

    required_root_files = ["README.md", "TEMPLATE.md", "index.md"]
    for file_name in required_root_files:
        if not (base_dir / file_name).exists():
            messages.append(f"Repository knowledge store is missing {file_name}.")

    index_path = base_dir / "index.md"
    if index_path.exists() and "## Entries" not in index_path.read_text(encoding="utf-8"):
        messages.append("Repository knowledge index is missing the Entries section.")

    for repo_dir in sorted(path for path in base_dir.iterdir() if path.is_dir()):
        brief_path = repo_dir / "brief.md"
        facts_path = repo_dir / "facts.json"
        if not brief_path.exists():
            messages.append(f"{repo_dir.name} is missing brief.md.")
            continue
        if not facts_path.exists():
            messages.append(f"{repo_dir.name} is missing facts.json.")
            continue

        brief_sections = _sections(brief_path.read_text(encoding="utf-8"))
        for section in REPOSITORY_BRIEF_REQUIRED_SECTIONS:
            if not brief_sections.get(section):
                messages.append(f"{repo_dir.name} brief is missing {section}.")

        try:
            facts = json.loads(facts_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            messages.append(f"{repo_dir.name} facts.json is invalid JSON: {exc.msg}.")
            continue

        for key in REPOSITORY_FACTS_REQUIRED_KEYS:
            value = facts.get(key)
            if key == "open_questions" and isinstance(value, list):
                continue
            if not isinstance(value, str) or not value.strip():
                messages.append(f"{repo_dir.name} facts.json is missing '{key}'.")

    return _validation_result(messages, "Repository knowledge store is valid.")


def validate_transition(trigger: str, current_phase: str) -> ValidationResult:
    transition = transition_spec(trigger)
    messages: list[str] = []
    if transition["from"] != current_phase:
        messages.append(
            f"Transition '{trigger}' cannot start from '{current_phase}'. Expected '{transition['from']}'."
        )
    for validator_name in transition.get("validators", []):
        result = _run_named_validator(validator_name)
        if not result.valid:
            messages.extend(result.messages)
    return _validation_result(messages, f"Transition '{trigger}' is valid.")


def _run_named_validator(name: str) -> ValidationResult:
    if name == "requirements_artifact_ready":
        return validate_requirements()
    if name == "design_artifact_ready":
        return validate_design()
    if name == "development_outputs_present":
        return validate_development()
    if name == "review_approved":
        decision = load_artifact("review").get("decision")
        messages = [] if decision == "Approved for testing." else ["Review artifact is not approved for testing."]
        return _validation_result(messages, "Review is approved.")
    if name == "review_rework_required":
        decision = load_artifact("review").get("decision")
        messages = [] if decision == "Rework required." else ["Review artifact does not request rework."]
        return _validation_result(messages, "Review requires rework.")
    if name == "dod_ready_for_user_review":
        result = validate_dod()
        if result.valid and load_artifact("dod").get("decision") != "Accepted for user review.":
            return ValidationResult(False, ["DoD artifact is not accepted for user review."])
        return result
    return ValidationResult(False, [f"Unknown validator: {name}"])


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
