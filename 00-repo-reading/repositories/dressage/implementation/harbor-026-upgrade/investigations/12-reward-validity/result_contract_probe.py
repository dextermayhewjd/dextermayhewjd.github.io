"""Exercise the Harbor result consumed by Dressage, using fixed verifier and proxy inputs."""

import json
from importlib.metadata import version
from types import SimpleNamespace

import pytest
from harbor.models.trial.config import TrialConfig
from harbor.models.trial.result import ExceptionInfo, StepResult
from harbor.models.verifier.result import VerifierResult
from harbor.trial.hooks import TrialEvent
from harbor.trial.trial import Trial

from dressage.integrations.harbor.artifacts import HarborArtifactStore
from dressage.integrations.harbor.plugin import _event_key, _trial_dir
from dressage.integrations.harbor.rollout import _bundle_samples, _eval_output


@pytest.mark.asyncio
async def test_result_contract(tmp_path, segment_factory, proxy_client_factory, group_factory):
    task = tmp_path / "task"
    for subdir in ("environment", "solution", "tests"):
        (task / subdir).mkdir(parents=True)
    (task / "instruction.md").write_text("Return the fixture answer.\n")
    (task / "task.toml").write_text(
        'schema_version = "1.3"\n[task]\nname = "dressage-probe/result"\n'
    )
    (task / "environment/Dockerfile").write_text("FROM scratch\n")
    for script in ("solution/solve.sh", "tests/test.sh"):
        (task / script).write_text("#!/bin/sh\nexit 0\n")

    config = TrialConfig.model_validate({
        "task": {"path": task}, "agent": {"name": "oracle"},
        "trial_name": "trial-a", "trials_dir": tmp_path / "trials",
    })
    harbor_version = version("harbor")
    assert harbor_version in {"0.18.0", "0.25.0", "0.26.0"}
    trial = await Trial.create(config)
    try:
        trial._init_result()
        received = []

        async def capture(event):
            received.append(event)

        # Exercise the event payload itself at a chosen point in the test.
        trial.add_hook(TrialEvent.END, capture)
        await trial._emit(TrialEvent.END)
        event, = received
        trial_name, trial_id = _event_key(event)
        assert (trial_name, trial_id) == (trial.result.trial_name, str(trial.result.id))
        assert event.result is trial.result and _trial_dir(event) == trial.paths.trial_dir
        print(f"Harbor {harbor_version} | {type(event).__name__} -> {type(event.result).__name__}")
        print("event name, physical id and Trial directory agree with Dressage")

        score = VerifierResult(rewards={"reward": 0.75, "aux": 0.25})
        error = ExceptionInfo(
            exception_type="NonZeroAgentExitCodeError", exception_message="fixture exit",
            exception_traceback="", occurred_at=trial.result.started_at,
        )
        step = StepResult(step_name="last", verifier_result=score)
        cases = [
            ("normal", score, None, [], True, 0.75, True, []),
            ("nonzero-exit", score, error, [], True, 0.75, False, ["HARBOR_TRIAL_EXCEPTION"]),
            ("other-key", VerifierResult(rewards={"aux": 0.25}), None, [], True, None, False, ["REWARD_MISSING"]),
            ("step-only", None, None, [step], False, 0.75, True, []),
        ]
        for name, top_reward, exception, steps, valid, selected, trainable, failures in cases:
            result = event.result.model_copy(deep=True)
            result.verifier_result = top_reward
            result.exception_info = exception
            result.step_results = steps
            segments = [
                segment_factory(trial_id, "logical-a", segment_index=i, segment_count=2)
                for i in range(2)
            ]
            store = HarborArtifactStore(tmp_path / name, run_id=name, mode="disk")
            bundle = await store.commit_attempt(
                proxy_client=proxy_client_factory(segments), job_id="job-a",
                trial_name=trial_name, trial_id=trial_id, session_id=trial_id,
                instance_id="logical-a", attempt_ordinal=0, trial_result=result,
                trial_dir=_trial_dir(event), routing_guarantee="configure_only",
                task_network_class="public",
            )
            codes = [failure.code for failure in bundle.failures]
            reward_valid = getattr(result, "reward_valid", "absent")
            expected_valid = valid
            if harbor_version == "0.18.0":
                expected_valid = "absent"
            elif harbor_version == "0.25.0" and name == "nonzero-exit":
                expected_valid = False
            assert reward_valid == expected_valid
            assert (bundle.reward, bundle.trainable, codes) == (selected, trainable, failures)
            saved = json.loads(store.bundle_path(bundle).read_text())
            assert saved["trial_id"] == trial_id and saved["rewards"] == bundle.rewards
            print(f"{name}: reward_valid={reward_valid} selected={bundle.reward} "
                  f"trainable={bundle.trainable} failures={codes}")
            if name == "normal":
                samples = _bundle_samples(
                    template=group_factory(0)[0], bundle=bundle,
                    args=SimpleNamespace(max_tokens_per_gpu=16, context_parallel_size=1),
                    reward_key="reward",
                )
                assert all(sample.metadata["harbor_trial_id"] == trial_id for sample in samples)
                training_rewards = [sample.reward for sample in samples]
                evaluation = _eval_output([samples], {})
                data = evaluation if isinstance(evaluation, dict) else evaluation.data
                assert training_rewards == [{"reward": 0.0}, score.rewards]
                assert data["harbor"]["rewards"] == [0.75]
                print(f"two segment rewards={training_rewards} | eval rewards={data['harbor']['rewards']}")
    finally:
        trial._close_logger_handler()
