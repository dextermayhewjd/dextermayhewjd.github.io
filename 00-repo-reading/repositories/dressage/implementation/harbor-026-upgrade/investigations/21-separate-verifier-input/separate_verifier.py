"""Exercise the generated DAPO task from Trial._run_separate_verifier with real bwrap.

Only the model's output artifact is synthetic. Optional input variations isolate log mounts
from ordinary host-managed tests and from the optional environment directory.
"""
import argparse
import asyncio
import json
import os
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from dressage.integrations.harbor.environment import DressageEnvironment
from examples.harbor.dataset_tools.dapo.prepare_dataset import prepare_dataset
from harbor.models.trial.config import TrialConfig
from harbor.trial.trial import Trial


async def observe(case: str, root: Path) -> dict:
    source = root / "input.jsonl"
    source.write_text(json.dumps({
        "prompt": [{"role": "user", "content": "What is 2 + 2?"}],
        "label": "4", "metadata": {"instance_id": "dapo_math_00000"},
        "agent_mode": "blackbox", "blackbox_type": "claude_code",
        "reward_fn": "contains_label", "task_type": "math",
    }) + "\n")
    dataset = prepare_dataset(source, cache_root=root / "cache", limit=1)
    task = dataset.tasks_dir / "dapo_math_00000"
    envdir = task / "environment"
    if case == "missing-envdir":
        envdir.rmdir()
    elif case == "nonempty-envdir":
        (envdir / "agent-input.txt").write_text("ordinary agent workspace input\n")
    profile = root / "profile.json"
    profile.write_text(json.dumps({
        "gateway": {"listen_port": 39100},
        "environment": {"mode": "bwrap", "runtime_root": str(root / "runtime")},
        "security": {"routing_guarantee": "enforced"},
    }))
    backend = {"import_path": "dressage.integrations.harbor.environment:DressageEnvironment"}
    if case != "default-mounts" and version("harbor") != "0.18.0":
        backend["kwargs"] = {"auto_mounting": True}
    config = TrialConfig.model_validate({
        "task": {"path": task}, "agent": {"name": "oracle"}, "environment": backend,
        "trial_name": "local-grade", "trials_dir": root / "trials",
    })
    observations = {"case": case, "harbor": version("harbor")}
    start_original = DressageEnvironment.start
    download_original = DressageEnvironment.download_dir

    async def start(environment, force_build):
        observations["verifier_input_directory"] = environment.environment_dir.relative_to(task).as_posix()
        await start_original(environment, force_build)
        observations["tests_at_start"] = sorted(f.name for f in environment._host_path("/tests").iterdir())

    async def download(environment, source_dir, target_dir):
        observations["same_verifier_download_source_destination"] = environment._host_path(source_dir).resolve() == Path(target_dir).resolve()
        return await download_original(environment, source_dir, target_dir)

    with patch.dict(os.environ, {"DRESSAGE_HARBOR_INTEGRATION_CONFIG": str(profile)}):
        trial = await Trial.create(config)
        try:
            stream = trial.paths.artifacts_dir / "logs/agent/claude-code.txt"
            stream.parent.mkdir(parents=True, exist_ok=True)
            stream.write_text(json.dumps({"type": "result", "result": "4"}) + "\n")
            with patch.object(DressageEnvironment, "start", start), patch.object(DressageEnvironment, "download_dir", download):
                result = await trial._run_separate_verifier(key="verify", timeout_sec=15, user=None, artifacts_dir=trial.paths.artifacts_dir)
            observations["result"] = result.rewards
        except Exception as exc:
            observations["exception"] = type(exc).__name__
            observations["message"] = str(exc).replace(str(task), "<task>").replace(str(root), "<temp>")[:240]
            observations["cause"] = type(exc.__cause__).__name__ if exc.__cause__ is not None else None
        finally:
            if trial.paths.reward_json_path.exists():
                observations["reward_file"] = json.loads(trial.paths.reward_json_path.read_text())
            if trial.paths.test_stdout_path.exists():
                observations["test_stdout"] = trial.paths.test_stdout_path.read_text()[:250]
            trial._close_logger_handler()
    return observations


if __name__ == "__main__":
    cases = ("default-mounts", "direct-mounts", "missing-envdir", "nonempty-envdir")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=cases)
    parser.add_argument("--check-compatible", action="store_true")
    args = parser.parse_args()
    failures = []
    for case in (args.case,) if args.case else cases:
        with TemporaryDirectory() as tmp:
            observed = asyncio.run(observe(case, Path(tmp)))
        print(json.dumps(observed, sort_keys=True))
        if args.check_compatible and (
            observed.get("result") != {"reward": 1}
            or observed.get("reward_file") != {"reward": 1}
            or "agent-input.txt" in observed.get("tests_at_start", [])
        ):
            failures.append(case)
    if failures:
        raise SystemExit("Failed compatibility cases: " + ", ".join(failures))
