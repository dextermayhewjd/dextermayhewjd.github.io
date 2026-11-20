"""Use separate processes to save and restore one HarborDataSource checkpoint."""

import argparse
import os
from importlib.metadata import version
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dressage.integrations.harbor import compat
from dressage.integrations.harbor.data_source import HarborDataSource, HarborDataSourceCheckpointError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("save", "load"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    installed = version("harbor")
    assert installed in {"0.18.0", "0.26.0"}
    config = {
        "job_name": "stable-name",
        "tasks": [{"path": "a"}, {"path": "b"}],
        "agents": [{"name": "claude-code", "model_name": "Qwen/Qwen3.5-4B"}],
    }
    with patch.object(compat, "SUPPORTED_HARBOR_VERSION", installed):
        source = HarborDataSource(SimpleNamespace(
            harbor_integration_config={"execution_mode": "training", "training": {"model_override": "fixture"}},
            harbor_job_config=config, harbor_data_source_checkpoint_dir=args.directory,
            n_samples_per_prompt=2, rollout_seed=7, rollout_shuffle=False, harbor_run_id="checkpoint-probe",
        ))
        if args.operation == "save":
            source.get_samples(1)
            source.save(1)
            outcome = "saved"
        else:
            try:
                source.load(1)
            except HarborDataSourceCheckpointError as exc:
                outcome = str(exc)
            else:
                outcome = "restored"
    print(installed, f"hashseed={os.environ['PYTHONHASHSEED']}", args.operation, outcome,
          f"source={source._source_digest[:12]}", f"registry={source._resolved_digest[:12]}",
          f"cursor={source.sample_offset}", f"index={source.sample_index}")


if __name__ == "__main__":
    main()
