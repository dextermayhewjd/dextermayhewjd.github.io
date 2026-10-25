# Step 2 · CLI 结束后的运行统计与补丁提取

[前一步：一次模型请求](../step-001-harness-to-adapter/README.md) · [后一步：独立评测](../step-003-swe-evaluation/README.md) · [当前阅读进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

Step 1 已沿 `_run_turn` 讨论一次模型请求。这里回到 `_generate`，将观察位置移到整个 `harness.run` 返回之后：执行沙箱仍可访问，主流程先读取运行统计，再提取代码补丁。

本步问题是：**这两个调用分别取什么、如何取、交回什么，以及结果随后交给谁？** 按 `collect_metrics → git_diff` 的顺序逐个阅读；评测保留在独立的下一步。

```text
harness.run 返回：CLI 已结束
    ↓
collect_metrics → agent_metrics：运行统计
    ↓
swe.git_diff → diff_text：代码补丁
    ↓
退出执行沙箱 → 后一步进入独立评测
```

这是当前范围的导航图，不是阅读完成后的总结。`agent_metrics` 与 `diff_text` 各有消费者，前者不作为后者的输入。

- [01 · 阅读范围](01-scope.md)：整体骨架、具体实现、局部调用，以及 [3.4 阅读路径图与函数导航](01-scope.md#reading-path)。
- [02 · 本步短期记忆](02-short-term-memory/overview.md)：随逐个函数的实际阅读建立，当前不预填理解。
- [03 · 前序累计记忆](03-long-term-memory/overview.md)：完整继承 Step 1 的 20 份函数、类与实现引用记录，保留来源、版本和未知。
- [04 · 问题与解释](04-flow.md)：保存本步为何独立、已确认范围和后续反馈。
- [05 · 阅读后的任务链路](05-task-flow.md)：按执行图串起实际交接、结果去向与本步边界；阅读导航统一回到 scope。

**第一处阅读入口**：[ClaudeCodeHarness.collect_metrics 函数卡片](02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.collect_metrics.md)，对应 `claude_code.py:111–120`。先对照统计文件内容与返回字典，再回到调用方读 `git_diff`。

需要解释统计从哪里产生时，进入[压缩统计的产生与收集机制](references/compaction-metrics-lifecycle.md)。它集中连接初始化、事件更新与读取；函数卡只保留本次调用的输入输出和机制入口。

本次追溯文件的写入，单独进入 [run_hook 函数卡片](02-short-term-memory/functions/slime/agent/harness/compaction.py/run_hook.md)：先看一个事件怎样读取、修改并写回统计，再回到 `collect_metrics`。这是回看输入生产者，不是 `collect_metrics` 内部调用了 hook。

随后按用户确认补看准备阶段：[write_config 的脚本复制与 hook 注册](02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md) → [launch_and_wait 的统计清零与启动](02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md#compaction-initialization)。旧函数完整记录已调入本步；本轮只展开与统计输入有关的阶段。

统计部分按本轮目标收束后，进入 [git_diff 函数卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/git_diff.md)：先接住运行前的 `baseline`，取得结束时的 `current`，再比较并返回补丁。快照辅助函数先保留接口与源码入口，不自动展开全部 Git 内部机制。

本步绑定 Slime `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。2026-10-23，按已确认范围收束这轮阅读，并保存 [task flow](05-task-flow.md)：统计与补丁提取的输入、处理和下游用途已经接清。用户的具体表述与尚未确认的细分理解仍保留在卡片和 flow；真实远端运行、Git 快照内部机制与 hook 的完整停止处理未展开。原 Step 002–008 已顺延为 Step 003–009，历史编号与记忆快照的关系见[编号对照](../../../../step-numbering-2026-10-23.md)。
