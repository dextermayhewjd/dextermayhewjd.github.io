# inflight：按 sid 登记正在处理的请求

[先读 sid](session-id.md) · [返回 shutdown_session](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md) · [此前 _run_turn 的登记与清理](../03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md#inflight-cleanup)

前置只需知道：`sid` 标识 Agent 的哪一次执行。本页集中解释 `inflight` 中放什么、怎样变化，以及关闭时怎样使用这张表；以下为助手按固定源码整理的解释。

## 登记表里存的是什么

| 名字 | 它是什么 | 在本场景中代表什么 |
| --- | --- | --- |
| `task` | 一个 `asyncio.Task` 对象 | 当前正在处理一份 HTTP 请求、执行 `_run_turn` 的任务，可能正在等待模型或发送响应 |
| `self.inflight` | Adapter 对象上的字典 | 按会话编号登记尚在处理中的请求 Task，供关闭会话时查找 |

`inflight` 可以记作“在途请求登记表”。源码定义是：

```python
self.inflight: dict[str, set[asyncio.Task]] = {}
```

字典的键是会话编号，值是一组 Task。下面是**教学状态示意**，`task_A` 代表一个已存在的 Task 对象：

```python
sid = "sid-demo"
self.inflight = {
    "sid-demo": {task_A},
}
```

这表示：**会话 `sid-demo` 当前有一个请求还在处理。** `sid` 只是编号，Task 才是正在执行的工作；把 Task 放进字典只是登记，不会启动它。

## 请求登记怎样变化

下面只观察一个会话，前后有两个请求 A、B；A 先结束，B 随后开始。这是静态推导的示意，不是实际请求运行日志。

| 时刻 | `self.inflight` 的内容 | 发生了什么 |
| --- | --- | --- |
| 请求 A 尚未登记 | `{}` | 当前没有登记中的请求 |
| A 进入 `_run_turn` 并登记 | `{"sid-demo": {task_A}}` | 登记当前已有的请求 Task |
| A 退出 `_run_turn` | `{"sid-demo": set()}` | 移除 `task_A`；会话编号保留，集合为空 |
| 同一会话的请求 B 进入并登记 | `{"sid-demo": {task_B}}` | 编号沿用，登记的是另一份请求工作 |
| B 未结束时开始关闭会话，执行 `inflight.pop(sid, ())` 后 | `{}` | 该条登记被取走，`task_B` 由局部 `tasks` 接住，后面继续等待或取消它 |

- **谁登记、谁移除**：`_run_turn` 在处理开始时 `add(task)`，退出时在 `finally` 中 `discard(task)`；具体代码见页首链接。
- **谁查这张表**：`shutdown_session(sid)` 按编号取出这组任务，处理会话关闭前的剩余请求。它另外把 `sid` 加入 `closed`，使后续同会话请求在入口被拒绝。
- **表里不保存历史内容**：已经结束的请求不会作为历史一直留在这组 Task 中。逐轮消息与生成记录由 `manager` 保存，会话配置由 `store` 保存。
- **空集合有明确含义**：`{"sid-demo": set()}` 表示这个会话暂时没有登记中的请求；它不等于会话已经关闭。一个 Adapter 还可以登记其他 `sid`，关闭本会话不会取走其他会话的条目。

> `inflight[sid]` 回答“这次执行目前还有哪些请求没有结束”。

<details>
<summary>源码与原始讨论</summary>

- 固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。字典定义、登记与移除分别在 [common.py:156–158](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L156-L158)、[327–338](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L327-L338)、[392–393](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L392-L393)；关闭时取出在 [225–243](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L225-L243)。
- `sid-demo` 与 Task 名称是教学示意。状态变化按源码静态核对，本轮未运行新实验，也未假定用户已经掌握。
- [原始问题与记录分工](../04-flow.md#sid-inflight-background)；[本次拆分决定](../04-flow.md#split-sid-inflight-references)。2026-10-22 从原合并说明迁入，保留状态表和源码证据，未改写前序长期记忆。

</details>
