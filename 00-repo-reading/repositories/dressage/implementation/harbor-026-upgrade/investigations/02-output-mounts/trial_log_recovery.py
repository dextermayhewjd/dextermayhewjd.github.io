"""Replay Harbor's agent-log recovery with a direct or separately bound log directory."""

import argparse
import asyncio
import json
import os
import shutil
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from harbor.models.trial.config import TrialConfig
from harbor.trial.trial import Trial

from dressage.integrations.harbor.environment import DressageEnvironment


async def observe(root: Path, *, check_compatible: bool, separate_source: bool) -> None:
    task = root / "task"
    fixture = Path(__file__).resolve().parents[1] / "09-trial-plan/tasks/first"
    shutil.copytree(fixture, task)
    for directory in ("environment", "solution", "tests"):
        (task / directory).mkdir()
    for script in ("solution/solve.sh", "tests/test.sh"):
        (task / script).write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

    profile = root / "dressage.json"
    profile.write_text(json.dumps({
        "gateway": {"listen_port": 39100},
        "environment": {"mode": "bwrap", "runtime_root": str(root / "runtime")},
        "security": {"routing_guarantee": "enforced"},
    }), encoding="utf-8")
    environment_config = {"import_path": "dressage.integrations.harbor.environment:DressageEnvironment"}
    external_logs = root / "external-agent-logs"
    if separate_source:
        external_logs.mkdir()
        environment_config["mounts"] = [
            {"type": "bind", "source": str(external_logs), "target": "/logs/agent"},
        ]
    config = TrialConfig.model_validate({
        "task": {"path": task}, "agent": {"name": "oracle"},
        "environment": environment_config,
        "trial_name": "logs-a", "trials_dir": root / "trials",
    })
    with patch.dict(os.environ, {"DRESSAGE_HARBOR_INTEGRATION_CONFIG": str(profile)}), patch(
        "dressage.integrations.harbor.environment._required_binary", side_effect=lambda name: f"/usr/bin/{name}",
    ):
        trial = await Trial.create(config)
    env = trial.agent_environment
    try:
        assert isinstance(env, DressageEnvironment)
        await env.start(force_build=False)
        sandbox_dir = env._host_path(trial.agent_env_paths.agent_dir.as_posix())
        assert sandbox_dir == (external_logs if separate_source else trial.paths.agent_dir)
        sample = b"one nonempty agent log\n"
        (sandbox_dir / "probe.log").write_bytes(sample)
        target_file = trial.paths.agent_dir / "probe.log"
        target_existed_before = target_file.is_file()
        assert target_existed_before == (not separate_source)

        # Count the calls while running both original methods, including their I/O.
        with patch.object(env, "prepare_logs_for_host", wraps=env.prepare_logs_for_host) as prepare, patch.object(
            env, "download_dir", wraps=env.download_dir,
        ) as download:
            result = await trial._download_agent_logs()
        log_text = trial.paths.log_path.read_text(encoding="utf-8")
        preserved = target_file.is_file() and target_file.read_bytes() == sample
        copy_error = "Failed to download logs" in log_text
        relation = "!=" if separate_source else "=="
        print(f"Harbor {version('harbor')} | Trial._download_agent_logs | /logs/agent {relation} host agent_dir")
        if separate_source:
            print(f"target file present before={target_existed_before} | after={target_file.is_file()}")
        print(f"prepare_logs_for_host calls={prepare.await_count} | download_dir calls={download.await_count}")
        print(f"return={result!r} | marked_downloaded={trial._are_agent_logs_downloaded} | file_preserved={preserved}")
        print(f"trial log: copy_error={copy_error} | shutil.Error={'shutil.Error' in log_text}")
        assert result is None and trial._are_agent_logs_downloaded
        if separate_source:
            if check_compatible:
                assert download.await_count == 1 and preserved and not copy_error, (
                    "Logs written outside the Trial directory must be copied once and arrive intact."
                )
        else:
            assert preserved
            if check_compatible:
                assert download.await_count == 0 and not copy_error, (
                    "Direct-mounted logs should already be available without a directory copy or copy error."
                )
    finally:
        try:
            await env.stop(delete=True)
        finally:
            trial._close_logger_handler()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--separate-source", action="store_true", help="Bind /logs/agent to another host directory.")
    parser.add_argument("--check-compatible", action="store_true", help="Assert the expected copy count and file delivery.")
    args = parser.parse_args()
    with TemporaryDirectory() as temporary:
        asyncio.run(observe(Path(temporary), check_compatible=args.check_compatible, separate_source=args.separate_source))
