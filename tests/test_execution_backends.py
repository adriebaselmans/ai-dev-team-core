from __future__ import annotations

import subprocess
from types import SimpleNamespace
from typing import Any

from team_orchestrator.backends import (
    GitHubCopilotCLIExecutionBackend,
    OpenAIClientSettings,
    OpenAIResponsesExecutionBackend,
)
from team_orchestrator.execution import RoleExecutionRequest


def _request(*, role: str = "reviewer") -> RoleExecutionRequest:
    return RoleExecutionRequest(
        role=role,
        step_name="review",
        model={
            "provider": "openai",
            "backend": "openai_responses",
            "model": "gpt-5.4",
            "options": {"reasoning_effort": "medium"},
            "provider_options": {"verbosity": "medium", "store": False},
            "env": {},
        },
        prompt="You are the reviewer role.",
        prompt_hash="abc123",
        context={"summary": "Review the implementation."},
        tool_policy={
            "allow_local_read": True,
            "allow_local_write": False,
            "allow_shell": False,
            "allow_browser": False,
            "allow_external_research": False,
            "writable_paths": [],
            "notes": [],
        },
        output_schema={
            "type": "object",
            "properties": {
                "review": {
                    "type": "object",
                    "properties": {
                        "approved": {"type": "boolean"},
                    },
                    "required": ["approved"],
                    "additionalProperties": True,
                }
            },
            "required": ["review"],
            "additionalProperties": False,
        },
    )


def test_openai_backend_uses_responses_api_with_structured_output() -> None:
    calls: list[dict[str, Any]] = []

    class FakeResponses:
        def create(self, **kwargs: Any) -> Any:
            calls.append(kwargs)
            return SimpleNamespace(output_text='{"review":{"approved":true}}')

    client = SimpleNamespace(responses=FakeResponses())
    backend = OpenAIResponsesExecutionBackend(
        settings=OpenAIClientSettings(api_key="test-key"),
        client=client,
    )

    result = backend.invoke(_request())

    assert result == {"review": {"approved": True}}
    assert calls[0]["model"] == "gpt-5.4"
    assert calls[0]["text"]["format"]["type"] == "json_schema"
    assert calls[0]["text"]["verbosity"] == "medium"
    assert calls[0]["reasoning"] == {"effort": "medium"}
    assert calls[0]["store"] is False


def test_github_copilot_backend_builds_programmatic_command_and_parses_json() -> None:
    recorded: list[list[str]] = []

    def fake_runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        recorded.append(list(args[0]))
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout='{"review":{"approved":true}}',
            stderr="",
        )

    backend = GitHubCopilotCLIExecutionBackend(
        executable="copilot",
        options={
            "silent": True,
            "no_ask_user": True,
            "no_custom_instructions": True,
            "no_auto_update": True,
            "stream": "off",
            "output_format": "text",
        },
        runner=fake_runner,
    )
    request = _request()
    request.tool_policy["allow_local_write"] = True
    request.tool_policy["writable_paths"] = ["src/*.py"]
    request.tool_policy["allow_shell"] = True

    result = backend.invoke(request)

    assert result == {"review": {"approved": True}}
    command = recorded[0]
    assert command[0] == "copilot"
    assert "-p" in command
    assert "--model" in command
    assert "--stream=off" in command
    assert "--output-format=text" in command
    assert "-s" in command
    assert "--no-ask-user" in command
    assert "--no-custom-instructions" in command
    assert "--allow-tool=write(src/*.py)" in command
    assert "--allow-tool=shell" in command


def test_github_copilot_backend_repair_uses_follow_up_prompt() -> None:
    outputs = iter(
        [
            subprocess.CompletedProcess(
                args=["copilot"],
                returncode=0,
                stdout='{"broken":true}',
                stderr="",
            ),
            subprocess.CompletedProcess(
                args=["copilot"],
                returncode=0,
                stdout='{"review":{"approved":true}}',
                stderr="",
            ),
        ]
    )

    def fake_runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return next(outputs)

    backend = GitHubCopilotCLIExecutionBackend(runner=fake_runner)
    request = _request()

    first = backend.invoke(request)
    repaired = backend.repair(
        request,
        invalid_output=first,
        validation_errors=["'review' is a required property"],
    )

    assert first == {"broken": True}
    assert repaired == {"review": {"approved": True}}
