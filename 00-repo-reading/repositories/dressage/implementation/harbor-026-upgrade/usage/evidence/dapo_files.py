"""Compare the generated DAPO task and reward file with the installed Harbor reader."""

import json
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from examples.harbor.dataset_tools.dapo.prepare_dataset import prepare_dataset
from harbor.environments.base import BaseEnvironment
from harbor.models.task.task import Task
from harbor.models.trial.paths import TrialPaths
from harbor.models.verifier.result import VerifierResult
from harbor.verifier.verifier import Verifier


def observe(root: Path) -> None:
    source = root / "input.jsonl"
    prompt = "What is 2 + 2?"
    row = {
        "prompt": [{"role": "user", "content": prompt}],
        "label": "4",
        "metadata": {"instance_id": "dapo_math_00000"},
        "agent_mode": "blackbox",
        "blackbox_type": "claude_code",
        "reward_fn": "contains_label",
        "task_type": "math",
    }
    source.write_text(json.dumps(row) + "\n", encoding="utf-8")
    dataset = prepare_dataset(source, cache_root=root / "cache", limit=1)
    task = Task(dataset.tasks_dir / "dapo_math_00000")
    assert task.name == "dressage/dapo_math_00000" and task.instruction.strip() == prompt
    print(f"Harbor {version('harbor')} | Task.name={task.name} | instruction={task.instruction.strip()}")

    paths = TrialPaths(root / "trial")
    paths.mkdir()
    environment = Mock(spec=BaseEnvironment)
    verifier = Verifier(task, paths, environment)
    for case, answer, expected in (("correct", "4", 1), ("incorrect", "5", 0)):
        stream = root / "claude-code.txt"
        stream.write_text(json.dumps({"type": "result", "result": answer}) + "\n", encoding="utf-8")
        subprocess.run([
            sys.executable, str(task.paths.tests_dir / "verify.py"),
            "--stream", str(stream), "--expected", str(task.paths.tests_dir / "expected.json"),
            "--reward", str(paths.reward_json_path), "--details", str(root / "details.json"),
        ], check=True)
        raw = paths.reward_json_path.read_text(encoding="utf-8").strip()
        result = VerifierResult(rewards=verifier._parse_reward_json())
        assert json.loads(raw) == result.rewards == {"reward": expected}
        print(f"{case} | reward.json={raw} | VerifierResult.rewards={result.rewards}")
    assert not environment.mock_calls


if __name__ == "__main__":
    with TemporaryDirectory() as directory:
        observe(Path(directory))
