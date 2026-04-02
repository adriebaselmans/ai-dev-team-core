from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from team_orchestrator.backends import BackendRegistry
from team_orchestrator.models import RoleModelConfig, load_role_model_map
from team_orchestrator.prompts import RolePromptConfig, load_role_prompt_map
from framework.runtime.role_contracts import load_role_output_schema, validate_role_output


class ContextBuilder(Protocol):
    def build(self, *, role_key: str, state: dict[str, Any], step_name: str) -> dict[str, Any]:
        raise NotImplementedError


class ExecutionBackend(Protocol):
    def invoke(self, request: "RoleExecutionRequest") -> dict[str, Any]:
        raise NotImplementedError

    def repair(
        self,
        request: "RoleExecutionRequest",
        *,
        invalid_output: dict[str, Any],
        validation_errors: list[str],
    ) -> dict[str, Any] | None:
        raise NotImplementedError


@dataclass(frozen=True)
class ToolPolicy:
    allow_local_read: bool = True
    allow_local_write: bool = False
    allow_shell: bool = False
    allow_browser: bool = False
    allow_external_research: bool = False
    writable_paths: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "allow_local_read": self.allow_local_read,
            "allow_local_write": self.allow_local_write,
            "allow_shell": self.allow_shell,
            "allow_browser": self.allow_browser,
            "allow_external_research": self.allow_external_research,
            "writable_paths": list(self.writable_paths),
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class RoleExecutionRequest:
    role: str
    step_name: str
    model: dict[str, Any]
    prompt: str
    prompt_hash: str
    context: dict[str, Any]
    tool_policy: dict[str, Any]
    output_schema: dict[str, Any]


@dataclass(frozen=True)
class RoleExecutionMetadata:
    role: str
    step_name: str
    prompt_hash: str
    model: dict[str, Any]
    tool_policy: dict[str, Any]
    validation_status: str
    repair_count: int
    tools_used: list[str]
    sources: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "step_name": self.step_name,
            "prompt_hash": self.prompt_hash,
            "model": dict(self.model),
            "tool_policy": dict(self.tool_policy),
            "validation_status": self.validation_status,
            "repair_count": self.repair_count,
            "tools_used": list(self.tools_used),
            "sources": list(self.sources),
        }


@dataclass(frozen=True)
class RoleExecutionResult:
    update: dict[str, Any]
    metadata: RoleExecutionMetadata


class RoleExecutionError(RuntimeError):
    """Raised when the execution backend fails or returns an unusable result."""


class RoleExecutionContractError(RoleExecutionError):
    """Raised when role output does not satisfy the role contract."""


class RoleExecutor:
    def __init__(
        self,
        *,
        role_models: dict[str, RoleModelConfig] | None = None,
        role_prompts: dict[str, RolePromptConfig] | None = None,
        backend_registry: BackendRegistry | None = None,
    ) -> None:
        self.role_models = role_models or load_role_model_map()
        self.role_prompts = role_prompts or load_role_prompt_map()
        self.backend_registry = backend_registry or BackendRegistry()

    def execute(
        self,
        *,
        role_key: str,
        state: dict[str, Any],
        step_name: str,
        context_builder: ContextBuilder,
        tool_policy: ToolPolicy,
        backend: ExecutionBackend | None = None,
    ) -> RoleExecutionResult:
        request = self._build_request(
            role_key=role_key,
            state=state,
            step_name=step_name,
            context_builder=context_builder,
            tool_policy=tool_policy,
        )

        backend = backend or self.backend_registry.create_for_role(self.role_models[role_key])
        try:
            raw_payload = backend.invoke(request)
        except RoleExecutionError:
            raise
        except Exception as exc:
            raise RoleExecutionError(
                f"Execution backend for role '{role_key}' failed during invoke()."
            ) from exc

        raw_output = self._ensure_mapping(raw_payload, role_key=role_key)
        validation_errors = validate_role_output(role_key, raw_output)
        if not validation_errors:
            return self._build_result(
                role_key=role_key,
                step_name=step_name,
                request=request,
                update=raw_output,
                validation_status="valid",
                repair_count=0,
            )

        repaired_output = self._repair(
            backend=backend,
            request=request,
            invalid_output=raw_output,
            validation_errors=validation_errors,
            role_key=role_key,
        )
        if repaired_output is not None:
            repaired_errors = validate_role_output(role_key, repaired_output)
            if not repaired_errors:
                return self._build_result(
                    role_key=role_key,
                    step_name=step_name,
                    request=request,
                    update=repaired_output,
                    validation_status="repaired",
                    repair_count=1,
                )
            validation_errors = repaired_errors

        error_text = "; ".join(validation_errors)
        raise RoleExecutionContractError(
            f"Role '{role_key}' returned output that does not satisfy its contract: {error_text}"
        )

    def _build_request(
        self,
        *,
        role_key: str,
        state: dict[str, Any],
        step_name: str,
        context_builder: ContextBuilder,
        tool_policy: ToolPolicy,
    ) -> RoleExecutionRequest:
        try:
            model = self.role_models[role_key]
        except KeyError as exc:
            raise RoleExecutionError(f"Missing model config for role '{role_key}'.") from exc
        try:
            prompt = self.role_prompts[role_key]
        except KeyError as exc:
            raise RoleExecutionError(f"Missing prompt config for role '{role_key}'.") from exc

        context = context_builder.build(role_key=role_key, state=state, step_name=step_name)
        if not isinstance(context, dict):
            raise RoleExecutionError(f"Context builder for role '{role_key}' must return a mapping.")

        return RoleExecutionRequest(
            role=role_key,
            step_name=step_name,
            model=model.as_dict(),
            prompt=prompt.prompt,
            prompt_hash=prompt.prompt_hash,
            context=context,
            tool_policy=tool_policy.as_dict(),
            output_schema=load_role_output_schema(role_key),
        )

    def _repair(
        self,
        *,
        backend: ExecutionBackend,
        request: RoleExecutionRequest,
        invalid_output: dict[str, Any],
        validation_errors: list[str],
        role_key: str,
    ) -> dict[str, Any] | None:
        repair = getattr(backend, "repair", None)
        if repair is None:
            return None
        try:
            repaired = repair(
                request,
                invalid_output=invalid_output,
                validation_errors=validation_errors,
            )
        except RoleExecutionError:
            raise
        except Exception as exc:
            raise RoleExecutionError(
                f"Execution backend for role '{role_key}' failed during repair()."
            ) from exc
        if repaired is None:
            return None
        return self._ensure_mapping(repaired, role_key=role_key)

    def _build_result(
        self,
        *,
        role_key: str,
        step_name: str,
        request: RoleExecutionRequest,
        update: dict[str, Any],
        validation_status: str,
        repair_count: int,
    ) -> RoleExecutionResult:
        metadata = RoleExecutionMetadata(
            role=role_key,
            step_name=step_name,
            prompt_hash=request.prompt_hash,
            model=request.model,
            tool_policy=request.tool_policy,
            validation_status=validation_status,
            repair_count=repair_count,
            tools_used=[],
            sources=[],
        )
        return RoleExecutionResult(update=update, metadata=metadata)

    def _ensure_mapping(self, payload: Any, *, role_key: str) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise RoleExecutionError(
                f"Execution backend for role '{role_key}' must return a mapping, got {type(payload).__name__}."
            )
        return payload
