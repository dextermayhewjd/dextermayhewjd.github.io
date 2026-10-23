# Scope 样例：从结果读取回查输入来源

本页与 [Step 001 scope 样例](step-001-reading-path.md)都是用户已认可的完整 scope，均保留整体定位、局部骨架、阅读图和导航表。本例重点展示：读到输入来路不清楚时，沿问题回查产生与配置的位置，再带着答案返回原调用。配合 [scope skill](../SKILL.md)使用。

- 来源：[Step 002 的完整 scope](../../../../00-repo-reading/repositories/slime/steps/step-002-agent-results/01-scope.md)。2026-10-23 按用户反馈补入；对应 Slime 固定提交 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。
- 下方正文完整保留，仅调整复制后的相对链接。文中步骤编号、观察点和已读情况属于当时记录；项目文件以后可能更新，本样例保留此次快照。

## 复用时关注什么

1. **保留真实入口。** 本步是 `_generate` 中相邻的两个调用，scope 用整体骨架定位它们，再给局部展开。
2. **按问题回查。** 从 `collect_metrics` 发现统计文件的来源问题，回查写入、配置与初始化，再返回读取者，随后继续 `git_diff`。已有认识足够时直接沿主线继续。
3. **分别表达两种顺序。** 3.3 展示程序实际调用；[3.4](#reading-path)展示阅读时的追问、回查和返回，图与表使用相同编号。
4. **复用深度与边界。** 回查只展开当前缺失的关系；辅助接口可保留用途，未确认的新问题留待后续。六个观察点属于本例，具体函数和顺序按目标步骤重新确定。

---

<!-- scope-snapshot -->

# 01 · 阅读范围：CLI 结束后，收集运行统计与代码补丁

[本步入口](../../../../00-repo-reading/repositories/slime/steps/step-002-agent-results/README.md) · [前一步：模型请求处理](../../../../00-repo-reading/repositories/slime/steps/step-001-harness-to-adapter/README.md) · [后一步：独立评测](../../../../00-repo-reading/repositories/slime/steps/step-003-swe-evaluation/README.md)

## 1. 阅读目标

总目标仍是理解 Coding Agent / Coding RL。本步单独弄清：**CLI 结束后，怎样从仍可访问的执行沙箱中取得运行统计与代码补丁，并把两份结果交回主流程？**

主线按 `harness.collect_metrics → swe.git_diff` 推进，输入来源不清楚时按 3.4 回查，再返回当前函数。前者收集运行情况，后者提取待评测的代码改动；二者都需要说明输入从哪里来、内部完成什么、返回什么、下游怎样使用。

入口条件是 `harness.run` 已经返回，`sb` 仍处于使用期，`md["workdir"]` 指向本次工作区，`baseline` 保存工作区准备完成时的 Git 树标识。先恢复这几个条件的含义，不把重读沙箱创建、CLI 安装和整个工作区准备过程作为前置。

本步以两份结果交回 `_generate` 为边界。`run_evaluation` 的内部评分过程属于后一步；样本导出与截断处理先定位消费者，完整机制回到相应步骤。这里只确认范围，不预写个人理解或阅读完成状态。

## 2. 找到指挥官函数

源码版本：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`，本地仓库为 `/home/hongshi/projects/slime`。

- 整体入口是 [generate.py 的 `generate → _generate`](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L225-L259)。实际业务编排由 `_generate` 负责。
- 本步入口是 [同文件 296–298 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L283-L308)的两个相邻调用。它们之间没有额外的“结果收集函数”，直接在 `_generate` 中交接。
- 继续以 Claude Code 场景阅读。`harness` 是当前样本选中的 `ClaudeCodeHarness` 实例，实际进入 [claude_code.py 的 `collect_metrics`，111–120 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L111-L120)。`BaseHarness.collect_metrics` 只是默认返回空字典的实现；Codex 的对应方法作为对照，不重复建立一套模型。

## 3. 给出真正干活的核心骨架

### 3.1 继承整体骨架，标出本步位置

以下继承 [Step 0 的整体骨架](../../../../00-repo-reading/repositories/slime/steps/step-000-coding-agent/01-scope.md)，是 `evaluation=False` 正常路径的教学裁剪。参数通常省略；`baseline` 与本步输入交接直接相关，因此保留。配置、入口检查、trace、异常与失败包装暂时折叠，源码中仍存在。

```python
adapter.open_session(...)                              # 登记会话
async with boot_agent_sandbox(...) as sb:                # 进入执行沙箱的使用期
    baseline = await swe.prepare_workspace(...)         # 准备工作区，取得初始 Git 树
    agent_exit_code = await harness.run(...)             # 运行 CLI，等待它结束
    # CLI 运行期间，通过 HTTP 进入 Step 1 的 _run_turn；单轮返回不等于 CLI 结束
    agent_metrics = await harness.collect_metrics(...) # 本步先读：取得运行统计
    diff_text = await swe.git_diff(sb, ..., baseline)     # 本步再读：提取代码补丁

reward, applied_cleanly = await swe.run_evaluation(...)  # 后一步：独立评测
samples = await adapter.finish_session(...)              # 轨迹与奖励交成样本
...  # 附加运行信息、处理截断状态；最终还有会话清理
return samples
```

两个读取动作都在退出执行沙箱之前完成。取得统计与补丁后，主流程离开该上下文，再进入评测；本步不展开沙箱退出内部。

### 3.2 先对准调用对象与输入来路

| 已有材料 | 在哪里形成 | 本步先需要知道什么 |
| --- | --- | --- |
| `harness` | `generate.py:257–258` 按当前样本选取实现 | 本例是 `ClaudeCodeHarness`，因此读它的 `collect_metrics` |
| `sb`、`workdir` | 执行沙箱与本题元数据 | 两个函数都操作刚刚运行 CLI 的同一个工作区 |
| `.harness/compaction.json` | CLI 启动时初始化，运行期间由压缩 hook 更新 | `collect_metrics` 读取的统计文件；字段含义和写入来路随该函数补清 |
| `baseline` | `prepare_workspace` 在 `swe.py:209` 返回 `_repository_tree` 的结果 | CLI 开始前的工作区快照标识；与结束时的快照比较 |

文件来路参考：[Claude Code 启动初始化](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L98-L109)、[压缩 hook 配置](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L57-L75)、[工作区准备的返回](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L187-L209)。这几处先恢复输入来源，不要求一次读完调用者。

### 3.3 局部调用骨架

下图的两个主分支按源码先后顺序执行；缩进表示各函数内部调用，不表示同时运行。每个调用完成后返回 `_generate`，再走下一行。

```text
_generate                                             generate.py:296–298
├─ 296：await harness.collect_metrics(...)
│  └─ ClaudeCodeHarness.collect_metrics                 harness/claude_code.py:111–120
│     ├─ sb.read_file(...)                             读取统计文件
│     └─ 空内容返回 {}；否则解析 JSON 并整理字段           返回 agent_metrics
│
└─ 298：await swe.git_diff(...)
   └─ git_diff                                         examples/coding_agent_rl/swe.py:265–272
      ├─ _repository_tree(...)                         取得结束时的工作区快照
      └─ sb.exec(...)                                  对比 baseline 与当前快照
                                                       返回 diff_text
```

`agent_metrics` 不传入 `git_diff`：两个调用共用沙箱，但分别形成不同的结果。后面 `diff_text` 传给评测，统计则进入样本元数据，其触限字段还参与截断状态判断。

<a id="reading-path"></a>

### 3.4 每次读哪一段，读到什么程度

这张图根据本轮已经展开的问题整理，供阅读和复习时导航；箭头表示回查、返回和继续。统计来源已清楚时，可从①直接接⑥；②–④用于补齐这项输入。`claude_code.py` 中的三个方法都属于 `ClaudeCodeHarness`；它与 `compaction.py` 位于 `slime/agent/harness/`，`swe.py` 位于 `examples/coding_agent_rl/`。

```text
① 进入 collect_metrics                         claude_code.py:111–120
   要看清：已有统计文件 → agent_metrics
   疑问：这份文件是谁写好的？
    ↓ 回查写入者
② 阅读 run_hook                                compaction.py:23–68
   要看清：一次事件 → 读取旧统计、修改并写回
   疑问：谁把事件接到这个脚本？
    ↓ 回查配置
③ 阅读 write_config                            claude_code.py:57–84
   要看清：放置脚本，注册 PreCompact / PostCompact
    ↓ 补齐另一项前置：统计的初始值在哪里写入？
④ 阅读 launch_and_wait 的初始化片段            claude_code.py:103–109
   要看清：启动命令执行时，先写入零值，再启动 CLI
    ↓ 带着输入来路返回
⑤ 回到 collect_metrics                         claude_code.py:111–120
   把“初始化 → 事件更新 → 最后读取”连起来
    ↓ 继续主线，查看下一份结果
⑥ 阅读 git_diff                                swe.py:265–272
   要看清：baseline 与 current 两份工作区快照 → diff_text
   _repository_tree 暂按“取得快照标识”的接口使用
```

按图进入下表的函数卡片；表格补充阅读深度与返回位置。统计的跨阶段关系集中在[机制参考](../../../../00-repo-reading/repositories/slime/steps/step-002-agent-results/references/compaction-metrics-lifecycle.md)，完整追问与修正保存在 [04-flow](../../../../00-repo-reading/repositories/slime/steps/step-002-agent-results/04-flow.md#collect-metrics-first-read)。

| 顺序与源码入口 | 本次要弄清什么 | 读完回到哪里 |
| --- | --- | --- |
| **①⑤ [ClaudeCodeHarness.collect_metrics，111–120 行](../../../../00-repo-reading/repositories/slime/steps/step-002-agent-results/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.collect_metrics.md)** | 从哪个文件读取什么内容，怎样变成三个统计字段，空内容返回什么；用文件内容与返回字典对照 | 输入来路不清楚时走②–④，再回到⑤；`_generate:296` 接住 `agent_metrics` 后继续⑥ |
| **② [run_hook，23–68 行](../../../../00-repo-reading/repositories/slime/steps/step-002-agent-results/02-short-term-memory/functions/slime/agent/harness/compaction.py/run_hook.md)** | 一次事件怎样读取旧统计、选择更新字段并写回；触限停止先保留职责边界 | 继续③，补清事件处理怎样被配置 |
| **③ [ClaudeCodeHarness.write_config，57–84 行](../../../../00-repo-reading/repositories/slime/steps/step-002-agent-results/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md)** | 重点看脚本复制、两个事件注册到同一命令、传入统计目录与上限 | 继续④，补齐统计文件的初始状态 |
| **④ [ClaudeCodeHarness.launch_and_wait，103–109 行](../../../../00-repo-reading/repositories/slime/steps/step-002-agent-results/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md#compaction-initialization)** | 只展开本轮需要的初始化片段：先组装命令，沙箱执行时才写入零值并启动 CLI | 返回⑤，将准备、事件更新与最终读取接起来 |
| **⑥ [swe.git_diff，265–272 行](../../../../00-repo-reading/repositories/slime/steps/step-002-agent-results/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/git_diff.md)** | `baseline` 与 `current` 分别代表哪份状态，执行什么比较，返回的补丁是什么样子；不要把 `agent_metrics` 或模型回复当作它的输入 | `_generate:298` 接住 `diff_text`，再看两份结果的交接 |
| ⑥ 内部按需进入：[swe._repository_tree，241–262 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L241-L262) | 本轮先用“工作区状态 → 快照标识”的接口；需要解释具体文件为何进入补丁时，再看临时索引。Git 底层对象存储不作为前置 | `git_diff:267–272` 比较两份快照并返回 |
| **两份结果的交接**：[generate.py:301–349](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L301-L349) | 在调用处指出补丁交给评测、统计交给样本记录与状态处理；明确谁产生 reward | 到 `run_evaluation` 的入口停住，后一步再展开评分 |

从①开始，按当前缺口选择是否回查。`read_file`、`exec` 先按沙箱接口理解输入输出；出现具体通信疑问时再调取已有记录。这份导航随本轮已确认的问题补全，不表示开始时就已知全部分支，也不把列出函数视为已经掌握。字段整理、局部变量和每条 Git 命令不自动拆成独立函数卡。

**停止条件**：能够连续说明“CLI 结束 → 读取统计 → 提取补丁 → 两份结果交回主流程”，并分别指出输入、输出和下游消费者。阅读后的串联与保留问题见 [task flow](../../../../00-repo-reading/repositories/slime/steps/step-002-agent-results/05-task-flow.md)。
