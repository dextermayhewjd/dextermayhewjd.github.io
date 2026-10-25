# Step 3 · 代码改动如何在独立环境中得到奖励

**目录编号调整**：本目录由原 Step 002 顺延而来；历史过程、函数来源和固定样例里的原编号保留当时语境，见[新旧编号对照](../../../../step-numbering-2026-10-23.md)。编号调整本身不改变原源码版本或学习结论。

[前一步：运行统计与补丁提取](../step-002-agent-results/README.md) · [当前阅读进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

**2026-10-23 新版校准**：[scope](01-scope.md#reading-path)已按 `18868a79` 更新整体入口、输入来路、环境工厂与阅读导航；[旧版 scope](references/scope-at-2f231865.md)完整保留。新增 [_metadata_scaleswe 卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_metadata_scaleswe.md)补清本步输入，[_evaluation_sandbox 卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_evaluation_sandbox.md)解释新版环境交付与退出；[ensure_agent_user 卡片](02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)、[_apply_diff 卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_apply_diff.md)和 [_run_eval_cmd 卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_run_eval_cmd.md)已校准新版条件、命令和路径，旧卡完整归档。[_grade_scaleswe](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md)与 [run_evaluation](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/run_evaluation.md)也已接回新版结果交接，完整旧卡保存在 references。两张 E2B 卡片的实现经核对未变，保留原版本证据；task flow 已同步本轮评测交接并归档旧稿，累计记忆保留原版本，具体变化见[核对记录](references/scope-version-review-2026-10-23.md)。

2026-10-21，用户确认开启本步，并要求先重新核对腾讯混元 Agent 强化学习框架工程师 JD。前一步已理解 `_run_turn` 的整体处理；现在回到 `generate`，跟随 CLI 结束后的代码改动，读清评测环境、测试结果与奖励的交接。[范围确认与岗位依据](04-flow.md#scope-confirmed)

## 为什么此时读评测

岗位涉及可复用的评估组件、不同评测逻辑的接入、验证机制，以及资源和行为一致性。本步用一份具体补丁研究这些接口：什么进入评测，谁准备环境，怎样产生奖励，哪些失败会影响对结果的判断。详细条款映射见[岗位对照](../../../../../../../slime_photo/code-reading/job-alignment.md#step-2-evaluation-choice)。

本步以 `swe.run_evaluation` 为入口，实际编排函数是 `_grade_scaleswe`。先走源码支持的 `scaleswe → eval_cmd` 分支；这是教学选定的最小场景，未声称当前实际数据集已经采用它。`swepro`、`f2p_script` 和 SWE-bench 分支保留位置，后续按问题展开。

## 从这里开始读

1. [scope：整体骨架与阅读图](01-scope.md#reading-path)：定位 `_generate` 的第 6 项，再按观察点进入、回查和返回。
2. [3.2 输入衔接](01-scope.md#input-bridge)与 [_metadata_scaleswe 卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_metadata_scaleswe.md)：接住 Step 002 的 `diff_text`，对照原始样本与完整返回字典，认识本步的 `md`、`grading` 与 `eval_cmd`；其余参数先识别用途。
3. [run_evaluation 卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/run_evaluation.md)：对照输入例子看协议分派、`trace` 传递与返回值。
4. [_grade_scaleswe 卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md)：先看从 `md` 取值，再进入 [_evaluation_sandbox 卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_evaluation_sandbox.md)，理解 `ev` 的交付与退出；后续按 scope 继续补丁、测试与返回。

环境入口先从 [scope 的实现来路](01-scope.md#step-3-branch)定位 `_evaluation_sandbox → create_sandbox`，看清 `ev` 的交付与使用期。新版默认选择 Sunabako，内部实现暂不展开；显式选择 `e2b` 时，可回查 [E2BSandbox.__aenter__](02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md)、[__aexit__](02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md)及[原基础说明](references/sandbox-entry.md)。具体传输、重试与集群部署不作为读通评测的前置；本步接口理解也不等于完成 Kubernetes 实践。

## 本步材料与记忆继承

- [02 · 本步函数记录](02-short-term-memory/overview.md)：元数据整理、评分入口、评分编排、环境进入与退出、用户准备、补丁应用、命令评分。
- [03 · 前序函数记忆](03-long-term-memory/overview.md)：原步形成时继承 Step 1 的 `03 + 02`，共 17 份函数记录；当前仍是当时的快照，保留原话、来源、版本和未知。
- [04 · 问题与解释](04-flow.md)：范围确认、岗位核对、首轮解释与后续反馈。
- [05 · 阅读后的任务总结](05-task-flow.md)：按 `18868a79` 收拢环境、补丁、评分与返回交接，保留层级图、两项结果和未展开边界；[旧版总结](references/task-flow-at-2f231865.md)完整归档，各函数实现仍从 `02` 回查。

历史学习、验证记录及尚未校准的函数卡片依据 Slime `2f2318653f6f794dddd321eff7c9d4b7b174643f`；新版 scope 的更新不改变这些历史结论。样例是教学构造；`__aenter__` 另用替身 SDK 验证本地传参与对象关系，没有执行真实 E2B、pytest 或训练。用户已复述进入 `async with` 时根据已有镜像配置申请远端沙箱的关系；首轮其余创建机制暂作黑箱。本轮已按既定范围收拢评测主线，返回层级的校准与收束判断见[本次记录](04-flow.md#evaluation-flow-closure-18868a79)。实际接续只在[唯一路线](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)维护。
