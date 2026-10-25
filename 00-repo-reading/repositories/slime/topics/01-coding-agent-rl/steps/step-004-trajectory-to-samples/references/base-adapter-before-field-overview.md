# BaseAdapter

> 2026-10-24 扩展全字段总览前的类卡片，保留当时仅记录 closed、inflight 的范围；正文仅调整相对链接。[当前类卡片](../02-short-term-memory/classes/slime/agent/adapters/common.py/BaseAdapter.md)单独维护。

- 源码定位：[slime/agent/adapters/common.py:190–223](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L190-L223)，本轮只记录 `closed`、`inflight` 两项实例状态。
- 首次接触：此前已通过 Adapter 的方法接触；2026-10-24 在 Step 004 建立独立类卡片，归并会话状态的说明。
- 最近认识更新：暂无对本类状态的独立技术复述；本次保存用户的记录归属提议，字段含义由助手据源码整理。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：阅读 `_run_turn` 与 `shutdown_session` 时，先明确两者操作的是同一个 Adapter 实例上的哪些状态。
2. **具体内容**：`closed` 保存已关闭的会话编号，`inflight` 按会话编号登记正在处理的请求 Task。
3. **建议构建的心智模型**：

   > 一个 Adapter 可以管理多个 `sid`。`closed` 回答“哪些会话不再接受新请求”，`inflight` 回答“各会话还登记着哪些请求任务”。

4. **调用代码**（`_run_turn:406–407`，登记当前请求任务）：

   ```python
   task = asyncio.current_task()
   self.inflight.setdefault(sid, set()).add(task)
   ```

## 本场景的输入与输出

本轮观察已创建的 Adapter 对象，保留其状态形态与读写关系。类卡记录字段的定义，实际数据分别保存在各个 Adapter 实例上。

<a id="session-tracking"></a>

### 状态里保存什么

下面两项在 `BaseAdapter.__init__` 中初始化：

```python
self.inflight: dict[str, set[asyncio.Task]] = {}
self.closed: set[str] = set()
```

| 字段 | 保存的内容 | 用途 |
| --- | --- | --- |
| `closed` | 一组 `sid` 字符串 | 请求入口据此拒绝已关闭会话的新请求 |
| `inflight` | `sid → 一组 asyncio.Task` | 按会话找到已登记的请求任务，供收尾时筛选与等待 |

教学状态示意，`task_A`、`task_B`、`task_C` 代表已存在的请求 Task：

```python
adapter.closed = {"sid-done"}
adapter.inflight = {
    "sid-demo": {task_A, task_B},
    "sid-other": {task_C},
}
```

- `sid` 是分类用的编号，集合里的 Task 才是正在执行的工作。关闭 `sid-demo` 时取出它的任务集合，`sid-other` 的登记仍保留。
- `inflight` 的某个集合为空，只说明当前没有登记中的请求；会话是否已关闭要看 `closed`。
- 会话配置由 `store` 保存，逐轮轨迹由 `manager` 保存；这两项状态表负责请求的准入与在途登记。

### 谁读写这些状态

| 使用位置 | 对状态的操作 |
| --- | --- |
| `_run_turn:397–407` | 检查 `closed`，通过入口检查后把当前 Task 加入 `inflight[sid]` |
| `_run_turn:475` | 请求退出时，从该会话的集合中移除当前 Task |
| [shutdown_session:296–299](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md) | 添加关闭标记，取出该会话的任务集合并筛选未完成者 |

具体的等待、取消和跨循环提交，回到 [shutdown_session 的流程图与源码](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md#shutdown-cross-loop)阅读。

## 我的直接表述（原话）

2026-10-24，用户提出记录归属：

> 我在想这里的这个closed和inflight的内容是否更加适合放在adapter short term中的adapter class里面

这是将对象状态集中到类卡片的提议；此前关于收尾过程的完整复述保存在 [shutdown_session 的原话区](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md#shutdown-user-restatement-2026-10-24)。

## 尚不清楚

- `sid` 与请求 Task 的区别、字段中保存的具体对象，仍需结合本轮复述核对。
- 同一 Adapter 的请求为何共用事件循环，以及 `run_coroutine_threadsafe` 怎样提交收尾协程，仍在当前函数问题中继续澄清。
- 本轮未展开 `BaseAdapter` 的全部字段、协议钩子与初始化过程。

<details>
<summary>来源与记录范围</summary>

- 固定源码：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`，本机 `/home/fredkeira/projects/slime`。
- [状态初始化](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L221-L228)、[请求入口与登记](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L394-L407)、[请求退出](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L473-L475)。
- [会话配置登记](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L275-L292)、[关闭与取任务](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L294-L312)。
- [原 inflight 状态推演](inflight.md)和 [sid 说明](session-id.md)保留历史依据；本卡为当前状态定义的集中入口。
- 本轮为静态源码核对与记录归并，没有运行真实 HTTP 请求，也不代表用户已掌握全部状态机制。

</details>
