# Trial.run（Harbor）

- Step 016 调取：2026-11-16，从前一步累计卡片保留完整历史。当前看 [取消分支](#trial-cancellation)，不重新展开正常执行；新解释不代表已掌握。

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../step-014-model-routing-and-api-contract/02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md) 完整继承；不改变原认识时间或掌握状态。

- Step 014 调取：2026-11-13，从 [本步前序快照](../../../../../../step-015-harbor-results-and-samples/03-long-term-memory/functions/harbor/trial/trial.py/Trial.run.md) 调取，保留原话、版本和认识时间；本步回看执行入口，并按当前问题回查开头 START 的触发位置。

**Step 014 当时回查**：先看开头的 `_emit(TrialEvent.START)` 怎样触发 [DressageHarborPlugin._on_start](../../../../../../step-015-harbor-results-and-samples/03-long-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_start.md#trial-start-mainline)，回调正常结束后才进入 _prepare。此前已接清的 _prepare → _run 关系继续保留。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/trial/trial.py/Trial.run.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/harbor/trial/trial.py/Trial.run.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

- 源码：[src/harbor/trial/trial.py:601–631](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L601)。
- 首次单独展开：Step 011，2026-11-10（Harbor 0.18）。
- 最近认识更新：2026-11-11，用户接清结果初始化 → 环境与 Agent 准备 → 执行 → finalize → 其他收尾 → 返回 TrialResult 的正常主干；子方法内部尚未展开。
- 源码依据更新：2026-11-11 核对 v0.25.0；这是版本校准，不代表个人已经读懂新版差异。
- [0.18 完整卡片快照](../../../../../../step-011-harbor-trial-lifecycle/references/history/2026-11-11-harbor-018-before-025/02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md)。
- Step 016 范围：普通任务在执行期间收到一次取消；沿下方 [1]–[6] 接清处理与收尾。此前正常路径移入折叠对照。

[队列函数的 [2] 运行阶段](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/job.py/Job._run_trials_with_queue.md#queue-stage-2) → **Trial.run** · [本步导航](../../../../../01-scope.md#current-reading)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Dressage 已创建 Harbor Job 并挂接插件；Job 通过其调度器运行一次 Trial。这里研究其中一份任务与一个 Agent 的尝试。
2. **具体内容**：建立结果记录、准备与执行、最终收尾；正常到达末尾时返回 TrialResult，本步取消路径则记录异常、通知回调，经 finally 后继续传播取消。
3. **建议构建的心智模型**：

   > 管好一次任务尝试的生命周期：准备与执行，随后收尾；正常返回结果，取消则继续传播异常。

   Trial 不是一个模型 API 调用；一个 Agent 执行任务期间可以多次调用模型和工具。

   **Trial 是一次任务尝试的组织者。** 它通过 Environment 使用沙箱，安排 Agent 执行与 Verifier 评测，最后保存本次结果和收尾。沙箱提供命令、文件等运行能力，不等同于 Trial 的全部职责。

4. **调用位置**：当前 Task 已进入 TrialQueue._execute_trial_with_retries（queue.py:201–203）。

   ```python
   trial = await Trial.create(trial_config)  # Trial 对象已创建。
   self._setup_hooks(trial)                 # 回调已挂接。
   result = await trial.run()               # 当前进入这里。
   ```

   这属于上游 TaskGroup 正在等待的工作；Job 和 Trial 对象都已经存在。

## 本场景的输入与输出

<a id="trial-cancellation"></a>

### Step 016 当前：收到取消后，怎样收尾并继续传播？

**进入时**：Trial 已持有 config、task、agent 和环境对象，回调已登记；假设在 `_run()` 中收到一次取消。当前只看清理正常完成的路径，Harbor v0.25.0 与 Dressage 的跨版本运行仍未验证。

**交出什么**：本次结果记录会被更新；清理正常完成后向上抛出 CancelledError，调用者不会在这条路径接到正常返回的 TrialResult。

下面与 [scope 3.2](../../../../../01-scope.md#reading-navigation) 使用同一份骨架、同一套 [1]–[6] 编号；这里是源码裁剪，不是完整实现。

```python
# 已完成结果初始化和 START 通知；本轮省略普通 Exception 分支与日志。
try:
    await self._prepare()
    if not self.config.install_only:
        await self._run()               # 假设在这里收到一次取消。
except asyncio.CancelledError as exc:
    self._record_exception(exc)         # [1] 记录取消原因。
    await self._emit(TrialEvent.CANCEL)  # [2] 通知取消回调。
    await self._close_bridge()          # [3] 关闭桥接、恢复已有输出。
    await self._recover_outputs()       # 单步实现还会收集产物并停止环境。
    raise                              # [4] 继续传播，但先经过 finally。
finally:
    try:
        await self._finalize()          # [5] 主要收尾与 END 通知。
    finally:
        try:
            self._scrub_jobs_dir()      # [6] 尝试脱敏，随后关闭日志。
        finally:
            self._close_logger_handler()
# 原函数末尾还有 return self.result；取消路径不走这个正常返回。
```

<a id="cancel-record"></a>
**[1] 记录取消原因 · 已讨论**：进入 [Trial._record_exception 函数卡](Trial._record_exception.md)，看捕获的 exc 怎样写进结果对象和异常文本文件；已有异常则保留。返回后接 [2]，当前调用不负责清理或重抛。

<a id="cancel-notify"></a>
**[2] 通知取消回调 · 已讨论**：进入 [DressageHarborPlugin._on_cancel](../../../dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_cancel.md)。`_emit(CANCEL)` 依次等待已登记回调。Dressage 的 `_on_cancel` 标记取消并按需 quiesce，不在这里完成最终提交和关闭；回调结束后回到 [3]。不展开通用事件分发或网关内部。

<a id="cancel-recover"></a>
**[3] 关闭桥接、恢复输出 · 已讨论主干**：执行已被取消，接下来尽量保留已经产生的输出，再收尾环境；不是重新运行 Agent 或恢复解题。

```python
await self._close_bridge()
await self._recover_outputs()
```

**先处理可选的 bridge。** Harbor 的 BaseBridge 用协议连接 user agent 与目标 agent，不是这里的 Dressage Gateway/Proxy。启用且已开始 setup 时，关闭流程会在 bridge ready 的条件下尝试导出交互轨迹，再执行 teardown。当前选择没有 user-agent bridge 的普通 SingleStepTrial，所以 `_close_bridge` 直接返回，不下钻其清理 Task。

**再进入 SingleStepTrial._recover_outputs。** 三句源码顺序不变（single_step.py:57–60）：

```python
await self._sync_agent_output(self.result)  # 取回日志，并补本次 Agent 结果信息。
await self._collect_artifacts(stop_main_before_sidecars=False)  # 收集已产出的任务文件。
await self._stop_agent_environment()       # 委托后端停止环境，按配置决定删除。
```

| 动作 | 具体保留或改变什么 |
| --- | --- |
| `_sync_agent_output(self.result)` | 调用日志下载；需要时由 Agent 补充结果上下文，model_usage 缺失时尝试从 trajectory.json 加载。配置 user agent/bridge 时还有对应补充。不是重新请求模型，也不是这里读取 Proxy 的训练 segments。 |
| `_collect_artifacts(...)` | 收集约定目录及配置指定的任务文件，例如代码修改、报告等。只收集存在且符合配置的产物，不保证所有工作区修改都自动带回；已经收集则跳过。 |
| `_stop_agent_environment()` | 将执行环境的停止/删除工作交给实际 Environment 后端。日志与产物的恢复安排在它之前，以免先关闭环境而无法取回。 |

**两层分工：Trial 决定何时收尾，Environment 后端负责具体怎样停止。**

```text
Trial._stop_agent_environment()
    → 检查停止标记、组织 shield 等待和异常处理
    → self.agent_environment.stop(delete=...)
         → 实际后端执行停止/删除请求
```

以后接 Agent Sandbox，需要在 Environment 的 `stop()` 实现中映射具体沙箱资源清理；不是另写一个后端 `_stop_agent_environment()`。

停止环境的核心委派（trial.py:2039 起，省略状态判断和异常处理）：

```python
await asyncio.shield(
    self.agent_environment.stop(delete=self.config.environment.delete)
)
```

`delete` 是停止时是否删除环境的请求；具体支持与效果由后端决定，不能把这句直接等同于“已经删除 Kubernetes Pod”。`shield` 用于避免等待者的取消直接连带取消这次 stop 操作。停止方法还记录 `_is_agent_environment_stopped`，后续 `_finalize` 再调用时可跳过重复操作；但取消或异常分支也会设置标记，因此标记不能证明远端资源释放成功。

**一句话串起来：有桥接先收尾桥接 → 尽量取回日志/结果信息和文件产物 → 停止执行环境。** 三步正常完成后，回到 [4] 的 raise，再进入 [5] 的 finally；这些恢复语句顺序执行，不保证某一步出错后其余恢复步骤仍全部执行，外层 finally 仍负责后续收尾。

来源：BaseBridge（bridges/base.py:11）；Trial._create_bridge:526、_sync_agent_output:1167、_cleanup_bridge:1950、_close_bridge:2007、_stop_agent_environment:2039。均为 Harbor v0.25.0 静态核对，未运行取消或资源回收实验。

<a id="cancel-reraise"></a>
**[4] 继续传播取消**：裸 `raise` 重新抛出当前异常，但离开函数前先执行 [5]、[6]；不会直接跳过清理。

<a id="cancel-finalize"></a>

本步独立入口：[Trial._finalize 函数卡](Trial._finalize.md)，读完返回这里继续外层清理。

**[5] 主要收尾与 END**：`_finalize` 正常收尾时停止环境、保存结果并发出 END；插件的 `_finalize_attempt` 在取消分支跳过训练 bundle 提交，但仍进入其 finally 关闭尝试。随后接 [6]。

<a id="cancel-final-cleanup"></a>
**[6] 最后处理两件事：文件脱敏、关闭本次日志输出**

```python
try:
    await self._finalize()
finally:
    try:
        self._scrub_jobs_dir()         # 处理已保存文件中的已知敏感值
    finally:
        self._close_logger_handler()  # 移除并关闭本 Trial 的文件日志 handler
```

具体方法现在分别记录在独立卡中，按调用顺序阅读：

| 当前调用 | 函数卡 | 返回位置 |
| --- | --- | --- |
| 6a. 脱敏本地结果文件 | [Trial._scrub_jobs_dir](Trial._scrub_jobs_dir.md) | 回到内层 finally，继续 6b |
| 6b. 关闭本次日志 handler | [Trial._close_logger_handler](Trial._close_logger_handler.md) | 回到 Trial.run；清理正常完成后继续传播取消 |

两者都正常完成时，本次取消继续向上传播，不走末尾 return self.result。清理异常可能改变最终传播的异常；未进行实际运行验证。

<details>
<summary>此前正常路径对照（历史编号与说明）</summary>

以下为此前正常路径的记录；其中 [1]–[5] 仅属于历史正常路径，不是当前取消路径的导航编号。


本步按 Harbor 0.25 的有效 Trial 对象理解；Dressage 已读调用方提供整体背景，跨版本运行尚未验证。

输入承载在 self 中：Trial 已持有本次 config、task、agent 和环境对象。当前不是直接传入一份 Slime Sample；输出为记录本次尝试的 TrialResult。结果对象在执行期间逐步填写，不能把返回 TrialResult 自动等同于任务答对。

<a id="normal-lifecycle"></a>
<a id="prepare-call"></a>
<a id="run-call"></a>
<a id="finalize-call"></a>

### 此前正常主干：记录开始 → 准备 → 执行 → 收尾 → 返回

以下节选省略 except 恢复分支，原函数保留在文末；注释只标关键阶段。

```python
self._init_result()
await self._emit(TrialEvent.START)  # [1] 建立结果记录，通知一次尝试开始。
try:
    await self._prepare()          # [2] 准备环境和 Agent。
    if not self.config.install_only:
        await self._run()          # [3] 执行任务；普通路径还会进行评测。
finally:
    try:
        await self._finalize()     # [4] 收尾、保存结果、发出结束事件。
    finally:
        try:
            self._scrub_jobs_dir() # 对落盘文本中的敏感值脱敏；本轮只定位。
        finally:
            self._close_logger_handler()
return self.result                 # [5] 交回这一次尝试的 TrialResult。
```

- **[1] 记录开始**：初始化的是本次 TrialResult，随后通知已挂接的开始回调；它与整份 JobResult 不同。
- **[2] 准备**：安排环境启动、环境检查和 Agent 准备，尚未在这里执行解题主流程。
- **[3] 执行**：本轮 install_only=False，所以进入 _run；普通单步实现组织 Agent 执行、产物收集与评测。
- **[4] 收尾**：进入 finally 执行收尾；落盘文本脱敏与日志关闭的嵌套 finally 本轮先保留位置。
- **[5] 返回**：正常走到末尾时返回 self.result。队列接住后判断是否重试；最终 TrialResult 才成为外层 Task 的结果。

本轮选择普通 SingleStepTrial：使用基类 Trial.run，self._run 对应 SingleStepTrial._run。single-step 指任务没有单独配置多个工作步骤，不表示 Agent 只能调用一次模型。

| 本函数中的入口 | 先知道它做什么 | 后续回到哪里 |
| --- | --- | --- |
| [_prepare 函数卡](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-mainline) | 准备运行环境、检查环境并准备 Agent | 回到 install_only 判断和 _run 调用 |
| [SingleStepTrial._run 函数卡](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run.md#single-step-run-mainline) | 普通实现组织 Agent、产物及 Verifier | 返回 run，进入 finally |
| [_finalize 函数卡](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial._finalize.md#finalize-mainline) | 关闭 bridge、停止环境、写入结束时间/结果文件、发出 END | 回到嵌套 finally 清理目录和日志，再返回 self.result |

环境停止并非只在 _finalize：SingleStepTrial._run 会按评测模式在评测前后停止环境；这里先保留位置，后续读具体执行体时再展开。

核心委派仍是准备、执行、收尾三段。[_prepare](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-mainline) 已读主干，[SingleStepTrial._run](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run.md#single-step-run-mainline) 主干已讨论；当前按用户确认进入 [_finalize](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial._finalize.md#finalize-mainline)。

</details>

## 我的直接表述（原话）

Step 016，2026-11-17 的当前疑问（节选）：

> 这里的close bridge更多的是
> 关掉对应的和别的agent桥接的部分对吧
> 同步已经有的agent 输出
> 手机这里的这个artifacts？
> 还有这里的这个stop agent environment是在做什么呢？

助手核对：关闭桥接的方向正确，具体是 Harbor user agent 与目标 agent 的协议桥接；日志/结果恢复、文件产物收集和环境停止是三个不同动作。尚不将讲解补充记为用户已掌握。

用户随后反馈：

> 好的 我差不多了解了
> 简单写一下这个吧
> 我觉得这个还是挺重要的？
> 不过这里的内容我觉得差不多了
> 还有什么是我需要理解的吗

本轮据此保留停止职责的两层分工，第[3]段先收束；具体后端实现与远端回收效果未展开或验证。

此前原话保留如下：

> 那么现在step011就是在讲述
> 这里的这个run round里面的部分内容对吧
> 那么现在开始吧

助手校准：这是 _run_round 下游 Job 所调度的 Trial 生命周期，不是 _run_round 函数本体。当时尚无对 Trial.run 内部职责的独立复述；后续表述见下方。

本轮表述：

> 好的 我大概理解了
> 原来的这个job run trials这里就不要缩进了
> 还是正常的直接考虑一下展开吧
>
> 然后我来看一下这里的这个trial
> 这里就是这个单次的实验 考虑直接运行
> 这里就是准备环境和执行人物
> 然后这里保存结果
> 清理罗盘内容
> 返回结果
>
> 像是一个sandbox需要做的事情

助手校准：可以先把 Trial 看成一次任务尝试，包含准备、执行、评测与收尾；Trial 组织过程，Environment/沙箱提供执行环境。_scrub_jobs_dir 更准确是对落盘文本中的敏感值脱敏，不表示删除全部结果文件。以上区别由助手核对补充，尚待用户确认。

最新主干复述：

> 好的
> 也就是准备这里的结果记录
> 然后准备环境和对应的agent
> 然后看的就是这里的执行任务
> 人物执行完了之后后考虑finalize首位
> 之后是这里的其他结尾工作
> 以及返回trialresul是我的理解
> 还有什么需要做的吗?

助手核对：正常路径的顺序已接清；本轮普通执行路径的 _run 还包括评测。Trial.run 的首轮编排阅读可先停在此处，环境/Agent 准备和执行细节仍待下钻，不表示 Step 011 已完成。下一处建议是 _prepare，尚未展开。

## 尚不清楚

- Step 016 当前：取消与清理责任已给出局部说明，用户尚未确认全部理解；清理异常、再次取消及实际资源回收尚未验证。以下保留此前记录的未知，不作为当前新阅读清单。

- 环境与 Agent 各自在 _prepare 的什么位置准备，下一处再看。
- 工作与 Verifier 的具体组织，以及 Dressage 事件回调如何参与，后续逐段读。
- 此前正常路径阶段未深入失败恢复与取消传播；本步仅展开上述取消主线。_init_result/START 在 try 之前，不应泛化为函数内任何错误都一定经过本 finally。

<details>
<summary>完整函数与来源</summary>

Harbor v0.25.0，固定提交 fdba28fc411e47e8765420a1a063b4918fce3def；2026-11-11 从本地 git 对象核对，未切换源码工作区或安装环境。项目采用 [Apache-2.0 许可](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/LICENSE)。以下保留该发布版完整函数。

```python
async def run(self) -> TrialResult:
    self._init_result()
    await self._emit(TrialEvent.START)

    try:
        await self._prepare()
        if not self.config.install_only:
            # Setup/install ran in _prepare(); skip the agent run + verification.
            await self._run()
    except asyncio.CancelledError as exc:
        self.logger.debug(f"Trial {self.config.trial_name} cancelled")
        self._record_exception(exc)
        await self._emit(TrialEvent.CANCEL)
        await self._close_bridge()
        await self._recover_outputs()
        raise
    except Exception as exc:
        self.logger.debug(f"Trial {self.config.trial_name} failed: {exc}")
        self._record_exception(exc)
        await self._close_bridge()
        await self._recover_outputs()
    finally:
        try:
            await self._finalize()
        finally:
            try:
                self._scrub_jobs_dir()
            finally:
                self._close_logger_handler()

    return self.result
```

_prepare:641、_finalize:660；普通执行体见 single_step.py:37。本版取消分支先发 CANCEL，再关闭 bridge、恢复输出；finally 中用嵌套清理保证后续清理仍被尝试。本轮不深入这些辅助实现。仅静态核对，无 Harbor Job、模型、环境创建或训练运行。

形成过程：[Step 011](../../../../../../step-011-harbor-trial-lifecycle/04-flow.md#start-step011)。

</details>
