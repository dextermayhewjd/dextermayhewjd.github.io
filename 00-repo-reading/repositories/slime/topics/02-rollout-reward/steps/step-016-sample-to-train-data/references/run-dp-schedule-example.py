"""Run the fixed static scheduling example using unmodified source functions.

Only build_dp_schedule and _pack_step_into_mbs are extracted, so importing
Slime's training dependencies is unnecessary. This does not run split_by_dp,
Ray, tensorization, or any dynamic packing/workload-balancing branch.
"""

import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any


source_path = Path("/home/hongshi/projects/slime/slime/utils/dp_schedule.py")
source = source_path.read_bytes()
source_sha256 = hashlib.sha256(source).hexdigest()
expected_sha256 = "ed87386712ecc0e296f038354878c9dd6f8ab5561832febe0f5f272caa9cfd02"
if source_sha256 != expected_sha256:
    raise RuntimeError("Source changed; recheck the example before rerunning.")

names = {"_pack_step_into_mbs", "build_dp_schedule"}
nodes = [
    node for node in ast.parse(source).body
    if isinstance(node, ast.FunctionDef) and node.name in names
]
namespace = {"Any": Any}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source_path), "exec"), namespace)

args = SimpleNamespace(
    use_dynamic_batch_size=False,
    micro_batch_size=1,
    balance_by_flops=False,
    balance_data=False,
)
train_parallel_config = {
    "dp_size": 2,
    "cp_size": 1,
    "vpp_size": 1,
    "microbatch_group_size_per_vp_stage": 1,
}
inputs = {
    "total_lengths": [3, 4],
    "global_batch_size": 2,
    "rollout_indices": [10, 20],
}
result = namespace["build_dp_schedule"](args, train_parallel_config, **inputs)
output_names = ("partitions", "micro_batch_indices", "num_microbatches", "global_batch_sizes")
print(json.dumps({
    "source": str(source_path),
    "source_sha256": source_sha256,
    "runtime_scope": "Unmodified function bodies; static micro-batches, no workload balancing. No split_by_dp, Ray, tensors or training execution.",
    "input": {"args": vars(args), "train_parallel_config": train_parallel_config, **inputs},
    "output": dict(zip(output_names, result)),
}, ensure_ascii=False, indent=2))
