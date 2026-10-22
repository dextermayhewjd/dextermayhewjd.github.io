# Step 2 · 代码改动如何在独立环境中得到奖励

[前一步：一次模型请求](../step-001-harness-to-adapter/README.md) · [当前阅读进度](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

2026-10-21，用户确认开启本步，并要求先重新核对腾讯混元 Agent 强化学习框架工程师 JD。前一步已理解 `_run_turn` 的整体处理；现在回到 `generate`，跟随 CLI 结束后的代码改动，读清评测环境、测试结果与奖励的交接。[范围确认与岗位依据](04-flow.md#scope-confirmed)

## 为什么此时读评测

岗位涉及可复用的评估组件、不同评测逻辑的接入、验证机制，以及资源和行为一致性。本步用一份具体补丁研究这些接口：什么进入评测，谁准备环境，怎样产生奖励，哪些失败会影响对结果的判断。详细条款映射见[岗位对照](../../../../../slime_photo/code-reading/job-alignment.md#step-2-evaluation-choice)。

本步以 `swe.run_evaluation` 为入口，实际编排函数是 `_grade_scaleswe`。先走源码支持的 `scaleswe → eval_cmd` 分支；这是教学选定的最小场景，未声称当前实际数据集已经采用它。`swepro`、`f2p_script` 和 SWE-bench 分支保留位置，后续按问题展开。

## 从这里开始读

1. [scope：整体骨架与本步分支](01-scope.md)：定位 `generate` 的第 6 项，并区分入口与实际编排函数。
2. [run_evaluation](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/run_evaluation.md)：先看 `md + diff_text + timeout_sec → EvalResult`。
3. [_grade_scaleswe](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md)：跟随同一个例子，看新环境、补丁、测试与返回；在实际调用处进入相应子函数卡片。

Sandbox 从 [E2BSandbox.__aenter__ 的精简卡片](02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md) 看创建配置、SDK 对象与 `ev` 的交接，再回父卡看后续用途；退出实现见 [E2BSandbox.__aexit__](02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md)，[基础概念、语法和实现说明](references/sandbox-entry.md)按需回查。具体 E2B 传输、重试与集群部署不作为读通评测的前置；本步接口理解也不等于完成 Kubernetes 实践。

## 本步材料与记忆继承

- [02 · 本步函数记录](02-short-term-memory/overview.md)：评分入口、评分编排、环境进入与退出、用户准备、补丁应用、命令评分。
- [03 · 前序函数记忆](03-long-term-memory/overview.md)：完整继承 Step 1 的 `03 + 02`，共 17 份函数记录；保留原话、来源、版本和未知。
- [04 · 问题与解释](04-flow.md)：范围确认、岗位核对、首轮解释与后续反馈。
- [05 · 阅读后的任务总结](05-task-flow.md)：将已读的环境、补丁、评分与返回交接收拢为一条链，保留关键边界与下一问；各函数实现仍从 `02` 回查。

当前材料依据 Slime `2f2318653f6f794dddd321eff7c9d4b7b174643f` 核对。样例是教学构造；`__aenter__` 另用替身 SDK 验证本地传参与对象关系，没有执行真实 E2B、pytest 或训练。用户已复述进入 `async with` 时根据已有镜像配置申请远端沙箱的关系；其余创建机制暂作黑箱，尚未确认本步完整评测流程。实际接续只在[唯一路线](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)维护。
