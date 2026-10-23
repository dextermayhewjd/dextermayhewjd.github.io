# 02 · Step 3 的短期函数记录

[本步主线](../README.md) · [前序函数记忆](../03-long-term-memory/overview.md)

| 源码文件 | 函数记录 | 来源与状态 |
| --- | --- | --- |
| `examples/coding_agent_rl/swe.py` | [_metadata_scaleswe](functions/examples/coding_agent_rl/swe.py/_metadata_scaleswe.md) | Step 3 新版校准；已局部验证完整 `md` 字典；用户初步概括取得所需任务信息，字段回退规则未逐项确认 |
| `examples/coding_agent_rl/swe.py` | [run_evaluation](functions/examples/coding_agent_rl/swe.py/run_evaluation.md) | Step 3；已按 `18868a79` 校准；用户已概括 `EvalResult` 的两个字段，助手校准与 `_run_eval_cmd` 的返回层级；分派和退出细节未逐项确认 |
| `examples/coding_agent_rl/swe.py` | [_grade_scaleswe](functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md) | Step 3；已按 `18868a79` 接回组装、退出与返回，已有六种路径的替身验证；本轮按 scope 收束主线，结果组合及清理细节仍保留边界 |
| `examples/coding_agent_rl/swe.py` | [_evaluation_sandbox](functions/examples/coding_agent_rl/swe.py/_evaluation_sandbox.md) | Step 3 新版校准；已用替身验证环境交接；用户已概括进入与退出阶段的追踪，完整流程未逐项复述 |
| `slime/agent/sandbox.py` | [E2BSandbox.__aenter__](functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md) | Step 3；用户已复述进入时根据镜像配置申请远端沙箱；内部过程暂作黑箱，已有替身 SDK 的局部验证 |
| `slime/agent/sandbox.py` | [E2BSandbox.__aexit__](functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md) | Step 3；退出实现已从父卡独立归档，保留已有四条替身验证；尚无行为理解反馈 |
| `slime/agent/sandbox.py` | [ensure_agent_user](functions/slime/agent/sandbox.py/ensure_agent_user.md) | Step 3；已按 `18868a79` 校准后端标记、命令及超时并做替身验证；保留此前“创建后执行准备内容”的复述，尚无新版分支的理解反馈 |
| `examples/coding_agent_rl/swe.py` | [_apply_diff](functions/examples/coding_agent_rl/swe.py/_apply_diff.md) | Step 3；已按 `18868a79` 校准并做替身验证；用户已复述保存补丁、应用修改、判断成功的主线，工具冲突处理未展开 |
| `examples/coding_agent_rl/swe.py` | [_run_eval_cmd](functions/examples/coding_agent_rl/swe.py/_run_eval_cmd.md) | Step 3；已按 `18868a79` 校准并做替身验证；用户已概括通过得 1、未通过得 0，助手补充命令来源与退出码口径；长命令细节尚无理解反馈，未运行真实测试 |

`E2BSandbox.__aenter__` 保留精简函数模型，[展开说明](../references/sandbox-entry.md)单独回查；其余必要能力仍在 `_grade_scaleswe` 中定位，未展开完整后端实现。以上文件存在表示材料已整理，不表示用户已经理解或实际运行；接续统一见[阅读路线](../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。
