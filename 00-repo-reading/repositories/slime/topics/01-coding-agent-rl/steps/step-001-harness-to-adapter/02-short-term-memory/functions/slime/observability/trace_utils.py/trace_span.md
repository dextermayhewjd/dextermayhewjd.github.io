# trace_span

- 源码定位：[slime/observability/trace_utils.py:345](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L345-L425)，版本 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，由助手核对。
- 首次接触：2026-10-23，Step 1 回看 `_run_turn` 的执行追踪包装。
- 最近认识更新：2026-10-23，用户开始用“通过 TraceHandle 向列表写事件，类似 logger”概括职责。本轮补清当前调用使用已有 handle，以及 trace_id、span_id 和记录位置的区别；这些澄清尚待反馈。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据当前调用和源码整理，不代表用户已经确认理解。

1. **使用场合**：`_run_turn` 执行消息转换、输入编码和模型生成时，用 `trace_span` 标记这些阶段。阅读时回头解释这个包装；实际执行时，记录从进入相应 `with` 块就开始。

2. **具体内容**：接收要写入的追踪目标 `target`、阶段名 `name`、可选属性 `attrs` 和异常详情开关 `record_error`。进入时追加开始事件，退出时追加结束事件，并维护嵌套阶段的父子关系。本场景的事件保存在 `s.trace.carrier["events"]`。

3. **建议构建的心智模型**：

   > - **接住记录位置**：`s.trace` 指向已有的追踪数据，阶段名说明这次观察哪段代码。
   > - **记录进入与退出**：往原来的 `events` 列表追加开始、结束事件，用同一个 `span_id` 将它们配对。
   > - **留下执行过程**：阶段名、时间戳和关联编号用于后续定位问题；模型输入输出仍由块内业务函数产生。

4. **调用代码**（[当前调用处](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L410-L423)）：

   ```python
   with trace_span(s.trace, "agent_model_turn", record_error=False) if s.trace else nullcontext():
       ...  # 消息转换、输入编码和模型生成；此处只展示外层包装
   ```

## 本场景的输入与输出

**① 输入：给哪份记录、哪个阶段添加追踪。**

`s` 是当前会话的 `Session`；它的 `trace` 字段保存一个 `TraceHandle` 对象。这个对象指向 `carrier` 字典，字典里的 `events` 是保存事件的列表。图中只列本轮需要的字段：

```text
s                                      # Session 对象
└─ trace                               # TraceHandle 对象
   └─ carrier                          # dict：一份追踪的数据
      ├─ trace_id = "demo-trace"        # 这份追踪的标识
      └─ events = []                   # list：每个元素是一条事件 dict
```

因此，`s.trace.carrier["events"]` 就是沿这条路径取到**那个待追加的列表**。`carrier` 是字段名；在当前场景，它保存的是本地 Python 字典。图中使用新建追踪的局部示例，真实会话的列表可能已有其他事件；本函数继续追加，不清空原记录。

可以把这套功能理解为结构化的执行日志。本场景的 `TraceHandle` 已保存在 `s.trace`，`trace_span` 使用它向 `carrier["events"]` 追加事件。`trace_id` 标记事件属于哪份追踪，实际写入位置由对象中的 `carrier` 引用提供；`span_id` 则配对某一段执行的开始与结束。当前记录先保存在内存列表中，打印或导出由后续机制处理。

| 输入 | 本场景的值与作用 |
| --- | --- |
| `target` | `s.trace`，告诉函数事件写到哪份追踪记录 |
| `name` | `"agent_model_turn"`，标识被观察的业务阶段 |
| `attrs` | 未传入，默认 `None`；本次外层调用没有额外属性 |
| `record_error` | `False`，不自动把异常类型和消息加入结束事件；异常仍继续抛出 |

<a id="trace-span-data-structure"></a>

**② 处理与输出：同一段执行怎样留下开始和结束。**

沿用上面的局部输入，初始列表是 `[]`。先把当前外层 span 的三段处理与源码对应起来；块内的其他 span 可以另行追加事件，此处暂不展开。

| 时机 | 本函数中的实际位置 | 当前这段追踪发生什么 |
| --- | --- | --- |
| **进入 `with`** | `trace_span:362–384`，调用 `_append_event(..., kind="span_start", ...)` | 取得时间、分配本次编号，向原列表追加开始事件 |
| **执行 `with` 主体** | `trace_span:398`，`yield span_context` | 本函数暂停，由调用处执行转换、编码和模型请求 |
| **正常离开 `with`** | `trace_span:412–425`，调用 `_record_span_end(...)` 并恢复上下文 | 沿用本次编号追加结束事件，完成当前追踪 |

因此，输出首先表现为原列表新增了记录。下面只展示本次外层 `agent_model_turn` 的两条事件，内层事件及公共元数据暂时省略；编号 `A` 和时间 `10.0 / 12.0` 是教学替换值：

```python
[
    {"type": "span_start", "name": "agent_model_turn", "span_id": "A", "ts": 10.0},
    {"type": "span_end",   "name": "agent_model_turn", "span_id": "A", "ts": 12.0},
]
```

