from __future__ import annotations

from pathlib import Path

import yaml

from team_orchestrator.context_status import ContextPaths, build_context_doctor


def test_context_profiles_cover_active_flow_roles() -> None:
    root = Path(__file__).resolve().parents[2]
    profile_path = root / ".ai-team" / "context" / "policy.yaml"
    flow_path = root / ".ai-team" / "flows" / "software_delivery.yaml"

    profiles = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    flow = yaml.safe_load(flow_path.read_text(encoding="utf-8"))

    profile_roles = {value["role"] for value in profiles["profiles"].values()}
    flow_roles = {
        step["agent"]
        for step in flow["steps"].values()
        if isinstance(step, dict) and step.get("kind") in {"agent", "parallel-agent"}
    }
    flow_roles.add("explorer")

    assert flow_roles.issubset(profile_roles)


def test_context_profiles_are_phase_scoped_and_budgeted() -> None:
    root = Path(__file__).resolve().parents[2]
    profile_path = root / ".ai-team" / "context" / "policy.yaml"
    profiles = yaml.safe_load(profile_path.read_text(encoding="utf-8"))

    assert profiles["defaults"]["wiki_entrypoint"] == ".ai-team/memory/wiki/_index.yaml"
    assert profiles["defaults"]["cache_policy"]["committed_cache_allowed"] is False

    for name, profile in profiles["profiles"].items():
        assert profile["role"]
        assert isinstance(profile["wiki_categories"], list), name
        assert isinstance(profile["skills"], list), name
        assert profile["token_budget"]["context"] > 0, name
        assert profile["token_budget"]["output"] > 0, name
        assert profile["output"], name


def test_context_policy_defines_safe_output_classes() -> None:
    root = Path(__file__).resolve().parents[2]
    profile_path = root / ".ai-team" / "context" / "policy.yaml"
    policy = yaml.safe_load(profile_path.read_text(encoding="utf-8"))

    output_policy = policy["output_policy"]
    assert output_policy["default_mode"] == "compact"
    assert "formal_artifact" in output_policy["never_compress"]
    assert "safety_warning" in output_policy["never_compress"]
    assert output_policy["classes"]["formal_artifact"]["allowed_adapters"] == []
    assert output_policy["classes"]["safety_warning"]["allowed_adapters"] == []


def test_context_adapters_define_modes_detection_and_fallbacks() -> None:
    root = Path(__file__).resolve().parents[2]
    adapters_path = root / ".ai-team" / "context" / "adapters.yaml"
    adapters_config = yaml.safe_load(adapters_path.read_text(encoding="utf-8"))

    valid_modes = set(adapters_config["modes"])
    adapters = adapters_config["adapters"]
    assert {"rtk", "caveman", "headroom", "serena", "memory-index"}.issubset(adapters)

    for name, adapter in adapters.items():
        assert adapter["mode"] in valid_modes, name
        assert adapter["kind"], name
        assert adapter.get("fallback") or adapter.get("optional") is False, name


def test_skeleton_wiki_contains_only_indexes_and_schema() -> None:
    root = Path(__file__).resolve().parents[2]
    wiki_root = root / ".ai-team" / "memory" / "wiki"

    markdown_pages = [path for path in wiki_root.rglob("*.md") if path.name != "README.md"]
    assert markdown_pages == []

    assert (wiki_root / "_index.yaml").exists()
    assert (wiki_root / "_schema.yaml").exists()


def test_obsolete_paths_and_provider_names_are_absent() -> None:
    root = Path(__file__).resolve().parents[2]
    forbidden_terms = ["doc" + "_templates", ".ai-team/framework/" + "memory", "Co" + "dex"]
    checked_suffixes = {".md", ".yaml", ".yml", ".py", ".json", ".toml", ".ps1"}

    for path in root.rglob("*"):
        if ".git" in path.parts or path.is_dir() or path.suffix not in checked_suffixes:
            continue
        text = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            assert term not in text, f"{term!r} found in {path.relative_to(root)}"


def test_context_doctor_reports_invalid_yaml_without_crashing(tmp_path: Path) -> None:
    context_dir = tmp_path / ".ai-team" / "context"
    context_dir.mkdir(parents=True)
    policy_path = context_dir / "policy.yaml"
    adapters_path = context_dir / "adapters.yaml"
    policy_path.write_text("version: 1\nprofiles: {}\nmemory_policy: {}\n", encoding="utf-8")
    adapters_path.write_text("adapters:\n  bad: value: nope\n", encoding="utf-8")

    result = build_context_doctor(
        ContextPaths(root=tmp_path, context_dir=context_dir, policy_path=policy_path, adapters_path=adapters_path)
    )

    assert result["passed"] is False
    assert any("Adapter config validation failed" in error for error in result["errors"])