from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from execution import (
    DispatchEnvelope,
    ExecutionPolicy,
    MockExecutionBackend,
    ModelSelection,
    ProcessEvent,
)


class FakeProcess:
    def __init__(
        self,
        *,
        exit_code: int = 0,
        events: list[ProcessEvent] | None = None,
        readiness_sequence: list[bool] | None = None,
        wait_timeout: bool = False,
        stdout: str = "stdout",
        stderr: str = "stderr",
        logs: str = "logs",
    ) -> None:
        self.exit_code = exit_code
        self.events = list(events or [])
        self.readiness_sequence = list(readiness_sequence or [])
        self.wait_timeout = wait_timeout
        self.stdout = stdout
        self.stderr = stderr
        self.logs = logs
        self.stdout_reads = 0
        self.stderr_reads = 0
        self.log_reads = 0
        self.poll_calls = 0
        self.wait_calls = 0

    def wait(self, timeout: float | None = None) -> int:
        self.wait_calls += 1
        if self.wait_timeout:
            raise TimeoutError("process timed out")
        return self.exit_code

    def iter_events(self) -> list[ProcessEvent]:
        return list(self.events)

    def read_stdout(self) -> str:
        self.stdout_reads += 1
        return self.stdout

    def read_stderr(self) -> str:
        self.stderr_reads += 1
        return self.stderr

    def read_logs(self) -> str:
        self.log_reads += 1
        return self.logs

    def poll_ready(self) -> bool:
        self.poll_calls += 1
        if self.readiness_sequence:
            return self.readiness_sequence.pop(0)
        return False


class FakeRunner:
    def __init__(self, process: FakeProcess) -> None:
        self.process = process

    def launch(self, envelope: DispatchEnvelope) -> FakeProcess:
        return self.process


class InfiniteEventProcess(FakeProcess):
    def __init__(self, *, exit_code: int = 0) -> None:
        super().__init__(exit_code=exit_code)

    def iter_events(self):
        index = 0
        while True:
            yield ProcessEvent("chunk", str(index))
            index += 1


def build_envelope(policy: ExecutionPolicy) -> DispatchEnvelope:
    return DispatchEnvelope(
        role="developer",
        phase="development",
        objective="Implement runtime policy.",
        context_slice={"development": "context"},
        owned_outputs=["framework/runtime/execution.py"],
        skill_contracts=[],
        model_selection=ModelSelection(provider="openai", model="gpt-test", mode="one-shot", placeholder=True),
        correlation_id="corr-1",
        execution_policy=policy,
    )