- `type` 区分开始与结束，`name` 标出阶段名称。
- 同一个阶段可以执行多次，`span_id` 用来区分具体哪一次，并把它的开始和结束配对。
- `ts` 是时间戳，后续可以据两者之差计算耗时。

实际写入最终落到 `_append_event` 的这一句：

```python
handle.carrier["events"].append(event)
```

当前外层场景的 `handle` 就是传入的 `s.trace`，`event` 是刚组好的事件字典。这句位于 `_append_event:612`；该辅助函数承担具体写入，`trace_span` 负责安排开始和结束时机。

| 分清三种结果 | 本场景中对应什么 |
| --- | --- |
| **函数调用的返回值** | 上下文管理器，供 `with` 使用 |
| **对原对象的修改** | `s.trace.carrier["events"]` 增加事件；这才是要观察的数据变化 |
| **块内的业务结果** | `prompt_ids`、`turn` 仍由各业务函数产生，不是 `trace_span` 的返回值 |

**③ 本轮需要读到哪一层。**

本轮读清三件事即可：**记录写到哪里、进入与退出分别追加什么、函数返回值与原对象变化有什么区别**。父子阶段先知道用途，具体实现按需继续。

<details>
<summary>需要继续时再看：两层嵌套、as span 与退出边界</summary>

**在调用处圈住什么：先看已读的业务代码。**

下面从 `common.py:412–425` 裁剪，假定已有追踪目标，省略 `nullcontext` 分支与业务函数实参。`bind_trace_carrier` 在这里继续指向同一份事件字典。

```python
with trace_span(s.trace, "agent_model_turn", record_error=False):
    target = bind_trace_carrier(s.trace.carrier)
    with trace_span(target, "agent_tokenize", record_error=False):
        translated, tools_schema = self._translate(body)
        prompt_ids = _session_prompt_ids(...)
    turn = await call_sglang_generate(...)

raw_output = tok.decode(...)  # 已离开上面两层 span
```

- 内层 `agent_tokenize` 包住消息转换和输入编码。
- 外层 `agent_model_turn` 包住内层阶段和模型生成。`call_sglang_generate` 内部每次请求还可以建立 `sglang_generate` 子 span。
- `tok.decode`、后续协议响应及 manager 记录位于这两层 `with` 之外。阶段名不能代替真实缩进范围。

**可选的 as span 与完整嵌套事件。**

`trace_span(...)` 先得到供 `with` 使用的上下文管理器。追踪目标有效时，进入后可通过 `as span` 取得 `TraceSpanContext`，用于补充属性；当前 `_run_turn` 的这两处没有接住它。

最重要的可观察变化是 `s.trace.carrier["events"]` 增加记录。局部实验只运行上述两层追踪，省略业务函数执行，得到下表；它不是完整 `_run_turn` 的全部事件：

| 次序 | `type` | `name` | `span_id` | `parent_span_id` | `ts` |
| --- | --- | --- | --- | --- | --- |
| 1 | `span_start` | `agent_model_turn` | outer | 无 | t0 |
| 2 | `span_start` | `agent_tokenize` | inner | outer | t1 |
| 3 | `span_end` | `agent_tokenize` | inner | 无 | t2 |
| 4 | `span_end` | `agent_model_turn` | outer | 无 | t3 |

- `outer / inner` 是实际随机编号的显示别名，`t0–t3` 代表实际时间戳；完整原值见[局部实验 JSON](../../../../../references/trace-span-local-example-18868a79.json)。
- 开始与结束用同一个 `span_id` 配对；父子关系写在子阶段的开始事件里。后续工具可据时间戳计算耗时。
- 所有事件还携带同一 `trace_id="demo-trace"`，以及样本、分组与尝试次数信息。本例未设置样本和分组，二者为 `None`，`attempt=0`。
- 这里不会自动复制函数的全部入参、输出 token 或 logprob。`TurnRecord` 继续负责保存生成数据；调用处可显式追加诊断属性。

**没有追踪目标与异常退出。**

- **没有追踪目标**：调用处使用 `nullcontext()`，仍执行块内业务，不增加这里的 span 记录。
- **块内抛出异常**：本场景仍尝试追加结束事件并恢复追踪上下文，然后继续抛出原异常。`record_error=False` 不等于忽略异常。

当前读到“圈住哪里、写到哪里、怎样开始和结束”即可。跨线程传递、两个 ContextVar 栈、导出与查看器留待对应问题，不在本轮逐层展开。

**后续按问题选择阅读深度：**

| 阅读层次 | 当前需要做到什么 |
| --- | --- |
| **现在需要读清** | `TraceHandle → carrier 字典 → events 列表`；一条事件的 `type / name / span_id / ts`；进入、退出各追加什么；包住了哪段业务 |
| **暂时认得作用** | `parent_span_id` 表示属于哪个外层阶段；`record_error=False` 不自动记异常详情，仍会传播异常 |
| **以后按问题展开** | ContextVar 栈怎样维护嵌套、`TraceSpanContext` 怎样补属性、多目标兼容、跨事件循环传递、导出和查看器 |

