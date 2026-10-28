# _TRACE_STACK：当前追踪经过哪些阶段

[返回 trace_span 的四行准备](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#entry-preparation) · [另一套句柄栈](trace-handle-stack.md)

这是模块级共享状态的说明。定义位于 trace_utils.py:47–50；本页解释对象与数据，具体 get、set、reset 的时机仍归 trace_span 函数卡。以下 T1、S0、S1 是示意编号，不是真实 Agent 运行结果。

## 1. 它是什么对象

```python
_TRACE_STACK: contextvars.ContextVar[tuple[tuple[str, str], ...]] = contextvars.ContextVar(
    "slime_trace_stack",
    default=(),
)
```

模块里创建的是一个 ContextVar 对象，它在当前执行上下文中保存一个元组。`.get()` 取得的是该上下文中的值。没有设置过时，使用默认值 `()`。

这不是本次 `_coerce_handles` 的返回值，也不是 trace_span 每次新建的变量。trace_span 进入时读取它，使用期间临时登记本次阶段，退出时恢复。

<a id="contextvar-with"></a>

### ContextVar 与 with 分别负责什么

ContextVar 保存的是**当前执行上下文中的值**，不是以 class 或某个 with 代码块作为自动作用域。普通代码中也能调用它的 get、set、reset。asyncio 原生支持这种上下文；默认新建 Task 时复制创建时的上下文绑定，后续可以设置各自的值。[ContextVar 文档](https://docs.python.org/3.12/library/contextvars.html)、[Task 的 context 说明](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.Task)。

当前 Slime 场景由 trace_span 把这些操作组织成进入与退出：

```python
# 进入：显式设置本阶段的值，并保存恢复凭据
token = _TRACE_STACK.set(stack_before + tuple(new_entries))
try:
    yield span_context  # with 中的业务在这里执行
finally:
    _TRACE_STACK.reset(token)  # 退出：显式恢复此前绑定
```

这是生命周期的教学裁剪，省略其他准备、异常记录及结束事件。with 驱动上下文管理器；实际改变和恢复 ContextVar 的是代码中的 set、reset。仅仅写一个 with，并不会自动替任意 ContextVar 安排恢复。

这里的 `.set()` 是设置值的方法，保存的栈值本身是 tuple。不同上下文的绑定可以独立变化，但 ContextVar 不会因此为其中的每个 Sample、TraceHandle 自动制作独立副本。

## 2. 保存的值长什么样

```python
(
    ("T1", "S0"),   # 追踪 T1 的外层阶段 S0
    ("T1", "S1"),   # 追踪 T1 的内层阶段 S1
)
```

每个条目都是 `(trace_id, span_id)`。外层元组保存当前上下文中的阶段记录，尾部是最近登记的阶段。内部条目只包含编号，不含 Sample，也不含事件字典。

## 3. 为什么需要它

当内部再进入一个 span，而且 handle 没有显式指定 parent_span_id 时，trace_span:371 调用 `_get_current_parent_span_id`。该函数从后向前寻找相同 trace_id 的条目，把找到的 span_id 作为父阶段编号。

例如上面的值中，对 T1 查找会得到 S1，于是下一个内部阶段能关联到 S1。这个栈回答的是：**同一条追踪中，当前最近的阶段是谁？**

## 4. 一次进入与退出怎样改变它

假设进入本次 S1 前，值是 `(("T1", "S0"),)`：

```python
stack_before = _TRACE_STACK.get()  # 363：读取旧值，仍只有 S0
new_entries = []                  # 366：本次的新编号条目

# 382：循环中登记本次的追踪编号和阶段编号
new_entries.append((handle.trace_id, span_id))

# 383：旧条目加本次条目，同时取得恢复用的 token
token = _TRACE_STACK.set(stack_before + tuple(new_entries))

# 419：with 使用期结束后，在 finally 中恢复
_TRACE_STACK.reset(token)
```

| 时机 | 当前上下文中保存的值 |
| --- | --- |
| 进入前 | `(("T1", "S0"),)` |
| 登记 S1 后 | `(("T1", "S0"), ("T1", "S1"))` |
| 使用 token 恢复后 | `(("T1", "S0"),)` |

`stack_before` 是读出的旧元组；`token` 是这次 set 返回的恢复凭据，二者用途不同。用 `+` 拼出新元组，没有在旧元组上原地 append。

所以这个过程是“旧条目加上本次条目，得到新值；当前上下文改为引用新值”。旧元组仍可由 stack_before 引用，退出时用 token 恢复之前的绑定，并非拿旧栈去覆盖刚生成的阶段记录。

## 5. 回到当前四行

现在回到父卡的 `stack_before = _TRACE_STACK.get()`：它只是读取进入前的阶段编号，不会新建 span 或写事件。随后得到的 `new_entries` 才记录本次新增编号。

本轮先看清值的形状、父编号查询、进入登记与退出恢复。ContextVar 在任务之间如何传播属于后续问题。

<a id="tuple-cost"></a>

## 6. 这种写法的效率怎样判断

要把 ContextVar 的存取与 Python 表达式的开销分开。当前 get 取出已有值；这里明显随栈长度增长的工作，是 `stack_before + tuple(new_entries)` 构造新的元组。

以 CPython 3.12.3 的实现为依据，两个非空元组相加会分配新元组，并复制两边的元素引用；有空元组时存在直接复用的快路径。如果旧栈有 n 项、本次新增 k 项，普通拼接的时间和新元组槽位数量为 O(n+k)。这不会深拷贝 Sample、TraceHandle 或整个 events 列表。[CPython tupleconcat 实现](https://github.com/python/cpython/blob/v3.12.3/Objects/tupleobject.c)。

工程判断：嵌套浅、单次目标少时，这里的复制规模也小，可以先保留这种直接表达进入与恢复的实现。嵌套非常深、每次目标很多或跨度创建频繁时，分配与引用复制就值得测量。当前没有做性能基准，不能据此断言它在实际 workload 中占用多少时间，也不把所有 get/set/reset 宣称为同一种 O(1) 操作。

<details>
<summary>来源与边界</summary>

- Slime 固定版本 18868a79：[定义](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L47-L50)、[读写](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L362-L384)、[查询父编号](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L630-L639)、[恢复](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L417-L425)。
- ContextVar 的存取、恢复语义已核对本机 Python 3.12 文档字符串；补充教材：[24.2 · token 与 reset](../../../../../../../../content/projects/python-async-concurrency/24-contextvar-reset/index.md)。不因此改变独立 Python 课程的进度。
- 例子用于说明本地状态变化，没有执行真实 Agent。
- 本轮将源码中的两个 ContextVar 定义、TraceHandle 和两个读取辅助函数隔离运行：确认编号栈从 S0 临时加入 S1，查父编号得到最近条目，reset 后恢复 S0。此验证没有执行完整 trace_span。

</details>
