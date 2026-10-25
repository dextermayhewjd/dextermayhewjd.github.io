# 从 Slime `generate.py` 切入 Dressage：提炼抽象层级与评测方式

记录日期：2026-10-24。

本文保存读完 `slime/examples/coding_agent_rl/generate.py` 后，围绕“**构建合适的评测方式并提炼合适的抽象层级，同时能够测试不同场景**”这一目标，切入 [`Dressage`](/home/fredkeira/projects/Dressage/README.md) 的判断、四层解耦对照与三步最小阅读路线。

它补充 [Slime 后续阅读顺序](README.md)、[generate() 生命周期的阅读结论](generate-lifecycle-reading-conclusion.md)、[Slime 到 Dressage 的阅读顺序](slime-to-dressage-reading-order.md) 与 [混元岗位对齐与评测抽象分析](hunyuan-jd-and-eval-abstraction-analysis.md)。本文记录后续选读路线，实际阅读进度与掌握状态继续以 [唯一阅读路线](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续) 为准；保存本文不表示已经开始或完成这些函数的阅读。

- 本地源码路径与版本基准：
  - Slime：`/home/fredkeira/projects/slime`（HEAD `18868a79b0b083a093798a94ed0f8cb4f71b9c14`）
  - Dressage：`/home/fredkeira/projects/Dressage`（HEAD `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`）

---

## 为什么现在适合直接切入 Dressage？

**非常适合直接看 [`Dressage`](/home/fredkeira/projects/Dressage/README.md)，而且现在正是切入 `Dressage` 最好的时机。**

原因很直接：

1. **`Dressage` 就是为了解决你说的这个耦合问题而生的**：它把 [`slime`](/home/fredkeira/projects/slime) 作为底层 submodule，没有改 `slime` 的训练内核，而是专门把 `slime/examples/coding_agent_rl/generate.py` 里揉成一团的**“沙箱管理、Agent 交互、任务前后置准备、评测执行、奖励计算”**拆成了正交的抽象层。
2. **你刚读完 `slime` 的 `generate.py`，正好有具体的对照基线**：如果没读过 `slime` 直接看 `Dressage`，会觉得它的 `Paddock`、`Stage Hooks`、`Reward Registry` 很绕；但现在你清楚 `coding_agent_rl` 耦合的痛点，拿 `Dressage` 做 **1 对 1 对照**，马上就能看懂“为什么要这么抽、评测怎么跟 rollout 解耦”。

---

## 一、怎么通过 `Dressage` 提炼“抽象层级”与“评测方式”？（对照图）

你**不需要**通读整个 `Dressage`（像 MoE 路由回放 R3、TransferQueue 内存卸载、Step Balance 负载均衡、TITO 分词细节都可以先忽略），只需要紧盯它把 `slime` 的 `_generate` 拆开的 **4 个核心抽象层**：

```text
【Slime 的 coding_agent_rl/_generate（全部耦合在一个函数里）】
  boot_agent_sandbox → swe.prepare_workspace → harness.run → swe.git_diff → swe.run_evaluation → adapter.finish_session(reward)

                      ⇓  Dressage 的解耦与提炼  ⇓

【第 1 层：环境与 Agent 交互抽象（Paddock）】
  BlackboxPaddock (init / register_agent / call_agent / execute_cmd / write_files / terminate)
  （屏蔽底层是 local_bwrap 还是 E2B，屏蔽里面跑的是 claude_code、codex 还是 openclaw）

【第 2 层：数据驱动的阶段钩子（Stage Hooks：before_agent / after_agent）】
  由每条样本的 metadata["blackbox_execute_cmds"] 决定跑什么准备命令和收集命令，输出结果记入 metadata["execute_cmds"]

【第 3 层：可插拔的评测执行方式（Evaluation Staging）】
  ├─ 方式 A（同沙箱常规钩子）：Agent 结束后直接在原沙箱跑 after_agent 命令（blackbox_dispatch.py）
  ├─ 方式 B（同沙箱分阶段注入 Grader，如 Claw）：防提前泄露，Agent 跑完后才注入 after_agent_files + 对话历史，再跑评测脚本
  └─ 方式 C（异沙箱干净评测 Fresh Eval，如 SWE-Gym）：提取 patch + 防作弊检查（禁改测试文件）→ 新开干净沙箱打补丁跑测试

【第 4 层：解耦的奖励计算注册表（Reward Registry）】
  generate() 只管把评测命令输出留在 sample.metadata["execute_cmds"]，不直接耦合算分逻辑；
  Slime 外层调 custom_rm(sample)，按 sample.metadata["reward_fn"] 路由给对应的 @register_reward 纯函数解析出分数
```

对应的具体代码位置对照表：

