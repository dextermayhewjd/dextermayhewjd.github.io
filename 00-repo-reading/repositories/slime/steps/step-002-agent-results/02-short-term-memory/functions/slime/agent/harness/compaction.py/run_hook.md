# run_hook

- 源码定位：[slime/agent/harness/compaction.py:23–68](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/compaction.py#L23-L68)，由助手核对。
- 首次接触：2026-10-23，Step 002 追溯统计文件来源时定位；本轮开始单独阅读。
- 最近认识更新：2026-10-23，用户初步串起“预先准备 → 事件触发 hook → 写入 JSON”；注册、初始化与累计更新的具体区别为本轮助手补充，尚待进一步反馈。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据当前调用场景与源码整理，作为理解参考。

1. **使用场合**：Claude CLI 运行期间发生压缩事件，按配置启动沙箱内的脚本（源码 `compaction.py` 被复制为 `/tmp/slime-claude-compaction.py`）。脚本从 stdin 读取事件，再调用其中的 `run_hook`。本函数运行在沙箱内，直接读写该沙箱的统计文件。

2. **具体内容**：接收 `event`、统计目录 `directory`、次数上限 `limit` 和停止方式 `stop_mode`，读取并更新 `compaction.json`。普通事件完成后返回 `0`；如果本次压缩请求触及上限，先保存触限标记，再按停止方式通知 CLI 停止。它记录压缩事件并执行预算控制，不负责生成压缩摘要。

3. **建议构建的心智模型**：

   > - 上游已配置好压缩 hook；本函数接收一次传入的事件。脚本部署、hook 注册与启动时的统计清零由上游负责。
   > - 先读旧统计，再按事件修改，最后写回同一份文件。
   > - 放行压缩前增加 `attempts`；收到压缩后事件增加 `count`；因上限阻止压缩时设置 `limit_reached`。
   > - 累计结果留在文件里，供下次事件和最终的 `collect_metrics` 读取；触限时还要执行停止通知。

4. **调用代码**（[compaction.py:71–80](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/compaction.py#L71-L80)，保留脚本入口的真实调用）：

   ```python
   request = json.load(sys.stdin)
   raise SystemExit(
       run_hook(
           request["hook_event_name"],
           directory=sys.argv[1],
           limit=int(sys.argv[2]),
           stop_mode=sys.argv[3] if len(sys.argv) > 3 else "signal",
       )
   )
   ```

## 本场景的输入与输出

本例观察第一次被放行的 `PreCompact`。教学设定次数上限为 `2`，沿用 Claude 场景实际使用的默认 `stop_mode="signal"`；本次未触限，因此不发送信号。文件的零值初始化、hook 注册与最终读取之间的关系，见[压缩统计的产生与收集机制](../../../../../../references/compaction-metrics-lifecycle.md)。

### 输入

```python
event = "PreCompact"
directory = "/workspace/repo/.harness"
limit = 2
stop_mode = "signal"
```

调用前，`directory/compaction.json` 的内容：

```json
{"attempts": 0, "count": 0, "limit_reached": false}
```

### 输出与文件变化

函数返回整数 `0`，脚本入口把它用作退出码。本次没有标准输出；更新后的文件内容为：

```json
{"attempts": 1, "count": 0, "limit_reached": false}
```

此时只记录了“放行一次压缩尝试”。以后收到 `PostCompact`，另一次调用才把 `count` 加到 `1`。上面的两次普通事件已用原函数和本地临时文件验证；没有运行真实 CLI 或远端沙箱。

### 这一次怎样把文件写好

23–36 行先检查停止方式、准备目录、打开并锁住文件，读取 JSON 成为本次的 `state`，补上缺失字段的零值。37–49 行的连续片段决定修改哪项并写回：

```python
stop = event == "PreCompact" and limit >= 0 and state["attempts"] >= limit
if stop:
    state["limit_reached"] = True
elif event == "PreCompact":
    state["attempts"] += 1
elif event == "PostCompact":
    state["count"] += 1
else:
    raise ValueError(f"Unexpected compaction hook: {event}")
stream.seek(0)
json.dump(state, stream)
stream.truncate()
stream.flush()
```

- **选择分支**：本例旧 `attempts=0 < limit=2`，因此 `stop=False`；进入 `PreCompact` 分支，只把 `attempts` 加一。
- **写回文件**：`seek(0)` 回到文件开头，`json.dump` 把更新后的字典写成 JSON；`truncate` 去掉可能残留的旧尾部，`flush` 刷出写入缓冲。这里覆盖的是累计状态，不是追加一条事件日志。
- **结束这次调用**：本例不进入 50–67 行的触限处理，最后返回 `0`。下一次调用重新读取文件，因此能接着这次结果累计；`state` 本身只是本次调用的局部变量。

### 另外两种事件结果

| 事件与条件 | 对旧状态做什么 | 随后怎样结束 |
| --- | --- | --- |
| `PostCompact` | `count += 1`，其余字段保留 | 写回文件，返回 `0` |
| `PreCompact` 且 `limit >= 0`、旧 `attempts >= limit` | 只设置 `limit_reached=True`，不增加 `attempts` | 写回文件后进入停止处理 |

`limit=-1` 表示不启用次数上限；次数刚到上限时不会立即设置触限标记，要等下一次 `PreCompact` 被阻止。

触限处理保留完整职责边界，内部暂不展开：默认 `signal` 模式读取 `cli.pid`，验证对应进程的祖先关系后发送 `SIGTERM`，成功后返回 `2`；`json` 模式输出 `{"continue": false, "stopReason": "Compaction budget reached"}` 并返回 `0`。停止不是通过向 `collect_metrics` 返回一个字典实现的。

读完回到 [collect_metrics 函数卡片](../claude_code.py/ClaudeCodeHarness.collect_metrics.md)：它在 CLI 结束后读取这个文件，整理成 `agent_metrics`。那张卡采用两次压缩后再次触限的例子，比本页的第一次事件更晚，不是本次返回时的文件状态。

## 我的直接表述（原话）

最初提出阅读问题：

> 那么下一步应该怎么做呢？
> 我的意思是这里的输入文件是怎么写好的这里需要具体看一下吗？
> 我的意思是单独创建函数卡？

随后对预先准备与事件写入的关系作出初步复述：

> 好的我大概理解了
> 简单道理姐就是这里应该在一开始就安装好了这个部分？
> 或者单独创建了这个compaction.json
> 然后通过hook的方式在发生这个行为的时候
> 就会在json中写下这里的内容？
> 这是我的理解？

随后追问当前卡片的覆盖范围：

> 那么这里的心智模型里面有写清楚吗？
> 这个只是一个compaction的python文件对吗？
> 但是我在想的问题是
> 这个函数覆盖了吗？
> 还是说这里的1，2,3我还需要看别的函数文件呢？

## 尚不清楚

- 用户已初步理解预先准备后由事件触发写入；hook 注册与统计文件初始化是两个动作，以及写回的是累计状态，这些具体区别经助手补充后尚待反馈。
- 当前进一步追问脚本文件、函数本体和上游准备的覆盖范围；三步与源码的对应关系见[机制参考](../../../../../../references/compaction-metrics-lifecycle.md#function-coverage)。
- CLI 怎样决定压缩、实际如何修改上下文，本轮未展开。
- 文件锁的并发细节，以及触限时 PID 核验和停止通知的实现，本轮只保留职责边界；错误事件、无效文件或失败的进程检查会抛出异常，不能概括为任何情况都返回退出码。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码版本：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`；本地路径 `/home/hongshi/projects/slime`。
- 函数整体：`slime/agent/harness/compaction.py:23–68`；状态更新：29–49 行；触限处理：50–67 行；调用入口：71–80 行。Claude 注册命令在 `harness/claude_code.py:62–72`，没有传第四个脚本参数，因此使用默认 `signal` 模式。
- [本页普通事件验证](../../../../../../references/run-hook-example-18868a79.json)：直接调用原函数，`limit=2`、默认停止模式，依次观察 `PreCompact` 与 `PostCompact` 的文件变化、返回值和标准输出。实际文件位于本地临时目录；初始化由实验写入，没有执行远端注册、真实 CLI 或信号停止。
- [此前完整状态序列的局部验证](../../../../../../references/compaction-state-origin-18868a79.json)：两轮事件后再触限；该实验使用 `stop_mode="json"`，用于观察状态分支，不能当作 Claude 默认信号模式的停止验证。
- [首次定位的讨论](../../../../../../../step-002-agent-results/04-flow.md#compaction-file-origin) · [本轮单独阅读](../../../../../../../step-002-agent-results/04-flow.md#run-hook-file-update) · [回到本步 scope](../../../../../../01-scope.md)。
- [初步复述与准备动作的澄清](../../../../../../../step-002-agent-results/04-flow.md#hook-setup-and-state-understanding)。
- [脚本与函数覆盖范围的追问](../../../../../../../step-002-agent-results/04-flow.md#hook-function-coverage)。

</details>
