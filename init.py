from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent


def ai_team_root() -> Path:
    return REPO_ROOT / ".ai-team"


def metadata_path() -> Path:
    return ai_team_root() / "framework" / "init-metadata.json"


def required_paths() -> list[Path]:
    return [
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "README.md",
        REPO_ROOT / "CHANGELOG.md",
        ai_team_root() / "framework",
        ai_team_root() / "framework" / "runtime",
        ai_team_root() / "framework" / "roles",
        ai_team_root() / "context",
        ai_team_root() / "runtime",
        ai_team_root() / "memory",
        REPO_ROOT / ".github" / "skills",
        REPO_ROOT / "phase_artifacts",
        REPO_ROOT / "docs",
        REPO_ROOT / "src",
    ]


def active_artifact_paths() -> dict[str, dict[str, Path]]:
    return {
        "requirements": {
            "yaml": REPO_ROOT / "phase_artifacts" / "requirements" / "current.yaml",
        },
        "design": {
            "yaml": REPO_ROOT / "phase_artifacts" / "design" / "current.yaml",
        },
        "review": {
            "yaml": REPO_ROOT / "phase_artifacts" / "review" / "current.yaml",
        },
        "dod": {
            "yaml": REPO_ROOT / "phase_artifacts" / "dod" / "current.yaml",
        },
    }


def ensure_python_version() -> None:
    if sys.version_info < (3, 12):
        raise SystemExit("Python 3.12 or newer is required.")


def validate_version_consistency() -> str:
    version_file = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    pyproject_version = pyproject.get("project", {}).get("version")
    if version_file != pyproject_version:
        raise SystemExit(
            f"Version mismatch: VERSION has {version_file!r}, pyproject.toml has {pyproject_version!r}"
        )
    return version_file


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
        "artifact_persistence": True,
        "memory_persistence": True,
        "docs_export_on_release": True,
        "repo_root": str(REPO_ROOT),
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    written = json.loads(path.read_text(encoding="utf-8"))
    if written.get("name") != name or written.get("description") != description:
        raise SystemExit(f"Failed to verify bootstrap metadata at {path.relative_to(REPO_ROOT)}")
    return path


def _seed_if_blank(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8").strip():
        return False
    path.write_text(content, encoding="utf-8")
    return True


def _seed_artifacts(metadata: dict[str, str]) -> list[str]:
    from team_orchestrator.artifact_templates import blank_artifact_payloads

    seeds = blank_artifact_payloads()

    requirements = seeds["requirements"]
    requirements["status"] = "Pending first feature request."
    requirements["title"] = metadata["name"]
    requirements["user_need"] = metadata["description"]
    requirements["goal"] = metadata["description"]
    requirements["constraints"] = [f"Target stack: {metadata['target_stack']}"]
    requirements["assumptions"] = ["Bootstrap metadata recorded by init.py."]

    design = seeds["design"]
    design["title"] = metadata["name"]
    design["design_goal"] = metadata["description"]
    design["technology_and_environment_considerations"] = [
        f"Target stack: {metadata['target_stack']}"
    ]
    design["clean_code_constraints"] = ["Follow .ai-team/framework/clean-code.md."]

    review = seeds["review"]
    review["status"] = "Pending implementation review."
    review["title"] = metadata["name"]
    review["decision"] = "Not reviewed yet."
    review["recommendation"] = "No recommendation yet."

    dod = seeds["dod"]
    dod["status"] = "Pending implementation validation."
    dod["title"] = metadata["name"]
    dod["decision"] = "Not accepted."

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
    validate_version_consistency()

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
