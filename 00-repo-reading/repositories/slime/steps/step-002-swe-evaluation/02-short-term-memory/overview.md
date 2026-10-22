# 02 · Step 2 的短期函数记录

[本步主线](../README.md) · [前序函数记忆](../03-long-term-memory/overview.md)

| 源码文件 | 函数记录 | 来源与状态 |
| --- | --- | --- |
| `examples/coding_agent_rl/swe.py` | [run_evaluation](functions/examples/coding_agent_rl/swe.py/run_evaluation.md) | Step 2；已讨论两个 grader 的分派与选择理由；完整输入输出为提前整理的材料 |
| `examples/coding_agent_rl/swe.py` | [_grade_scaleswe](functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md) | Step 2；已展开结果组装、上下文退出与向外返回；四条退出路径有替身验证，完整交接尚未确认理解 |
| `slime/agent/sandbox.py` | [E2BSandbox.__aenter__](functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md) | Step 2；用户已复述进入时根据镜像配置申请远端沙箱；内部过程暂作黑箱，已有替身 SDK 的局部验证 |
| `slime/agent/sandbox.py` | [E2BSandbox.__aexit__](functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md) | Step 2；退出实现已从父卡独立归档，保留已有四条替身验证；尚无行为理解反馈 |
| `slime/agent/sandbox.py` | [ensure_agent_user](functions/slime/agent/sandbox.py/ensure_agent_user.md) | Step 2；用户已复述创建后调用 exec 执行准备内容；具体命令、协议关系与运行位置仍在核对 |
| `examples/coding_agent_rl/swe.py` | [_apply_diff](functions/examples/coding_agent_rl/swe.py/_apply_diff.md) | Step 2；用户已初步理解先写补丁、再执行命令修改源码；通用接口边界及命令细节仍待澄清 |
| `examples/coding_agent_rl/swe.py` | [_run_eval_cmd](functions/examples/coding_agent_rl/swe.py/_run_eval_cmd.md) | Step 2；已随用户继续阅读展开命令来源、执行与退出码评分；尚无理解反馈，未运行真实测试 |

`E2BSandbox.__aenter__` 保留精简函数模型，[展开说明](../references/sandbox-entry.md)单独回查；其余必要能力仍在 `_grade_scaleswe` 中定位，未展开完整后端实现。以上文件存在表示材料已整理，不表示用户已经理解或实际运行；接续统一见[阅读路线](../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。
