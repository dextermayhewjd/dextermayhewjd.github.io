# ClaudeCodeHarness.collect_metrics

- 源码定位：[slime/agent/harness/claude_code.py:111–120](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L111-L120)，由助手核对。
- 首次接触：2026-10-23，Step 002 · 运行统计与补丁提取。
- 最近认识更新：2026-10-23，用户提出“读取已经写好的统计”的理解，并追问写入位置和时机；初始化与运行中更新的区别尚待反馈。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据当前调用场景与源码整理，作为理解参考。

1. **使用场合**：`_generate` 等待 `harness.run` 返回后，在执行沙箱还可访问时收集运行统计。本例的 `harness` 是 `ClaudeCodeHarness`；实际进入本方法，`BaseHarness.collect_metrics` 默认返回空字典的实现不参与这次读取。

2. **具体内容**：读取工作区下 `.harness/compaction.json`，把已有的上下文压缩统计整理为 `compact_count`、`compact_attempts`、`compact_limit_reached` 三个整数字段，返回给调用方的 `agent_metrics`。本函数只读取和整理，统计的累加发生在 CLI 运行期间。

3. **建议构建的心智模型**：

   > - CLI 已经结束，沙箱里的统计文件还在。
   > - `collect_metrics` 读取这份文件，把已有记录整理成运行统计字典。
   > - 字典交回 `_generate`，供后续记录样本信息和判断截断状态；本函数不执行上下文压缩，也不计算奖励。

4. **调用代码**（[generate.py:296–298](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L296-L298)，省略两行之间的追踪包装）：

   ```python
   agent_metrics = await harness.collect_metrics(sb, workdir=md["workdir"])
   diff_text = await swe.git_diff(sb, md["workdir"], baseline)
   ```

## 本场景的输入与输出

<a id="metrics-file-origin"></a>

输入是 CLI 运行期间已更新的 `.harness/compaction.json`；本函数从读取现有文件开始。统计何时初始化、由谁更新，见[压缩统计的产生与收集机制](../../../../../../references/compaction-metrics-lifecycle.md)。

### 当前调用的输入与输出

教学构造：`self` 是已选定的 `ClaudeCodeHarness`，`sb` 连接到刚运行完 CLI 的沙箱。本例记录两次已放行且已完成的压缩；随后再次请求压缩时触及次数上限。以下文件内容与返回值经过局部函数验证，没有运行真实 CLI 或远端沙箱。

输入：

```python
workdir = "/workspace/repo"

# sb.read_file("/workspace/repo/.harness/compaction.json") 返回的字符串
contents = '{"attempts": 2, "count": 2, "limit_reached": true}'
```

输出，完整返回字典：

```python
agent_metrics = {
    "compact_count": 2,
    "compact_attempts": 2,
    "compact_limit_reached": 1,
}
```

| 返回字段 | 从文件取哪项 | 当前源码中的含义 |
| --- | --- | --- |
| `compact_count` | `count` | 收到 `PostCompact` 事件的次数，即已记录的压缩完成次数 |
| `compact_attempts` | `attempts` | 已放行的 `PreCompact` 尝试次数；触限被拦截的那一次不增加计数 |
| `compact_limit_reached` | `limit_reached` | 是否曾因次数上限阻止继续压缩；`False/True` 转成 `0/1`。次数刚好等于上限时，不一定已标记触限 |

### 函数内部怎样完成这次转换

下面保留完整函数体，对应源码 111–120 行：

```python
async def collect_metrics(self, sb: Sandbox, *, workdir: str) -> dict[str, int | float]:
    contents = await sb.read_file(f"{workdir}/.harness/compaction.json")
    if not contents.strip():
        return {}
    state = json.loads(contents)
    return {
        "compact_count": int(state.get("count", 0)),
        "compact_attempts": int(state.get("attempts", 0)),
        "compact_limit_reached": int(state.get("limit_reached", False)),
    }
```

- **112 行，读字符串**：`workdir` 决定文件位置，`sb.read_file` 从沙箱读取内容。这里先按“给路径，得到文本”理解该接口。
- **113–114 行，处理空内容**：文本为空或只有空白，直接返回 `{}`。
- **115 行，解析 JSON**：`json.loads` 将字符串变成 `state` 字典；它没有新增一次压缩记录。
- **116–120 行，整理返回字段**：取出三项已有值，换成对外字段名并转成整数。文件缺少某个字段时使用默认值；文件内容为 `"{}"` 时会返回三个零，与空文本直接返回空字典不同。

返回后，`_generate:296` 接住 `agent_metrics`，下一行业务调用再去提取补丁。本结果不传入 `git_diff`；它在后面的 `finish_session(extra_metadata=...)` 中进入样本元数据，触限字段还参与 `Sample.Status.TRUNCATED` 的设置。

## 我的直接表述（原话）

初次进入时，先确认阅读入口：

> 好的那么先看一下这里的harness.collect_metrics吧
> 我第一个应该明白的函数是这里的collect metrics吗

随后对“读取已有统计”提出理解，并追问输入文件的来路：

> 这里harness以及统计好了是怎么知道的呢？
> 我的意思是这里的harness.collect_metrics
> 是在读取state过程中就已经写好的内容
> 包括这里的compact_count以及这里的attempts还有这里的limit_reached?
> 那么这个compaction应该是在一开始就已经录入的？
> 具体是在哪里就开始写的呢是一个问题？

## 尚不清楚

- 用户已提出读取已有统计的理解；初始零值与运行中逐次更新的区分尚待反馈。
- 已为说明输入来路定位 hook 注册与文件更新；CLI 何时决定压缩、怎样修改上下文，以及 hook 的完整停止和并发处理尚未展开。
- `sb.read_file` 的具体后端和通信实现尚未展开；非空文本的 JSON 解析失败或字段不能转成整数时，本方法没有自己的异常兜底。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码版本：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`；本地路径 `/home/hongshi/projects/slime`。
- 函数实现：`slime/agent/harness/claude_code.py:111–120`；基类默认方法在 `harness/common.py:106–108`。Codex 的同名实现位于 `harness/codex.py:150–159`，本轮不重复建卡。
- 调用与消费者：`generate.py:296、326–348`；`compact_limit_reached` 影响状态标记，奖励来自独立评测。
- [局部验证结果](../../../../../../references/collect-metrics-example-18868a79.json)：从源码提取未经改写的方法，以替身 `read_file` 提供字符串，验证正常统计、空白文本、空 JSON 对象和无效 JSON 四种情况。仅验证本地转换及读取路径，不证明远端通信或实际 CLI 运行。
- [形成过程](../../../../../../../step-002-agent-results/04-flow.md#collect-metrics-first-read) · [回到本步 scope](../../../../../../01-scope.md)。
- [本轮输入来源追问](../../../../../../../step-002-agent-results/04-flow.md#compaction-file-origin)。

</details>