| 你关心的目标 | `slime` 里的原写法 | `Dressage` 里的解耦抽象与具体函数 |
| --- | --- | --- |
| **1. 顶层编排怎么去 SWE 化？** | [`coding_agent_rl/generate.py::_generate`](/home/fredkeira/projects/slime/examples/coding_agent_rl/generate.py#L254-L413) | [`dressage/rollout/generate/blackbox_dispatch.py::generate`](/home/fredkeira/projects/Dressage/dressage/rollout/generate/blackbox_dispatch.py#L116-L250)：只编排 `paddock.init → register_agent → before_agent hooks → call_agent → after_agent hooks → finalize_session`。 |
| **2. 环境与命令钩子怎么抽象？** | 写死 `swe.prepare_workspace` | - 接口契约：[`dressage/paddock/interface.py::BlackboxPaddock`](/home/fredkeira/projects/Dressage/dressage/paddock/interface.py#L32-L108)<br>- 前后置命令调度：[`dressage/paddock/blackbox/execute_hooks.py::execute_blackbox_cmds_for_stage`](/home/fredkeira/projects/Dressage/dressage/paddock/blackbox/execute_hooks.py#L77-L97) |
| **3. 不同场景的评测方式怎么设计？** | 写死 `swe.git_diff` + `swe.run_evaluation` | - **SWE-Gym（提取补丁 + 防篡改测试检查 + 干净沙箱评测）**：[`blackbox_dispatch_swegym.py::generate`](/home/fredkeira/projects/Dressage/dressage/rollout/generate/blackbox_dispatch_swegym.py#L213-L245) → [`execute_fresh_swegym_eval`](/home/fredkeira/projects/Dressage/dressage/recipes/swegym/evaluator.py#L48-L160)<br>- **Dressage-Claw（跑完后分阶段注入评测文件 + 导出对话消息给 Grader）**：[`dressage/recipes/dressage_claw/dispatch.py::generate`](/home/fredkeira/projects/Dressage/dressage/recipes/dressage_claw/dispatch.py#L233-L450) |
| **4. 算分（Reward）怎么跟评测执行解耦？** | 在 `_generate` 内部算完传给 `finish_session` | - 统一入口：[`dressage/reward/custom_rm.py::custom_rm`](/home/fredkeira/projects/Dressage/dressage/reward/custom_rm.py#L36-L47) + 注册表 [`dressage/reward/registry.py`](/home/fredkeira/projects/Dressage/dressage/reward/registry.py#L14-L71)<br>- 各场景解析器：[`swegym/reward.py::swegym_harness_marker_reward`](/home/fredkeira/projects/Dressage/dressage/recipes/swegym/reward.py#L43-L77)、[`dressage_claw/reward.py::claw_grader`](/home/fredkeira/projects/Dressage/dressage/recipes/dressage_claw/reward.py#L37-L51) |

---

## 二、建议接下来怎么推进（最小阅读路线）

为了直接服务于你的第一目的（**构建合适的评测方式 + 提炼合适的抽象层级**），建议只用 **3 步** 读完 `Dressage` 最精华的这层设计：

1. **第一步（提炼主干抽象）**：看 [`blackbox_dispatch.py::generate`](/home/fredkeira/projects/Dressage/dressage/rollout/generate/blackbox_dispatch.py#L116-L250) + [`BlackboxPaddock`](/home/fredkeira/projects/Dressage/dressage/paddock/interface.py#L32-L108) + [`execute_hooks.py`](/home/fredkeira/projects/Dressage/dressage/paddock/blackbox/execute_hooks.py#L18-L97)
   - **弄清什么**：对比 `slime` 的 `_generate`，看它是如何用 `Paddock` 统一环境操作、用 `before_agent / after_agent` 阶段钩子替掉写死的任务准备与后处理的。
2. **第二步（对比两种典型评测方式）**：横向对比 **SWE-Gym 的异沙箱评测**（[`execute_fresh_swegym_eval`](/home/fredkeira/projects/Dressage/dressage/recipes/swegym/evaluator.py#L48-L160)）与 **Dressage-Claw 的同沙箱分阶段注入评测**（[`dressage_claw/dispatch.py`](/home/fredkeira/projects/Dressage/dressage/recipes/dressage_claw/dispatch.py#L320-L435)）
   - **弄清什么**：不同评测场景（代码 diff 测试 vs 复杂文件/对话综合 Grader、防 Agent 作弊偷看测试）分别在哪个钩子位置接入。
3. **第三步（解耦算分与单元测试验证）**：看 [`custom_rm.py`](/home/fredkeira/projects/Dressage/dressage/reward/custom_rm.py#L14-L47) + [`registry.py`](/home/fredkeira/projects/Dressage/dressage/reward/registry.py#L14-L71) 以及对应的测试（如 `tests/` 下对 dispatch 和 reward 的测试）
   - **弄清什么**：如何把“在沙箱里跑评测脚本收集 stdout/marker”与“纯 Python 解析 stdout 算 reward”彻底分开，从而不用启动沙箱就能单测各种算分与防作弊逻辑。

---

## 三、待确认的下一步

1. 先从上面的 **第一步（[`blackbox_dispatch.py::generate`](/home/fredkeira/projects/Dressage/dressage/rollout/generate/blackbox_dispatch.py#L116-L250) 对照 `slime` 的 `_generate`）** 开始，使用 `repo-reading-scope` 方法提取它的核心骨架？
2. 这部分记录是希望在 `00-repo-reading/repositories/` 下新建一个 `dressage/` 项目目录来独立保存，还是先在聊天中带读对照？
