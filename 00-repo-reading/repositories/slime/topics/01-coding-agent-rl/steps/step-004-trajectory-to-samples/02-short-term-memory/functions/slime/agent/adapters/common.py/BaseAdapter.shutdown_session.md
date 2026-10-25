# BaseAdapter.shutdown_session

- 源码定位：[slime/agent/adapters/common.py:294–312](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L294-L312)，共同基类实现。
- 首次接触：Step 3；此前在 `finish_session` 中定位，2026-10-21 按用户要求独立展开。
- 最近认识更新：2026-10-24，用户复述了等待、对 pending 请求取消和收尾的顺序；sid 与 Task 的区别、任务所属循环及 `run_coroutine_threadsafe` 的作用仍需澄清。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`finish_session` 导出轨迹前，先处理仍可能写入轨迹的请求。
2. **具体内容**：标记会话关闭，取出当前 `sid` 的未完成 Task，在这些 Task 所属的循环中等待和取消。
3. **建议构建的心智模型**：

   > 关闭本会话的新请求入口，等已登记的请求收尾，再让调用方继续导出轨迹。

4. **调用代码**（[finish_session:330](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L330)）：

   ```python
   await self.shutdown_session(sid, wait_timeout=wait_timeout)
   ```

## 本场景的输入与输出

