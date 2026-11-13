# BlackboxAgentPaddock.init

> 历史归档：原先放在 Step 000 的初稿。2026-11-05 已修正归属；当前学习记录见 [Step 004（原 001） 的 init](../../../step-004-paddock-environment-preparation/02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md)。本页保留当时原话与说明，不计入现行短期或长期函数索引。

> 阅读位置：[Step 000 scope](../../01-scope.md#reading-navigation) → [generate 的环境取得段](../../02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#environment-init) → **init：当前** → 带着 state 返回 [generate 的注册段](../../02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#agent-registration)。

- 源码定位：[dressage/paddock/blackbox/paddock.py:64–151](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L64)，由助手静态核对。
- 首次接触：Step 000 的 generate 骨架；2026-11-05 用户确认进入本函数，建立独立短期记录。
- 最近认识更新：用户此前询问 Paddock 与 sandbox 的关系，本轮确认开始阅读；尚未表达对 init 内部过程的理解。

## LLM 整理：使用场合、具体内容与心智模型

以下由助手根据调用处与固定版本源码整理。

1. **使用场合**：generate 没有领取到预热环境，已整理环境参数并更新 session_id，调用当前黑盒 Paddock 的 init 取得本次环境访问状态。

2. **具体内容**：整理 SandboxSpec，交给 provider 创建或取得环境；取得 blackbox 服务地址，按配置检查健康；构造 SandboxState，保存本次环境记录并返回。

3. **建议构建的心智模型**：

   > Paddock 是操作环境的协调对象。init 将“这次需要什么环境”交给 provider，再将“环境在哪里、怎样找到它”的资料返回给 generate。
   >
   > 返回的 state 是访问资料；实际沙箱由 provider 管理。之后 generate 还要用 state 注册并调用 Agent。

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

本页沿用 generate 的预热未命中、正常初始化场景。具体 provider 已由配置选择；这里只看其接口，不展开 E2B 或 local_bwrap。没有实际启动环境，以下字段关系来自源码，未取得真实地址或 sandbox_id。

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

<a id="acquire-environment"></a>

#### 2. spec → lease 与 endpoint：取得环境及服务入口（86–116）

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
3. normalized 整理 URL 与请求头；开启健康检查时，用 BlackboxServerClient 请求该 endpoint 的 /health。这里的 self._client 访问沙箱中的 BlackboxServer，与 generate 中访问 Dressage Proxy 的 proxy_client 分工不同。

**本段结束**：已有 lease 和 endpoint；启用健康检查时，本次健康请求也已成功。具体环境怎样创建、服务怎样启动由选定 provider 实现，本页暂不展开。

| 必要时回查 | 带着什么返回 |
| --- | --- |
| [SandboxProvider.create 接口](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/provider.py#L20) | 理解返回的 SandboxLease，继续读取 blackbox endpoint；这只是协议定义，具体 provider 实现尚未阅读 |
| [BlackboxServerClient.health](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L49) | 健康请求正常返回后，继续下段构造 state |

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

**读完返回**：[generate 的环境取得段](../../02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#environment-init) → [注册段](../../02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#agent-registration)。到这里本轮的正常路径闭合。

<details>
<summary>本轮暂不展开的失败与取消边界</summary>

1. 等待 provider.create 时使用 shield，不表示调用方不会被取消；它避免取消直接传入创建 Task。若调用方取消，代码安排独立任务等待创建结束并处理环境清理，然后继续抛出取消。
2. 已取得 lease，但获取地址、检查健康或构造状态失败时，代码安排释放 lease，并清除本次条目后抛出异常。
3. 因此“本次没有正常返回 state”不能直接推出“环境一定没有被创建”。这些保护保留在源码中，当前先读正常的数据交接。

</details>

## 我的直接表述（原话）

此前在 generate 复述中，用户问：

> 然后才是这里的看一下是否能够获得这里的prewarm的sandbox
> 如果不恩能够够就获取一个这样子的sandbox也就是这里的paddock?

本轮确认进入 Paddock：

> 好的那么我们来看一下这里的paddock的内容吧

前一条是对象关系的疑问，后一条是阅读确认。尚无对本函数内部过程的复述；上面的解释属于助手核对结果。

## 尚不清楚

1. Paddock、provider、实际沙箱、lease 与 state 的分工已有本页说明，用户理解反馈待记录。
2. 当前配置具体采用哪个 provider，以及 provider 如何创建环境、启动 blackbox 服务，尚未展开。
3. 后续 register_agent 怎样使用 state 和 lease，下一处回到 generate 再接续。
4. 创建过程中的取消及独立清理机制只保留边界，未深入。

<details>
<summary>来源、验证与完整记录</summary>

- 固定源码 /home/fredkeira/projects/Dressage，提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，2026-11-05 核对工作区干净。
- 调用者 blackbox_dispatch.py:221–241；当前方法 paddock/blackbox/paddock.py:64–151；Paddock 构造字段只回查同文件 35–62 行，没有单独展开 __init__。
- [SandboxSpec / SandboxEndpoint / SandboxLease](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/types.py#L27)；[SandboxState](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/common/state.py#L10)。
- [Step 000 本轮阅读确认与解释](../../04-flow.md#paddock-init-reading)；此前完整复述见[保留的讨论](../generate-memory-revision-proposal.md#user-feedback)。
- 沿用短期函数样例的栏目、正常路径连续代码与返回导航，只创建本次确认的 init 卡。原 generate 卡的六段讲解继续保留。
- 静态核对；没有实际创建沙箱、发出健康请求或运行 Agent，未取得真实环境值。

</details>
