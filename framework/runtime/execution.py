from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Iterable, Iterator, Literal, Protocol

import threading
import time

from spec_loader import load_models_config


LaunchMode = Literal["batch", "interactive", "daemon", "streamed"]


@dataclass(frozen=True)
class ModelSelection:
    provider: str
    model: str
    mode: str
    placeholder: bool = False
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionPolicy:
    mode: LaunchMode = "batch"
    observation_policy: Literal["exit-code-first", "event-stream", "readiness"] = "exit-code-first"
    readiness_probe: Literal["none", "event", "poll"] = "none"
    readiness_event: str | None = None
    allow_polling_fallback: bool = False
    timeout_seconds: float | None = None
    polling_interval_seconds: float = 0.1
    max_poll_attempts: int = 5
    max_observed_events: int = 50


@dataclass(frozen=True)
class ProcessEvent:
    kind: str
    payload: str = ""


@dataclass(frozen=True)
class DispatchEnvelope:
    role: str
    phase: str
    objective: str
    context_slice: dict[str, Any]
    owned_outputs: list[str]
    skill_contracts: list[dict[str, Any]]
    model_selection: ModelSelection
    correlation_id: str
    execution_policy: ExecutionPolicy = field(default_factory=ExecutionPolicy)
    collaboration_contract: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DispatchReceipt:
    status: str
    provider: str
    model: str
    summary: str
    changed_artifacts: list[str]
    blockers: list[str]
    diagnostics: dict[str, str] = field(default_factory=dict)
    process: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ManagedProcess(Protocol):
    def wait(self, timeout: float | None = None) -> int: ...

    def iter_events(self) -> Iterable[ProcessEvent]: ...

    def read_stdout(self) -> str: ...

    def read_stderr(self) -> str: ...

    def read_logs(self) -> str: ...

    def poll_ready(self) -> bool: ...


class ProcessRunner(Protocol):
    def launch(self, envelope: DispatchEnvelope) -> ManagedProcess: ...


@dataclass(frozen=True)
class ProcessObservation:
    mode: LaunchMode
    exit_code: int | None = None
    readiness_status: Literal["not-applicable", "ready", "timeout", "failed"] = "not-applicable"
    observed_events: list[ProcessEvent] = field(default_factory=list)
    used_polling: bool = False
    diagnostics: dict[str, str] = field(default_factory=dict)
    failure_reason: str | None = None


class ExecutionBackend:
    def dispatch(self, envelope: DispatchEnvelope) -> DispatchReceipt:
        raise NotImplementedError


class SuccessfulProcess:
    def wait(self, timeout: float | None = None) -> int:
        return 0

    def iter_events(self) -> Iterable[ProcessEvent]:
        return ()

    def read_stdout(self) -> str:
        return ""

    def read_stderr(self) -> str:
        return ""

    def read_logs(self) -> str:
        return ""

    def poll_ready(self) -> bool:
        return True


class SuccessfulProcessRunner:
    def launch(self, envelope: DispatchEnvelope) -> ManagedProcess:
        return SuccessfulProcess()