class ExecutionPolicyTests(unittest.TestCase):
    def test_batch_success_does_not_collect_diagnostics(self) -> None:
        process = FakeProcess(exit_code=0)
        backend = MockExecutionBackend(runner=FakeRunner(process), sleep=lambda _: None)

        receipt = backend.dispatch(build_envelope(ExecutionPolicy(mode="batch")))

        self.assertEqual(receipt.status, "completed")
        self.assertEqual(receipt.diagnostics, {})
        self.assertEqual(process.stdout_reads, 0)
        self.assertEqual(process.stderr_reads, 0)
        self.assertEqual(process.log_reads, 0)
        self.assertEqual(receipt.process["mode"], "batch")

    def test_batch_failure_collects_diagnostics(self) -> None:
        process = FakeProcess(exit_code=2, stdout="out", stderr="err", logs="trace")
        backend = MockExecutionBackend(runner=FakeRunner(process), sleep=lambda _: None)

        receipt = backend.dispatch(build_envelope(ExecutionPolicy(mode="batch")))

        self.assertEqual(receipt.status, "failed")
        self.assertEqual(receipt.diagnostics["stdout"], "out")
        self.assertEqual(receipt.diagnostics["stderr"], "err")
        self.assertEqual(receipt.diagnostics["logs"], "trace")
        self.assertEqual(process.stdout_reads, 1)
        self.assertEqual(process.stderr_reads, 1)
        self.assertEqual(process.log_reads, 1)

    def test_interactive_mode_observes_events(self) -> None:
        process = FakeProcess(exit_code=0, events=[ProcessEvent("prompt"), ProcessEvent("input")])
        backend = MockExecutionBackend(runner=FakeRunner(process), sleep=lambda _: None)

        receipt = backend.dispatch(
            build_envelope(
                ExecutionPolicy(
                    mode="interactive",
                    observation_policy="event-stream",
                )
            )
        )

        self.assertEqual(receipt.status, "completed")
        self.assertEqual(receipt.process["observed_event_count"], 2)
        self.assertEqual(process.stdout_reads, 0)

    def test_streamed_mode_observes_events(self) -> None:
        process = FakeProcess(exit_code=0, events=[ProcessEvent("chunk", "1"), ProcessEvent("chunk", "2")])
        backend = MockExecutionBackend(runner=FakeRunner(process), sleep=lambda _: None)

        receipt = backend.dispatch(
            build_envelope(
                ExecutionPolicy(
                    mode="streamed",
                    observation_policy="event-stream",
                )
            )
        )

        self.assertEqual(receipt.status, "completed")
        self.assertEqual(receipt.process["observed_event_count"], 2)
        self.assertEqual(receipt.process["mode"], "streamed")

    def test_streamed_mode_handles_non_terminating_event_source_without_buffering_entire_stream(self) -> None:
        process = InfiniteEventProcess(exit_code=0)
        backend = MockExecutionBackend(runner=FakeRunner(process), sleep=lambda _: None)

        receipt = backend.dispatch(
            build_envelope(
                ExecutionPolicy(
                    mode="streamed",
                    observation_policy="event-stream",
                    max_observed_events=3,
                )
            )
        )

        self.assertEqual(receipt.status, "completed")
        self.assertEqual(receipt.process["observed_event_count"], 3)
        self.assertEqual(process.wait_calls, 1)

    def test_daemon_mode_uses_event_readiness_without_polling(self) -> None:
        process = FakeProcess(events=[ProcessEvent("ready", "listening")])
        backend = MockExecutionBackend(runner=FakeRunner(process), sleep=lambda _: None)

        receipt = backend.dispatch(
            build_envelope(
                ExecutionPolicy(
                    mode="daemon",
                    observation_policy="readiness",
                    readiness_probe="event",
                    readiness_event="ready",
                )
            )
        )

        self.assertEqual(receipt.status, "running")
        self.assertEqual(receipt.process["readiness_status"], "ready")
        self.assertFalse(receipt.process["used_polling"])
        self.assertEqual(process.poll_calls, 0)

    def test_daemon_mode_falls_back_to_polling_when_requested(self) -> None:
        process = FakeProcess(readiness_sequence=[False, False, True])
        backend = MockExecutionBackend(runner=FakeRunner(process), sleep=lambda _: None)

        receipt = backend.dispatch(
            build_envelope(
                ExecutionPolicy(
                    mode="daemon",
                    observation_policy="readiness",
                    allow_polling_fallback=True,
                    max_poll_attempts=3,
                    polling_interval_seconds=0,
                )
            )
        )

        self.assertEqual(receipt.status, "running")
        self.assertEqual(receipt.process["readiness_status"], "ready")
        self.assertTrue(receipt.process["used_polling"])
        self.assertEqual(process.poll_calls, 3)

    def test_daemon_event_readiness_can_fall_back_to_polling(self) -> None:
        process = FakeProcess(
            events=[ProcessEvent("progress", "warming"), ProcessEvent("progress", "still-warming")],
            readiness_sequence=[False, True],
        )
        backend = MockExecutionBackend(runner=FakeRunner(process), sleep=lambda _: None)

        receipt = backend.dispatch(
            build_envelope(
                ExecutionPolicy(
                    mode="daemon",
                    observation_policy="readiness",
                    readiness_probe="event",
                    readiness_event="ready",
                    allow_polling_fallback=True,
                    max_observed_events=2,
                    max_poll_attempts=2,
                    polling_interval_seconds=0,
                )
            )
        )

        self.assertEqual(receipt.status, "running")
        self.assertEqual(receipt.process["readiness_status"], "ready")
        self.assertTrue(receipt.process["used_polling"])
        self.assertEqual(receipt.process["observed_event_count"], 2)
        self.assertEqual(process.poll_calls, 2)

    def test_batch_timeout_captures_diagnostics_and_reports_timeout(self) -> None:
        process = FakeProcess(wait_timeout=True, stdout="partial out", stderr="partial err", logs="partial log")
        backend = MockExecutionBackend(runner=FakeRunner(process), sleep=lambda _: None)

        receipt = backend.dispatch(
            build_envelope(
                ExecutionPolicy(
                    mode="batch",
                    timeout_seconds=0.01,
                )
            )
        )

        self.assertEqual(receipt.status, "failed")
        self.assertEqual(receipt.blockers, ["Process timed out."])
        self.assertEqual(receipt.diagnostics["stdout"], "partial out")
        self.assertEqual(receipt.diagnostics["stderr"], "partial err")
        self.assertEqual(receipt.diagnostics["logs"], "partial log")


if __name__ == "__main__":
    unittest.main()

