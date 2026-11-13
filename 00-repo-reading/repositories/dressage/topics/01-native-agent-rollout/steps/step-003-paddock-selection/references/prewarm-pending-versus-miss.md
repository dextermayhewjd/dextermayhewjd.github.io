# 预热仍在运行，为什么不会直接再创建一份

本页回答 Step 003 的会话 ID 追问，不改变当前阅读路线。源码静态核对；未执行真实远端创建或完整测试。

<a id="architecture-layers"></a>

## 先看职责分层

以下是职责层次，不代表四台机器或四个服务。先看环境准备这一条线，模型推理与轨迹代理是另一个协作方向。

| 层次 | 对象 | 主要责任 |
| --- | --- | --- |
| 任务调度 | rollout worker、PrewarmScheduler | 持续取任务组、提前准备未来任务的环境、派发任务 |
| 单任务编排 | blackbox_dispatch.generate | 为一份 sample 取得环境，注册/调用 Agent，读取轨迹并交付样本 |
| 统一操作 | Paddock | 对上提供 init/register_agent/call_agent/terminate，协调环境与 Agent 操作 |
| 环境后端 | SandboxProvider | 用具体后端创建/取得和释放沙箱，返回访问与管理资料 |

PrewarmStore 是调度侧与单任务编排侧之间的本地记录表，按 session_id 保存初始化 Task 和相关对象。它并不保存一个实体容器；record.task 也不是远端容器，而是本地等待初始化完成的 asyncio.Task。

### 提前准备和直接初始化是同一种初始化的两条入口

1. 提前准备：worker → scheduler → store.start → 调度 paddock.init → provider 创建/取得环境。store 立即登记 Task，环境未必已完成。
2. 接手结果：worker 将该 sample 派给 generate → store.claim(session_id) → 等待已登记的 Task → 得到包含 state 的 handle。
3. 未命中：generate 取得 Paddock → 自己等待 paddock.init → 得到 state。

不论提前准备还是未命中初始化，最终都要拿到可供后续使用的 Paddock 和 state；命中路径取得的是已有初始化的结果，不再重做初始化。

### 四个容易混淆的东西

- sample：要执行的题目/任务数据。
- asyncio.Task（record.task）：本地运行初始化协程的任务对象。
- sandbox：provider 创建/取得的实际执行环境，具体形态由后端决定。
- state：初始化成功后返回的环境访问资料。

因此判断不能写成“远端还没准备好就 miss”：只要本地有记录，generate 就等待那项初始化。没有可领取记录或初始化普通失败才回退。Proxy 客户端用于访问会话/轨迹服务，不负责从 PrewarmStore 领取或创建沙箱。

## 1. 预热未完成，不等于 miss

start 的同步代码先创建初始化 Task，再立即将其放入 _records[session_id]，中间没有 await。记录不必等环境 Ready 才出现。正常单事件循环调用中，claim 执行时即使初始化尚未开始或还没完成，也能取得已经登记的记录。

```python
# PrewarmStore.start，省略记录中的其他字段
# task = asyncio.create_task(_initialize(), ...)
# self._records[session_id] = _PrewarmRecord(..., task=task)

# PrewarmStore.claim，摘录正常路径；异常处理见源码
record = self._take(session_id)
if record is None:
    return None
state = await record.task
```

| 状态 | claim 的行为 | generate 是否立即另行初始化 |
| --- | --- | --- |
| 有记录，初始化仍在进行 | 等待已有 Task | 不会 |
| 有记录，初始化已成功 | 取得结果并返回 handle | 不会 |
| 没有记录 | 返回 None | 进入未命中分支 |
| 有记录，Task 抛普通异常 | 日志后返回 None | 进入未命中分支 |
| 等待被取消或 Task 取消 | 安排处理并传播取消 | 不是正常的 miss 回退 |

### 具体什么时候是 miss

1. 没有对应记录：例如标准预热功能没有开启，或者这份任务没有经过预取启动流程。claim 按该 session_id 查不到 record，返回 None。
2. 曾经安排了预热，但初始化 Task 抛出普通异常：claim 等到了失败，捕获异常后返回 None。已有预热安排也可能最终 miss。
3. 记录已被领取或清理：之后再用同一 ID 查询也会查不到。正常单次领取流程不应把重复调用当成新的有效预热。

反过来，单纯“慢、还在初始化”不属于 miss：只要记录存在，claim 就 await 原来的 Task，没有在本函数中设置“稍慢就另建一份”的超时回退。

Task 并非完全不知道进度：它有未完成、成功、失败或取消等状态。此处直接 await，统一处理等待和取结果，不需要先由调用者判断 ready。取消走异常传播，不属于返回 None 的普通 miss。

## 2. 正常调度如何避免重复启动

1. start 在记录仍存在时检查同一 session_id，已存在就返回 None，不创建第二个初始化 Task。
2. 异步 worker 先 do_prefetch，再 pop_next_group 派发先前的任务组。不是 generate 先发现空记录，调度器才在正常路径为同一组补发预热。
3. claim 的 _take 在等待前将记录从未领取集合和组索引移除，普通组清理不会再将已交接记录当作未使用预热处理。

边界：上述去重依赖同一进程内的 store 与正常调度关系。_records 不是全局永久的“曾启动会话”表；记录取走后，若外部再次人为对同一会话调用 start，单凭这个检查不能阻止再次创建。也不能由它推出跨进程、远端 API 的严格仅创建一次保证。

## 3. 新会话 ID 和清理各负责什么

真正进入 miss 路径时，确定性 ID 加 -miss，普通 ID 清空后重新生成；后续初始化、Agent 注册、轨迹操作和该次退出清理使用新 ID。

这个变化将新初始化与旧预热尝试的身份分开，不会主动取消旧 Task，也不会删除远端环境。

资源处理由具体路径负责：

1. 未使用预热的 cleanup_group/cleanup_all 调用 _dispose：取消未完成初始化，等待处理，再尝试终止环境。
2. claim 被取消时安排 _schedule_dispose 并重新抛出取消。
3. Paddock 创建资源后，若取端点或健康检查失败，init 尝试释放取得的 lease；provider.create 自身失败时，资源处理由 provider 的实现负责。
4. 如果调用方取消而远端创建仍可能完成，Paddock 的 terminate_when_provider_create_finishes 等待晚到的 lease 并尝试释放。E2B provider 也有创建取消后的资源处理。

因此不能把“换 ID”理解成“已经清理完旧资源”。旧资源清理与新尝试在某些情况下可能短暂重叠；代码分别维护身份和清理责任，不保证远端资源永不同时存在，也不保证清理必定成功。

## 4. 源码与已有测试依据

- [PrewarmStore.start/claim](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/store.py#L78)：记录登记、去重、等待和返回。
- [store 的清理](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/store.py#L143)：未领取记录与取消处理。
- [worker 先预取再派发](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/fully_async_rollout.py#L360)。
- [miss 后更换身份](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L204)。
- [Paddock.init 的失败/取消处理](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L86)、[等待创建后释放](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/lifecycle.py#L115)。
- 已阅读测试：test_prewarm_store.py 中 duplicate-session、pending cleanup、cancelled claim；test_blackbox_dispatch.py 的 miss 使用新 ID；test_prewarm_provider_integration.py 的晚到 E2B 环境清理。本轮未执行这些测试。
