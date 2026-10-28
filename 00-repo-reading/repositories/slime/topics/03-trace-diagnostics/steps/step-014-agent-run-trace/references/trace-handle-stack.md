# _TRACE_HANDLE_STACK：当前阶段使用哪些追踪句柄

[返回 trace_span 的四行准备](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#entry-preparation) · [阶段编号栈](trace-stack.md)

这是 trace_utils.py:51–54 定义的另一份模块级 ContextVar。与编号栈配套使用，但保存的对象和消费者不同。下面 handle_outer、handle_A、handle_B 都是 TraceHandle 的示意名称。

## 1. 它是什么对象

```python
_TRACE_HANDLE_STACK: contextvars.ContextVar[tuple[tuple[TraceHandle, ...], ...]] = contextvars.ContextVar(
    "slime_trace_handle_stack",
    default=(),
)
```

`.get()` 返回当前执行上下文保存的元组，没有设置过时得到 `()`。它保存的是一组组句柄，而不是 `(trace_id, span_id)` 编号对。

ContextVar 的作用域、with 驱动与显式 set/reset 的分工，见[编号栈说明](trace-stack.md#contextvar-with)。这里使用相同机制：with 的进入退出时机来自 trace_span，ContextVar 自身不自动跟随某个 class 或代码块清空。

## 2. 为什么有两层元组

```python
(
    (handle_outer,),        # 外层阶段的一组目标
    (handle_A, handle_B),   # 内层阶段的一组目标
)
```

外层元组按嵌套阶段组织，里面每个元组保存该阶段的一组 handles。一个 trace_span 可以接受一个或多个目标，所以每层都用句柄元组表示。

最后一组是当前最近登记的目标。每个 handle 自身继续携带 trace_id、carrier 等信息；它和编号栈不是同一个数据结构。

## 3. 谁会使用它

`_get_current_trace_target` 在 755 行读取它，在 758 行取最后一组：

```python
handle_stack = _TRACE_HANDLE_STACK.get()
if not handle_stack:
    return None
current_handles = list(handle_stack[-1])
```

后面根据这一组的长度，返回一个句柄或句柄列表。`_resolve_trace_function_target:692` 在前面未解析出目标时使用这个结果。因此这份栈回答的是：**当前上下文有哪些可用于追踪的目标？**

这里先定位消费者，不展开完整的自动推断与装饰器流程。

## 4. 进入与退出怎样改变它

假设进入前只有外层的 `(handle_outer,)`，本次 handles 是 `[handle_A]`：

```python
handle_stack_before = _TRACE_HANDLE_STACK.get()  # 364：读取已有分组

# 384：本次 handles 作为新的一组，追加到旧分组之后
handle_token = _TRACE_HANDLE_STACK.set(
    handle_stack_before + (tuple(handles),)
)

# 423：在 finally 中恢复本次修改之前的绑定
_TRACE_HANDLE_STACK.reset(handle_token)
```

| 时机 | 当前上下文中保存的值 |
| --- | --- |
| 进入前 | `((handle_outer,),)` |
| 本次登记后 | `((handle_outer,), (handle_A,))` |
| 使用 handle_token 恢复后 | `((handle_outer,),)` |

`tuple(handles)` 得到本次的一组句柄；外面的 `(tuple(handles),)` 将这一组作为一个元素接到旧栈后面。`handle_stack_before` 是旧值，`handle_token` 是恢复凭据。

这一表达式会构造本次句柄元组，再拼接外层分组元组；复制的是引用，不会复制每个句柄关联的事件数据。性能判断沿用[编号栈的开销说明](trace-stack.md#tuple-cost)，具体开销仍需实际测量。

## 5. 和编号栈怎样区分

| 对象 | 每层保存什么 | 主要用途 |
| --- | --- | --- |
| _TRACE_STACK | `(trace_id, span_id)` | 查找某条追踪的父阶段编号 |
| _TRACE_HANDLE_STACK | 一组 `TraceHandle` | 取得当前阶段的追踪目标 |

回到父卡的 get：此时只是读取旧的一组组句柄；登记本次 handles 在循环之后的 384 行进行。

<details>
<summary>来源与边界</summary>

- Slime 固定版本 18868a79：[定义](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L51-L54)、[读写与恢复](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L362-L425)、[当前目标查询](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L754-L763)、[使用查询结果](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L679-L692)。
- 与另一份栈采用相同的 ContextVar 存取和恢复语义；跨任务传播不在本页展开。
- 表格是状态形状示意，没有执行真实 Agent。
- 隔离运行源码中的 ContextVar 定义与读取函数，确认句柄分组深度由 1 变为 2，当前目标查询得到内层句柄，reset 后回到外层句柄；未执行完整 trace_span。

</details>
