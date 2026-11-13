# Step 011 · 本步短期记录

| 函数 | 本轮范围 |
| --- | --- |
| [Harbor Job.run](functions/harbor/job.py/Job.run.md#job-mainline) | v0.25.0；建立结果 → 等待 Trial → 汇总返回，队列内部尚未展开 |
| [Job._run_trials_with_queue](functions/harbor/job.py/Job._run_trials_with_queue.md#queue-mainline) | 提交配置、创建 Task 并等待、按顺序取回结果；队列包装只定位 |
| [Harbor Trial.run](functions/harbor/trial/trial.py/Trial.run.md#normal-lifecycle) | 正常生命周期主干已复述，已整理首轮总结 |
| [Trial._prepare](functions/harbor/trial/trial.py/Trial._prepare.md#prepare-mainline) | 准备主干已讨论；子方法暂缓 |
| [SingleStepTrial._run](functions/harbor/trial/single_step.py/SingleStepTrial._run.md#single-step-run-mainline) | 执行与评测主干已复述，子方法暂缓 |
| [Trial._finalize](functions/harbor/trial/trial.py/Trial._finalize.md#finalize-mainline) | 收尾主干与 END 调用职责；跨函数连接见 scope 第 5 项 |
| [_run_partition（本步回查）](functions/dressage/integrations/harbor/rollout.py/_run_partition.md#run-job) | 接回 JobResult、组结果检查与产物选用；原卡在 Step 010，补齐本步调取 |

_run_round 与 _run_partition 已按用户确认归回 [Step 010 函数索引](../../step-010-harbor-rollout-entry/02-short-term-memory/overview.md)。_prepare、SingleStepTrial._run 与 _finalize 均已按实际阅读建卡；具体后端、Agent 与事件回调内部按需展开。
