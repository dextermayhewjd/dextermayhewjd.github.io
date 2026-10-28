# TraceSpanContext

- 源码定位：[trace_utils.py:68–111](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L68-L111)，固定版本 18868a79。
- 首次接触：Step 014 已定位；2026-10-27 按用户要求进入 scope 第 7 项，建立本卡。
- 最近认识更新：用户觉得数据关系耦合较多，明确要求返回 scope 看本类职责；下文为助手核对，尚无独立理解确认。

## 1. 对象职责

当前先用[同一阶段的完整数据案例](../../../../examples/trace-span-agent-run/README.md)观察事件怎样逐步形成，再回本卡查对象字段。这里不再作为必须逐层读完的前置。

**TraceSpanContext 是一次 span 的操作对象：关联本次阶段的信息，并让业务代码为结束事件补充属性。**

在当前正常路径中，[trace_span](../../../../functions/slime/observability/trace_utils.py/trace_span.md#span-context-yield) 创建它，通过 yield 交给调用处的 as span。调用方操作的 span 与 trace_span 保存的 span_context 是同一个对象。

| 对象 | 当前先记住的职责 |
| --- | --- |
| [TraceHandle](TraceHandle.md) | 标识记录目标，并指向保存事件的 carrier |
| TraceSpanContext | 关联这一次阶段，暂存业务补充的结束属性 |
| trace_span 函数 | 组织进入、交出对象、写结束事件及恢复上下文 |

业务只需调用 span.set("exit_code", 0)，无需自己查句柄、生成事件或处理阶段退出。TraceSpanContext 类没有 __enter__ / __exit__；当前 with 的进入退出由外层 @contextmanager 装饰的 trace_span 组织。

<a id="usage-method"></a>

## 使用方法：业务拿到 span 后做什么

具体数据见 [set：退出码样例](../../../../examples/trace-span-agent-run/README.md)与 [update：模型元信息样例](../../../../examples/sglang-meta-update/README.md)。

| 方法 | trace_utils.py 外的真实调用 | 当时在做什么 | 留下的结果 |
| --- | --- | --- | --- |
| set | [Coding Agent generate.py:295](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L286-L296) | Agent 运行结束，把返回的退出码交给本阶段 | end_attrs 增加 exit_code，退出 with 后出现在结束事件 |
| update | [SGLang generate:230](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L219-L230) | 模型请求返回，把整理后的响应元信息交给本阶段 | 普通属性进入 end_attrs，退出时写入结束事件；子阶段描述另展开 |

```python
span.set("exit_code", agent_exit_code)
```

```python
span.update(build_sglang_meta_trace_attrs(output["meta_info"]))
```

两行来自两个不同业务场景，不能当作同一次调用连续执行。完整上下文和前后结果分别见 [trace_span 用法](../../../../functions/slime/observability/trace_utils.py/trace_span.md#usage-method)与[元信息组合用法](../../../../functions/slime/observability/trace_utils.py/build_sglang_meta_trace_attrs.md#usage-method)。下面的构造与内部收尾继续用于解释这些行为，不充当外部使用案例。

## 2. 当前路径：创建对象，交给业务，再带回结束属性

### 创建与交出

<a id="construct-context"></a>

**本段只看构造语句：新建一个 TraceSpanContext 对象，把前面已经准备好的四项数据保存成它的字段，再用 span_context 这个变量接住。** 括号左侧是新对象的字段名，等号右侧是当前函数中的数据。

真实调用位于 trace_span:390–398；下列仅省略包围 yield 的 try：

```python
span_context = TraceSpanContext(
    target=handles[0] if len(handles) == 1 else handles,
    handles=handles,
    span_records=span_records,
    start_ts=timestamp,
)
yield span_context
```

假设这一刻已有 handles=[h]、span_records=[(h, "S1")]、timestamp=10.0：

| 构造参数 | 新对象里保存什么 | 为什么区分这一项 |
| --- | --- | --- |
| target=handles[0] if len(handles) == 1 else handles | 只有一个目标时保存 h；多个目标时保存整个 handles 列表 | 保留“一个目标 / 多个目标”的形态 |
| handles=handles | 原来的 [h] 列表 | 这里始终保留列表形态；与 target 引用的是相同目标 |
| span_records=span_records | 原来的 [(h, "S1")] 列表 | 额外保留“哪个目标对应本次哪个阶段编号”，供结束配对 |
| start_ts=timestamp | 10.0 | 保存前面取得的开始时间，不在此重新计时 |

构造完成后的关系是：

```text
span_context：新对象
├─ target       → h
├─ handles      → 原来的 [h]
├─ span_records → 原来的 [(h, "S1")]
└─ start_ts     = 10.0
```

target 和 handles 确实涉及同一批目标，但保存的形态不同；span_records 另外带着本次的阶段编号。这里新建的是外层状态对象，传入的两个列表没有被复制，也没有新生成句柄或写入事件。未传入的 end_attrs、end_events、closed 则使用类中定义的初始值 {}、[]、False。

紧接着的 yield 是下一次交接，把刚创建的对象交出去：

```text
trace_span 中的 span_context ─┐
                             ├─→ 同一个 TraceSpanContext 对象
调用处 as span 得到的 span ──┘
                                  └─ end_attrs = {}
```

<a id="business-methods"></a>

### 业务怎样补属性：set / update

以下是调用方取得 as span 后的使用。set/update 可由业务调用；build_end_attrs/finalize 由 trace_span 内部收尾，不组成四个业务步骤。

#### set：业务补充退出码

调用处在 generate.py:286–295。这里只节选 with 行和本次关注的操作；harness.run 的完整调用仍在父函数卡：

```python
with trace_span(base_sample, "agent_run", record_error=False) as span:
    # 中间 await harness.run(...)，得到 agent_exit_code
    span.set("exit_code", agent_exit_code)
```

set 的真实实现，trace_utils.py:78–81：

```python
def set(self, key: str, value: Any) -> TraceSpanContext:
    self.end_attrs[key] = value
    self._sync_end_events({key: value})
    return self
```

<a id="set-and-sync"></a>

本次进一步展开 set，只需要跟住两个位置：

| 位置 | 里面放什么 | 当前调用时 |
| --- | --- | --- |
| end_attrs | 本阶段要附加到结束记录的属性 | 开始是 {} |
| end_events | 已经生成的结束事件字典的引用 | 仍然是 [] |

set 的三行分别做三件事：

1. self.end_attrs[key] = value：把本次属性放进暂存字典；已有同名键时覆盖它。
2. self._sync_end_events({key: value})：如果对象已经持有结束事件，就把这项属性同步到那些字典。
3. return self：返回的还是当前 TraceSpanContext；当前调用处不使用这个返回值。

第二行对应的真实代码是：

```python
def _sync_end_events(self, attrs: dict[str, Any]) -> None:
    if not self.end_events or not attrs:
        return
    for event in self.end_events:
        event.setdefault("attrs", {})
        event["attrs"].update(attrs)
```

**当前正常路径走第一个 return。** 调用 set 时还在 with 内，没有生成本阶段的结束事件，因此 end_events 为空。假设 agent_exit_code=0，实际变化只有：

```text
                         调用前                  调用后
span.end_attrs           {}                      {"exit_code": 0}
span.end_events          []                      []
carrier 中本阶段的事件   已有 span_start          仍只有 span_start
```

set 不在这里创建 span_end，也不为 span_start 加退出码。退出 with 后，外层 trace_span 才会读取暂存属性并写结束事件。

_sync_end_events 的非空分支是另一种状态：finalize 已把结束事件交给这个对象后，再补属性可以更新那些已有字典。这里只交代该分支为什么存在，不把它当成当前 agent_run 里这次 set 已经发生的行为；完整结束过程仍放在第 9 项。

<a id="attribute-constraints"></a>

### set 的属性是否固定

不是只允许 exit_code。接口约定 key 为 str、value 为 Any，当前 set 没有字段名白名单，也没有值的类型校验；实际执行的是 end_attrs[key] = value。同名键再次设置会覆盖原值。

以下是独立的小例子，不改变 scope 中只设置 exit_code=0 的主例：

```python
span.set("tool_name", "pytest")
span.set("retry_count", 2)
```

如果原来的 end_attrs 是 {}，这两次调用后就是 {"tool_name": "pytest", "retry_count": 2}；最终作为结束事件的 attrs 内容。这不会给 TraceSpanContext 增加同名对象字段，也不会改写事件顶层的 type、name、ts、trace_id 或 span_id。即使把 key 写成 "trace_id"，也只是 attrs 里的同名键，不是更换追踪编号。

通常使用字符串、数字、布尔值、None 及由这些值组成的列表/字典，便于保存和查看。查看器的 [_json_safe](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tools/trace_timeline_viewer.py#L89-L96)会保留这些基本值、递归处理容器，对其他对象转为字符串；因此 set 接受值，不等于后续保留该 Python 对象的原始类型。

<a id="update-usage"></a>

#### update：批量补属性，可接收子 Trace 描述

```python
with trace_span(sample, "sglang_generate") as span:
    span.update({"completion_tokens": 7, "finish_reason": "stop"})
```

- 使用前：end_attrs={}。
- 调用 update 后：end_attrs={"completion_tokens": 7, "finish_reason": "stop"}，返回 span 自身；普通属性暂不新建事件。
- 离开 with 后：这些属性进入父阶段的 span_end。
- 特殊键 _trace_children 会被单独取出，转换为子阶段或瞬时事件，不作为普通属性直接保留。set 不具备这项专门解析步骤。
- [源码 83–95](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L83-L95)。

官方组合的输入与输出见 [build_sglang_meta_trace_attrs](../../../../functions/slime/observability/trace_utils.py/build_sglang_meta_trace_attrs.md)；只需补一项普通属性时仍可用 set。

<details>
<summary>内部收尾回查：build_end_attrs / finalize</summary>

### 交回结束流程：本轮只定位接口

正常退出 with 后，trace_span:414 先调用 build_end_attrs() 得到属性字典副本，再交给 _record_span_end 写结束事件，最后由 finalize 接住返回的结束事件列表并把 closed 设为 True。build_end_attrs 仅执行 dict(self.end_attrs) or None，不解析、检查错误或决定终止；异常属性由 trace_span 的 except 分支按 record_error 决定是否添加，详见[连续过程](../../../../examples/trace-span-agent-run/README.md)与[异常对照](../../../../functions/slime/observability/trace_utils.py/trace_span.md#exception-boundary)。

这里的 finalize 不负责创建结束事件；它保存的 event 引用指向已经写进 carrier 的那些结束字典。完整结束过程见 [案例 A 的退出环节](../../../../examples/trace-span-agent-run/README.md#use-exit)，对应[旧内部编号 9](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/01-scope.md#internal-reading-map)；本段先看清 **创建的对象怎样交给业务，业务结果怎样留在 end_attrs**。

</details>

## 3. 需要时回查字段与其余方法

<details>
<summary>七个声明字段及本次取值</summary>

| 字段 | 本次构造后的值 | 用途 |
| --- | --- | --- |
| target | h | 本次构造选出的单个目标；多目标时是 handles |
| handles | 原来的 [h] 列表 | 保留所有记录目标 |
| span_records | 原来的 [(h, "S1")] 列表 | 关联本次开始的阶段与句柄，供结束配对 |
| start_ts | timestamp，本例 10.0 | 本阶段开始时间；类的 update 子阶段导入路径也会使用 |
| end_attrs | 新建的 {} | 暂存要写入结束事件的属性 |
| end_events | 新建的 [] | finalize 时接住已经生成的结束事件列表 |
| closed | False | finalize 后变成 True；不是靠这个字段触发退出 |

构造时传入的已有列表保留引用；默认 end_attrs / end_events 则分别由 default_factory 为本实例新建。当前只需知道各对象的归属，不展开 dataclass 的生成机制。

</details>

<details>
<summary>方法定位与边界</summary>

- set:78–81：设置一项结束属性；如已有结束事件，同时同步到这些事件。
- update:83–95：批量补属性；普通用法见上方，子 Trace 描述的展开实现按需回查。
- build_end_attrs:97–98：返回 end_attrs 的字典副本；空时返回 None。
- finalize:100–104：接住结束事件列表、标记关闭，并同步已有结束属性。
- _sync_end_events:106–111：更新已经持有的结束事件字典；没有结束事件或属性时返回。

调用角色以 [scope 的官方用法复核](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/01-scope.md#tool-catalog)为准：set/update 是业务拿到 span 后的补充接口；build_end_attrs/finalize 在当前源码中由 trace_span 的收尾过程调用，名称没有下划线也不表示业务应手工调用。

这些方法没有各建函数卡；本轮先保留本类对外用途和 set 的必要行为。异常、子 Trace、结束后补属性等细节按实际问题继续展开。

</details>

## 4. 我的直接表述与尚不清楚

2026-10-27，用户原话：

> 我总觉得这里的数据有太多的耦合的部分的感觉？
> 我们还是回到scope吧
> 我们看一下这里的tracespancontext是在做什么吧

用户要求从职责重新定位本类，没有确认已理解其字段或方法。已有对象之间确实共享部分引用；是否需要改造这种设计不在本轮结论中。

本轮先留两个观察点：as span 是否指向刚创建的 span_context；span.set 的属性写到哪里。其余方法与结束路径仅定位，不因此记为已掌握。

随后用户要求继续查看类本体：

> 好的那么这里是否需要看一下这里的这个tracespancontext到底在做什么了呢？

据此展开 set → _sync_end_events 的最小路径；“好的”与继续阅读不记为已经掌握。

随后用户追问设计动机：

> 好的 我们来简单看一下这里的内容吧
> 这里其实我就不是特别清楚了
> 为什么需要这样子的一个tracespancontext.set的工具呢？
> 我不是特别能够理解这一点

当前卡点是“为什么需要向追踪系统补交业务结果”，不是要求继续下钻同步代码。这一用途解释尚待用户反馈。

**随后用户明确纠正：上述 set 用途不是当前要问的内容；当前要解释的是 TraceSpanContext(...) 的四个构造实参。** 原问题与误解保留为历史，活动阅读入口已改回本卡的构造部分。

> 不要写这个
> 我需要知道的是这里的这个
>
> 为什么这么些这个意思
> 重点是需要知道这里在做什么这件事

用户随后进一步要求看同一条 Trace 怎样逐步构建，追问 build_end_attrs 是否解析错误；已在[trace_span 的异常对照](../../../../functions/slime/observability/trace_utils.py/trace_span.md#exception-boundary)将属性快照与异常处理分开。此前的构造定位和 set 回查继续保留，不把这些说明当成已经理解。

在使用视角的 scope 改写后，用户反馈：

> 我大概清楚这样子地来去之后这里的内容了
> 更多的就是按照这里的来设置字段对吗？
> 还是说这里的字段是有限制的呢？

用户表达了对使用过程的大致理解；本轮区分“set 补充自定义属性”和“框架自动填写事件字段”，没有据此标记整个 Trace 实现已掌握。

## 5. 来源与验证

<details>
<summary>固定源码、记录边界与原始讨论</summary>

- [类与方法](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L68-L111)。
- [构造与 yield](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L390-L398)；[正常结束调用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L412-L425)。
- [业务调用处](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L286-L295)。
- 输入中的 h、S1、10.0 与退出码 0 是教学示例。以上为当前源码的静态核对，没有执行真实 Agent。
- [本轮定位与问题](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/04-flow.md#step014-span-context-purpose)。
- [set 与同步分支的继续阅读](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/04-flow.md#step014-span-context-set)；隔离执行原类方法只验证暂存属性、返回自身和同步已有结束字典，不代表真实 Agent 或完整 trace_span 已运行。
- [此前偏离目标的 set 说明与后续纠正](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/04-flow.md#step014-why-span-set)；[当前构造语句的解释](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/04-flow.md#step014-context-constructor)。

</details>
