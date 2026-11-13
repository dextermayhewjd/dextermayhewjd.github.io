# Trial.run（Harbor）

- 源码：[src/harbor/trial/trial.py:322–343](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L322)。
- 首次单独展开：Step 011，2026-11-10。
- 本轮范围：一份普通任务尝试的正常主干，install_only=False；先不深入子方法和失败恢复。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Dressage 已创建 Harbor Job 并挂接插件；Job 通过其调度器运行一次 Trial。这里研究其中一份任务与一个 Agent 的尝试。
2. **具体内容**：建立结果记录、发出开始事件；准备环境与 Agent，委派具体工作；进入 finally 收尾，正常走到末尾时返回 TrialResult。
3. **建议构建的心智模型**：

   > 管好一次任务尝试的生命周期：准备好，执行它，收尾并交回结果。

   Trial 不是一个模型 API 调用；一个 Agent 执行任务期间可以多次调用模型和工具。

4. **调用位置**：

   ```text
   Dressage _run_harbor_rollout 的第 3 段
     → _run_round → 内部 run_partition → _run_partition
       → Harbor Job.run → Harbor 调度器 → Trial.run
   ```

## 本场景的输入与输出

输入承载在 self 中：Trial 已持有本次 config、task、agent 和环境对象。当前不是直接传入一份 Slime Sample；输出为记录本次尝试的 TrialResult。结果对象在执行期间逐步填写，不能把返回 TrialResult 自动等同于任务答对。

<a id="normal-lifecycle"></a>

### 本轮先看这条正常主干

以下节选省略 except 恢复分支，原函数保留在文末；注释只标关键阶段。

```python
self._init_result()
await self._emit(TrialEvent.START)  # 建立结果记录后，通知一次尝试开始。
try:
    await self._prepare()          # 准备环境和 Agent。
    if not self.config.install_only:
        await self._run()          # 委派本次任务的执行；普通路径还会进行评测。
finally:
    await self._finalize()         # 收尾、保存结果、发出结束事件。
    self._close_logger_handler()
return self.result
```

本轮选择普通 SingleStepTrial：基类 run 不变，self._run 对应 SingleStepTrial._run。single-step 指任务没有单独配置多个工作步骤，不表示 Agent 只能调用一次模型。

| 本函数中的入口 | 先知道它做什么 | 后续回到哪里 |
| --- | --- | --- |
| _prepare | 准备运行环境、检查环境并准备 Agent | 回到 install_only 判断和 _run 调用 |
| _run | 普通实现组织 Agent、产物及 Verifier | 返回 run，进入 finally |
| _finalize | 停止环境、写入结束时间/结果文件、发出 END | 关闭日志处理器，再返回 self.result |

先停在三段交接。_prepare、_run、_finalize 的详细卡片待实际进入时再建，当前不创建未读函数卡。

## 我的直接表述（原话）

> 那么现在step011就是在讲述
> 这里的这个run round里面的部分内容对吧
> 那么现在开始吧

助手校准：这是 _run_round 下游 Job 所调度的 Trial 生命周期，不是 _run_round 函数本体。尚无对 Trial.run 内部职责的独立复述。

## 尚不清楚

- 环境与 Agent 各自在 _prepare 的什么位置准备，下一处再看。
- 工作与 Verifier 的具体组织，以及 Dressage 事件回调如何参与，后续逐段读。
- 失败恢复与取消传播当前不深入。_init_result/START 在 try 之前，不应泛化为函数内任何错误都一定经过本 finally。

<details>
<summary>完整函数与来源</summary>

Harbor 0.18.0，对应固定提交 527d50deb63a5d279e8c20593c18a2cbc7f61f9e；2026-11-10 从官方固定版本源码核对，项目采用 [Apache-2.0 许可](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/LICENSE)。以下保留原函数。旧 scope 的 run 行号为 345，本轮校正为 322。

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
        await self._recover_outputs()
        await self._emit(TrialEvent.CANCEL)
        raise
    except Exception as exc:
        self.logger.debug(f"Trial {self.config.trial_name} failed: {exc}")
        self._record_exception(exc)
        await self._recover_outputs()
    finally:
        await self._finalize()
        self._close_logger_handler()
    return self.result
```

_prepare:352、_finalize:359；普通执行体见 single_step.py:34。仅静态阅读，无 Harbor Job、模型、环境创建或训练运行。

形成过程：[Step 011](../../../../../../../../04-flow.md#start-step011)。

</details>
