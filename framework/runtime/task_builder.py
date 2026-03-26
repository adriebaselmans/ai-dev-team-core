from __future__ import annotations

from pathlib import Path

from spec_loader import phase_spec, repo_root


TASK_TEMPLATE_PATH = repo_root() / "framework" / "runtime" / "task-template.md"


PHASE_OBJECTIVES = {
    "requirements": "Produce an implementation-ready requirements baseline.",
    "architecture": "Produce an implementation-safe design for the current requirements baseline.",
    "development": "Implement the approved design and add supporting unit tests.",
    "review": "Review the implementation and produce a clear technical review decision.",
    "testing": "Validate the implementation and produce the current Definition of Done record.",
}


PHASE_COMPLETION = {
    "requirements": "docs/requirements/current.md is updated and the Definition of Ready is ready.",
    "architecture": "docs/design/current.md is updated and clear enough for development to proceed without guessing.",
    "development": "src/ contains the intended implementation and relevant unit tests, with lint issues addressed where practical.",
    "review": "docs/review/current.md is updated with a clear decision and findings.",
    "testing": "docs/dod/current.md is updated with a clear decision and verification details.",
}


def _role_file(role: str) -> str:
    return f"framework/roles/{role}.md"


def _normalize_skill_path(path: str) -> str:
    if path.endswith(".md"):
        return path
    return f"{path}/SKILL.md"


def _skill_file(role_spec: dict[str, object]) -> list[str]:
    files: list[str] = []
    primary = role_spec.get("primary_skill")
    if isinstance(primary, str):
        files.append(_normalize_skill_path(primary))
    for item in role_spec.get("supporting_skills", []):
        if isinstance(item, str):
            files.append(_normalize_skill_path(item))
    return files


def build_task_payload(phase: str, team_spec: dict, workflow_spec: dict, active_feature: str | None) -> str:
    p_spec = phase_spec(phase)
    owner = p_spec["owner"]
    role_spec = team_spec["roles"][owner]
    owned_outputs = p_spec.get("required_outputs", role_spec.get("writes", []))
    inputs = list(p_spec.get("required_inputs", []))
    inputs.append(_role_file(owner))
    inputs.extend(_skill_file(role_spec))
    deduped_inputs = list(dict.fromkeys(inputs))

    template = TASK_TEMPLATE_PATH.read_text(encoding="utf-8")
    payload = template
    payload = payload.replace("`<role-name>`", f"`{owner}`")
    payload = payload.replace("`<bounded task objective>`", f"`{PHASE_OBJECTIVES.get(phase, 'Complete the assigned phase work.')}`")
    payload = payload.replace(
        "- `<artifact or files this subagent owns>`",
        "\n".join(f"- `{item}`" for item in owned_outputs) or "- `None`",
    )
    payload = payload.replace(
        "- `<required docs, code areas, memory, and role/skill files>`",
        "\n".join(f"- `{item}`" for item in deduped_inputs),
    )
    payload = payload.replace(
        "- `<what must be true for the task to be complete>`",
        f"- {PHASE_COMPLETION.get(phase, 'Phase outputs are complete and validated.')}",
    )

    header = [
        f"Feature: `{active_feature or 'unspecified'}`",
        f"Phase: `{phase}`",
    ]
    return "\n".join(header) + "\n\n" + payload
