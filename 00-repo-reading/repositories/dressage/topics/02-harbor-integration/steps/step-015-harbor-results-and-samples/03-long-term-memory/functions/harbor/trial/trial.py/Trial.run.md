# Trial.run（Harbor）

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../step-014-model-routing-and-api-contract/02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md) 完整继承；不改变原认识时间或掌握状态。

- Step 014 调取：2026-11-13，从 [本步前序快照](Trial.run.md) 调取，保留原话、版本和认识时间；本步回看执行入口，并按当前问题回查开头 START 的触发位置。

**本步当前回查**：先看开头的 `_emit(TrialEvent.START)` 怎样触发 [DressageHarborPlugin._on_start](../../../dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_start.md#trial-start-mainline)，回调正常结束后才进入 _prepare。此前已接清的 _prepare → _run 关系继续保留。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/trial/trial.py/Trial.run.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/harbor/trial/trial.py/Trial.run.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

- 源码：[src/harbor/trial/trial.py:601–631](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L601)。
- 首次单独展开：Step 011，2026-11-10（Harbor 0.18）。
- 最近认识更新：2026-11-11，用户接清结果初始化 → 环境与 Agent 准备 → 执行 → finalize → 其他收尾 → 返回 TrialResult 的正常主干；子方法内部尚未展开。
- 源码依据更新：2026-11-11 核对 v0.25.0；这是版本校准，不代表个人已经读懂新版差异。
- [0.18 完整卡片快照](../../../../../../step-011-harbor-trial-lifecycle/references/history/2026-11-11-harbor-018-before-025/02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md)。
- 本轮范围：一份普通任务尝试的正常主干，install_only=False、无 user-agent bridge；先不深入子方法和失败恢复。

[队列函数的 [2] 运行阶段](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/job.py/Job._run_trials_with_queue.md#queue-stage-2) → **Trial.run** · [本步导航](../../../../../../step-011-harbor-trial-lifecycle/01-scope.md#current-reading)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Dressage 已创建 Harbor Job 并挂接插件；Job 通过其调度器运行一次 Trial。这里研究其中一份任务与一个 Agent 的尝试。
2. **具体内容**：建立结果记录、发出开始事件；准备环境与 Agent，委派具体工作；进入 finally 收尾，正常走到末尾时返回 TrialResult。
3. **建议构建的心智模型**：

   > 管好一次任务尝试的生命周期：准备好，执行它，收尾并交回结果。

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

本步按 Harbor 0.25 的有效 Trial 对象理解；Dressage 已读调用方提供整体背景，跨版本运行尚未验证。

输入承载在 self 中：Trial 已持有本次 config、task、agent 和环境对象。当前不是直接传入一份 Slime Sample；输出为记录本次尝试的 TrialResult。结果对象在执行期间逐步填写，不能把返回 TrialResult 自动等同于任务答对。

<a id="normal-lifecycle"></a>
<a id="prepare-call"></a>
<a id="run-call"></a>
<a id="finalize-call"></a>

### 本轮先看这条正常主干：记录开始 → 准备 → 执行 → 收尾 → 返回

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

## 我的直接表述（原话）

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

- 环境与 Agent 各自在 _prepare 的什么位置准备，下一处再看。
- 工作与 Verifier 的具体组织，以及 Dressage 事件回调如何参与，后续逐段读。
- 失败恢复与取消传播当前不深入。_init_result/START 在 try 之前，不应泛化为函数内任何错误都一定经过本 finally。

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