- **已有条件**：`sid="sid-demo"`，`wait_timeout=5.0`；`inflight[sid]` 中仍有一个未结束的请求 Task。字段含义统一见 [BaseAdapter 类卡片](../../../../../classes/slime/agent/adapters/common.py/BaseAdapter.md#session-tracking)，执行编号的含义见 [sid 说明](../../../../../../references/session-id.md#what-session-identifies)。
- **正常结果**：返回 `None`；`closed` 留下关闭标记，当前 sid 的任务登记被取走，所取出的请求 Task 已结束。会话配置与轨迹仍保留，交给调用方继续处理。

<a id="shutdown-five-steps"></a>
<a id="shutdown-cross-loop"></a>

### 状态变化与跨循环交接

当前调用场景中，A 是调用方循环，B 是 Adapter HTTP 服务的循环，二者位于同一进程的不同线程。双线框内均为本函数的直接职责，包含内部协程 `_drain`；框外的 HTTP 请求 Task 是已经运行的协同对象。

图中编号对应下方三段源码：第 2 段先在 A 中定义，经第 3 段提交后才在 B 中执行。无任务时从第 1 段直接返回。

```text
╔ shutdown_session: direct code ═══════════════════════╗
║ Loop A / caller                                      ║
║ [1] closed.add(sid); pop/filter inflight[sid]        ║
║     no unfinished tasks -> return None               ║
║ [2] define _drain()                                  ║
║ [3] run_coroutine_threadsafe(_drain(), loop)         ║
║     await wrap_future(...)  (caller suspended)       ║
║                      |                               ║
║                      v                               ║
║ Loop B / Adapter HTTP                                ║
║ [2] _drain body: wait(tasks, timeout)                ║
║     if pending: cancel -> gather                     ║
║                      |                               ║
║                      | completion                    ║
║                      v                               ║
║ Loop A / caller                                      ║
║ [3] resume -> return None                            ║
╚══════════════════════════════════════════════════════╝
Background: existing HTTP request Tasks on loop B
```

### 1. 在 A 中标记关闭、取出任务（296–299）

```python
self.closed.add(sid)
tasks = [t for t in self.inflight.pop(sid, ()) if not t.done()]
if not tasks:
    return
```

- 关闭的是已有会话的新请求入口；`_run_turn:397–399` 检查标记并返回 `503`。
- `pop` 移除当前 `sid` 的登记，未完成的 Task 由 `tasks` 接住并继续运行；其他会话的登记保留。

### 2. 在 A 中定义收尾，提交后由 B 执行（301–306）

```python
async def _drain() -> None:
    _, pending = await asyncio.wait(tasks, timeout=wait_timeout)
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)
```

- `_drain` 捕获前面的 `tasks`；定义时尚未等待或取消它们，也不重新启动请求。
- 在 B 执行时，`wait` 先等待任务全部结束或时间到达，再交回 `done`、`pending`；随后取消仍 pending 的 Task，并用 `gather` 等它们结束。这里没有接收或使用 `gather` 返回的结果列表。

### 3. 在 A 中提交并等待完成（308–312）

```python
loop = tasks[0].get_loop()
try:
    await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(_drain(), loop))
except Exception:
    self.logger.exception("[%s] sid=%s shutdown drain failed", self.log_prefix, sid)
```

- 同一 Adapter 的这些请求 Task 均属于 B，因此 `tasks[0]` 只是用来取得共同的循环。`_drain` 仍处理前面捕获的整份 `tasks` 列表，范围限定为当前 `sid`。
- `run_coroutine_threadsafe(_drain(), loop)` 把新建的收尾协程提交给 B 执行，返回的 Future 跟踪它的完成；`wrap_future` 让 A 可以 `await` 这个完成状态。
- **时间边界**：`wait_timeout` 只限制 `asyncio.wait`；后续取消与清理没有另设超时。
- **结果边界**：正常收尾后返回 `None`；捕获 `Exception` 并记录日志后也会返回 `None`，所以该返回值不保证收尾成功。

正常返回后，接回 [finish_session:331–332](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L331-L332) 的配置读取，再进入轨迹导出；[父函数旧卡片](BaseAdapter.finish_session.md#session-close-and-config)保留原解释。

<details>
<summary>完整场景示例与前后状态（沿用原实验）</summary>

沿用 `finish_session` 的 `sid-demo`，但改为**还有一个已登记的请求没有结束**，以观察等待分支。父卡原例没有在途请求，两例不是同一次运行。下面是教学状态示意；沿用 2026-10-21 的局部实验依据，以真实 `asyncio.Task` 代替 HTTP 请求任务，本轮仅静态复核。

**输入**：

```python
sid = "sid-demo"
wait_timeout = 5.0

# 调用前已有状态；turn_task 是一个尚未结束的 Task
self.closed = set()
self.inflight = {sid: {turn_task}}
turn_task.done()                         # False
self.store[sid].max_context_tokens      # 4096
# self.manager 中已有这个 sid 的轨迹树
```

**输出**：本例请求在等待期限内正常结束，`await shutdown_session(...)` 的结果为 `None`；主要变化在状态中。

```python
sid in self.closed                      # True：后续请求走到入口检查时被拒绝
sid in self.inflight                    # False：该会话的任务登记已取走
turn_task.done()                        # True：本例任务已经结束
turn_task.cancelled()                   # False：本例没有触发取消
self.store[sid].max_context_tokens     # 4096：仍可读取配置
# self.manager 中仍有这个 sid 的轨迹树，尚未在这里导出或移除
```

- 运行中的真实请求在结束前仍可能追加轨迹；“树仍在”不表示树内容必然不变。
- 没有未完成任务时直接返回；超时场景则会请求取消剩余任务，再等它们结束。任务结束不等于一定成功生成了回复。

</details>

## 我的直接表述（原话）

<a id="shutdown-user-restatement-2026-10-24"></a>

2026-10-24，阅读跨循环图后的完整表述：

> 我也觉得这样子会比较好
> 这样子就会比较清楚
> 这里的简单说的就是在adapter中加入这个session id
> 同时把还在运行中的sessionid取出来
>
> 然后通过这个收尾函数
> 先通过asynico.wait的方式获取到所有pending的部分
> 然后对于所有pending的部分发出一个cancel的指令
> 最后手机这里的pending部分返回的内容
>
> 最后这里的这个给出对于这个task所在进行的loop
> 对于在这个loop这个线程中所有的
> 但是这里为什么是单个的一个loop?
> 以及为什么这里的loop只是属于tasks[0]?
> 这是是通过这个coroutine threadsafe来做这件事情
> 其实我不是特别理解这里的run coroutine threadsafe

本轮已表达等待、取消 pending 与收尾的顺序；对象类型、等待返回时机和跨循环交接仍按下方未知继续核对。原话中的措辞保留，助手说明写在前面的对应代码段中。

<a id="shutdown-restatement-after-split"></a>

2026-10-22 的复述节选，完整上下文见下方折叠区：

> 来做到sid本身只是标记session id
> inflight来控制这里具体pop out移除哪一项内容

<details>
<summary>完整历史复述、前置疑问与校正记录</summary>

用户先指出前置缺口：

> 不对啊 这里不是需要考虑这里的shutdown session先吗 怎么直接快进到这里的get trajectory了呢？
> 以及不需要先知道store pop吗？

本轮确认：

> 好的，那么先处理一下这里的shut down session吧

以上确认阅读对象。阅读后用户第一次复述：

> 好的 我大概理解了
> 这里就是把目前还在跑得这个sid先拿掉？
> 然后让这个无法在一开始再被开始
> 同时取消掉所有目前还在跑得
> 同时获得同时把这些还在pending的收集起来
> 放到coroutine的里面
> 确保都处理掉？
> 这是我对于这个shutdown session的理解

这段复述表达了关闭入口与处理剩余请求的初步认识。具体校正对应上方前两段代码，完整说明见[本轮澄清](../../../../../../04-flow.md#shutdown-session-restatement)；不将助手的校正自动记为用户已确认掌握。

在补入五步摘要之后，用户继续指出：

> 但是这里对于inflight的部分我其实还是不知道是什么 包括这里的sid 我其实也不知道是否应该单独开一个short term memroy记录一下 否则我感觉我一直记不住这里到底是什么

本轮因此先补两个状态名称的含义及来源，不将此前的流程复述当作已理解这些前置概念。

2026-10-22 返回本步后，用户进一步追问：

> 但是这里的sid究竟是什么呢？
> 我的意思是当前的sid这里所谓的会话编码到底是什么意思是呢？
> 是image中的某一个题目
> 还基于一棵树？
> 还是说之前的messages群
> 这里我还是没有特别清楚

这次问题聚焦 sid 所标识的对象，补充解释见[执行、题目、消息与树的关系](../../../../../../references/session-id.md#what-session-identifies)；仍未据此标为用户已理解。

随后用户要求分开解释：

> 我觉得这里的sid和对应的inflight还是拆开比较好吧
> 拆分开来解释我觉得会非常有益处？

已将两份说明分开，按“先 sid、再 inflight、回到本函数”的顺序链接；这次反馈确认的是记录方式，不代表已掌握两个对象。

2026-10-22 拆开两份说明后，用户再次复述：

> 好的我简单的理解就是这里的shutdown session 会保存一个session
> 也就是某一个题目的单次会话
> 首先需要在closed中添加这个session否则后续的内容会接着添加这个请求
> 然后同时需要得到当前的这个adapter中已经在跑的所有的请求
> 如果这些task没有done的话
> 首先是拿到这些依旧在等待的部分
> 给出这里的task.cancel
> 以及这里的这个事件循环的这个loop
> 就集中使用这个wrap_future把这个cancel的部分分发出去
> 来做到sid本身只是标记session id
> inflight来控制这里具体pop out移除哪一项内容
> 这是我对于shutdown session的理解

这次已表达 sid 对应某道题的单次会话、closed 用于阻止后续请求，并注意到 inflight 按编号取出登记。仍需区分关闭与创建、当前 sid 与整个 Adapter、先等待与立即取消，以及提交协程与等待其结果。校正分别补在上方第 1–3 段，完整对照见[本轮讨论](../../../../../../04-flow.md#shutdown-restatement-after-split)；不把校正自动记成用户已掌握。

</details>

## 尚不清楚

2026-10-24，用户明确要求先走完 Step 004 主线；跨循环提交与等待细节后续回访。以下疑问继续保留。

- 本轮仍把添加关闭标记说成“在 adapter 中加入 session id”，把取出请求 Task 说成“取出运行中的 sessionid”；两项字段的对象模型集中到 BaseAdapter 类卡片后继续核对。
- 已复述 `wait → 取消 pending → 等待收尾` 的顺序；`wait` 取得 pending 的时机，以及本函数不使用 `gather` 返回列表的区别，仍待本轮反馈。
- 用户明确不理解 `run_coroutine_threadsafe`，并询问为何只取 `tasks[0]` 的循环。共同循环、处理范围、协程提交与结果等待的关系仍需澄清；底层完成通知机制继续留白。

<details>
<summary>尚未展开的异常与远端行为</summary>

- 真实请求取消时，远端生成如何中止、轨迹是否记录、哪些资源需要清理：需要结合请求当时所在位置阅读，不能由本地 Task 已结束直接推断远端已停止。
- 本轮尚未验证循环停止、收尾本身失败、调用方被取消等情形；现有等待逻辑不提供这些情况的完整成功保证。

</details>

<details>
<summary>来源、验证与完整例子</summary>

- 当前源码：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`。状态容器定义见 [common.py:221–223](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L221-L223)，关闭检查与 Task 登记见 [397–407](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L397-L407)，轨迹记录与登记清理见 [463–475](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L463-L475)。本轮比较确认关闭检查及 `inflight` 的添加、移除规则不变；未据此认定 `_run_turn` 的其他处理均未变化。
- HTTP 服务线程现由 `_AdapterService.endpoint` 启动，见 [generate.py:184–209](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L184-L209)；专用循环与线程的创建仍见 [aiohttp_threaded.py:65–88](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/aiohttp_threaded.py#L65-L88)。这里只核对本函数所需的线程关系，请求断开与远端中止的完整链路仍保留在未知中。
- 2026-10-24 静态复核：`shutdown_session`、`finish_session` 的新旧函数文本逐字相同；[本轮记录](../../../../../../04-flow.md#shutdown-session-version-refresh)保存比较范围。旧实验、参考说明与此前累计记忆继续保留各自的原版本依据。
- 2026-10-21 使用 Python 3.12.3，从本地源码通过 AST 原样提取本方法，在构造的 Adapter 状态上验证四种情况：无任务、只有已完成任务、期限内完成、超时取消。后两种使用另一个线程中循环所属的真实 Task，确认调用方等到其清理结束；没有运行 HTTP、模型、沙箱或真实请求取消。
- [异步语义依据与运行结果](../../../../../../references/session-shutdown-asyncio.md)：书籍短引文、当前 Python 实现、局部实验边界。
- 形成过程：[Step 3：独立阅读 shutdown_session](../../../../../../04-flow.md#shutdown-session-reading)。此前的在途请求认识见[继承的 _run_turn](../../../../../../03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md)。
- 2026-10-24 按状态变化与跨循环交接重排：保留原有场景、源码和历史表述，[重排前完整卡片](../../../../../../references/shutdown-session-before-cross-loop-layout.md)与[旧版源码卡片](../../../../../../references/shutdown-session-at-2f231865.md)分别存档；本次不重跑原实验，也不改变认识日期。[格式确认](../../../../../../../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#shutdown-state-cross-loop-applied)。

</details>
