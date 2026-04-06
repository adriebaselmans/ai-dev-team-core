from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class DiscoveredRole:
    key: str
    display_name: str
    description: str
    source: str
    role_doc_path: Path | None = None


ROLE_DISPLAY_OVERRIDES = {
    "explorer": "Repository Exploration Support",
}


def discover_roles(repo_root: Path | None = None) -> list[DiscoveredRole]:
    root = repo_root or Path(__file__).resolve().parents[2]
    team_spec_path = root / ".ai-team" / "framework" / "runtime" / "team.yaml"
    roles_dir = root / ".ai-team" / "framework" / "roles"
    with team_spec_path.open("r", encoding="utf-8") as handle:
        team_spec = yaml.safe_load(handle) or {}

    ordered_keys: list[str] = []
    for role_key in (team_spec.get("roles") or {}).keys():
        ordered_keys.append(str(role_key))
    for role_path in sorted(roles_dir.glob("*.md")):
        if role_path.stem not in ordered_keys:
            ordered_keys.append(role_path.stem)

    discovered: list[DiscoveredRole] = []
    for key in ordered_keys:
        role_doc_path = roles_dir / f"{key}.md"
        display_name, description = _read_role_doc(role_doc_path, key)
        source = ".ai-team/framework/runtime/team.yaml"
        if role_doc_path.exists():
            source += " + .ai-team/framework/roles"
        discovered.append(
            DiscoveredRole(
                key=key,
                display_name=display_name,
                description=description,
                source=source,
                role_doc_path=role_doc_path if role_doc_path.exists() else None,
            )
        )
    return discovered


def _read_role_doc(path: Path, key: str) -> tuple[str, str]:
    if not path.exists():
        return ROLE_DISPLAY_OVERRIDES.get(key, key.replace("-", " ").title()), ""

    title = ROLE_DISPLAY_OVERRIDES.get(key)
    mission_lines: list[str] = []
    current_section: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            if current_section == "mission" and mission_lines:
                break
            continue
        if line.startswith("# "):
            title = title or line.removeprefix("# ").strip()
            continue
        if line.startswith("## "):
            current_section = line.removeprefix("## ").strip().lower()
            continue
        if current_section == "mission":
            mission_lines.append(line)
    return title or key.replace("-", " ").title(), " ".join(mission_lines)
