from __future__ import annotations

from pathlib import Path

import pytest

from team_orchestrator.backends import BackendConfigurationError, BackendRegistry
from team_orchestrator.models import load_provider_map, load_role_model_map


def test_provider_map_includes_real_openai_and_github_copilot_backends() -> None:
    provider_map = load_provider_map()

    assert provider_map["openai"].backend == "openai_responses"
    assert provider_map["github-copilot"].backend == "github_copilot_cli"
    assert provider_map["openai"].env["api_key"] == "OPENAI_API_KEY"


def test_role_model_map_resolves_provider_backend_and_options() -> None:
    model_map = load_role_model_map()

    architect = model_map["architect"]
    assert architect.provider == "openai"
    assert architect.backend == "openai_responses"
    assert architect.provider_options["verbosity"] == "medium"
    assert architect.options["reasoning_effort"] == "medium"


def test_backend_registry_uses_provider_backend_factory(tmp_path: Path) -> None:
    config_path = tmp_path / "models.yaml"
    config_path.write_text(
        "\n".join(
            [
                "version: 1",
                "providers:",
                "  github-copilot:",
                "    backend: github_copilot_cli",
                "    options:",
                "      executable: copilot",
                "roles:",
                "  scout:",
                "    provider: github-copilot",
                "    model: github-copilot-gpt-5",
            ]
        ),
        encoding="utf-8",
    )

    providers = load_provider_map(config_path)
    roles = load_role_model_map(config_path)
    registry = BackendRegistry(providers=providers)

    backend = registry.create_for_role(roles["scout"])

    assert backend.__class__.__name__ == "GitHubCopilotCLIExecutionBackend"


def test_backend_registry_rejects_unknown_backend() -> None:
    class DummyProvider:
        name = "bad"
        backend = "missing"
        options = {}
        env = {}

    class DummyRole:
        provider = "bad"
        role = "scout"
        model = "unused"
        options = {}

    registry = BackendRegistry(providers={"bad": DummyProvider()})  # type: ignore[arg-type]

    with pytest.raises(BackendConfigurationError):
        registry.create_for_role(DummyRole())  # type: ignore[arg-type]
