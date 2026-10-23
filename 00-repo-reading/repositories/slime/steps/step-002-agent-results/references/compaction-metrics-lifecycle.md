# 机制参考：压缩统计怎样产生并交给 collect_metrics

[回到 collect_metrics 函数卡片](../02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.collect_metrics.md) · [本步 scope](../01-scope.md)

本页围绕同一份 `compaction.json` 的生命周期，连接初始化者、运行中的更新者与最终读取者。它解释当前项目中的协作关系；通用 hook 概念沿用已有认识。

<a id="function-coverage"></a>

`compaction.py` 是 Python 脚本文件，`run_hook` 是其中处理事件的函数，`compaction.json` 是存放累计统计的数据文件。脚本复制进沙箱后叫 `/tmp/slime-claude-compaction.py`；事件触发时，其入口从 stdin 读取事件并调用 `run_hook`（`compaction.py:71–80`）。

下面前三行对应讨论中的第 1、2、3 步：**第 1、2 步在 `claude_code.py`，第 3 步才由 `run_hook` 执行。** `run_hook` 卡片的主体覆盖第 3 步。当前已按用户要求回看前两步：[write_config 的复制与注册](../02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md) → [launch_and_wait 的统计初始化](../02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md#compaction-initialization)。两张卡在本步 `02` 可直接读取，旧版记录完整保留在卡片末尾。

<a id="metrics-file-origin"></a>

## 统计文件怎样产生、更新与读取

正常路径先 `await harness.run(...)`，返回后才调用 `collect_metrics`。依据是执行顺序，以及启动脚本和压缩 hook 对同一文件的写入；`harness` 对象并没有预先算好最终次数。

| 时机 | 源码位置 | 实际发生什么 |
| --- | --- | --- |
| 1. 启动前配置 | [ClaudeCodeHarness.write_config，57–79 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L57-L79) | 把 `compaction.py` 复制进沙箱，将运行它的命令注册到 `PreCompact`、`PostCompact`，并传入本次 `.harness` 目录。这一步配置以后由谁更新统计 |
| 2. 启动命令在沙箱执行时 | [launch_and_wait，103–109 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L103-L109) | 命令先用 `printf` 写入 `{"attempts":0,"count":0,"limit_reached":false}`，再启动 CLI。Python 这里先组装命令，由 `run_agent` 交给沙箱执行后才真正写文件 |
| 3. CLI 运行期间发生压缩事件 | [compaction.py 的 run_hook，23–48 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/compaction.py#L23-L48) | 读取同一文件；已放行的 `PreCompact` 增加 `attempts`，`PostCompact` 增加 `count`，被上限阻止时设置 `limit_reached`；用 `json.dump` 写回文件 |
| CLI 结束后 | [collect_metrics，111–120 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L111-L120) | 读回文件，在当前调用中解析出 `state`，整理返回字段 |

**一开始录入的是零值，最终统计随着运行逐次更新。** 文件里的字段叫 `attempts`、`count`、`limit_reached`；`compact_count` 等带前缀的名称在 `collect_metrics` 返回时才产生。这里的 `state = json.loads(contents)` 只是本次读取所得的字典，并非读取时才开始统计，也不是保存在 `self` 上的统计对象。

需要具体看“收到一次事件以后，文件怎样被更新”时，进入 [run_hook 函数卡片](../02-short-term-memory/functions/slime/agent/harness/compaction.py/run_hook.md)。它只展开一次调用的输入、分支、文件变化与返回；本页继续负责跨阶段的顺序。初始零值写入是 `launch_and_wait:103–105` 中的命令片段，没有另一个独立的初始化函数，不为这两行另造函数卡。

边界补充：`run_hook:26–36` 自身也能在目录或文件不存在时创建它，并补上缺失字段；已有计数会保留。这与启动命令每次明确写入全零状态不同，不能据此把第 1、2 步都归入 `run_hook`。

## 第 1、2 步怎样交接

两步由 `BaseHarness.run:103–104` 顺序调用：先等待配置写完，才进入启动。

```python
await self.write_config(sb, ctx)
return await self.launch_and_wait(sb, ctx, prompt, time_budget_sec)
```

本轮统一用 `ctx.workdir="/workspace/repo"`、压缩上限 `2` 对照三个具体产物：

1. **处理脚本**：`write_config` 将本地 `compaction.py` 放到沙箱的 `/tmp/slime-claude-compaction.py`。
2. **触发配置**：同一函数在 CLI 配置中，为 `PreCompact` 和 `PostCompact` 写入命令 `python3 /tmp/slime-claude-compaction.py /workspace/repo/.harness 2`。目录与上限通过命令参数交付，事件名在实际触发时由 hook 输入传入。
3. **统计文件**：`launch_and_wait` 组装的启动命令先向 `/workspace/repo/.harness/compaction.json` 写零值，再运行 CLI。这两步使用同一个 `ctx.workdir`，因此 hook 最终读写的就是这个统计文件。

Python 拼接命令时文件尚未写入。109 行把命令交给 `run_agent`；下层先建立 `.harness` 目录，再让沙箱执行命令。CLI 运行期间触发事件，才进入第 3 步的 `run_hook`。完整参数与源码分别留在两张函数卡中，本页连接它们的产物与时机。

## 读完返回哪里

回到 [`collect_metrics` 的输入与输出](../02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.collect_metrics.md)，将这份已记录统计的文件作为输入，继续看读取、字段整理与返回。本函数的具体例子和空内容分支只在函数卡片维护。

这里覆盖的是统计产生与读取这一条机制，不代替整个 Step 002 的阅读后总结；补丁提取、评测和样本交接仍按 scope 的范围继续。

<details>
<summary>来源、验证与迁移说明</summary>

- 固定源码版本：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`。本地仓库为 `/home/hongshi/projects/slime`。
- 文件初始化：`slime/agent/harness/claude_code.py:103–109`；配置注册：57–79 行；实际更新：`slime/agent/harness/compaction.py:23–48`。
- [写入过程的局部验证](compaction-state-origin-18868a79.json)：原 `run_hook` 在本地临时文件中执行，使用 `stop_mode="json"`；没有执行真实 Claude CLI、远端 hook 注册或进程信号。这里只迁移既有证据，没有追加新的运行验证。
- [原始追问与解释](../04-flow.md#compaction-file-origin) · [本次职责纠正](../04-flow.md#function-mechanism-boundary)。
- [第 1、2 步的本轮阅读](../04-flow.md#hook-upstream-preparation) · [配置与启动材料的局部验证](hook-preparation-example-18868a79.json)。该验证使用原方法及调用记录器，没有执行 shell、远端文件写入或真实 CLI。
- 本页主体从 `collect_metrics` 卡片的“输入文件是何时写好的”移出，原解释保留；函数卡保留输入来源提示和入口。

</details>
