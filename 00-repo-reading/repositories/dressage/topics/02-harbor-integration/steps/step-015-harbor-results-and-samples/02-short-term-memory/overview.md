# Step 015 · 本步函数记录

| 函数 | 本次用途 |
| --- | --- |
| [SingleStepTrial._run](functions/harbor/trial/single_step.py/SingleStepTrial._run.md) | 调取已读父函数，定位日志、产物与评测交接 |
| [Trial._upload_agent_logs](functions/harbor/trial/trial.py/Trial._upload_agent_logs.md) | 前序：同步哪些日志、从哪里到哪里、为何需要；已建卡，待个人反馈 |
| [SingleStepTrial._collect_artifacts](functions/harbor/trial/single_step.py/SingleStepTrial._collect_artifacts.md) | 前序：配置与约定目录中的文件如何收集、本地结果与防重复标记；用户表示差不多明白，未展开全部实现 |
| [SingleStepTrial._run_verifier](functions/harbor/trial/single_step.py/SingleStepTrial._run_verifier.md) | 前序：评测开关、环境选择与结果写回；已建卡，待个人反馈 |
| [Verifier.verify](functions/harbor/verifier/verifier.py/Verifier.verify.md) | 前序：部署并运行题目测试、取得奖励文件、返回 VerifierResult；官方任务示例静态推演 |
| [DressageHarborPlugin._on_end](functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_end.md) | 前序：Harbor END 如何交给 Dressage，定位尝试并创建/复用收尾 Task |
| [DressageHarborPlugin._finalize_attempt](functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._finalize_attempt.md) | 后续返回：提交、登记 bundle、关闭本次路由；随后进入 commit_attempt 的任务复用与返回 |
| [Trial._finalize](functions/harbor/trial/trial.py/Trial._finalize.md) | 前序回查：调取前序卡，补清 Harbor 收尾与 _emit(END) 如何进入 Dressage |
| [HarborArtifactStore.commit_attempt](functions/dressage/integrations/harbor/artifacts.py/HarborArtifactStore.commit_attempt.md) | 前序：按 Trial 身份查找/复用提交 Task，等待并返回 bundle；下游仅选读数据汇合 |
| [HarborArtifactStore._commit_attempt_once](functions/dressage/integrations/harbor/artifacts.py/HarborArtifactStore._commit_attempt_once.md) | 前序局部阅读：数据来源、bundle 构造与 trainable；保存和恢复仅定位 |
| [DressageHarborPlugin.on_job_end](functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin.on_job_end.md) | 前序：Job 结果身份、推迟选择分支、收尾并返回外层 |
| [_bundle_samples](functions/dressage/integrations/harbor/rollout.py/_bundle_samples.md) | 前序：模型记录展开为 Sample，补来源与奖励，返回外层 |
| [expand_segments_to_samples](functions/dressage/rollout/multi_segment.py/expand_segments_to_samples.md) | 本步调取：补 Harbor 场景下一个 segment 到一个 Sample 的具体字段例子，保留历史记录 |
| [_run_partition](functions/dressage/integrations/harbor/rollout.py/_run_partition.md) | 当前调取：保留历史主干，接续 Sample 归组、组检查、最终登记及返回 |
| [HarborArtifactStore.write_job_manifest](functions/dressage/integrations/harbor/artifacts.py/HarborArtifactStore.write_job_manifest.md) | 当前：按 final_keys 更新选用状态，形成清单并标记提交完成 |

[本步 scope](../01-scope.md) · [前序累计](../03-long-term-memory/overview.md)
