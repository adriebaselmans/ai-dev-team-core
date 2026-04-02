from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from team_orchestrator.models import ProviderConfig, RoleModelConfig, load_provider_map, repo_root

if TYPE_CHECKING:
    from team_orchestrator.execution import RoleExecutionRequest


class BackendConfigurationError(RuntimeError):
    """Raised when a configured backend cannot be constructed or used."""


class MockExecutionBackend:
    def invoke(self, request: "RoleExecutionRequest") -> dict[str, Any]:
        raise BackendConfigurationError(
            f"Role '{request.role}' is assigned to the mock backend. "
            "Provide an explicit execution backend or update framework/config/models.yaml."
        )


@dataclass(frozen=True)
class OpenAIClientSettings:
    api_key: str | None = None
    base_url: str | None = None
    organization: str | None = None
    project: str | None = None


class OpenAIResponsesExecutionBackend:
    def __init__(
        self,
        *,
        settings: OpenAIClientSettings | None = None,
        options: dict[str, Any] | None = None,
        client: Any | None = None,
        client_factory: Callable[[OpenAIClientSettings], Any] | None = None,
    ) -> None:
        self.settings = settings or OpenAIClientSettings()
        self.options = dict(options or {})
        self._client = client
        self._client_factory = client_factory

    def invoke(self, request: "RoleExecutionRequest") -> dict[str, Any]:
        client = self._get_client()
        response = client.responses.create(**self._request_payload(request))
        return self._parse_response_json(response)

    def repair(
        self,
        request: "RoleExecutionRequest",
        *,
        invalid_output: dict[str, Any],
        validation_errors: list[str],
    ) -> dict[str, Any] | None:
        client = self._get_client()
        response = client.responses.create(
            **self._request_payload(
                request,
                user_message=self._render_repair_message(
                    request=request,
                    invalid_output=invalid_output,
                    validation_errors=validation_errors,
                ),
            )
        )
        return self._parse_response_json(response)

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        client_factory = self._client_factory or self._default_client_factory
        self._client = client_factory(self.settings)
        return self._client

    def _default_client_factory(self, settings: OpenAIClientSettings) -> Any:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise BackendConfigurationError(
                "OpenAI backend requires the 'openai' package. Install it before using the "
                "openai_responses backend."
            ) from exc

        kwargs = {
            key: value
            for key, value in {
                "api_key": settings.api_key,
                "base_url": settings.base_url,
                "organization": settings.organization,
                "project": settings.project,
            }.items()
            if value
        }
        return OpenAI(**kwargs)

    def _request_payload(
        self,
        request: "RoleExecutionRequest",
        *,
        user_message: str | None = None,
    ) -> dict[str, Any]:
        text_options: dict[str, Any] = {
            "format": {
                "type": "json_schema",
                "name": self._schema_name(request),
                "schema": request.output_schema,
                "strict": True,
            }
        }
        verbosity = self._option(request, "verbosity")
        if verbosity:
            text_options["verbosity"] = verbosity

        payload: dict[str, Any] = {
            "model": request.model["model"],
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": request.prompt}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_message or self._render_user_message(request),
                        }
                    ],
                },
            ],
            "text": text_options,
            "store": bool(self._option(request, "store", False)),
        }
        reasoning_effort = self._option(request, "reasoning_effort")
        if reasoning_effort:
            payload["reasoning"] = {"effort": reasoning_effort}
        return payload

    def _option(self, request: "RoleExecutionRequest", key: str, default: Any = None) -> Any:
        role_options = request.model.get("options", {}) or {}
        provider_options = request.model.get("provider_options", {}) or {}
        if key in role_options:
            return role_options[key]
        if key in provider_options:
            return provider_options[key]
        if key in self.options:
            return self.options[key]
        return default

    def _schema_name(self, request: "RoleExecutionRequest") -> str:
        return f"{request.role.replace('-', '_')}_{request.step_name.replace('-', '_')}"

    def _render_user_message(self, request: "RoleExecutionRequest") -> str:
        return (
            "Execute the assigned role task using the provided context and tool policy.\n"
            "Return only a JSON object that satisfies the supplied schema.\n\n"
            f"Role: {request.role}\n"
            f"Step: {request.step_name}\n"
            f"Tool policy:\n{json.dumps(request.tool_policy, indent=2, sort_keys=True)}\n\n"
            f"Context:\n{json.dumps(request.context, indent=2, sort_keys=True)}"
        )

    def _render_repair_message(
        self,
        *,
        request: "RoleExecutionRequest",
        invalid_output: dict[str, Any],
        validation_errors: list[str],
    ) -> str:
        return (
            "Repair the previous response so it satisfies the required JSON schema.\n"
            "Return only the corrected JSON object.\n\n"
            f"Role: {request.role}\n"
            f"Step: {request.step_name}\n"
            f"Validation errors:\n{json.dumps(validation_errors, indent=2)}\n\n"
            f"Previous output:\n{json.dumps(invalid_output, indent=2, sort_keys=True)}"
        )

    def _parse_response_json(self, response: Any) -> dict[str, Any]:
        payload_text = self._extract_output_text(response)
        try:
            data = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise BackendConfigurationError(
                "OpenAI backend did not return valid JSON text for the structured response."
            ) from exc
        if not isinstance(data, dict):
            raise BackendConfigurationError(
                f"OpenAI backend returned {type(data).__name__}; expected a JSON object."
            )
        return data

    def _extract_output_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text.strip():
            return output_text
        if isinstance(response, dict):
            output_text = response.get("output_text")
            if isinstance(output_text, str) and output_text.strip():
                return output_text
            output = response.get("output", [])
        else:
            output = getattr(response, "output", [])
        for item in output or []:
            item_type = getattr(item, "type", None)
            content = getattr(item, "content", None)
            if isinstance(item, dict):
                item_type = item.get("type")
                content = item.get("content")
            if item_type != "message" or not isinstance(content, list):
                continue
            parts: list[str] = []
            for chunk in content:
                chunk_type = getattr(chunk, "type", None)
                chunk_text = getattr(chunk, "text", None)
                if isinstance(chunk, dict):
                    chunk_type = chunk.get("type")
                    chunk_text = chunk.get("text")
                if chunk_type == "output_text" and isinstance(chunk_text, str):
                    parts.append(chunk_text)
            if parts:
                return "".join(parts)
        raise BackendConfigurationError("OpenAI backend response did not contain output_text.")


