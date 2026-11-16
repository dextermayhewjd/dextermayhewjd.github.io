# SingleStepTrial._run_agent

- 源码：[single_step.py:74–86](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L74)，Harbor v0.25.0，固定提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独展开：Step 014，2026-11-13。
- 最近认识更新：2026-11-13，用户已接回 Trial.run 到 SingleStepTrial._run 的关系；本轮区分 _run_agent 与 _run_agent_phase，并查看 try/except/finally。

[Trial.run：准备之后](../trial.py/Trial.run.md#run-call) → [SingleStepTrial._run](SingleStepTrial._run.md#single-step-run-mainline) → **_run_agent** → [Trial._run_agent_phase](../trial.py/Trial._run_agent_phase.md#run-agent-phase-mainline)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：准备阶段正常结束，install_only=False，开始一次普通单步任务的 Agent 执行。
2. **具体内容**：将题目、结果对象和执行参数交给 _run_agent_phase；处理指定的执行失败，最后同步 Agent 输出。
3. **建议构建的心智模型**：

   > 单步任务提供这次执行的数据，共用执行函数负责组织 Agent 运行；回来后接好输出。

4. **调用代码**（SingleStepTrial._run:40–41）：

   ```python
   await self._run_agent()          # 当前进入。
   await self._upload_agent_logs()  # 本函数正常返回后才继续。
   ```

## 本场景的输入与输出

<a id="run-agent-origin"></a>

**忘记从哪里开始时**：TrialConfig 是一次尝试的配置；TrialQueue 先用 `Trial.create(trial_config)` 创建 Trial，再调用 `await trial.run()`。先回看 [Trial.run 的 _prepare → _run](../trial.py/Trial.run.md#run-call)，再看 [SingleStepTrial._run 的第一项 _run_agent](SingleStepTrial._run.md#single-step-run-mainline)，就回到当前函数。具体 Agent.run 还在更下一层。

Agent、环境和 self.result 已存在；题目在 self.task.instruction 中。本轮普通运行，无待载入轨迹。方法正常返回 None，执行信息沿同一个结果对象保存，并通过最后的同步步骤补充。

<a id="run-agent-mainline"></a>

完整函数，仅添加就地注释：

```python
async def _run_agent(self) -> None:
    try:  # 当前函数委派下一层执行。
        await self._run_agent_phase(
            target=self.result,               # 本次尝试已有的结果对象。
            instruction=self.task.instruction, # 交给 Agent 的题目内容。
            timeout_sec=self._agent_timeout_sec, # Agent 执行阶段的超时。
            user=self.task.config.agent.user,
            load=self._load_trajectory is not None, # 当前普通运行，为 False。
        )
    except (AgentTimeoutError, NonZeroAgentExitCodeError) as exc:
        self._record_exception(exc)  # 记录这两类执行失败。
    finally:
        await self._sync_agent_output(self.result)  # 正常或异常后都尝试取回日志、补充 AgentContext。
```

`_run_agent` 与 `_run_agent_phase` 是两个函数：当前函数用 try 委派执行、用 except 记录指定失败、用 finally 同步输出。这里还没有直接调用具体 Agent.run；下一层是 [Trial._run_agent_phase](../trial.py/Trial._run_agent_phase.md#run-agent-phase-mainline)。它正常返回后，先完成本函数的输出同步，再回到 [SingleStepTrial._run](SingleStepTrial._run.md#single-step-run-mainline) 继续日志上传。

## 我的直接表述（原话）

用户要求继续：

> 好的 那么看一下下一个部分吧 这里应该需要看一下这个run agent ?

用户回查启动来路：

> 其实我有点没明白 我知道这里是run 但是我有点忘了这里的这个run具体是在哪里开始的?
> 我知道trial这里的这个应该是有一个trial config的部分?
> 然后是需要看一下这里的这个run具体是看哪一个函数的?

上次先恢复 TrialConfig 到 Trial.run 的调用背景。本轮用户进一步表示：

> 好的
> 也就是这里的run会执行具体的这个singlestep trial run
> 是我的理解
> 那么之后我是需要看一下这里的这个run agent 也就是run agent phase?
> 那么现在我是需要看一下这里的这个try还有对应的这个finaly了吗?

助手校准：当前普通任务中，Trial.run 的 self._run 确实进入 SingleStepTrial._run；但 _run_agent 与 _run_agent_phase 不是同名或同一个函数。当前先看前者的 try/except/finally，后者是 try 中等待的下一层。

用户随后反馈并继续：

> 好的我差不多理解了
> 那么现在看一下这个run agent phase吧

## 尚不清楚

- _run_agent_phase 现已进入，具体交接与执行边界在子卡继续；实际 Agent.run 尚未展开。
- 输出同步的内部转换和日志传输暂不展开；具体 Agent.install 也未逐段读，先沿执行主线继续。

<details>
<summary>来源与验证</summary>

- 本地 `git show v0.25.0` 核对 TrialQueue._execute_trial_with_retries（queue.py:201–203）的创建/启动位置、Trial.run:606–609、SingleStepTrial._run:37–54、当前方法及 Trial._run_agent_phase:700。
- `_sync_agent_output:1167` 取回 Agent 日志、填充 AgentContext，并按需从轨迹补 model_usage；本卡只核对用途，不另建同步函数卡。
- 这里只显式捕获 AgentTimeoutError 与 NonZeroAgentExitCodeError；其他异常也会先经过 finally，再向上传播。正常返回 None 不代表任务答对。
- 没有执行 Agent、模型或沙箱；[本轮记录](../../../../../04-flow.md#run-agent-entry-restored-scope)。

</details>
