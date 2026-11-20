"""Compare real local Job, Trial and plugin lifecycles with deterministic offline I/O fixtures."""

import asyncio
import json
import os
import sys
from contextlib import ExitStack
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

os.environ["HARBOR_TELEMETRY"] = "0"
from harbor.agents.installed.base import ApiUsageLimitError, NonZeroAgentExitCodeError
from harbor.agents.oracle import OracleAgent
from harbor.job import Job
from harbor.models.job.config import JobConfig
from harbor.models.verifier.result import VerifierResult
from harbor.trial.hooks import TrialEvent
from harbor.trial.multi_step import MultiStepTrial
from harbor.trial.single_step import SingleStepTrial
from harbor.trial.trial import Trial
from harbor.verifier.verifier import RewardFileNotFoundError

from dressage.integrations.harbor import compat
from dressage.integrations.harbor.artifacts import HarborArtifactStore
from dressage.integrations.harbor.config import HarborIntegrationConfig
from dressage.integrations.harbor.plugin import DressageHarborPlugin
from dressage.integrations.harbor.rollout import (
    HarborRolloutError,
    _bundle_samples,
    _eval_output,
)
from tests.integrations.harbor.conftest import (
    RecordingRuntime,
    segment_factory,
    group_factory,
)

V = version("harbor")
assert V in {"0.18.0", "0.25.0", "0.26.0"}
MARKER = "fixture-audit-text-84a91"
GROUP = group_factory.__wrapped__()(0)[0]
SEGMENT = segment_factory.__wrapped__()


async def noop(*args, **kwargs):
    return None


class OfflineProxy:
    def __init__(self):
        self.finalizations = []

    async def finalize_session(self, session_id, **kwargs):
        self.finalizations.append(session_id)
        return {"success": True}

    async def read_trajectory(self, *, trajectory_id, instance_id, drain, **kwargs):
        return {
            "success": True,
            "data": [
                SEGMENT(trajectory_id, instance_id, segment_count=2, segment_index=i)
                for i in range(2)
            ],
            "drained": drain,
        }


def taskfiles(task, multi):
    (task / "environment").mkdir(parents=True)
    (task / "environment/Dockerfile").write_text("FROM scratch\n")
    config = 'schema_version = "1.3"\n[task]\nname = "audit/offline"\n'
    if multi:
        config = 'schema_version = "1.3"\nmulti_step_reward_strategy="final"\n[task]\nname = "audit/offline"\n'
        config += '[[steps]]\nname="first"\n[[steps]]\nname="second"\n'
    (task / "task.toml").write_text(config)
    for path in [task / "steps/first", task / "steps/second"] if multi else [task]:
        (path / "instruction.md").parent.mkdir(parents=True, exist_ok=True)
        (path / "instruction.md").write_text(path.name)
        for script in ("tests/test.sh", "solution/solve.sh"):
            (path / script).parent.mkdir(parents=True)
            (path / script).write_text("#!/bin/sh\nexit 0\n")


