# 05 · 任务链路：CLI 结束后，取回运行统计与代码补丁

> CLI 结束后，`_generate` 趁执行沙箱仍可访问，先读取压缩统计，再比较运行前后的工作区快照。它接回 `agent_metrics` 与 `diff_text`：前者供后续样本记录和状态判断，后者交给独立评测。

[本步 scope](01-scope.md) · [步骤入口](README.md) · [函数记录](02-short-term-memory/overview.md) · [本次收束](04-flow.md#agent-results-closure)

## 1. 本步在任务中的位置

Step 1 讨论的是 CLI 运行期间的一次模型请求；本步来到整个 `harness.run` 已经返回之后。当前仍采用 Claude Code 场景，`harness` 是 `ClaudeCodeHarness`，沿 `evaluation=False` 路径说明后续样本去向。

此时已经有三份输入：

- **`sb` 与 `workdir`**：仍可访问的执行沙箱及其中的任务仓库。两次收集都在退出这个沙箱的上下文之前完成。
- **`baseline`**：`prepare_workspace` 在 CLI 开始前取得的工作区快照标识。它保留准备完成时的文件状态，供结束时比较。
- **`.harness/compaction.json`**：启动命令先写入零值，CLI 运行期间由压缩事件更新，结束后留在沙箱里供读取。

统计的来路已经回查到三个环节：`write_config` 放置脚本并注册事件；`launch_and_wait` 交出的命令在执行时初始化文件并启动 CLI；运行中的 `PreCompact` / `PostCompact` 触发脚本入口，再进入 `run_hook` 更新累计状态。它们发生在最终读取之前，完整衔接见[统计机制参考](references/compaction-metrics-lifecycle.md)。

本步入口是 `generate.py:296–298`，终点是两份结果交回 `_generate`；评测如何打分、样本如何组装不在本页展开。

<a id="2-两个相邻调用怎样完成交接"></a>

## 2. 程序实际怎样完成交接

<a id="reading-path"></a>

阅读路径图与函数入口已移到 [scope 3.4](01-scope.md#reading-path)，用于阅读时判断先看哪里、为何回查和读完返回哪里。本页继续总结程序的实际交接。

<a id="execution-flow"></a>

下面按执行顺序画出 `_generate` 的这一小段。**①完成后才进入②，缩进表示函数内部的调用或处理。** `run_hook` 由运行中的 CLI 事件触发，不是 `collect_metrics` 的子调用。追踪包装和外层异常处理按本步边界省略。

```text
_generate                                       examples/coding_agent_rl/generate.py
│  harness.run 已返回；sb 仍在使用期
│
├─ ① collect_metrics(sb, workdir=...)           调用：296；harness/claude_code.py:111–120
│  ├─ sb.read_file(...)                         112
│  │  → 从沙箱读取 .harness/compaction.json，得到文本
│  ├─ 空白文本 → 返回 {}                       113–114
│  └─ 否则：解析 JSON，整理三个整数字段          115–120
│     → 返回运行统计字典
│  回到 _generate:296，保存为 agent_metrics
│
└─ ② swe.git_diff(sb, workdir, baseline)        调用：298；examples/coding_agent_rl/swe.py:265–272
   ├─ _repository_tree(sb, workdir)             266 → 241–262
   │  → 取得结束时的工作区快照标识 current
   ├─ 组织 baseline 与 current 的比较命令        267–270
   │  → 排除 PROBLEM_STATEMENT.md 和 .harness
   └─ sb.exec(...) → 取标准输出 out → return    271–272
      → 返回补丁文本
   回到 _generate:298，保存为 diff_text

两份结果已在调用方：agent_metrics + diff_text
    ↓ 退出执行沙箱的上下文
_generate:301–306 将 diff_text 交给 swe.run_evaluation
```

从图中进入具体说明：[collect_metrics](02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.collect_metrics.md)、[git_diff](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/git_diff.md)。`_repository_tree` 目前按“工作区状态 → Git 树标识”的接口使用，其源码入口保留在 `git_diff` 卡片内。

## 3. 两份结果分别表示什么、交给谁

下面沿用函数卡片中的两份独立局部样例，不把它们描述为同一次真实 CLI 运行。

统计样例把文件中的 `attempts=2`、`count=2`、`limit_reached=true` 整理为：

```python
agent_metrics = {
    "compact_count": 2,
    "compact_attempts": 2,
    "compact_limit_reached": 1,
}
```

`count` 是收到压缩完成事件的次数，`attempts` 是已放行的压缩尝试次数；`limit_reached` 表示后来有一次尝试被次数上限阻止，不能只凭“次数等于上限”推断已触限。

补丁样例比较运行前后的 `source.py`，返回文本中包含以下节选：

```diff
-result = 0
+result = 42
```

这里比较文件状态，不要求 Agent 先提交改动；即使没有执行 `git add` 或 `git commit`，已保存的修改也可以被提取。没有需要输出的差异时，`diff_text` 是空字符串。

| 结果 | 后续接收方与用途 |
| --- | --- |
| `diff_text`：代码补丁字符串 | `_generate:301–306` 将它交给 `swe.run_evaluation`，由评测产生 `reward` 与 `applied_cleanly` |
| `agent_metrics`：运行统计字典 | `_generate:326–336` 通过 `finish_session(extra_metadata=...)` 交给样本记录；342–349 行还依据 `compact_limit_reached` 等条件标记截断状态 |

两份结果来自同一个执行沙箱，但各自形成、各自交接。`agent_metrics` 不作为 `git_diff` 的输入，也不在这两个收集函数中计算奖励。

## 4. 本步收束与下一次交接

按已经确认的 scope，本步已接清 **输入来源 → 统计读取 → 补丁提取 → 两份结果的下游用途**。用户表示当前内容已差不多，并询问是否可以结束；据此将 Step 002 的这轮阅读收束。各卡片中的个人表述、助手澄清和未展开细节仍分别保留。

以下内容不作为本步结束的前置：

| 保留的问题 | 再展开的条件 |
| --- | --- |
| `_repository_tree` 的临时索引、Git 对象与更细的文件筛选 | 需要解释具体文件为何进入或没有进入补丁时 |
| CLI 如何决定压缩、hook 的文件锁、PID 核验与停止实现 | 需要研究压缩策略、并发更新或触限故障时 |
| 真实远端执行、沙箱通信与完整异常清理 | 进入实际运行或排障任务时 |

主线的下一次交接是 `generate.py:301` 的 `swe.run_evaluation`，归入已有 [Step 003 · 独立评测](../step-003-swe-evaluation/README.md)。它已有旧版阅读记录；进入新版校准时再确认本轮入口与深度，本次不提前改写该步或扩展评分实现。

<details>
<summary>源码、形成依据与验证范围</summary>

- 固定版本：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`，本地源码 `/home/hongshi/projects/slime`。
- 收集顺序及消费者：[generate.py:283–350](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L283-L350)。
- 配置、初始化与统计读取：[harness/claude_code.py:57–120](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L57-L120)；事件入口与状态更新：[harness/compaction.py:23–80](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/compaction.py#L23-L80)。
- 初始快照来源：[swe.py:187–209](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L187-L209)；当前快照与补丁：[swe.py:241–272](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L241-L272)。
- 形成过程：[统计部分收束](04-flow.md#collect-metrics-reading-checkpoint)、[快照与提交的澄清](04-flow.md#git-diff-snapshots-not-commits)、[整步收束](04-flow.md#agent-results-closure)。本页由 LLM 整理，不代填用户对每项实现的掌握状态。
- 已有局部证据：[读取转换](references/collect-metrics-example-18868a79.json)、[普通事件更新](references/run-hook-example-18868a79.json)、[配置与启动参数](references/hook-preparation-example-18868a79.json)、[真实本地 Git 示例](references/git-diff-example-18868a79.json)。本次只核对源码、示例和链接，没有新增真实 CLI、远端沙箱、模型或评测运行。
- 四部分结构沿用 task-flow skill 的 Step 003 主 reference；调用层级沿用 Step 007 reference 的组织方式，函数、行号和内容均按本步版本填写。
- 2026-10-23，先按用户确认[增加阅读路径图](04-flow.md#task-flow-reading-path-applied)，随后按阅读时的使用方式[移入 scope](04-flow.md#reading-path-moved-to-scope)；原执行图保留，通用 skill 未修改。

</details>