这轮先停在第一层。父子关系的实现、对象创建链和完整追踪系统不作为当前继续阅读的前提；读清第一层后，再决定是否需要向下追。

</details>

## 我的直接表述（原话）

本轮阅读选择与深度要求：

> 其余都是细枝末节的东西
> 暂时不考虑直接看下一步吧
> 那么当前是否需要考虑一下看一下这里的trace_span的部分了呢？

这是此前阅读范围的确认。随后用户明确反馈：

> 这里我就不理解了
> 我完全不理解这里的数据结构等内容
> 不是很清楚这里到底在做什么
> 这里的内部实现细节我需要掌握多少呢？

用户随后明确本次修改对象：

> 那么你觉得你会考虑如何修改这里的关于trace_utils.py的 我的意思是这里的short term memroy的内容

此前调整的是这张单函数卡片的组织方式，不能把卡片调整或局部验证视为用户已理解。随后用户提出新的职责概括：

> 我可以简单的理解为这里通过这个trace函数能够通过这里的trace id什么的 通过保存一个tracehandle对象
> 然后通过在对应的list中写入对应的事件
> 更多的像是一个logger的行为 我可以简单这么理解吗？

助手认可 logger 类比适合当前职责层，补清本场景是使用已有 TraceHandle 追加事件。用户尚未确认这项细化，也未表示掌握内部实现。

## 尚不清楚

- 用户已开始用 logger 类比概括事件写入；“已有 TraceHandle 被使用”、标识与写入位置的区别尚待确认，其余内部机制仍未展开。
- `s.trace` 怎样从任务绑定到会话，跨事件循环为何要显式携带。
- 内部怎样用 ContextVar 管理嵌套，以及 `as span` 追加属性的完整接口。
- 这些事件怎样导出、与其他组件关联并在查看器中展示。

<details>
<summary>来源、验证与 Python 语义依据</summary>

**局部示例对象的准备（此前展示的代码，按需回查）：**

调用处已经有 `s.trace`。本地示例用真实辅助函数准备同样类型的对象，不展开其创建链：

```python
s.trace = bind_trace_carrier(None, trace_id="demo-trace")
# s.trace 是 TraceHandle；s.trace.carrier 是承载追踪信息的字典
# 初始 s.trace.carrier["events"] == []
```

本轮新增的两条事件示意对应既有局部实验中外层阶段的开始与结束；只选取 `type / name / span_id / ts`，将随机编号与时间替换为教学值。它不是完整事件列表，也不是新增真实模型运行。

本轮呈现调整：保留原栏目与输入结构，增加“进入 → 执行主体 → 退出”的源码对应，单独区分返回值、对象修改与业务结果；原阅读深度表和完整嵌套材料收在折叠区。未新增对内部机制的掌握结论。

本轮讨论：[数据结构与阅读深度](../../../../../04-flow.md#trace-data-structure-depth)。

- 固定源码：[`trace_span`](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L345-L425)；[`bind_trace_carrier`](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L257-L286)；[`_append_event`](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L587-L613)；[`_record_span_end`](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L499-L518)。
- `yield span_context` 位于 `398` 行：其前面准备并记录开始，暂停后运行调用处的 `with` 主体；恢复时根据正常或异常路径记录结束，`finally` 恢复此前上下文。本页没有递归展开辅助函数。
- 当前源码的局部实验验证：两层嵌套产生四个事件、同一编号配对、子阶段指向外层、退出后恢复原上下文；另验证 `record_error=False` 时异常仍传播且留下结束事件。业务函数被省略，没有运行真实模型、CLI 或 HTTP。
- 已有 `tests/observability/test_trace_utils.py` 共 **3 项通过**，覆盖模型附加属性、查看器读取与取消时的收尾；不代表完整分布式追踪已经运行。
- 讨论来源：[Step 1 · 回看追踪包装](../../../../../04-flow.md#trace-span-local-reading)。

### 书上怎么说

`@contextmanager` 包装的生成器在 `yield` 处暂停，执行调用处的 `with` 主体。[依据 A]

### 我的判断（本书未覆盖）

Slime 将开始事件放在暂停前，将结束及恢复放在后续正常/异常路径；事件字段和存储位置以本页列出的仓库源码与局部实验为据，不能当作 Python 自动提供的追踪功能。

### 依据

A · 《Fluent Python》第 2 版，第 18 章，Using @contextmanager。

- 英文：[corpus/en/ch18.md](/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/en/ch18.md:266)，266–436 行，锚点 `using-contextmanager`。
- 中文：[corpus/zh/ch18.md](/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/zh/ch18.md:260)，260–419 行，18.2.2 使用 @contextmanager。
- 版本：本书基于 Python 3.10；局部实验环境为 Python 3.12.3。
- 原文：The generator pauses at this point while the body of the `with` executes.
- 对照：这个函数在该处暂停，`with` 块的主体开始执行。

</details>