class EventObserver:
    def __init__(self, events: Iterable[ProcessEvent], limit: int) -> None:
        self._events: Iterator[ProcessEvent] = iter(events)
        self._limit = max(limit, 0)
        self._observed: list[ProcessEvent] = []
        self._lock = threading.Lock()
        self._done = threading.Event()
        self._limit_reached = threading.Event()
        self._thread = threading.Thread(target=self._consume, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def snapshot(self) -> list[ProcessEvent]:
        with self._lock:
            return list(self._observed)

    def wait_until_done(self, timeout: float | None = None) -> bool:
        return self._done.wait(timeout)

    def reached_limit(self) -> bool:
        return self._limit_reached.is_set()

    def has_event(self, kind: str) -> bool:
        with self._lock:
            return any(event.kind == kind for event in self._observed)

    def _consume(self) -> None:
        try:
            while len(self._observed) < self._limit:
                event = next(self._events)
                with self._lock:
                    self._observed.append(event)
            self._limit_reached.set()
        except StopIteration:
            pass
        finally:
            self._done.set()


class MockExecutionBackend(ExecutionBackend):
    def __init__(
        self,
        runner: ProcessRunner | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self._runner = runner or SuccessfulProcessRunner()
        self._sleep = sleep or time.sleep

    def dispatch(self, envelope: DispatchEnvelope) -> DispatchReceipt:
        _assert_mock_placeholder(envelope)
        process = self._runner.launch(envelope)
        observation = execute_process(process, envelope.execution_policy, sleep=self._sleep)
        blockers = _blockers_for_observation(observation)
        return DispatchReceipt(
            status=_status_for_observation(observation),
            provider=envelope.model_selection.provider,
            model=envelope.model_selection.model,
            summary=_summary_for_observation(envelope, observation),
            changed_artifacts=envelope.owned_outputs if not blockers else [],
            blockers=blockers,
            diagnostics=observation.diagnostics,
            process={
                "mode": observation.mode,
                "exit_code": observation.exit_code,
                "readiness_status": observation.readiness_status,
                "observed_event_count": len(observation.observed_events),
                "used_polling": observation.used_polling,
            },
        )


def model_selection_for_role(role: str) -> ModelSelection:
    config = load_models_config()
    roles = config.get("roles", {})
    if role not in roles:
        raise KeyError(f"Role '{role}' has no model configuration.")
    selection = roles[role]
    if not isinstance(selection, dict):
        raise ValueError(f"Role '{role}' model selection must be a mapping.")
    return ModelSelection(
        provider=selection["provider"],
        model=selection["model"],
        mode=selection.get("mode", config.get("default_mode", "one-shot")),
        placeholder=bool(selection.get("placeholder", False)),
        options=dict(selection.get("options", {})),
    )


def backend_for_provider(provider: str) -> ExecutionBackend:
    providers = load_models_config().get("providers", {})
    if provider not in providers:
        raise KeyError(f"Unknown provider: {provider}")
    return MockExecutionBackend()


def dispatch(envelope: DispatchEnvelope) -> DispatchReceipt:
    backend = backend_for_provider(envelope.model_selection.provider)
    return backend.dispatch(envelope)


def _assert_mock_placeholder(envelope: DispatchEnvelope) -> None:
    if envelope.model_selection.placeholder:
        return
    raise RuntimeError(
        "MockExecutionBackend requires placeholder: true for "
        f"role '{envelope.role}' using model '{envelope.model_selection.model}'."
    )


def execute_process(
    process: ManagedProcess,
    policy: ExecutionPolicy,
    *,
    sleep: Callable[[float], None] | None = None,
) -> ProcessObservation:
    if policy.mode == "batch":
        return _execute_batch(process, policy)
    if policy.mode in {"interactive", "streamed"}:
        return _execute_stream_observed(process, policy)
    if policy.mode == "daemon":
        return _execute_daemon(process, policy, sleep=sleep or time.sleep)
    raise ValueError(f"Unsupported execution mode: {policy.mode}")


def _execute_batch(process: ManagedProcess, policy: ExecutionPolicy) -> ProcessObservation:
    try:
        exit_code = process.wait(timeout=policy.timeout_seconds)
    except TimeoutError:
        return ProcessObservation(
            mode="batch",
            readiness_status="timeout",
            diagnostics=_capture_diagnostics(process),
            failure_reason="timeout",
        )
    if exit_code == 0:
        return ProcessObservation(mode="batch", exit_code=exit_code)
    return ProcessObservation(
        mode="batch",
        exit_code=exit_code,
        readiness_status="failed",
        diagnostics=_capture_diagnostics(process),
        failure_reason="exit-code",
    )


def _execute_stream_observed(process: ManagedProcess, policy: ExecutionPolicy) -> ProcessObservation:
    observer = EventObserver(process.iter_events(), policy.max_observed_events)
    observer.start()
    try:
        exit_code = process.wait(timeout=policy.timeout_seconds)
    except TimeoutError:
        return ProcessObservation(
            mode=policy.mode,
            readiness_status="timeout",
            observed_events=observer.snapshot(),
            diagnostics=_capture_diagnostics(process),
            failure_reason="timeout",
        )
    observer.wait_until_done(0)
    observed_events = observer.snapshot()
    diagnostics = _capture_diagnostics(process) if exit_code != 0 else {}
    return ProcessObservation(
        mode=policy.mode,
        exit_code=exit_code,
        readiness_status="failed" if exit_code != 0 else "not-applicable",
        observed_events=observed_events,
        diagnostics=diagnostics,
        failure_reason=("exit-code" if exit_code != 0 else None),
    )


def _execute_daemon(
    process: ManagedProcess,
    policy: ExecutionPolicy,
    *,
    sleep: Callable[[float], None],
) -> ProcessObservation:
    if policy.readiness_probe == "event" and policy.readiness_event:
        observer = EventObserver(process.iter_events(), policy.max_observed_events)
        observer.start()
        finished = observer.wait_until_done(policy.timeout_seconds)
        observed_events = observer.snapshot()
        if observer.has_event(policy.readiness_event):
            return ProcessObservation(
                mode="daemon",
                readiness_status="ready",
                observed_events=observed_events,
            )
        if policy.allow_polling_fallback:
            return _poll_daemon_readiness(process, policy, sleep=sleep, observed_events=observed_events)
        return ProcessObservation(
            mode="daemon",
            readiness_status="timeout" if not finished else "failed",
            observed_events=observed_events,
            diagnostics=_capture_diagnostics(process),
            failure_reason="timeout" if not finished else "readiness-event-missing",
        )

    if policy.readiness_probe == "poll" or policy.allow_polling_fallback:
        return _poll_daemon_readiness(process, policy, sleep=sleep)

    if process.poll_ready():
        return ProcessObservation(mode="daemon", readiness_status="ready")
    return ProcessObservation(
        mode="daemon",
        readiness_status="failed",
        diagnostics=_capture_diagnostics(process),
        failure_reason="readiness-failed",
    )


def _capture_diagnostics(process: ManagedProcess) -> dict[str, str]:
    return {
        "stdout": process.read_stdout(),
        "stderr": process.read_stderr(),
        "logs": process.read_logs(),
    }


def _poll_daemon_readiness(
    process: ManagedProcess,
    policy: ExecutionPolicy,
    *,
    sleep: Callable[[float], None],
    observed_events: list[ProcessEvent] | None = None,
) -> ProcessObservation:
    for attempt in range(policy.max_poll_attempts):
        if process.poll_ready():
            return ProcessObservation(
                mode="daemon",
                readiness_status="ready",
                observed_events=list(observed_events or []),
                used_polling=(attempt > 0 or policy.readiness_probe == "poll" or policy.allow_polling_fallback),
            )
        if attempt + 1 < policy.max_poll_attempts:
            sleep(policy.polling_interval_seconds)
    return ProcessObservation(
        mode="daemon",
        readiness_status="timeout",
        observed_events=list(observed_events or []),
        used_polling=True,
        diagnostics=_capture_diagnostics(process),
        failure_reason="timeout",
    )


def _status_for_observation(observation: ProcessObservation) -> str:
    if observation.mode == "daemon":
        return "running" if observation.readiness_status == "ready" else "failed"
    return "completed" if observation.exit_code == 0 else "failed"


def _blockers_for_observation(observation: ProcessObservation) -> list[str]:
    if observation.mode == "daemon":
        if observation.readiness_status == "ready":
            return []
        return [f"Daemon readiness failed with status '{observation.readiness_status}'."]
    if observation.failure_reason == "timeout":
        return ["Process timed out."]
    if observation.exit_code == 0:
        return []
    return [f"Process exited with code {observation.exit_code}."]


def _summary_for_observation(envelope: DispatchEnvelope, observation: ProcessObservation) -> str:
    if observation.mode == "daemon" and observation.readiness_status == "ready":
        return f"Started {envelope.role} for phase {envelope.phase}; daemon is ready."
    if observation.exit_code == 0:
        return f"Completed {envelope.role} for phase {envelope.phase} in {observation.mode} mode."
    return f"{envelope.role} for phase {envelope.phase} failed in {observation.mode} mode."
