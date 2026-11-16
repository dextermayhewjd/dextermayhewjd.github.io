# DressageHarborPlugin._on_start

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../../step-014-model-routing-and-api-contract/02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_start.md) 完整继承；不改变原认识时间或掌握状态。

- 源码：[plugin.py:639–692](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L639)，Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次单独展开：Step 014，2026-11-13。
- 最近认识更新：2026-11-13，用户已串起 Harbor 的 START 触发、Dressage 的 _on_start 回调与 lease.register；登记对象进一步校准为已有网关中的本次 Trial 路由。

[on_job_start 登记回调](DressageHarborPlugin.on_job_start.md#job-start-hooks) → Job 开始执行 → [Trial.run 发出 START](../../../../harbor/trial/trial.py/Trial.run.md#prepare-call) ⇒ **当前 _on_start** → 返回事件分发，Trial 继续 _prepare。

**先知道它为什么存在**：Harbor 在 Trial 开始时通知 Dressage；Dressage 的 `_on_start` 为这次尝试登记模型请求路由，让已有 Gateway 知道“带这个 token 的请求属于哪个 Trial、交给哪个 Proxy”。Gateway 本身此前已取得，CLI 的地址此前已配置。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Harbor 的 Trial 发出 START，调用此前挂上的 Dressage 回调；此时尚未进入 _prepare。
2. **具体内容**：Dressage 取得这次 Trial 的身份，将它与已有 token、对应 Proxy 的路由关联起来，保存后续操作这条路由的对象。
3. **建议构建的心智模型**：

   > Harbor 告知“这次尝试开始了”；Dressage 为它准备好模型请求通道。

4. **调用背景**（两处源码节选，不属于同一函数）：

   ```python
   # Dressage 调用 Harbor 的钩子接口，把自己的处理函数交给 Harbor。
   job.on_trial_started(self._safe(self._on_start, "START"))

   # Harbor.Trial.run：触发时调用已登记函数，再进入准备。
   self._init_result()
   await self._emit(TrialEvent.START)  # 分发给已登记的回调，最终来到当前函数。
   await self._prepare()              # START 的回调正常完成后才继续。
   ```

这里出现的是两种不同的“登记”：

| 代码 | 谁提供接口 | 登记什么 |
| --- | --- | --- |
| `job.on_trial_started(...)` | Harbor Job | “Trial 开始时调用这个函数”——登记回调 |
| `self._lease.register(spec)` | Dressage GatewayLease | “这个 token 对应这次 Trial 和它的 Proxy”——登记请求路由 |

第二种登记返回 `AttemptHandle` 对象，保存为 `record.handle`。它是 Dressage 后续操作这条路由的入口，例如通过 `handle.open_turn(...)` 开启一轮交互。

**请求归属与响应返回分开理解**：登记让 Gateway 知道“这个 token 对应哪次 Trial、交给哪个 Proxy 处理”，并关联本次会话记录。响应沿发起请求的那条 HTTP 连接返回 CLI；这里不需要再登记一个 Sandbox 回传地址。

## 本场景的输入与输出

输入 `event` 提供本次 `trial_name/trial_id`；`self` 是 Dressage 插件，已有 on_job_start 保存的 `_slots`、Gateway 租约和 token 注册表。这里的 START 指完整 Trial 的开始，不是内部某个工作步骤，也不是稍后的 AGENT_START。

<a id="trial-start-mainline"></a>

首次成功登记路径节选：省略重复检查、记录的附加字段和失败分支；完整源码折叠保留。先分清上面的钩子回调与路由登记，再沿数据变化读下面的主干。

```python
trial_name, trial_id = _event_key(event)    # 从 START 事件读身份，不在这里生成新 ID。
slot = self._slots.get(trial_name)           # 按名称接上 on_job_start 先前保存的资料。
registry = self._runtime.secret_slots
token = registry.current(slot.slot_id)      # 取出当前路由 token。

# 原码在这里创建 AttemptRecord，变量为 record，
# 并存入 self._attempts[(trial_name, trial_id)]；session_id 使用 trial_id。

spec = self._make_route_spec(
    trial_name=trial_name,
    trial_id=trial_id,                      # 这一次实际尝试的身份。
    instance_id=slot.instance_id,
    token=token,                            # 与 CLI 将携带的路由身份对应。
    expected_version=slot.expected_weight_version,
)
record.handle = await self._lease.register(spec)  # 向 Dressage 网关登记路由，保存操作对象。
record.phase = AttemptPhase.READY
```

**输出是状态变化，正常返回 None**：插件保存本次 AttemptRecord，以及注册返回的 handle。READY 表示这里的路由准备已完成；稍后的 [AGENT_START 回调](DressageHarborPlugin._on_agent_start.md#agent-start-mainline) 才打开 turn、激活执行。返回 [_emit(START)](../../../../harbor/trial/trial.py/Trial.run.md#prepare-call) 后，Trial 继续 `_prepare()`。

当前先看清 `trial_id + 已有 token → RouteSpec → register → record.handle`；从 [GatewayLease.register](../gateway.py/GatewayLease.register.md#lease-register-mainline) 继续看委派，实际业务可直接接 [GatewayRuntime._register](../gateway.py/GatewayRuntime._register.md#runtime-register-mainline)，看如何建立 token 到 Proxy 的表；调度机制按已有职责理解。

<details>
<summary>完整函数：尝试记录字段、重复事件与 token 轮换检查</summary>

```python
async def _on_start(self, event: Any) -> None:
    trial_name, trial_id = _event_key(event)
    slot = self._slots.get(trial_name)
    if slot is None:
        raise KeyError(f"no Dressage slot for Harbor trial {trial_name!r}")
    if (trial_name, trial_id) in self._attempts:
        return
    if self._runtime is None or self._lease is None:
        raise RuntimeError("Gateway lease is not active")

    registry = self._runtime.secret_slots
    token = registry.current(slot.slot_id)
    fingerprint = registry.fingerprint(slot.slot_id)
    record = AttemptRecord(
        trial_name=trial_name,
        trial_id=trial_id,
        session_id=trial_id,
        instance_id=slot.instance_id,
        attempt_ordinal=len(slot.attempt_ids),
        token_fingerprint=fingerprint,
        resolved_task_sha256=slot.resolved_task_sha256,
        task_network_class=slot.task_network_class,
        expected_weight_version=slot.expected_weight_version,
    )
    if slot.bound_attempt_ordinal is not None:
        record.attempt_ordinal = slot.bound_attempt_ordinal
    self._attempts[(trial_name, trial_id)] = record
    slot.attempt_ids.append(trial_id)

    if (
        slot.previous_token_fingerprint is not None
        and fingerprint == slot.previous_token_fingerprint
    ):
        record.poisoned = True
        record.phase = AttemptPhase.BROKEN
        record.failures.append(
            AttemptFailure(
                code="ROUTE_TOKEN_NOT_ROTATED",
                stage=FailureStage.START,
                message="Harbor retry reused the previous attempt route token",
                fatal=True,
            )
        )
        return

    spec = self._make_route_spec(
        trial_name=trial_name,
        trial_id=trial_id,
        instance_id=slot.instance_id,
        token=token,
        expected_version=slot.expected_weight_version,
    )
    record.handle = await self._lease.register(spec)
    record.phase = AttemptPhase.READY
```

已有同一 `(trial_name, trial_id)` 记录时会返回；重试复用旧 token 的检查可能将记录置为 BROKEN。本页主干只选择首次成功登记，不将失败分支当成不存在。

</details>

## 我的直接表述（原话）

> 好的 刚才是某一个具体的job开始了对吗?
> 心在是某一个具体的trial中的某一个步?
> 清闲生成一下这个short term memory吧

助手校准：on_job_start 是整份 Job 运行前的准备；当前 _on_start 是一次 Trial 开始时的事件回调，发生在其 _prepare 之前。用户对函数内部机制尚未复述。

用户在澄清阅读目的后确认：

> 好的 那么开始看一下这个函数的short term memory吧

当前问题是已有 Gateway 怎样登记这次尝试；本轮先说明身份与 token 的来源，不据此认定已理解整个注册机制。

用户要求先明确整体职责：

> 简单来说这里在做的内容是什么呢?
> 这里的又是handle 又是这里的register的
> 我觉得在这个具体看这里的函数的输入和输出之前
> 是否需要考虑让我理解这里到底在做什么呢?
> 这里到底是harbor留了钩子还是dressage留了钩子
> 我很不理解

本轮先补清 Harbor 提供事件接口、Dressage 提供回调，以及回调内部向 Dressage Gateway 登记路由的分工；理解状态仍待反馈。

本轮进一步复述：

> 我是否可以理解为这里的这个harbor是钩子
> 然后这里的这个trial部分运行这个emit的trialevent start
> 这里的这个钩子?
> 是我的理解?
>
> 然后就是这里的dressage harbor的plugin?
>
> 也就是这个on start的部分?
> 我们目前看的这个函数?
> 那么这里在做的内容大概就是
>
> 这里的这个lease register?
> 这里我们可以通过向dressage 登记路由网关
> 也就是我们下一个需要看的函数对吗?

助手校准：Harbor 提供事件钩子机制，START 是事件，_emit 触发已登记回调；当前 _on_start 属于 Dressage。lease.register 向已有 Gateway 登记本次 Trial 的路由，不是在此登记或重新创建网关本身。

本轮回顾时的追问：

> 也就是说这里的内容其实更多的是
> 记住了这个sandbox的一系列信息应该发还给哪里 我可以这么理解吗
> 因为对于sandbox 发送给什么base url很简单
> 但是这里的这个网关需要知道这条消息发还给谁?

助手校准：本轮追踪的是请求属于哪个 Trial、选哪个 Proxy 处理；响应返回原 HTTP 请求连接，不能将路由登记概括成 Sandbox 回传地址登记。

## 尚不清楚

- [GatewayLease.register](../gateway.py/GatewayLease.register.md) 已进入，实际路由创建仍需下一层 GatewayRuntime._register。
- 后面的 AGENT_START 怎样激活 turn、Gateway 怎样分派请求，尚未逐段阅读。

<details>
<summary>来源与验证</summary>

- 本地 Dressage 固定提交核对 _on_start:639–692、_event_key:1239–1240、on_job_start:407 的回调登记。
- Harbor v0.25.0 Trial.run:601–609 的顺序是初始化结果、await START、再进入 _prepare；这是事件与执行时序的静态对照。
- Harbor Job.on_trial_started:235 将回调交给 add_hook(TrialEvent.START, callback)；Trial._emit:590 依次 await 已登记回调。Dressage GatewayLease.register:389 返回 AttemptHandle，其 open_turn:292 操作绑定的 Proxy 并更新路由状态。本轮只核对职责，不扩展为这些辅助函数的完整阅读。
- AttemptRecord 保存在插件，不是把一个新的 TrialResult 返回给 Harbor；句柄也保存在 record.handle，不作为当前函数返回值。
- 未执行路由注册、创建 Proxy 或启动环境；固定版本间的运行兼容性仍未验证。
- [本轮记录](../../../../../../../step-014-model-routing-and-api-contract/04-flow.md#trial-start-callback-entry)。

</details>