async def exercise(case):
    multi = case.startswith("step")
    with TemporaryDirectory() as temporary, ExitStack() as patches:
        root = Path(temporary)
        task = root / "task"
        taskfiles(task, multi)
        runtime, proxy = RecordingRuntime(), OfflineProxy()
        store = HarborArtifactStore(root / "outside", run_id=case, mode="disk")
        # Only test-fixture bytes are observed. The second scan runs after the END hooks.
        config = JobConfig.model_validate(
            {
                "job_name": case,
                "jobs_dir": root / "jobs",
                "tasks": [{"path": task}],
                "agents": [
                    {
                        "name": "oracle",
                        "env": {"AUDIT_API_KEY": MARKER},
                        **(
                            {"override_timeout_sec": 0.02}
                            if case in {"timeout", "step-mixed"}
                            else {}
                        ),
                    }
                ],
                "n_attempts": 1,
                "quiet": True,
                "retry": {
                    "max_retries": 0 if case == "agent-runtime-error" else 1,
                    "min_wait_sec": 0,
                    "max_wait_sec": 0,
                },
            }
        )
        settings = HarborIntegrationConfig.model_validate(
            {
                "execution_mode": "rollout",
                "agent_protocol_overrides": {"oracle": "openai"},
                "artifacts": {"root": str(root / "outside")},
            }
        )
        # Bypass only Dressage version gate in this test process.
        patches.enter_context(patch.object(compat, "SUPPORTED_HARBOR_VERSION", V))
        job = await Job.create(config)
        plugin = DressageHarborPlugin(
            settings, gateway_runtime=runtime, artifact_store=store, proxy_client=proxy
        )
        await plugin.on_job_start(job)
        commit = patches.enter_context(
            patch.object(store, "commit_attempt", wraps=store.commit_attempt)
        )
        phases = {}
        events, records, seen_first, seen_last = {}, {}, {}, {}

        async def observe(event):
            tid = str(event.trial_id)
            events.setdefault(tid, []).append(event.event.name)
            record = plugin.attempts[event.trial_name, tid]
            phases.setdefault(tid, []).append(record.phase.value)
            expected = {
                "START": "ready",
                "AGENT_START": "active",
                "AGENT_END": "ready",
                "VERIFICATION_START": "ready",
                "CANCEL": "ready",
                "END": "closed",
            }
            assert record.phase.value == expected[event.event.name]
            if event.event == TrialEvent.CANCEL:
                assert record.cancel_requested and record.poisoned
            if event.event in (TrialEvent.AGENT_START, TrialEvent.AGENT_END):
                assert record.handle.turns[-1] == f"{tid}:{record.turn_sequence - 1}"
                if event.event == TrialEvent.AGENT_END:
                    assert record.handle.quiesce_calls == record.turn_sequence
            result = event.result
            if event.event == TrialEvent.END:
                step_errors = [
                    s.exception_info.exception_type
                    for s in result.step_results or []
                    if s.exception_info
                ]
                records[tid] = [
                    result.exception_info.exception_type
                    if result.exception_info
                    else None,
                    step_errors,
                ]
                trial_dir = event.config.trials_dir / event.trial_name
                seen_first[tid] = MARKER in (trial_dir / "before-end.txt").read_text()
                (trial_dir / "created-by-end.txt").write_text(MARKER)
                seen_last[tid] = trial_dir / "created-by-end.txt"

        for event in (
            TrialEvent.START,
            TrialEvent.AGENT_START,
            TrialEvent.AGENT_END,
            TrialEvent.VERIFICATION_START,
            TrialEvent.CANCEL,
            TrialEvent.END,
        ):
            job.add_hook(event, observe)
        call_count = 0

        async def prepare(trial):
            (trial.paths.trial_dir / "before-end.txt").write_text(MARKER)

        async def run_agent(agent, *, instruction, **kwargs):
            nonlocal call_count
            call_count += 1
            if case == "agent-runtime-error":
                raise RuntimeError("controlled agent failure")
            if case == "api-quota" and call_count == 1:
                raise ApiUsageLimitError("offline fixture quota")
            if case == "nonzero" and call_count == 1:
                raise NonZeroAgentExitCodeError("offline fixture exit")
            if case == "step-retry" and call_count == 2:
                raise RuntimeError("offline second step unavailable")
            if (case == "timeout" and call_count == 1) or (
                case == "step-mixed" and call_count == 2
            ):
                await asyncio.Future()
            if case == "step-mixed" and call_count == 1:
                raise RuntimeError("offline first step unavailable")
            if case == "cancel":
                asyncio.current_task().cancel()
                await asyncio.sleep(0)

        async def verify(trial, *args, **kwargs):
            if case == "step-final-ungraded" and kwargs.get("step_name") == "second":
                raise RewardFileNotFoundError("controlled missing reward")
            score = 0.25 if kwargs.get("step_name") == "first" else 0.75
            return VerifierResult(rewards={"reward": score})

        async def artifact_dir(trial, *args, **kwargs):
            return trial.paths.artifacts_dir

        for cls, method, stub in [
            (Trial, "_prepare", prepare),
            (OracleAgent, "run", run_agent),
            (Trial, "_sync_agent_output", noop),
            (Trial, "_upload_agent_logs", noop),
            (Trial, "_stop_agent_environment", noop),
            (Trial, "_run_shared_verifier", verify),
            (SingleStepTrial, "_collect_artifacts", noop),
            (MultiStepTrial, "_prepare_step", noop),
            (MultiStepTrial, "_reset_shared_step_verifier_dirs", noop),
            (MultiStepTrial, "_collect_step_artifacts", artifact_dir),
        ]:
            patches.enter_context(patch.object(cls, method, stub))
        try:
            result = await job.run()
        except asyncio.CancelledError:
            assert case == "cancel"
            await plugin.aclose()
            assert (
                len(events) == 1
                and not proxy.finalizations
                and not plugin.results
                and commit.await_count == 0
            )
            assert [h.close_calls for h in runtime.lease.handles] == [1]
            assert list(events.values())[0] == [
                "START",
                "AGENT_START",
                "AGENT_END",
                "CANCEL",
                "END",
            ]
            assert runtime.lease.release_calls == 1
            print(
                json.dumps(
                    {
                        "case": case,
                        "events": list(events.values()),
                        "commits": commit.await_count,
                        "phases_after_hook": list(phases.values()),
                        "close_calls": [1],
                        "lease_releases": 1,
                    }
                )
            )
            return
        await plugin.on_job_end(result)
        final = result.trial_results[0]
        ids = list(events)
        final_id = str(final.id)
        bundle = plugin.get_result(final.trial_name, final_id)
        manifest = json.loads(
            next((root / "outside").rglob("manifest.json")).read_text()
        )
        state = [(r["superseded"], r["trainable"]) for r in manifest["attempts"]]
        errors = [
            (f.details.get("exception_type"), f.retryable)
            for f in bundle.failures
            if f.code == "HARBOR_TRIAL_EXCEPTION"
        ]
        samples = []
        if bundle.trainable:
            samples = _bundle_samples(
                template=GROUP,
                bundle=bundle,
                args=SimpleNamespace(max_tokens_per_gpu=16, context_parallel_size=1),
                reward_key="reward",
            )
            evaluation = _eval_output([samples], {})
            data = evaluation if isinstance(evaluation, dict) else evaluation.data
            assert data["harbor"]["rewards"] == [0.75]
            assert all(s.metadata["harbor_trial_id"] == final_id for s in samples)
        else:
            try:
                _bundle_samples(
                    template=GROUP,
                    bundle=bundle,
                    args=SimpleNamespace(
                        max_tokens_per_gpu=16, context_parallel_size=1
                    ),
                    reward_key="reward",
                )
            except HarborRolloutError as error:
                assert "HARBOR_TRIAL_EXCEPTION" in str(error)
            else:
                raise AssertionError("non-trainable bundle yielded samples")
        assert json.loads(store.bundle_path(bundle).read_text())["trial_id"] == final_id
        assert not store.bundle_path(bundle).is_relative_to(seen_last[final_id].parent)
        assert commit.await_count == len(ids)
        expected_counts = {
            "normal": 1,
            "step-retry": 2 if V == "0.26.0" else 1,
            "nonzero": 1 if V == "0.26.0" else 2,
            "api-quota": 2 if V == "0.26.0" else 1,
            "step-mixed": 1,
            "step-final-ungraded": 1,
            "agent-runtime-error": 1,
            "timeout": 1,
        }
        assert len(ids) == expected_counts[case], (case, V, len(ids), records)
        assert all(value == (V != "0.26.0") for value in seen_first.values())
        assert (MARKER in seen_last[final_id].read_text()) == (V == "0.18.0")
        assert len(set(ids)) == len(ids)
        assert ids[-1] == final_id
        assert [r["trial_id"] for r in manifest["attempts"]] == ids
        assert {r["trial_id"] for r in manifest["final_trials"]} == {final_id}
        assert len(proxy.finalizations) == len(ids) and all(
            h.close_calls == 1 for h in runtime.lease.handles
        )
        assert runtime.lease.release_calls == 1
        extra_output = {}
        if case in {"step-final-ungraded", "agent-runtime-error"}:
            top = (
                None if final.verifier_result is None else final.verifier_result.rewards
            )
            extra_output = {
                "top_rewards": top,
                "bundle_reward": bundle.reward,
                "reward_valid": getattr(final, "reward_valid", "absent"),
                "bundle_failure_codes": [f.code for f in bundle.failures],
            }
            assert not bundle.trainable
            if case == "step-final-ungraded":
                assert top is None and bundle.reward == 0.25
            else:
                expected = 0.75 if V == "0.26.0" else None
                assert bundle.reward == expected
                assert ("VERIFICATION_START" in events[final_id]) == (
                    expected is not None
                )
        # Independent sample conversion matches final reconciliation on trainable runs.
        print(
            json.dumps(
                {
                    **extra_output,
                    "case": case,
                    "attempts": len(ids),
                    "events": list(events.values()),
                    "phases_after_hook": list(phases.values()),
                    "commits": commit.await_count,
                    "errors": list(records.values()),
                    "manifest_superseded_trainable": state,
                    "final_errors_retryable": errors,
                    "sample_rewards": [s.reward for s in samples],
                    "final_id_matches": True,
                    "original_marker_visible_at_END": list(seen_first.values()),
                    "END_marker_visible_after_run": MARKER
                    in seen_last[final_id].read_text(),
                    "close_calls": [h.close_calls for h in runtime.lease.handles],
                    "lease_releases": runtime.lease.release_calls,
                },
                sort_keys=True,
            )
        )


async def main():
    print("Harbor", V, flush=True)
    for case in sys.argv[1:] or [
        "normal",
        "step-retry",
        "nonzero",
        "api-quota",
        "step-mixed",
        "timeout",
        "cancel",
    ]:
        await exercise(case)


if __name__ == "__main__":
    asyncio.run(main())
