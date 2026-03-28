from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parent


def metadata_path() -> Path:
    return REPO_ROOT / "framework" / "init-metadata.json"


def required_paths() -> list[Path]:
    return [
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "README.md",
        REPO_ROOT / "CHANGELOG.md",
        REPO_ROOT / "framework",
        REPO_ROOT / "framework" / "runtime",
        REPO_ROOT / "framework" / "roles",
        REPO_ROOT / ".github" / "skills",
        REPO_ROOT / "doc_templates",
        REPO_ROOT / "docs",
        REPO_ROOT / "src",
    ]


def active_artifact_paths() -> dict[str, dict[str, Path]]:
    return {
        "requirements": {
            "yaml": REPO_ROOT / "doc_templates" / "requirements" / "current.yaml",
        },
        "design": {
            "yaml": REPO_ROOT / "doc_templates" / "design" / "current.yaml",
        },
        "review": {
            "yaml": REPO_ROOT / "doc_templates" / "review" / "current.yaml",
        },
        "dod": {
            "yaml": REPO_ROOT / "doc_templates" / "dod" / "current.yaml",
        },
    }


def ensure_python_version() -> None:
    if sys.version_info < (3, 12):
        raise SystemExit("Python 3.12 or newer is required.")


def validate_structure() -> None:
    missing = [str(path.relative_to(REPO_ROOT)) for path in required_paths() if not path.exists()]
    if missing:
        raise SystemExit(f"Repository structure is incomplete: {', '.join(missing)}")


def install_dependencies() -> None:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", str(REPO_ROOT)],
        check=True,
    )


def prompt_value(label: str, preset: str | None) -> str:
    if preset:
        return preset
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("Value is required.")


def write_metadata(name: str, description: str, target_stack: str) -> Path:
    path = metadata_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": name,
        "description": description,
        "target_stack": target_stack,
        "repo_root": str(REPO_ROOT),
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _seed_if_blank(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8").strip():
        return False
    path.write_text(content, encoding="utf-8")
    return True


def _seed_artifacts(metadata: dict[str, str]) -> list[str]:
    seeds: dict[str, dict[str, Any]] = {
        "requirements": {
            "status": "Pending first feature request.",
            "title": metadata["name"],
            "user_need": metadata["description"],
            "goal": metadata["description"],
            "in_scope": [],
            "out_of_scope": [],
            "functional_requirements": [],
            "acceptance_criteria": [],
            "constraints": [f"Target stack: {metadata['target_stack']}"],
            "assumptions": ["Bootstrap metadata recorded by init.py."],
            "open_questions": [],
            "definition_of_ready": "Not ready.",
        },
        "design": {
            "title": metadata["name"],
            "design_goal": metadata["description"],
            "architecture_approach": [],
            "affected_areas": [],
            "separation_of_concerns": [],
            "module_boundaries": [],
            "data_flow": [],
            "interfaces": [],
            "technology_and_environment_considerations": [f"Target stack: {metadata['target_stack']}"],
            "clean_code_constraints": ["Follow framework/clean-code.md."],
            "performance_considerations": [],
            "risks_and_tradeoffs": [],
            "non_goals": [],
        },
        "review": {
            "status": "Pending implementation review.",
            "title": metadata["name"],
            "decision": "Not reviewed yet.",
            "findings": [],
            "residual_risks": [],
            "recommendation": "No recommendation yet.",
        },
        "dod": {
            "status": "Pending implementation validation.",
            "title": metadata["name"],
            "delivery_summary": [],
            "requirements_coverage": [],
            "what_was_built": [],
            "what_was_verified": [],
            "automated_regression_coverage": [],
            "acceptance_test_coverage": [],
            "known_gaps_or_risks": [],
            "decision": "Not accepted.",
            "user_feedback_needed": [],
        },
    }

    seeded: list[str] = []
    for name, payload in seeds.items():
        artifact_paths = active_artifact_paths()[name]
        yaml_content = yaml.safe_dump(payload, sort_keys=False)
        if _seed_if_blank(artifact_paths["yaml"], yaml_content):
            seeded.append(str(artifact_paths["yaml"].relative_to(REPO_ROOT)))
    return seeded


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap the ai-dev-team-core repository")
    parser.add_argument("--name", help="Project name to record in bootstrap metadata")
    parser.add_argument("--description", help="Project description to record in bootstrap metadata")
    parser.add_argument("--stack", help="Target stack to record in bootstrap metadata")
    parser.add_argument("--skip-install", action="store_true", help="Skip dependency installation")
    return parser


def main() -> int:
    ensure_python_version()
    parser = build_parser()
    args = parser.parse_args()

    validate_structure()

    if not args.skip_install:
        install_dependencies()

    name = prompt_value("Project name", args.name)
    description = prompt_value("Project description", args.description)
    target_stack = prompt_value("Target stack", args.stack)
    seeded_artifacts: list[str] = []
    seeded_artifacts.extend(
        _seed_artifacts(
            {
                "name": name,
                "description": description,
                "target_stack": target_stack,
            }
        )
    )
    metadata_path = write_metadata(name, description, target_stack)

    print(f"Validated repository structure at {REPO_ROOT}.")
    if seeded_artifacts:
        print(f"Seeded active artifacts: {', '.join(seeded_artifacts)}")
    print(f"Recorded bootstrap metadata in {metadata_path}.")
    print("Setup complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
