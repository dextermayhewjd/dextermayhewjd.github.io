# BaseAdapter.shutdown_session

- Step 012 继承：来自 [Step 011 完整记录](../../../../../../../step-011-generate-and-rm-group/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md)；保留原话、未知、版本与认识日期，仅重算链接。

- Step 011 继承：来自 [Step 010 · 03-long-term-memory](../../../../../../../step-010-generate-and-rm/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- Step 010 继承：2026-10-25，来自 [Step 009 · 03-long-term-memory 完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- 本次继承：2026-10-23，[Step 7 · 03 完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

- 源码定位：[slime/agent/adapters/common.py:225–243](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L225-L243)，共同基类实现。
- 首次接触：Step 3；此前在 `finish_session` 中定位，2026-10-21 按用户要求独立展开。
- 最近认识更新：2026-10-22，用户已初步将 sid 对应到某道题的一次会话，并复述 closed 拒绝后续请求的目的；请求筛选范围、等待与取消顺序、跨循环提交和等待的分工仍需校正。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`finish_session` 准备导出某个会话的轨迹时，先调用这里处理尚未结束的请求；这些请求还可能通过 `record_turn` 写入轨迹。

2. **具体内容**：用 `sid` 标记会话关闭，从 `inflight` 只取出这个 sid 下仍未完成的请求 Task。先给它们 `wait_timeout` 秒自行结束；超时后对剩余 Task 请求取消，并等待其结束。收尾工作交给这些 Task 所在的事件循环执行。

3. **建议构建的心智模型**：

   > `shutdown_session` 为一个会话做“导出前收尾”：关上新请求的入口，等已登记的请求结束，超时则请求取消并等待清理。
   >
   > 它通过改变会话与任务状态完成工作，返回 `None`。会话配置和轨迹仍交给后面的 `finish_session` 读取、导出和移除。

4. **调用代码**（`finish_session:261–263`）：

   ```python
   await self.shutdown_session(sid, wait_timeout=wait_timeout)
   session = self.store.pop(sid, None)
   max_sample_tokens = int(getattr(session, "max_context_tokens", 0) or 0) if session is not None else 0
   ```

## 本场景的输入与输出

按顺序认识这两个对象：

1. **先看 `sid`：这是 Agent 的哪一次执行？** 它是字符串编号，例如 `"sid-demo"`；同一次执行中的多轮请求沿用它。题目、镜像、消息与轨迹树的区别见 [sid 独立说明](../../../../../../../../../01-coding-agent-rl/steps/step-004-trajectory-to-samples/references/session-id.md#what-session-identifies)。
2. **再看 `self.inflight`：这次执行还有哪些请求没结束？** 它按 sid 登记请求 Task，例如 `{"sid-demo": {task_A}}`。登记、移除和状态变化见 [inflight 独立说明](../../../../../../../../../01-coding-agent-rl/steps/step-004-trajectory-to-samples/references/inflight.md)。

沿用 `finish_session` 的 `sid-demo`，但改为**还有一个已登记的请求没有结束**，以观察等待分支。父卡原例没有在途请求，两例不是同一次运行。下面是教学状态示意；局部实验用真实 `asyncio.Task` 代替 HTTP 请求任务。

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

### 函数内部怎样完成这次收尾

<a id="shutdown-five-steps"></a>

先按执行顺序看这五步，再对照后面的三段源码：

1. **标记关闭**：把 `sid` 加入 `closed`，后续使用这个 `sid` 的请求会在入口被拒绝。
2. **取走任务登记**：从 `inflight` 取出这个会话的未完成 Task，交给 `tasks` 保存。`sid` 是标识，真正运行的是这些 Task；配置和轨迹仍然保留。
3. **运行收尾协程 `_drain`**：它在这些 Task 所属的事件循环中执行，先给它们一段时间正常结束。
4. **取得剩余的 `pending`**：等待结束后，只对仍未完成的任务调用 `cancel()`。
5. **继续等待清理**：用 `gather` 等这些任务结束，再返回调用方。

没有未完成任务时，第 2 步后直接返回；等待后没有剩余任务时，无需取消或调用 `gather`。下面源码先出现 `_drain` 的定义，提交到事件循环后才执行它的函数体。

#### 1. 会话标识 → 关闭标记与待收尾任务（227–230）

```python
self.closed.add(sid)
tasks = [t for t in self.inflight.pop(sid, ()) if not t.done()]
if not tasks:
    return
```

- `closed.add(sid)` 保存的是关闭标记；本场景的会话配置早已由 `open_session` 注册。`_run_turn:328–330` 检查到标记时返回 `503`，拒绝后续同 sid 请求。
- `inflight.pop` 只取走该 `sid` 的 Task 集合，其他 sid 的登记保留；`not t.done()` 再只留下未结束者。没有登记时按空集合处理。本例得到 `tasks = [turn_task]`。
- 取走的是 `inflight[sid]` 这一项任务登记；`sid` 是会话标识，本身不是正在运行的任务。移除登记不会停止 Task，这里用局部变量 `tasks` 接住它们，配置与轨迹仍然保留。

#### 2. 定义如何等待与取消（232–237）

```python
async def _drain() -> None:
    _, pending = await asyncio.wait(tasks, timeout=wait_timeout)
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)
```

- 这里先定义内部收尾过程 `_drain`，下一段提交后才执行；它直接使用上一段的 `tasks`。请求 Task 已经在运行，`_drain` 负责等待和取消它们，不会重新启动这些请求。
- `tasks` 是进入时取出的未完成任务；`wait` 先等它们结束，或等待时间到达，才得到剩余的 `pending`。已结束的放在第一组，这里用 `_` 忽略。本例正常完成，`pending` 为空，不调用任何任务的 `cancel()`。
- 超时后，`cancel()` 向每个剩余 Task 发出取消请求；Task 可能还要执行自己的清理代码，因此继续用 `gather` 等待。`return_exceptions=True` 把各任务的取消或异常作为结果收集，本函数不使用这些结果。
- `wait_timeout=5.0` 只限制 `wait` 这一段。后续等待取消与清理没有另设超时，所以不能理解成整个函数最多执行 5 秒。

#### 3. 把收尾过程交给任务所在的循环，并等待返回（239–243）

```python
loop = tasks[0].get_loop()
try:
    await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(_drain(), loop))
except Exception:
    self.logger.exception("[%s] sid=%s shutdown drain failed", self.log_prefix, sid)
```

- `get_loop()` 找到请求 Task 所属的循环。当前 Adapter HTTP 服务有专用线程与循环，本实现依赖这些请求 Task 属于同一循环。
- `run_coroutine_threadsafe(_drain(), loop)` 负责把整个收尾协程提交过去；它执行的是“先等待 → 取消仍 pending 的 Task → 等待清理”，并非先在调用方取消，再分发取消结果。
- `wrap_future` 包装提交后返回的结果对象，使调用方能用 `await` 等收尾完成。它在这行代码中负责连接完成状态，提交由内层的 `run_coroutine_threadsafe` 完成；正常收尾后才接着执行 `finish_session`。
- 如果这里捕获到 `Exception`，只记录日志，随后也会返回 `None`；因此 `None` 本身不是“所有请求收尾成功”的状态报告。上面的输出示例对应正常收尾路径。

| 读完回到哪里 | 接下来使用什么 |
| --- | --- |
| [finish_session 的第一段](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md#session-close-and-config) | 用 `store.pop` 接住会话配置，取得长度上限；随后才将轨迹交给 `get_trajectory` 导出 |

## 我的直接表述（原话）

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

这段复述表达了关闭入口与处理剩余请求的初步认识。具体校正对应上方前两段代码，完整说明见[本轮澄清](../../../../../../../../../01-coding-agent-rl/steps/step-004-trajectory-to-samples/04-flow.md#shutdown-session-restatement)；不将助手的校正自动记为用户已确认掌握。

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

这次问题聚焦 sid 所标识的对象，补充解释见[执行、题目、消息与树的关系](../../../../../../../../../01-coding-agent-rl/steps/step-004-trajectory-to-samples/references/session-id.md#what-session-identifies)；仍未据此标为用户已理解。

随后用户要求分开解释：

> 我觉得这里的sid和对应的inflight还是拆开比较好吧
> 拆分开来解释我觉得会非常有益处？

已将两份说明分开，按“先 sid、再 inflight、回到本函数”的顺序链接；这次反馈确认的是记录方式，不代表已掌握两个对象。

<a id="shutdown-restatement-after-split"></a>

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

这次已表达 sid 对应某道题的单次会话、closed 用于阻止后续请求，并注意到 inflight 按编号取出登记。仍需区分关闭与创建、当前 sid 与整个 Adapter、先等待与立即取消，以及提交协程与等待其结果。校正分别补在上方第 1–3 段，完整对照见[本轮讨论](../../../../../../../../../01-coding-agent-rl/steps/step-004-trajectory-to-samples/04-flow.md#shutdown-restatement-after-split)；不把校正自动记成用户已掌握。

## 尚不清楚

- sid 与一次会话的对应已有初步复述；“shutdown 保存一个 session”仍需校正为给已有会话留下关闭标记，会话配置创建由 `open_session` 负责。
- 取出的范围是当前 sid 的请求，且先等待、再取消仍 pending 的任务；用户本次表述仍将它理解成 Adapter 全部请求及直接取消，校正后尚待反馈。
- 用户将 `wrap_future` 理解为分发取消；已区分 `run_coroutine_threadsafe` 提交整个 `_drain` 与 `wrap_future` 配合 `await` 等待结果。底层完成通知机制仍留白。
- 真实请求取消时，远端生成如何中止、轨迹是否记录、哪些资源需要清理：需要结合请求当时所在位置阅读，不能由本地 Task 已结束直接推断远端已停止。
- 本轮尚未验证循环停止、收尾本身失败、调用方被取消等情形；现有等待逻辑不提供这些情况的完整成功保证。

<details>
<summary>来源、验证与完整例子</summary>

- 源码固定为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。Task 登记和关闭检查见 [common.py:328–338](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L328-L338)，请求结束前的记录与登记清理见 [384–393](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L384-L393)。
- HTTP 服务线程的调用在 [generate.py:161–170](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L161-L170)，循环创建在 [aiohttp_threaded.py:65–88](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/aiohttp_threaded.py#L65-L88)。只核对本函数所需的线程关系，不表示完整展开服务启动。
- 2026-10-21 使用 Python 3.12.3，从本地源码通过 AST 原样提取本方法，在构造的 Adapter 状态上验证四种情况：无任务、只有已完成任务、期限内完成、超时取消。后两种使用另一个线程中循环所属的真实 Task，确认调用方等到其清理结束；没有运行 HTTP、模型、沙箱或真实请求取消。
- [异步语义依据与运行结果](../../../../../../../../../01-coding-agent-rl/steps/step-004-trajectory-to-samples/references/session-shutdown-asyncio.md)：书籍短引文、当前 Python 实现、局部实验边界。
- 形成过程：[Step 3：独立阅读 shutdown_session](../../../../../../../../../01-coding-agent-rl/steps/step-004-trajectory-to-samples/04-flow.md#shutdown-session-reading)。此前的在途请求认识见[继承的 _run_turn](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md)。

</details>
