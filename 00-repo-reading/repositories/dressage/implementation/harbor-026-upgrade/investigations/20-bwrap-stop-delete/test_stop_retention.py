"""Observe whether Harbor's delete flag preserves a stopped Dressage bwrap workspace."""

import json
import shutil
from importlib.metadata import version
from pathlib import Path

import pytest
from harbor.models.trial.config import TrialConfig
from harbor.trial.trial import Trial

from dressage.integrations.harbor.environment import DressageEnvironment


@pytest.mark.asyncio
@pytest.mark.parametrize("delete", [True, False], ids=["delete", "keep"])
async def test_trial_stop_retains_workspace_when_requested(tmp_path, monkeypatch, delete):
    task = tmp_path / "task"
    fixture = Path(__file__).resolve().parents[1] / "09-trial-plan/tasks/first"
    shutil.copytree(fixture, task)
    (task / "environment").mkdir()
    for relative in ("solution/solve.sh", "tests/test.sh"):
        script = task / relative
        script.parent.mkdir()
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

    profile = tmp_path / "dressage.json"
    profile.write_text(json.dumps({
        "gateway": {"listen_port": 39100},
        "environment": {"mode": "bwrap", "runtime_root": str(tmp_path / "runtime")},
        "security": {"routing_guarantee": "enforced"},
    }), encoding="utf-8")
    monkeypatch.setenv("DRESSAGE_HARBOR_INTEGRATION_CONFIG", str(profile))
    trial = await Trial.create(TrialConfig.model_validate({
        "task": {"path": task},
        "agent": {"name": "oracle"},
        "environment": {
            "import_path": "dressage.integrations.harbor.environment:DressageEnvironment",
            "delete": delete,
        },
        "trial_name": "stop-probe",
        "trials_dir": tmp_path / "trials",
    }))
    try:
        await trial._start_agent_environment()
        env = trial.agent_environment
        assert isinstance(env, DressageEnvironment)
        workspace_file = env._host_path("/app/stop-probe.txt")
        workspace_file.write_bytes(b"keep this workspace\n")
        assert env._session_root.is_dir() and workspace_file.is_file()

        await trial._stop_agent_environment()
        session_exists = env._session_root.is_dir()
        file_exists = workspace_file.is_file()
        print(f"Harbor {version('harbor')} | configured delete={delete} | "
              f"trial stopped={trial._is_agent_environment_stopped} | "
              f"session exists after stop={session_exists} | workspace file exists={file_exists}")
        assert trial._is_agent_environment_stopped and not env._started
        assert (session_exists, file_exists) == (not delete, not delete)
        if file_exists:
            assert workspace_file.read_bytes() == b"keep this workspace\n"
    finally:
        trial._close_logger_handler()
