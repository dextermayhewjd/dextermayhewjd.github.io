# BlackboxAgentPaddock.init

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../../step-006-agent-execution/03-long-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../../step-005-agent-registration/03-long-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

> 阅读位置：[Step 004（原 001） scope](../../../../../../../step-004-paddock-environment-preparation/01-scope.md#reading-navigation) → [generate 的环境取得段](../../../rollout/generate/blackbox_dispatch.py/generate.md#environment-init) → **init：当前** → 带着 state 返回 [generate 的注册段](../../../rollout/generate/blackbox_dispatch.py/generate.md#agent-registration)。

- 源码定位：[dressage/paddock/blackbox/paddock.py:64–151](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L64)，由助手静态核对。
- 首次接触：2026-11-05，从 generate 骨架进入本函数；当时目录仍是 Step 000。按已确认的阅读边界，正式归属为 Step 001 的短期记忆；早期讨论事实保留。
- 最近认识更新：2026-11-05，用户已明确 self._leases 属于 Paddock 对象，并能通过 traj_id 寻找特定 lease/state；本轮补充实例复用、字典归属与单次 init 的范围。整体正常路径已收束，具体机制未知保留。

- 记录归属：Step 001 / 02；这是本步环境准备的主读函数，不是从 Step 000 继承的已读函数。先前放置方式见[历史初稿](../../../../../../../step-000-slime-bridge-and-interfaces/references/history/2026-11-05-init-before-ownership-correction.md)与[归属纠正](../../../../../../../step-004-paddock-environment-preparation/04-flow.md#memory-ownership-corrected)。

## LLM 整理：使用场合、具体内容与心智模型

以下由助手根据调用处与固定版本源码整理。

1. **使用场合**：generate 没有领取到预热环境，已整理环境参数并更新 session_id，调用当前黑盒 Paddock 的 init 取得本次环境访问状态。

2. **具体内容**：整理 SandboxSpec，交给 provider 创建或取得环境；取得 blackbox 服务地址，按配置检查健康；构造 SandboxState，保存本次环境记录并返回。

3. **建议构建的心智模型**：

   > init 把环境需求变成上层可以使用的访问资料：
   >
   > 1. **取得环境**：整理 spec 交给 provider，取得 lease 和服务入口 endpoint；lease 中缺少入口时再向 provider 查询。
   > 2. **整理入口**：normalized 整理 URL 和 headers，不发送网络请求。
   > 3. **检查服务**：启用健康检查时，访问 endpoint 的 /health，正常返回后继续。
   > 4. **交付资料**：Paddock 保存本次 lease/state，把 SandboxState 返回给 generate，供后续注册和调用 Agent。state 是访问资料，实际环境由 provider 管理。

4. **调用代码**（generate:221–229，保留实参）：

   ```python
   paddock = get_paddock_from_env(allow_whitebox_mode=False)
   state = await maybe_await(
       paddock.init(
           session_id,
           metadata.get("env_type"),
           env_args,
       )
   )
   initialized = True
   ```

## 本场景的输入与输出

本页沿用 generate 的预热未命中、正常初始化场景。本轮重点是 provider 的共同输入输出与生命周期约定；local_bwrap 只作数据交接示例，管理器内部与 E2B 路径不展开。没有实际启动环境，以下字段关系来自源码，未取得真实地址或 sandbox_id。

先区分两个名称：创建 Paddock 对象时，Python 调用的是 **__init__**，它准备 provider、BlackboxServerClient、配置及记录字典；这里读的 **init** 是随后准备某次环境时显式调用的方法。Paddock 对象可以被复用，它的记录字典可以保存不同 traj_id 的条目。

**输入怎样接到这里：**

| 调用方已有内容 | init 内的名称 | 本轮用途 |
| --- | --- | --- |
| session_id | traj_id | 给本次环境需求和记录提供归属标识；只是参数名变了，不在这里生成另一套 ID |
| metadata.get("env_type") | env_type | 环境类型提示，具体含义由 provider 处理 |
| env_args | env_args | 环境设置，包括可选的 blackbox_port、sandbox_timeout_sec 等；其他 provider 参数继续传入 spec |
| 没有额外关键字参数 | kwargs={} | 本次没有额外覆盖；函数仍支持将 kwargs 合并到环境参数 |
| 已取得的 paddock 对象 | self | 持有 provider、BlackboxServerClient、默认端口、健康检查开关与环境记录 |

**正常输出与副作用：**

| 内容 | 来自哪里 | 接下来怎样使用 |
| --- | --- | --- |
| state.trajectory_id | 传入的 traj_id，也就是本次 session_id | 关联本次环境及 Paddock 内部记录 |
| state.sandbox_url | blackbox 服务的 endpoint.url | 后续注册和调用 Agent 时定位服务 |
| state.sandbox_id | provider 返回的 lease.sandbox_id | 保存实际环境标识，类型允许为 None |
| state.raw_register_response | 本函数整理的 provider、环境及地址摘要 | 辅助保存环境来源；虽然字段名含 register，此时尚未执行 register_agent |
| self._leases[traj_id] | provider 返回的完整 lease | 保留环境管理及后续操作需要的资料 |
| self._states[traj_id] | 本次构造的 state | 保留 Paddock 的访问状态记录；同一个 state 对象也返回给 generate |

### 正常路径的三段代码

下面连续保留本函数正常路径的实际语句，统一减少外层缩进；省略两处异常处理，用 `...` 标出。不是独立可运行程序。先读各段的数据变化，provider 内部与取消机制本轮不下钻。

<a id="build-spec"></a>

#### 1. 环境参数 → spec：写清这次需要什么（71–85）

```python
env_args = {**(env_args or {}), **kwargs}
spec = SandboxSpec(
    trajectory_id=traj_id,
    env_type=env_type,
    env_args=env_args,
    services=(
        SandboxServiceSpec(
            name="blackbox",
            port=int(env_args.get("blackbox_port") or self._blackbox_port),
            health_path="/health",
        ),
    ),
    timeout_sec=env_args.get("sandbox_timeout_sec"),
    metadata={"paddock_mode": "blackbox"},
)
```

1. 第一行创建一份合并后的参数字典；kwargs 中的同名项会覆盖 env_args。本次调用没有额外 kwargs。
2. spec 把本次身份、环境类型和环境参数集中交给 provider。
3. services 声明本次需要访问名为 blackbox 的服务，并给出端口与健康检查路径；创建 SandboxServiceSpec 对象本身还没有启动服务。

**本段结束**：已有一份环境需求 spec，下一段才将它交给 provider。

<a id="spec-types"></a>

这两个数据类的字段、默认值和对象含义已单独放入本步类卡：

| 从这里进入 | 看清后返回哪里 |
| --- | --- |
| [SandboxSpec](../../../../../classes/dressage/sandbox/types.py/SandboxSpec.md)：整个环境请求，包含 services | 回到上面的构造语句，接住 spec，继续 provider.create |
| [SandboxServiceSpec](../../../../../classes/dressage/sandbox/types.py/SandboxServiceSpec.md)：一项服务的名称、端口和健康检查路径 | 回到 SandboxSpec 的 services 参数 |

1. 本函数负责把任务信息填写进这些数据对象；构造对象时尚未创建环境。
2. 字段的含义在类卡中回查；本页继续跟随 spec 怎样交给 provider，以及结果怎样返回。

<a id="acquire-environment"></a>

#### 2. spec → lease 与 endpoint：取得环境及服务入口（86–116）

**本段重点：[provider 的共同约定](#provider-create-boundary)。** 先看下面的 self._provider.create(spec) 怎样交回 lease，再继续 endpoint；[local_bwrap 实现](../../../../../../../step-004-paddock-environment-preparation/references/local-bwrap-create.md)只用于对照数据来源。

```python
create_task = asyncio.create_task(
    self._provider.create(spec),
    name=f"sandbox-create:{traj_id}",
)
...  # Enter try; the cancellation branch is omitted.
lease = await asyncio.shield(create_task)
...  # Enter the next try after acquiring the lease.
endpoint = lease.endpoints.get("blackbox")
if endpoint is None:
    endpoint = await self._provider.get_public_url(
        lease,
        port=spec.services[0].port,
        service_name="blackbox",
    )
    lease.endpoints["blackbox"] = endpoint
endpoint = endpoint.normalized()
if self._wait_health:
    await self._client.health(endpoint)
```

1. 创建 Task 执行 provider.create(spec)，随后 await 等待结果，接住 lease。lease 是 provider 交回的环境管理记录，含 provider 名称、环境标识、服务入口等。
2. 优先使用 lease 已有的 blackbox 地址；缺少时调用 get_public_url 获取，并写回 lease。这里保留这个必要分支，避免误以为返回 lease 就一定已有地址。

**port/service_name 是查询条件，endpoint 是返回的访问资料。** 例如询问“blackbox 服务的 31000 端口怎么访问”，provider 返回的是 SandboxEndpoint(url=..., headers=...)；服务名是 lease.endpoints 的键，不是 Endpoint 自身的字段。实际 URL 可以经过网关映射，不一定直接显示原来的端口。

<a id="normalize-and-health"></a>

**当前返回处：入口整理与健康检查（114–116 行）。** 上方代码的两条入口路径已经汇合，此时手里都有 endpoint。

1. endpoint.normalized() 返回一个格式整理后的新 Endpoint：去掉 URL 尾部的斜杠，并复制 headers。它不发送网络请求，也不改变所指向的服务。 例如教学地址 "http://sandbox.example:31000/" 整理为 "http://sandbox.example:31000"；没有查询网络或检查可达性。
2. _wait_health 为 True 时，await self._client.health(endpoint) 发起健康检查；False 时跳过。这是一次带 endpoint.headers 的 GET /health，请求成功后才继续构造 state；此方法内部没有轮询直到健康的循环。
3. 这里的 self._client 是 BlackboxServerClient，访问沙箱中的 BlackboxServer，与 generate 中访问 Dressage Proxy 的 proxy_client 分工不同。init 不接收并处理其响应内容，只等待该调用正常结束；网络或 HTTP 错误交给外层异常处理。

完整短代码、请求结果与失败去向见 [BlackboxServerClient.health 函数卡](../client.py/BlackboxServerClient.health.md)。读完返回本段，继续构造 state。

源码定位：[normalized](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/types.py#L50)、[BlackboxServerClient.health](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L49)。normalized 继续作为本段的简短说明；health 已按用户请求单独保存函数卡。


**本段结束**：已有 lease 和 endpoint；启用健康检查时，本次健康请求也已成功。池管理器的内部创建与分配暂不展开。

<a id="task-lease-endpoint"></a>

本段最重要的是不要混淆正在执行的工作与完成后拿到的结果：

| 名称 | 本地对象的含义 | 从哪里得到 |
| --- | --- | --- |
| create_task | 执行 provider.create(spec) 的 asyncio Task | asyncio.create_task 返回 |
| lease | 已创建或已领取环境的记录 SandboxLease | 创建任务正常完成后的返回值 |
| endpoint | 本次 blackbox 服务的 URL 与 headers | lease.endpoints 中取出，或由 provider.get_public_url 补齐 |

具体字段见 [SandboxLease 类卡](../../../../../classes/dressage/sandbox/types.py/SandboxLease.md)及其中的 [SandboxEndpoint 说明](../../../../../classes/dressage/sandbox/types.py/SandboxLease.md#endpoint)。URL 用来访问沙箱的 blackbox 服务，可能通过网关转发；它不是创建环境时调用的 provider 管理接口。

<a id="shield-create-cancellation"></a>

**为什么这里需要 shield：外层停止等待后，创建工作仍需要有人接手。**

1. 正常路径中，await asyncio.shield(create_task) 等待创建任务完成，并把它的返回值赋给 lease；shield 不改变返回类型。
2. 如果 init 的调用方被取消，当前 await 仍会抛出 CancelledError，但这次取消不会通过 shield 自动取消 create_task。
3. 远端可能已收到创建请求，取消本地等待不一定撤销远端创建。保留 create_task，才能在创建完成后取得 lease 并尝试释放对应环境。
4. 所以下面的 except 安排独立清理任务接手，再把取消继续抛给调用方。不是让已经取消的 rollout 继续执行 Agent。

对应 92–104 行的异常分支，接在上面的 shield 等待之后：

```python
except asyncio.CancelledError:
    # The create request may still complete; transfer cleanup ownership.
    schedule_lifecycle_task(
        terminate_when_provider_create_finishes(
            self._provider,
            create_task,
            trajectory_id=traj_id,
        ),
        name=f"sandbox-create-cleanup:{traj_id}",
    )
    raise
```

[terminate_when_provider_create_finishes](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/lifecycle.py#L115) 继续等待 create_task；成功取得 lease 后，调用 provider 的释放流程。shield 本身不会清理资源，也不保证任务绝对不会被其他原因取消；创建失败时也不会凭空产生 lease。


<a id="provider-create-boundary"></a>

**前一接口：[SandboxProvider.create](../../../sandbox/provider.py/SandboxProvider.create.md)。** 读清 spec → lease 后回到本段继续服务入口处理。

**入口缺失时继续：[SandboxProvider.get_public_url](../../../sandbox/provider.py/SandboxProvider.get_public_url.md)。** 此分支复用已有 lease，取得 endpoint 后回填到 lease，再继续健康检查。

**共同约定集中在 [SandboxProvider 接口卡](../../../../../classes/dressage/sandbox/provider.py/SandboxProvider.md)。** 当前从这里理解 create、get_public_url、terminate 的输入输出、就绪程度与失败清理责任；字段分别回查已有数据类卡。

1. 本函数将 spec 交给具体 provider.create，接到 lease。
2. 本函数从 lease 取得服务入口，必要时调用 get_public_url，再按配置检查健康。
3. 本函数随后构造 state 返回；使用结束时，由生命周期清理路径触发资源释放。

| 需要回查 | 读完返回哪里 |
| --- | --- |
| [SandboxProvider 接口卡](../../../../../classes/dressage/sandbox/provider.py/SandboxProvider.md) | 回到本段的 lease 与 endpoint 交接 |
| [local_bwrap 完整例子：references](../../../../../../../step-004-paddock-environment-preparation/references/local-bwrap-create.md) | 仅对照后端字段怎样映射到 lease，不继续深入池管理器 |
| [BlackboxServerClient.health](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L49) | 健康请求正常返回后，继续构造 state |

<a id="return-state"></a>

#### 3. lease 与 endpoint → state：保存资料，返回 generate（117–151）

```python
state = SandboxState(
    trajectory_id=traj_id,
    sandbox_url=endpoint.url,
    sandbox_id=lease.sandbox_id,
    raw_register_response={
        "provider": lease.provider,
        "sandbox_id": lease.sandbox_id,
        "metadata": lease.metadata,
        "endpoints": {
            name: endpoint.url
            for name, endpoint in lease.endpoints.items()
        },
    },
)
...  # Omit cleanup on a post-create failure.
self._leases[traj_id] = lease
self._states[traj_id] = state
return state
```

1. 把轨迹归属、服务 URL、环境标识和来源摘要整理成 state；构造这个数据对象不执行题目。
2. Paddock 用 traj_id 分别保存完整 lease 和 state，供后续方法使用。这里是登记本次条目，不清空其他任务的记录。
3. 返回同一个 state 给 generate。调用方接住它、设 initialized=True，接着将 state 传入 register_agent。

<a id="trajectory-indexes"></a>

**_leases 和 _states 属于哪个对象，为什么可以有多个 traj_id？**

它们是 BlackboxAgentPaddock 的实例属性。源码在该类的 __init__ 中为每个新对象创建两个字典：

```python
self._leases: dict[str, SandboxLease] = {}
self._states: dict[str, SandboxState] = {}
```

1. __init__ 初始化 Paddock 对象自己的这两个字典；业务方法 init(traj_id, ...) 准备某次轨迹的环境。每次调用 init 不会自动创建新的 Paddock 对象，也不会重新清空这两个字典。
2. 同一个实例可以接到多次 init，分别使用不同 traj_id；一次只写本次键，其他键保留。字典保存的是该对象当前持有的环境记录，不是一条轨迹里的多个交互轮次，也不是整个集群的全局历史表。
3. get_paddock_from_env 的常规路径会缓存 Paddock 对象，后续调用可以返回同一个实例。该缓存和字典位于相应 Python 进程中，不意味着所有进程或所有 Paddock 实例共享一份状态。
4. 后续 register_agent 用 state.trajectory_id 找回 lease；terminate 按 traj_id 从这两个字典移除对应记录，再调用 provider 释放环境。这里的字段也不同于某个 provider 实现中自己的同名 _leases。

源码依据：[字段创建，61–62 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L61)、[Paddock 获取与缓存](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/runtime.py#L165)、[后续按标识查找](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L165)、[按标识移除](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L278)。本轮只据此解释记录归属，不展开完整注册和释放流程。

本次返回类型的字段与去向见 [SandboxState 类卡](../../../../../classes/dressage/paddock/blackbox/common/state.py/SandboxState.md)。Paddock 同时保存 lease 和 state，供不同层次的操作使用。

**读完返回**：[generate 的环境取得段](../../../rollout/generate/blackbox_dispatch.py/generate.md#environment-init) → [注册段](../../../rollout/generate/blackbox_dispatch.py/generate.md#agent-registration)。到这里本轮的正常路径闭合。

<details>
<summary>失败与取消边界回顾：取消后接手已在上文展开</summary>

1. 等待 provider.create 时使用 shield，不表示调用方不会被取消；它避免取消直接传入创建 Task。若调用方取消，代码安排独立任务等待创建结束并处理环境清理，然后继续抛出取消。
2. 已取得 lease，但获取地址、检查健康或构造状态失败时，代码安排释放 lease，并清除本次条目后抛出异常。
3. 因此“本次没有正常返回 state”不能直接推出“环境一定没有被创建”。这些保护保留在源码中，当前先读正常的数据交接。

</details>

## 我的直接表述（原话）

2026-11-06，接续回顾时的表述与问题：

> 我梦当时应该已经清楚了 我们需要清楚sandbox spec
> 这个是通过创建spec之后
> 以及这里的sandbox service spec之后的到的
> 以及这里会需要通过provider 的create来具体创建出来这个sandbox
> 然后我在想的事情是
> 这里的endpoint到底是什么?
> 好的这里的end point应该是provider提供的对于外界接入的port和service name对吗?
>
> 然后这里的normalized又是什么这个我不是特别明白是做什么的
> 以及这里根据endpoint 需要检查?
> 检查是否健康?
> A然后这个sandboxstate又是什么?
> 我觉得这里需要弄清楚?

助手校准：ServiceSpec 是 spec.services 中的服务要求；端口和服务名是查询条件，返回的 Endpoint 保存 URL 与请求头。normalized 只整理数据；health 才请求 /health。SandboxState 则把会话、环境 ID、URL 等资料交回 generate。用户对后半段关系尚待反馈，原有完整问答保留如下。


此前在 generate 复述中，用户问：

> 然后才是这里的看一下是否能够获得这里的prewarm的sandbox
> 如果不恩能够够就获取一个这样子的sandbox也就是这里的paddock?

本轮确认进入 Paddock：

> 好的那么我们来看一下这里的paddock的内容吧

前一条是对象关系的疑问，后一条是阅读确认；以下是随后出现的初步理解和阅读深度问题。上面的源码解释仍属于助手核对结果。


2026-11-05，用户继续读 init：

> 好的那么我来看一下这里的init
> 那么先看一下这里的这个init吧
> 我的理解是这个首先根据环境信息给出这里的应该怎么造这里的sandboxspec
> 但是这里是否需要单独看一下sandboxspec和这里的sandboxservicespec是什么呢?
> 以及这里的provider create
> 这里需要看吗?

用户已概括构造 spec 的作用；是否理解每个字段、provider 的实际创建流程，不能由这句话推定。


2026-11-05，用户继续读创建任务（节选）：

> 这里创建了一个task
> 是通过provider来创建一个sandbox是我的理解
> 然后是什么呢?

> 为什么这里需要用这个asyncio 的shield?
> 以及为什么下面还有一个lease我没有理解

完整问题与本轮校准见[创建任务、环境记录与取消](../../../../../../../step-004-paddock-environment-preparation/04-flow.md#lease-state-and-shield)。用户已表达任务的用途，尚未确认理解取消语义和返回类型。

用户随后询问健康检查要读到多深：

> 那么是否需要看一下这里的client health大概是什么呢?
> 还是只需要记住
> 这里会发送一个访问?
> 然后然后再构造这个state

助手补充等待请求结果及错误会阻止正常状态构造的区别；这不是用户已经确认理解所有 HTTP 语义的表述。

本次收束时，用户概括：

> 好的
> 那么我觉得这里的这个step差不多结束清楚了?
> 也就是这里从provider中拿到对应的handle 切丁创建好了这里的环境?
> 是我的理解

总体作用已经有个人表述；lease/state 的精确分工和健康检查开关的影响仍以本页助手说明为依据，未代写成用户已经掌握。收束记录见 [本次过程](../../../../../../../step-004-paddock-environment-preparation/04-flow.md#step001-closure)。

用户随后确认按轨迹索引的关系，并要求标明归属：

> 我知道这里的这个self ._leases 属于这里的这个blackboxpaddock对象
> 那么是否考虑一下
> 所以才可以通过traj来寻找到一个特定的lease或者state
> 但是这里会误以为init blackpaddock的时候就只有这一个instace?
> 我在想的是这里的_leses
> 是否是属于class的内容
> 所以会需要考虑这里是否在3.2的部分简单的写清楚嗯?
> 在代码旁边或者哪个合适的位置

本轮说明区分“类中定义的实例属性”和“类共享变量”，以及 __init__ 与单次 init 的范围。过程见[记录归属澄清](../../../../../../../step-004-paddock-environment-preparation/04-flow.md#paddock-instance-indexes)。

用户补清实例索引关系后，确认本函数已看完：

> 那么目前看完了这里的paddock.init
> 我们是否可以结束这个step
> 然后进入下一步了呢?

这是本轮阅读完成的表述；实现细节与真实运行的未知仍保留。见[本次接续](../../../../../../../step-004-paddock-environment-preparation/04-flow.md#step001-reading-complete)。

## 尚不清楚

1. 用户已描述构造 spec 的用途；两个 Spec 的字段与嵌套关系已补充说明，具体理解反馈待记录。Paddock、实际沙箱、lease 与 state 的区别仍需随阅读核对。
2. 当前重点为 provider 的共同约定；local_bwrap 仅作交接示例。实际 Kubernetes 后端未实现，池管理器和其他后端内部未展开。
3. 后续 register_agent 怎样使用 state 和 lease，下一处回到 generate 再接续。
4. 本轮已展开 shield 与取消后接手清理的关系；用户理解反馈待记录，重复取消、进程退出等完整故障行为仍未展开。

<details>
<summary>来源、验证与完整记录</summary>

- 固定源码 /home/fredkeira/projects/Dressage，提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，2026-11-05 核对工作区干净。
- 调用者 blackbox_dispatch.py:221–241；当前方法 paddock/blackbox/paddock.py:64–151；Paddock 构造字段只回查同文件 35–62 行，没有单独展开 __init__。
- [SandboxSpec / SandboxEndpoint / SandboxLease](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/types.py#L27)；[SandboxState](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/common/state.py#L10)。
- [Step 000 本轮阅读确认与解释](../../../../../../../step-000-slime-bridge-and-interfaces/04-flow.md#paddock-init-reading)；此前完整复述见[保留的讨论](../../../../../../../step-000-slime-bridge-and-interfaces/references/generate-memory-revision-proposal.md#user-feedback)。
- 沿用短期函数样例的栏目、正常路径连续代码与返回导航，只创建本次确认的 init 卡。原 generate 卡的六段讲解继续保留。
- [Step 004（原 001） 本次 Spec 与 create 阅读深度讨论](../../../../../../../step-004-paddock-environment-preparation/04-flow.md#spec-and-provider-reading-depth)。
- 静态核对；没有实际创建沙箱、发出健康请求或运行 Agent，未取得真实环境值。
- 本轮局部验证：用 asyncio.Event 控制模拟 provider 的创建完成，取消外层等待后，创建 Task 继续；调用原仓库生命周期函数接手，取得模拟 lease 后调用一次模拟 terminate。脚本 /tmp/dressage_shield_handoff_probe.py；只验证 Python 取消传播与接手路径，不代表远端环境验证。

</details>
