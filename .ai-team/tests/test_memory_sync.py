from __future__ import annotations

import json
from pathlib import Path

import yaml

from team_orchestrator.memory_sync import MemorySynchronizer


def _enable_memory(root: Path) -> None:
    metadata_path = root / ".ai-team" / "framework" / "init-metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps({"name": "memory-sync-test", "memory_persistence": True}) + "\n",
        encoding="utf-8",
    )


def test_explorer_sync_writes_repository_wiki_brief_facts_and_index(tmp_path: Path) -> None:
    _enable_memory(tmp_path)
    synchronizer = MemorySynchronizer(root=tmp_path)

    written = synchronizer.sync(
        {
            "repository": {"path": "C:/github/example-app"},
            "analysis": {
                "status": "ready",
                "insights": ["Uses a layered runtime layout."],
                "repository_roles": ["coordinator", "explorer"],
                "architecture": ["Uses a layered runtime layout."],
                "conventions": ["Uses role-bounded agent profiles."],
                "context": ["Python 3.12 is required."],
                "decisions": [],
                "incidents": ["Legacy path references can drift from wiki paths."],
            },
        },
        role_key="explorer",
        step_name="initial-exploration",
    )

    assert len(written) == 6
    brief_path = tmp_path / ".ai-team" / "memory" / "wiki" / "repositories" / "c-github-example-app" / "brief.md"
    facts_path = tmp_path / ".ai-team" / "memory" / "wiki" / "repositories" / "c-github-example-app" / "facts.yaml"
    index_path = tmp_path / ".ai-team" / "memory" / "wiki" / "repositories" / "_index.yaml"
    architecture_path = tmp_path / ".ai-team" / "memory" / "wiki" / "architecture" / "c-github-example-app-repository-architecture.md"
    conventions_path = tmp_path / ".ai-team" / "memory" / "wiki" / "conventions" / "c-github-example-app-repository-conventions.md"
    context_path = tmp_path / ".ai-team" / "memory" / "wiki" / "context" / "c-github-example-app-repository-context.md"
    incidents_path = tmp_path / ".ai-team" / "memory" / "wiki" / "incidents" / "c-github-example-app-repository-incidents.md"
    decisions_path = tmp_path / ".ai-team" / "memory" / "wiki" / "decisions" / "c-github-example-app-repository-decisions.md"
    changelog_dir = tmp_path / ".ai-team" / "memory" / "changelog"

    assert brief_path in written
    assert facts_path in written
    assert architecture_path in written
    assert conventions_path in written
    assert context_path in written
    assert incidents_path in written
    assert decisions_path not in written
    assert brief_path.exists()
    assert facts_path.exists()
    assert index_path.exists()
    assert list(changelog_dir.glob("*.yaml"))

    brief = brief_path.read_text(encoding="utf-8")
    assert "cat: repositories" in brief
    assert "by: explorer" in brief
    assert "Uses a layered runtime layout." in brief

    facts = yaml.safe_load(facts_path.read_text(encoding="utf-8"))
    assert facts["repository"]["path"] == "C:/github/example-app"
    assert facts["insights"] == ["Uses a layered runtime layout."]
    assert facts["categorized_findings"]["architecture"] == ["Uses a layered runtime layout."]

    assert architecture_path.exists()
    assert conventions_path.exists()
    assert context_path.exists()
    assert incidents_path.exists()
    assert not decisions_path.exists()
    assert "cat: architecture" in architecture_path.read_text(encoding="utf-8")
    assert "cat: conventions" in conventions_path.read_text(encoding="utf-8")
    assert "cat: context" in context_path.read_text(encoding="utf-8")
    assert "cat: incidents" in incidents_path.read_text(encoding="utf-8")

    index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    assert index["category"] == "repositories"
    assert index["pages"][0]["id"] == "c-github-example-app"


def test_explorer_sync_skips_when_memory_persistence_is_disabled(tmp_path: Path) -> None:
    synchronizer = MemorySynchronizer(root=tmp_path)

    written = synchronizer.sync(
        {
            "repository": {"path": "C:/github/example-app"},
            "analysis": {
                "status": "ready",
                "insights": [],
                "repository_roles": [],
                "architecture": ["Would be written only when memory is enabled."],
                "conventions": [],
                "context": [],
                "decisions": [],
                "incidents": [],
            },
        },
        role_key="explorer",
        step_name="initial-exploration",
    )

    assert written == []
    assert not (tmp_path / ".ai-team" / "memory" / "wiki" / "repositories").exists()
