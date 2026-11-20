"""Reproduce ordinary Oracle log delivery with an initially empty host bind at /logs."""

import json

import pytest
from harbor.models.trial.config import TrialConfig
from harbor.trial.trial import Trial


@pytest.mark.asyncio
async def test_trial_delivers_agent_log(monkeypatch, tmp_path):
    integration_config = {
        "environment": {"mode": "bwrap", "runtime_root": str(tmp_path / "runtime")},
        "gateway": {"listen_port": 39100},
        "security": {"routing_guarantee": "enforced"},
    }
    integration = tmp_path / "integration.json"
    integration.write_text(json.dumps(integration_config))
    monkeypatch.setenv("DRESSAGE_HARBOR_INTEGRATION_CONFIG", str(integration))
    host_logs = tmp_path / "host-logs"
    host_logs.mkdir()

    task = tmp_path / "task"
    for name in ("environment", "solution", "tests"):
        (task / name).mkdir(parents=True)
    (task / "task.toml").write_text(
        'schema_version = "1.3"\n[environment]\ngpus = 0\nnetwork_mode = "public"\n'
    )
    (task / "instruction.md").write_text("Write 4 to /app/answer.txt.")
    (task / "solution/solve.sh").write_text(
        "#!/bin/sh\nset -eu\nmkdir /logs/agent/run\n"
        "printf 'fresh probe\\n' > /logs/agent/run/probe.log\n"
        "echo 4 > /app/answer.txt\necho solved\n"
    )
    (task / "tests/test.sh").write_text(
        "#!/bin/sh\nset -eu\n"
        'test "$(cat /app/answer.txt)" = 4\n'
        "echo '{\"reward\": 1}' > /logs/verifier/reward.json\n"
    )
    config = TrialConfig.model_validate(
        {
            "task": {"path": task},
            "agent": {"name": "oracle"},
            "environment": {
                "import_path": "dressage.integrations.harbor.environment:DressageEnvironment",
                "mounts": [{"type": "bind", "source": str(host_logs), "target": "/logs"}],
            },
            "trial_name": "oracle-logs",
            "trials_dir": tmp_path / "trials",
        }
    )
    trial = await Trial.create(config)
    result = await trial.run()

    assert result.exception_info is None, result.exception_info
    assert result.verifier_result is not None
    assert result.verifier_result.rewards == {"reward": 1}
    assert (trial.paths.agent_dir / "oracle.txt").read_bytes() == b"solved\n"
    assert (trial.paths.agent_dir / "run/probe.log").read_bytes() == b"fresh probe\n"
