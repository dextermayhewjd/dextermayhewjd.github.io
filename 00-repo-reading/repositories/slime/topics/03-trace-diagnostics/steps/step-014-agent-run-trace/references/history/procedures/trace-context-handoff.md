> 历史归档（2026-10-27）：本稿退出当前阅读入口，仅保留此前解释、原话与验证边界。当前归属见[归档说明](README.md)。

# Procedure · 把当前 Trace 接给 Adapter

[返回 scope 的组合入口](../../../01-scope.md#tool-catalog) · [bind_trace 函数卡](../../../02-short-term-memory/functions/slime/observability/trace_utils.py/bind_trace.md)

**使用定位：这是有真实调用依据的上下文集成组合。** 官方普通打点没有要求每次先执行这些函数。这里把已经在 scope 展示的例子迁入 02，不新增必读实现链。固定源码 18868a79；下面的 T1/S0 和字典是教学值。

<a id="usage-method"></a>

## 1. 使用方法：把当前任务的 Trace 接到 Adapter 会话

完整数据样例见 [T3/C0 → session-9](../../../02-short-term-memory/examples/bind-trace/README.md)，包含共享引用和事件数的核对。

Coding Agent 的 generate.py:270–275 在准备 session 时执行如下调用，省略与本次追踪无关的参数：

```python
adapter.open_session(
    session_id,
    trace=import_trace(export_trace(bind_trace(base_sample)), base_sample.trace),
)
```

将其中嵌套的 trace 实参拆开阅读：

```python
session_trace = import_trace(export_trace(bind_trace(base_sample)), base_sample.trace)
```

session_trace 是等价拆读时增加的局部变量，不是原源码名称。求值先后与落点：

```text
bind_trace(base_sample)         → h，准备/复用 base_sample.trace
export_trace(h)                 → 身份与父阶段 payload（没有 events）
import_trace(payload, 同一字典) → session 用的句柄
adapter.open_session           → 接收该句柄，继续使用同一个本地 carrier
```

最后一步并没有搬运一份历史事件。这个调用复用本地字典；如果接收方提供另一个字典，事件就留在另一个字典，不能推断跨进程自动共享。

### 调用前后与真正的下一次使用

沿 Coding Agent 的外层 generate:229 进入时，coding_rollout 已经绑定 base_sample 并写入开始事件。本次 bind/export/import 复用这些已有记录，把句柄交给新会话；它们自己不新增 Agent 执行事件。

[BaseAdapter.open_session:287–292](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L287-L292)将传入的 trace 保存到 self.store[sid].trace。之后收到 CLI 的模型请求，[_run_turn:412–423](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L412-L423)使用该会话字段。以下省略 tokenize 的实参及分支之外的请求处理，保留实际空目标分支：

```python
with trace_span(s.trace, "agent_model_turn", record_error=False) if s.trace else nullcontext():
    target = bind_trace_carrier(s.trace.carrier) if s.trace else None
    with trace_span(target, "agent_tokenize", record_error=False) if target else nullcontext():
        translated, tools_schema = self._translate(body)
        prompt_ids = _session_prompt_ids(...)
    turn = await call_sglang_generate(prompt_ids, s, body, adapter=self, session_id=sid)
```

这里 bind_trace_carrier 的输入不是临时空字典，而是会话已有的 s.trace.carrier。它交回的 target 指向原容器；随后 agent_tokenize 等阶段事件写入这一容器。正常链路上，该容器就是 base_sample.trace，于是请求阶段记录能与原任务一起保存。

**整段使用的结果**：会话保存的是句柄，持久记录仍在 carrier 的 events 中；当前代码没有通过 export/import 复制一份历史事件，也没有使用这些函数保存文件。以上是固定源码推导，不是一次已执行会话的日志。[本轮核对](../../../04-flow.md#step014-real-business-usage)。

## 2. 分开看各个交接的输入与输出

下列保留为接口级教学对照，不是额外的真实业务调用点；export/import 两段共享同一个 payload，carrier 绑定例另用新字典。已导入各段对应接口。

<a id="tool-bind-carrier"></a>

### bind_trace_carrier：已有普通字典怎样变成目标

```python
from slime.observability.trace_utils import bind_trace_carrier

carrier = {}
handle = bind_trace_carrier(
    carrier, trace_id="T1", sample_id=7, group_id=2
)
```

- **使用前**：carrier={}。
- **使用后**：carrier 补齐六个基础键，trace_id="T1"、sample_id=7、group_id=2、attempt=0、events=[]；handle.carrier is carrier。
- **留下在哪里**：这个普通字典，没有自动挂到某个 Sample，也没有自动写文件。carrier=None 时会创建新的字典，由 handle.carrier 持有。
- **使用定位**：Adapter 有实际调用；官方普通打点示例没有要求业务先调用它。
- [源码 257–286](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L257-L286)。

<a id="tool-export"></a>

### export_trace：只交出身份与父阶段

```python
from slime.observability.trace_utils import bind_trace_carrier, export_trace

handle = bind_trace_carrier(
    {}, trace_id="T1", sample_id=7, group_id=2, parent_span_id="S0"
)
payload = export_trace(handle)
```

使用后返回：

```python
{
    "version": 1,
    "trace_id": "T1",
    "sample_id": 7,
    "group_id": 2,
    "attempt": 0,
    "parent_span_id": "S0",
}
```

- **使用前后**：handle 和原有 events 不因这次调用而改变。
- **留下在哪里**：payload 返回值，里面没有 events；它给接收方说明“属于哪条追踪、接在哪个阶段下”，没有写出任何文件。
- [源码 289–308](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L289-L308)。

<a id="tool-import"></a>

### import_trace：绑定到接收侧容器

假定 payload 是上例所示的六字段字典：

```python
from slime.observability.trace_utils import import_trace

received_trace = {}
remote_handle = import_trace(payload, received_trace)
```

- **使用前**：接收侧 received_trace={}。
- **使用后**：received_trace 包含 T1、样本 7、组 2、attempt=0 和空 events；remote_handle.parent_span_id="S0"，remote_handle.carrier is received_trace。
- **留下在哪里**：接收侧字典和返回句柄。import_trace 不会从发送方复制旧事件；之后对 remote_handle 写的事件只进入 received_trace，不会自动汇总回发送方。
- **当前仓库例子**：Coding Agent 在 [generate.py:272](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L272) 把 export/import 与同一个 base_sample.trace 一起交给 adapter.open_session，因此该处仍复用本地容器；不据此推断所有跨进程调用都共享字典。
- [源码 311–323](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L311-L323)。

## 3. 当前边界与未解问题

能指出 payload 不含 events，以及后续事件属于哪个 carrier，即达到这份用法记录的边界。分布式事件如何汇总不是 export/import 自动完成的事情，本轮不扩展为网络传输协议。

用户尚无对这些集成接口的独立理解表述；原有例子是助手核对，迁移不代表已掌握。

<details>
<summary>来源与验证</summary>

- [真实调用 generate.py:270–275](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L270-L275)。
- [Adapter 使用 carrier 的位置](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L412-L414)。
- [官方指南](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/docs/zh/developer_guide/trace.md)；[官方角色核对](../../official-trace-api-review.json)；[本轮记录分工](../../../04-flow.md#step014-scope-summary-short-term-usage)。
- 上述接口已有隔离示例核对；没有执行 Adapter 会话、跨进程传输或真实 Agent。

</details>
