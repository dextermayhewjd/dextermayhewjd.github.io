# PrewarmStore.claim：精简前的完整记录

2026-11-06 保存的历史快照；仅重定位链接，不继续维护为当前函数卡。[返回当前卡](../../02-short-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.claim.md)。原话、追问和扩展说明完整保留。

- 源码定位：[store.py:115](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/store.py#L115)。
- 首次单独展开：Step 002，2026-11-06。
- 最近认识更新：Step 002，2026-11-06；用户已串联按会话 ID 取记录、再交接 handle，询问记录是否为 Pod/容器；对象边界由助手补充。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：claim_prewarm 将当前 session_id 交给默认 store，尝试接手对应预热。
2. **具体内容**：取走记录，等待其初始化 Task，成功时构造 PrewarmHandle；无记录或普通初始化失败返回 None，取消则安排处理并重新抛出。
3. **建议构建的心智模型**：

   > 先从未领取记录中取走这一条，再等它完成，最后把可继续使用的对象交给 rollout。能查到记录不等于立即得到 handle。

4. **调用代码**：

   ```python
   return await _DEFAULT_STORE.claim(session_id)
   ```

## 本场景的输入与输出

输入：session_id="bbs-demo"，store 中可能存在对应的 _PrewarmRecord；它保存 Paddock、参数和此前启动的初始化 Task。PrewarmStore.start 内部用 paddock.init 创建该 Task，本轮只回查这一来源，不展开训练调度。

完整函数：

```python
async def claim(self, session_id: str | None) -> PrewarmHandle | None:
    """Atomically transfer one ready prewarm to active rollout ownership."""
    if session_id is None:
        return None
    record = self._take(session_id)
    if record is None:
        return None
    try:
        state = await record.task
    except asyncio.CancelledError:
        self._schedule_dispose(record)
        raise
    except Exception as exc:
        logger.warning(
            "sandbox prewarm failed for session_id=%s: %s; "
            "falling back to inline init",
            session_id,
            exception_summary(exc),
        )
        return None
    return PrewarmHandle(
        session_id=record.session_id,
        group_id=record.group_id,
        paddock=record.paddock,
        state=state,
        env_args=copy.deepcopy(record.env_args),
    )
```

1. **查找并取走记录**：_take 按 session_id 从 _records 中 pop，并从组索引移除。该同步段没有 await；在同一事件循环的任务间不会因等待而被另一领取操作插入。它不是跨进程或 Kubernetes 的分布式锁。
2. **等待初始化**：await record.task 得到 state。任务已完成则取得结果，否则先等待；claim 不在这里新建预热环境。
3. **构造交接记录**：复用 record 的会话/组编号和 Paddock，装入 state，对 env_args 深拷贝，返回 [PrewarmHandle](../../02-short-term-memory/classes/dressage/rollout/prewarm/store.py/PrewarmHandle.md)。
4. **交给调用者**：generate 解包 Paddock、state 和参数，设 initialized=True，跳过本次冷初始化并继续注册 Agent。

| 情况 | 本函数结果 |
| --- | --- |
| session_id 为 None 或没有记录 | 返回 None |
| 有记录，Task 正常完成 | 返回 PrewarmHandle |
| 初始化 Task 抛普通异常 | 记录日志并返回 None，调用者可进入未命中路径 |
| 等待被取消或 Task 已取消 | 调用 _schedule_dispose 安排清理并重新抛出取消；不是正常返回 None |

记录在等待前就已从未领取集合取走，因此成功后由 rollout 承担后续使用和清理。普通初始化失败的更底层资源处理不由本函数全部解释，不能仅凭返回 None 推断环境已经释放。

**两条正常后续路径**：有 handle，直接用它注册；None，generate 更新会话 ID、取得 Paddock 再初始化（Step 003/004）。这里的返回对象不是 Proxy 响应，也不是新生成的任务题目。

<a id="prewarm-origin"></a>

### generate 没有启动预热，记录是从哪里来的

**当前回查入口：[PrewarmStore.start（同文件第 78 行）](../../02-short-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.start.md)。** _initialize 定义在它的第 94 行，Task 在第 99 行创建、第 105 行存入记录。看完回到本函数第 123 行的 await record.task。

本场景是启用预热的异步 rollout 路径，不能假定每次调用 generate 前都有预热。当前预热开关要求 DRESSAGE_SANDBOX_PROVIDER=e2b，且未将 DRESSAGE_SANDBOX_PREWARM 设为 0。

1. **外层先取未来的任务。** 异步 worker 调用 PrewarmScheduler.do_prefetch(data_buffer)，调度器把未来的 group 放进 _prefetched_groups。
2. **调度器启动预热。** _prefetch_and_prewarm 对 group 中每个 sample 准备参数，调用 start_prewarm；后者转给默认 store.start。
3. **store 绑定身份并记录初始化任务。** start 调用 ensure_blackbox_session_id(sample)，把编号写入 sample.session_id；create_task 调度执行 paddock.init，同时以该编号作为 _records 的键保存记录。这时不等待初始化完成。
4. **外层之后派发同一组 sample。** pop_next_group 优先取此前存下的 group，经训练框架的生成调用进入本页所读的 blackbox_dispatch.generate。正常路径保留同一份 sample 的会话身份。
5. **generate 用同一个 ID 领取。** ensure_blackbox_session_id 默认复用已有 sample.session_id；确定性 ID 路径在相同基础 ID 和重试计数下也得到相同值。随后 claim_prewarm 用它从同一进程的默认 store 中查找记录。

```python
# 预热侧：PrewarmStore.start 中的身份绑定
session_id = ensure_blackbox_session_id(sample)
# 随后调度初始化，并保存 self._records[session_id] = _PrewarmRecord(...)

# 领取侧：blackbox_dispatch.generate，省略中间的参数准备
session_id = ensure_blackbox_session_id(sample)
handle = await claim_prewarm(session_id)
```

所以 session_id 能查到记录，是因为预热时已建立“同一 ID → 初始化记录”的映射，不是根据编号自动发现某个 Pod。预热具体工作仍由 paddock.init 及 provider 完成；初始化未完成时，claim 的 await 等待剩余工作。若没有开启这条预热路径或找不到记录，generate 得到 None，进入自己的按需初始化分支。

源码回查（仅补来路，不在本步展开整个调度器）：

- [AsyncRolloutWorker 的预取与派发](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/fully_async_rollout.py#L360)：先 do_prefetch，再 pop_next_group 和调度 _run_group；partial_async_rollout.py:302 也有对应调用。
- [PrewarmScheduler.do_prefetch](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/scheduler.py#L51)、[_prefetch_and_prewarm](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/scheduler.py#L89)：取得 sample 并调用 start_prewarm。
- [PrewarmStore.start](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/store.py#L78)：绑定 ID、create_task、登记记录。
- [预热开关](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/config.py#L12)：当前标准调度路径的启用条件。

### 为什么拿到 record 后还要 await record.task

**预热提前启动了初始化工作，但领取时这项工作不一定已完成。** record 保存的是正在执行或已完成的任务对象，不能直接代替初始化结果 state。

启动侧的关键源码（PrewarmStore.start，省略其他登记字段）：

```python
async def _initialize() -> Any:
    return await maybe_await(
        paddock.init(session_id, env_type, owned_env_args)
    )

task = asyncio.create_task(_initialize(), name=f"prewarm:{session_id}")
# 随后将 task 放进 _PrewarmRecord 并登记，启动侧不在这里等待初始化完成。
```

领取侧：

```python
state = await record.task
```

1. create_task 调度初始化协程，随后即可登记任务；登记完成不等于环境准备完成。
2. 领取时任务还未完成，await 暂停当前领取协程，事件循环仍可推进初始化和其他任务；任务已成功完成，则直接取得保存的结果，不会重新执行 init。
3. _initialize 返回的是 paddock.init 的结果，所以 await 得到 state。只有正常拿到它，claim 才能构造成功的 PrewarmHandle；任务失败或取消则进入已有异常分支。

因此 record.task 表示“初始化这项工作”，state 表示“这项工作完成后交出的环境资料”。预热只能让工作更早开始，不能保证每次领取时都已经完成。

### 谁确认远端环境已准备好

record.task 是本地 Python 的 asyncio.Task，跟踪 _initialize() 的执行；它不是远端 Pod，也不是题目数据中的 Task。await 不会自动查询容器状态，而是等待任务包裹的初始化流程正常返回。

1. _initialize 等待 paddock.init(...)。
2. 当前 BlackboxAgentPaddock.init 等待 provider.create(spec) 返回 lease，并取得 BlackboxServer 的访问 endpoint。具体远端创建/领取行为由 provider 实现。
3. 默认开启 _wait_health 时，init 等待 BlackboxServerClient.health(endpoint)：向 endpoint 的 /health 发 HTTP GET，并检查响应状态。这里是一次请求，不是 claim 中轮询 Kubernetes Pod Ready。
4. 上述步骤成功后，init 保存 lease/state 并返回 SandboxState；_initialize 随之返回相同结果，record.task 才成功完成，claim 的 await 才能取得 state。

因此成功 handle 的就绪依据是这套初始化流程的完成条件。可配置跳过 health；即使 health 成功，也不等于 Agent 已注册、题目已运行或之后永不故障。初始化抛异常时，不会产生正常成功的 state，claim 按原异常分支处理。

回查已有记录：[BlackboxAgentPaddock.init](../../../step-004-paddock-environment-preparation/02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md)。源码依据：paddock/blackbox/paddock.py:64–151；paddock/blackbox/client.py:49–58。此处只补就绪依据，不重读全部 provider 实现。

### _take 取出的究竟是什么

1. _take 按 session_id 取走一个 Python _PrewarmRecord 对象。session_id 是查找键，record 是预热工作的记录；不是取走会话本身，也不是从集群取走或删除一个 Pod。
2. record.task 是执行 paddock.init 的 asyncio.Task，不是题目 Task，也不是容器。记录存在只说明初始化任务已创建，不保证底层环境已准备完成。
3. claim 用 await record.task 等到初始化成功，取得 state，再与 record 中的 session_id、group_id、paddock、env_args 一起构造 PrewarmHandle。record 保存 task，handle 保存其成功返回的 state。
4. 无记录时 claim 返回 None；generate 接住后继续未命中分支，不表示整个 rollout 到此结束。实际环境由 provider 决定，当前内置 local_bwrap 与 e2b，不能直接把记录等同于 Kubernetes Pod。

## 我的直接表述（原话）

> 好的那么我们开始看一下这里的这个proxy client吧
> 看一下这个proxy是在做什么这件事情
> 然后重点看一下这里的这个handle吧

上述为最初阅读请求。后续理解与问题：

> 我可以简单理解为
> 按照会话id来拿到当前的预热记录
> 如果没有这个预热的record
> 那么就返回?
> 如果有这个记录
> 就通过record拿到task
> 然后返回这个prewarmhandle?
> 也就是这一个record对应的group id session id还有state还有env等一系列基础的信息?
>
> 我可以理解为
> 这里的_take 拿去的内容是这里的一个会话?
> session
> 对应的已经从沙箱中启动的一个pod? 或者一个容器?

助手校准：主流程方向正确，但需要等待初始化 Task 返回 state；_take 返回 Python 记录，不是 Pod/容器。此校准尚待用户确认。

本轮追问：

> 主要是为什么呢这个reocrod需要一个record task部分的await 我没有特别理解?

助手结合 start 中 create_task 和 claim 中 await 解释工作与结果的区别，尚待用户反馈。

本轮继续追问上游来路：

> 这里为什么能够做到直接通过session_id就能够直接
> 或者说
> 这里的预热是在哪里完成的
> 我很不理解这里的generate部分应该没有预热的部分吧

助手补上异步 worker、预取调度器、默认 store 与 generate 的关系，尚待用户确认。

本轮关于实际就绪的疑问：

> 好的也就是在这里的
> 有这样子的一个prewarm的store
> 但是我需要考虑的内容是
> 我需要使用这里的这个store部分的这个class
> 在一开始schedule的部分
> 能够确保
> 这里能够通过这里的claim方式看看这里是有这个session id
> 如果有拿到这个record
> 但是我是怎么知道远程的这个pod容器预热好了呢?
> 我不是特别理解
> 主要是这里的这个record.task到底是什么

助手补充了本地 Task → 初始化协程 → provider/health → 返回 state 的完成关系；尚待用户反馈。

本轮关于 start 与 claim 的联系，用户已表达创建 Task、登记记录、后续等待的理解，完整原话见 [start 卡](../../02-short-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.start.md)。助手补充：await 等待完成并取回 state，不只是检查是否启动。

## 尚不清楚

- 上游启动位置已补充；预取容量、与活跃任务如何配合、不同运行模式的完整调度策略未展开。
- 取消时的完整资源释放链尚未展开；这里保留领取端的责任边界。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- store.py 的 PrewarmHandle、PrewarmStore.start/claim/_take、claim_prewarm；generate:182–242。
- 静态源码核对，没有创建或领取真实环境，没有执行任务。
- [原始讨论](../../04-flow.md)。

</details>
