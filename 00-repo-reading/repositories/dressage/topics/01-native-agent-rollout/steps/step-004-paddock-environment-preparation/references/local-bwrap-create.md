# LocalBwrapSandboxProvider.create

> 2026-11-05 记录归位：本文从 Step 001 的 02 移至 references，完整内容与来源保留。当前主读 [SandboxProvider 接口卡](../02-short-term-memory/classes/dressage/sandbox/provider.py/SandboxProvider.md)；本文用于按需对照，不继续要求深入具体池实现。

> 阅读定位（2026-11-05）：本卡保留为 provider 共同约定的具体例子，只核对 spec → 请求 → payload → lease/endpoints；不再作为池管理器深读的入口。当前主线见 [init 中的 provider 约定](../02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#provider-create-boundary)。

> 阅读位置：[Step 004（原 001） scope](../01-scope.md#reading-navigation) → [Paddock.init 第 2 段](../02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#acquire-environment) → **LocalBwrapSandboxProvider.create** → 返回 lease，继续 init 的服务入口读取。

- 源码定位：[dressage/sandbox/local/bwrap/provider.py:49–104](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/local/bwrap/provider.py#L49)，由助手静态核对。
- 首次接触：Step 001 中为解释 lease 和 endpoint 的来源而回查，2026-11-05 建立本卡。
- 最近认识更新：用户要求先看 provider.create 并生成短期记忆；尚无对这个具体实现的内部复述。

## LLM 整理：使用场合、具体内容与心智模型

以下是助手按源码整理的解释。

1. **使用场合**：Paddock.init 已构造 SandboxSpec，当前 provider 选择 local_bwrap，需要取得本次可用的沙箱环境记录。这里选择源码默认后端作为阅读样例，不表示已经核验某次实际运行配置。

2. **具体内容**：检查请求模式与已连接池匹配，向管理器调用 acquire，接收 payload，将它整理成 SandboxLease，补上服务访问入口并保存、返回。

3. **建议构建的心智模型**：

   > 这是一次“请求分配环境，并整理领取结果”的调用。管理器负责分配；create 将返回信息变成 Paddock 接口所需的统一 lease。
   >
   > 函数名叫 create，但本实现并不在这里直接启动容器或 bubblewrap 进程；不能据此假设每次都新建一个运行环境。

4. **调用代码**：调用方是 Paddock.init，代码中的 self._provider 在本阅读场景中是 LocalBwrapSandboxProvider。进入本方法后，self 则是 provider 本身。

   ```python
   create_task = asyncio.create_task(
       self._provider.create(spec),
       name=f"sandbox-create:{traj_id}",
   )
   ```

   调用方随后在 try 中执行 `lease = await asyncio.shield(create_task)`，接住本函数的返回值。shield 与取消后接手的解释留在 [init 卡](../02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#shield-create-cancellation)。

## 本场景的输入与输出

选定正常路径：黑盒 Paddock，spec.metadata 中 paddock_mode 为 blackbox，spec.services 中有一项名为 blackbox 的服务；连接的管理器池模式匹配，acquire 正常返回有效 sandbox_url。管理器及池已由运行环境准备，本次不启动它们。

**输入：**

| 输入 | 来源与本次用法 |
| --- | --- |
| spec | [SandboxSpec](../02-short-term-memory/classes/dressage/sandbox/types.py/SandboxSpec.md)，由 init 构造；本方法读取 metadata、trajectory_id、env_type、env_args 和 services |
| self._manager | 已连接的管理器；生产路径通常是 Ray actor 句柄，本方法通过 _remote_call 调用它 |
| self.name | 当前 provider 的名称 local_bwrap |
| self._leases | provider 自己保存环境记录的字典；与 Paddock 中的同名字典是不同对象 |

**正常输出与状态：**

| 结果 | 从哪里来 | 交给哪里 |
| --- | --- | --- |
| lease | 由 spec 中的归属信息、管理器返回的 payload 和当前模式组装 | 返回给 Paddock.init 的等待处 |
| lease.sandbox_id | payload.get("lease_id") | 将管理器的领取标识放进统一字段；不直接等同于容器 ID |
| lease.endpoints["blackbox"] | 从 payload 的 sandbox_url 构造 SandboxEndpoint | 供 init 后续访问 BlackboxServer |
| self._leases[spec.trajectory_id] | 保存本次构造的同一个 lease 对象 | provider 后续管理和释放时使用 |

没有实际运行管理器，未取得真实 ID、地址或节点信息；下列是源码关系，不是运行日志。

```text
╔══════════════════════════════════════════════╗
║ Provider: create(spec)                       ║
║ spec -> acquire request                      ║
║ payload -> SandboxLease -> return            ║
╚══════════════════════════════════════════════╝
        | _remote_call          ^ payload
        v                       |
        Ray manager / slot pool
        allocation details: outside this card
```

上图表示所选生产路径。_remote_call 也兼容可直接调用的对象；测试路径不一定跨进程。管理器内部如何选槽位、等待资源不在本轮展开。

### 本函数的三个处理阶段

以下三段保留 50–104 行的全部函数体语句，统一减少缩进；说明紧接代码。这里只省略函数签名，各段应放回同一个 async 方法理解。

<a id="request-allocation"></a>

#### 1. 确认池模式，将环境需求交给管理器（50–68）

```python
paddock_mode = _paddock_mode_from_spec(spec)
expected_pool_mode = (
    POOL_BLACKBOX if paddock_mode == "blackbox" else POOL_COMMAND_ONLY
)
pool_mode = await _manager_pool_mode(self._manager)
if pool_mode != expected_pool_mode:
    raise RuntimeError(
        "local_bwrap pool mode does not match paddock mode: "
        f"paddock_mode={paddock_mode!r} requires pool_mode={expected_pool_mode!r}, "
        f"connected pool_mode={pool_mode!r}; stop the current pool and start "
        "the correct DRESSAGE_LOCAL_BWRAP_POOL_MODE"
    )
payload = await _remote_call(
    self._manager,
    "acquire",
    trajectory_id=spec.trajectory_id,
    env_type=spec.env_type,
    env_args=spec.env_args,
)
```

1. _paddock_mode_from_spec 读取 spec.metadata 中的 paddock_mode。当前为 blackbox，因此要求连接的池提供黑盒模式。
2. 读取管理器的实际池模式；不匹配时抛错。本函数验证已有池，不在这里另建第二个池。
3. 调用管理器的 acquire，并且只向该方法传 trajectory_id、env_type、env_args 这三项业务参数。
4. await 等待领取结果，接到 payload 字典；下一段从这里取出环境资料。本层没有直接消费 spec.timeout_sec 和 spec.env，不能仅凭统一字段存在就假设所有后端都同样使用它们。

| 必要时回查 | 读完回到哪里 |
| --- | --- |
| [_remote_call](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/local/bwrap/provider.py#L272)：按方法名分派，兼容 Ray 或直接调用 | 接住 acquire 的 payload，继续下面的 lease 构造 |
| [管理器 acquire 的核心实现位置](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/local/bwrap/manager.py#L243)：这里只定位，未展开 | 返回的是领取结果；本卡暂以 payload 为交接边界 |

<a id="build-lease"></a>

#### 2. payload → SandboxLease：整理统一环境记录（69–88）

```python
lease = SandboxLease(
    trajectory_id=spec.trajectory_id,
    provider=self.name,
    sandbox_id=payload.get("lease_id"),
    capabilities=(
        {"command", "file", "public_url"}
        if paddock_mode == "blackbox"
        else {"command", "file"}
    ),
    metadata={
        "pool_mode": pool_mode,
        "paddock_mode": paddock_mode,
        "node_id": payload.get("node_id"),
        "node_ip": payload.get("node_ip"),
        "slot_id": payload.get("slot_id"),
        "port": payload.get("port"),
        "generation": payload.get("generation"),
    },
    raw=payload,
)
```

1. trajectory_id 继续沿用 spec 的归属信息，provider 填本实现的名称。
2. 管理器的 lease_id 进入 lease.sandbox_id。node_id、node_ip、slot_id、port、generation 则进入 lease.metadata；这些值来自管理器返回，不能在此凭空推断实际节点或地址。
3. 黑盒模式声明 command、file、public_url 三项能力；其他模式采用代码中的另一组能力。声明能力不表示这里已经执行命令或读写文件。
4. raw=payload 保留同一份管理器返回数据的引用。此时 lease 的 endpoints 使用默认空字典，下一段再填写。

字段可回查 [SandboxLease 类卡](../02-short-term-memory/classes/dressage/sandbox/types.py/SandboxLease.md)；读完回到下面的服务入口处理。

<a id="fill-endpoint-and-return"></a>

#### 3. 填入服务入口，保存并返回 lease（89–104）

```python
if paddock_mode == "blackbox":
    sandbox_url = payload.get("sandbox_url")
    if not sandbox_url:
        raise RuntimeError("blackbox local_bwrap lease did not return sandbox_url")
    sandbox_endpoint = SandboxEndpoint(url=str(sandbox_url).rstrip("/"), headers={})
    lease.endpoints["blackbox"] = sandbox_endpoint
    for service in spec.services:
        if service.name == "blackbox":
            lease.endpoints[service.name] = sandbox_endpoint
        elif payload.get("node_ip") and service.port:
            lease.endpoints[service.name] = SandboxEndpoint(
                url=f"http://{payload['node_ip']}:{service.port}",
                headers={},
            )
self._leases[spec.trajectory_id] = lease
return lease
```

1. 当前黑盒路径要求 payload 提供 sandbox_url；没有地址就抛错，不能正常返回一个缺少黑盒地址的结果。
2. 用该 URL 构造 sandbox_endpoint，填入 lease.endpoints["blackbox"]。这是本次沙箱的服务访问入口，可能由转发层提供，不是创建环境的管理接口。
3. 遍历 spec.services：名为 blackbox 的服务复用同一个入口；其他服务只有在 payload 提供 node_ip 且配置了端口时才拼装相应入口。本场景只有 blackbox 一项。
4. 将 lease 保存到 provider 的 self._leases，再返回同一个对象。Paddock.init 接住之后，还会进行自己的健康检查、构造 state，并保存自己的记录。

**返回位置**：[Paddock.init 第 2 段](../02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#acquire-environment)。调用方从 await shield 接到 lease，接着读 `lease.endpoints.get("blackbox")`；随后才构造 SandboxState。本函数不执行 Agent 任务，也不返回训练 Sample。

## 我的直接表述（原话）

用户先问：

> 是否应该先看一下这里的provider 的create部分呢?

在推荐使用源码默认 local_bwrap 作为阅读样例后，用户要求：

> 那么是否应该生成一下这里第二这个provider的部分呢
> 生成一个short term memory
> provider.create

这是对阅读对象及记录的确认。尚无对本实现的数据交接或管理器行为的独立复述；详见[本轮过程](../04-flow.md#local-bwrap-create-memory)。

## 尚不清楚

1. 管理器怎样选择节点/槽位、等待资源、初始化或复用环境，尚未展开。
2. payload 中的 lease_id、sandbox_url 等怎样在管理器和下层实际生成，当前只看到它们进入 provider 的位置。
3. 池模式不匹配、acquire 失败或地址缺失等完整故障与资源收尾路径，尚未验证。
4. 用户对 spec、payload、lease 这三层数据的理解待后续反馈。

<details>
<summary>来源、后端选择与验证范围</summary>

- 固定源码提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；路径 /home/fredkeira/projects/Dressage。
- 当前实现 create:49–104；模式读取:246–252；_remote_call:272–280。
- 默认后端依据：[config.py:18](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/config/config.py#L18)；选择入口：[sandbox/factory.py:15](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/factory.py#L15)。选择默认实现用于阅读，不证明实际运行一定使用该配置。
- 管理器返回字段形状参考 LeaseRecord.to_dict，manager.py:138–153。当前只核对接口资料，不展开该模块内部。
- [Step 004（原 001） 本轮讨论](../04-flow.md#local-bwrap-create-memory)。这里只建立当前函数卡，不新建管理器、E2B 或辅助函数卡，不修改前序长期快照。
- 静态核对；未启动 Ray、管理器、bubblewrap 或 Agent，未取得真实 payload。

</details>