class GitHubCopilotCLIExecutionBackend:
    def __init__(
        self,
        *,
        executable: str = "copilot",
        options: dict[str, Any] | None = None,
        runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
        cwd: str | Path | None = None,
    ) -> None:
        self.executable = executable
        self.options = dict(options or {})
        self.runner = runner or subprocess.run
        self.cwd = Path(cwd) if cwd is not None else repo_root()

    def invoke(self, request: "RoleExecutionRequest") -> dict[str, Any]:
        completed = self.runner(
            self._build_command(request=request, prompt=self._render_prompt(request)),
            cwd=str(self.cwd),
            text=True,
            capture_output=True,
            check=False,
        )
        return self._parse_output(completed)

    def repair(
        self,
        request: "RoleExecutionRequest",
        *,
        invalid_output: dict[str, Any],
        validation_errors: list[str],
    ) -> dict[str, Any] | None:
        prompt = (
            "Repair the previous response so it satisfies the required JSON schema.\n"
            "Return only the corrected JSON object with no code fences.\n\n"
            f"Validation errors:\n{json.dumps(validation_errors, indent=2)}\n\n"
            f"Previous output:\n{json.dumps(invalid_output, indent=2, sort_keys=True)}"
        )
        completed = self.runner(
            self._build_command(request=request, prompt=prompt),
            cwd=str(self.cwd),
            text=True,
            capture_output=True,
            check=False,
        )
        return self._parse_output(completed)

    def _build_command(self, *, request: "RoleExecutionRequest", prompt: str) -> list[str]:
        command = [self.executable, "-p", prompt]
        model_name = request.model.get("model")
        if model_name:
            command.extend(["--model", str(model_name)])
        stream = self._option("stream")
        if stream:
            command.append(f"--stream={stream}")
        output_format = self._option("output_format")
        if output_format:
            command.append(f"--output-format={output_format}")
        if bool(self._option("silent", True)):
            command.append("-s")
        if bool(self._option("no_ask_user", True)):
            command.append("--no-ask-user")
        if bool(self._option("no_custom_instructions", True)):
            command.append("--no-custom-instructions")
        if bool(self._option("no_auto_update", True)):
            command.append("--no-auto-update")
        for allowance in self._tool_allowances(request):
            command.append(f"--allow-tool={allowance}")
        return command

    def _tool_allowances(self, request: "RoleExecutionRequest") -> list[str]:
        allowances: list[str] = []
        policy = request.tool_policy
        if policy.get("allow_local_write"):
            writable_paths = policy.get("writable_paths") or []
            if writable_paths:
                allowances.extend(f"write({path})" for path in writable_paths)
            else:
                allowances.append("write")
        if policy.get("allow_shell"):
            allowances.append("shell")
        if policy.get("allow_external_research") or policy.get("allow_browser"):
            allowances.append("url")
        return allowances

    def _option(self, key: str, default: Any = None) -> Any:
        return self.options.get(key, default)

    def _render_prompt(self, request: "RoleExecutionRequest") -> str:
        return (
            f"{request.prompt}\n\n"
            "Execute the assigned role task using the context below.\n"
            "Return only a JSON object that satisfies the required schema. "
            "Do not wrap the JSON in code fences.\n\n"
            f"Role: {request.role}\n"
            f"Step: {request.step_name}\n"
            f"Tool policy: {json.dumps(request.tool_policy, sort_keys=True)}\n"
            f"Required schema: {json.dumps(request.output_schema, sort_keys=True)}\n"
            f"Context: {json.dumps(request.context, sort_keys=True)}"
        )

    def _parse_output(self, completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
        if completed.returncode != 0:
            stderr = (completed.stderr or completed.stdout or "").strip()
            raise BackendConfigurationError(
                f"GitHub Copilot CLI exited with code {completed.returncode}: {stderr}"
            )
        stdout = (completed.stdout or "").strip()
        if not stdout:
            raise BackendConfigurationError("GitHub Copilot CLI produced no output.")
        candidate_lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        attempts = [stdout]
        if candidate_lines:
            attempts.append(candidate_lines[-1])
        for candidate in attempts:
            try:
                data = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                return data
        raise BackendConfigurationError(
            "GitHub Copilot CLI output was not valid JSON. "
            "Use silent text mode and prompt for raw JSON."
        )


def _openai_backend_factory(
    provider_config: ProviderConfig,
    role_config: RoleModelConfig,
) -> OpenAIResponsesExecutionBackend:
    env = provider_config.env or {}
    settings = OpenAIClientSettings(
        api_key=os.environ.get(env.get("api_key", "")) if env.get("api_key") else None,
        base_url=os.environ.get(env.get("base_url", "")) if env.get("base_url") else None,
        organization=(
            os.environ.get(env.get("organization", "")) if env.get("organization") else None
        ),
        project=os.environ.get(env.get("project", "")) if env.get("project") else None,
    )
    return OpenAIResponsesExecutionBackend(
        settings=settings,
        options={**(provider_config.options or {}), **(role_config.options or {})},
    )


def _github_copilot_backend_factory(
    provider_config: ProviderConfig,
    role_config: RoleModelConfig,
) -> GitHubCopilotCLIExecutionBackend:
    options = {**(provider_config.options or {}), **(role_config.options or {})}
    executable = str(options.pop("executable", "copilot"))
    return GitHubCopilotCLIExecutionBackend(executable=executable, options=options)


BackendFactory = Callable[[ProviderConfig, RoleModelConfig], Any]


class BackendRegistry:
    def __init__(
        self,
        *,
        providers: dict[str, ProviderConfig] | None = None,
        factories: dict[str, BackendFactory] | None = None,
    ) -> None:
        self.providers = providers or load_provider_map()
        self.factories = {
            "mock": lambda provider_config, role_config: MockExecutionBackend(),
            "openai_responses": _openai_backend_factory,
            "github_copilot_cli": _github_copilot_backend_factory,
        }
        if factories:
            self.factories.update(factories)

    def create_for_role(self, role_config: RoleModelConfig) -> Any:
        provider_config = self.providers.get(role_config.provider)
        if provider_config is None:
            raise BackendConfigurationError(
                f"Missing provider configuration for '{role_config.provider}'."
            )
        backend_key = provider_config.backend
        factory = self.factories.get(backend_key)
        if factory is None:
            raise BackendConfigurationError(
                f"Provider '{provider_config.name}' references unknown backend '{backend_key}'."
            )
        return factory(provider_config, role_config)
