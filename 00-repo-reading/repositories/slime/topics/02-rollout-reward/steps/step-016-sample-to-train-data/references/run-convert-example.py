"""Run a small data-conversion example using methods from the fixed checkout.

This does not import the full training stack or run a model. It compiles the
unchanged Sample class, get_source, and two BatchBuilder methods from their ASTs.
The chosen branch does not need torch, numpy, Ray, or BatchBuilder.__init__.
"""

import ast
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from types import ModuleType, SimpleNamespace
from typing import Any


SOURCE_ROOT = Path("/home/hongshi/projects/slime")
EXPECTED_HEAD = "18868a79b0b083a093798a94ed0f8cb4f71b9c14"


def main():
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=SOURCE_ROOT, text=True
    ).strip()
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"Review the example before using a new source version: {head}")

    paths = ("slime/utils/types.py", "slime/utils/data.py", "slime/data/batch_builder.py")
    texts = {name: (SOURCE_ROOT / name).read_text() for name in paths}
    trees = {name: ast.parse(text) for name, text in texts.items()}
    sample_node = next(n for n in trees[paths[0]].body if isinstance(n, ast.ClassDef) and n.name == "Sample")
    source_node = next(n for n in trees[paths[1]].body if isinstance(n, ast.FunctionDef) and n.name == "get_source")
    builder_node = next(n for n in trees[paths[2]].body if isinstance(n, ast.ClassDef) and n.name == "BatchBuilder")
    builder_node.body = [
        n for n in builder_node.body
        if isinstance(n, ast.FunctionDef) and n.name in {"_post_process_rewards", "convert"}
    ]

    module = ModuleType("step016_conversion_example")
    sys.modules[module.__name__] = module
    module.__dict__.update(dataclass=dataclass, field=field, Enum=Enum, Any=Any, math=math)
    code = ast.Module(
        body=[*ast.parse("from __future__ import annotations").body, sample_node, source_node, builder_node],
        type_ignores=[],
    )
    exec(compile(ast.fix_missing_locations(code), "<fixed-checkout-methods>", "exec"), module.__dict__)

    sample = module.Sample(
        index=7,
        rollout_id=7,
        tokens=[101, 102, 201, 202],
        response_length=2,
        reward=0.75,
        status=module.Sample.Status.COMPLETED,
    )
    builder = object.__new__(module.BatchBuilder)
    builder.args = SimpleNamespace(
        reward_key=None,
        advantage_estimator="grpo",
        rewards_normalization=False,
        use_score_centering=False,
        rollout_top_p=1.0,
        use_rollout_routing_replay=False,
    )
    builder.custom_reward_post_process_func = None
    builder.custom_convert_samples_to_train_data_func = None
    before = {
        "tokens": list(sample.tokens),
        "response_length": sample.response_length,
        "reward": sample.reward,
        "loss_mask": sample.loss_mask,
        "index": sample.index,
        "rollout_id": sample.rollout_id,
        "status": sample.status.value,
    }
    data = builder.convert([sample])
    result = {
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_root": str(SOURCE_ROOT),
        "source_head": head,
        "source_sha256": {name: hashlib.sha256(text.encode()).hexdigest() for name, text in texts.items()},
        "execution_scope": "Isolated fixed-source Sample/get_source and BatchBuilder.convert/_post_process_rewards; no full module import, constructor, model, Ray or training run.",
        "args": vars(builder.args),
        "input": [before],
        "output": data,
        "after": {
            "sample_loss_mask": sample.loss_mask,
            "sample_reward": sample.reward,
            "tokens_same_object": data["tokens"][0] is sample.tokens,
        },
    }
    destination = Path(__file__).with_name("convert-example-output.json")
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": data, "after": result["after"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
