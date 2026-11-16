# Trial._run_agent_phase

- 源码：[trial.py:700–785](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L700)，Harbor v0.25.0，固定提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独展开：Step 014，2026-11-13。
- 最近认识更新：2026-11-13，用户追问 AGENT_START 的作用及其与 run 参数交接的区别；本轮补充说明，理解仍待反馈。

[SingleStepTrial._run_agent 的 try](../single_step.py/SingleStepTrial._run_agent.md#run-agent-mainline) → **当前 _run_agent_phase** → [ClaudeCode.run](../../agents/installed/claude_code.py/ClaudeCode.run.md#claude-run-mainline) → 返回本函数 → 外层 _run_agent 同步输出。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：单步任务已把题目、结果对象和执行要求交过来，需要组织一次 Agent 执行。
2. **具体内容**：创建执行记录，安排执行期间的环境与同步，限时调用 Agent，最后记录结束并触发回调。
3. **建议构建的心智模型**：

   > 把题目、环境和结果记录交给 Agent.run，并管理这段执行的开始与结束。

4. **调用代码**（SingleStepTrial._run_agent:76–82）：

   ```python
   await self._run_agent_phase(
       target=self.result,
       instruction=self.task.instruction,
       timeout_sec=self._agent_timeout_sec,
       user=self.task.config.agent.user,
       load=self._load_trajectory is not None,
   )
   ```

## 本场景的输入与输出

沿用普通单步任务：`target` 是现有 TrialResult，`instruction` 是题目文本，`timeout_sec/user` 是执行要求；`step_cfg=None`、`resume=False`、`load=False`、`self.user_agent=None`。Agent 和环境都已存在。

<a id="run-agent-phase-mainline"></a>

### 1. 建立本次执行记录

```python
# AGENT_START 是事件类型；_emit 依次等待对应回调，为执行前的接入工作留入口。
await self._emit(TrialEvent.AGENT_START)  # 此处通知生命周期；下面的 run 才接收题目执行。
target.agent_result = AgentContext()     # 供 Agent 填写执行信息的记录对象。
target.agent_execution = TimingInfo(started_at=self._now())

running_agent = self.agent               # 本轮使用已选定的主 Agent。
exec_env = self.agent.extra_env          # 执行期间叠加给环境命令的变量。
```

这个事件的 Dressage 处理入口见 [_on_agent_start](../../../dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_agent_start.md#agent-start-mainline)。

`_emit` 把任务名、config、result、lock 等组成事件交给已登记的 hook；instruction/environment/context 的执行交接在下面的 run。现有 Dressage 的对应回调用 open_turn 为本轮交互准备 turn，跨版本组合仍未运行验证。

### 2. 把题目、环境与记录交给 Agent · 当前重点

正常分支节选：默认用户、网络策略、命令变量、日志与 sync_trajectory 的包裹代码在下方完整源码中保留；load/resume/user-agent 分支本轮不走。

```python
run = running_agent.run  # 本轮普通执行；这里只取得方法，还没有运行。

await asyncio.wait_for(
    run(
        instruction=instruction,            # 题目：要完成什么。
        environment=self.agent_environment, # 环境：在哪里执行命令、读写文件。
        context=target.agent_result,        # 执行信息容器；本例由后续日志解析补充。
    ),
    timeout=timeout_sec,                     # 限制本次 Agent 执行的等待时间。
)
```

Agent.run 的接口返回 None，AgentContext 用于承载执行信息。本例 [ClaudeCode.run](../../agents/installed/claude_code.py/ClaudeCode.run.md#claude-run-mainline) 不在函数体内直接填写 context，外层输出同步会尝试从日志补充。本函数没有用 `result = await run(...)` 接另一份结果。

<a id="run-agent-phase-finish"></a>

### 3. 执行段结束，回到调用方

以下位于执行段的 finally；当前没有 user-agent bridge，省略对应关闭分支。

```python
target.agent_execution.finished_at = self._now()
await self._emit(TrialEvent.AGENT_END)  # 调用已登记的结束回调。
```

一次模型 HTTP 响应返回后，CLI 可能继续调用工具或模型；要等整个 ClaudeCode.run 结束，才到这里的正常结束路径。AGENT_START 已经在运行前读过，本轮从等待 run 完成的位置接回即可。

AGENT_END 登记的 Dressage._on_agent_end 在正常路径中委派 _quiesce：停止本轮接收新请求，等待在途请求收尾、清掉当前 turn，让路由回到 READY。本轮只认这项收尾职责，不继续拆回调或调度内部。

本函数正常返回 None；外层 [SingleStepTrial._run_agent](../single_step.py/SingleStepTrial._run_agent.md#run-agent-mainline) 随后在自己的 finally 中执行 `_sync_agent_output(self.result)`。两层 finally 各有职责：这里记录执行结束，外层同步输出。

随后回到 [SingleStepTrial._run](../single_step.py/SingleStepTrial._run.md#single-step-run-mainline)，下一行是 `_upload_agent_logs()`，再到产物与评测，属于 Step 015。当前 Step 014 的接入首轮只需把这段返回接清；公共 Proxy 内部仍按共享补读单独安排。

<details>
<summary>完整函数：执行环境、网络策略、轨迹同步、其他模式与超时处理</summary>

```python
async def _run_agent_phase(
    self,
    *,
    target: TrialResult | StepResult,
    instruction: str,
    timeout_sec: float | None,
    user: str | int | None,
    step_cfg: StepConfig | None = None,
    resume: bool = False,
    load: bool = False,
) -> None:
    await self._emit(TrialEvent.AGENT_START)

    target.agent_result = AgentContext()
    target.agent_execution = TimingInfo(started_at=self._now())

    running_agent = self.agent
    exec_env = self.agent.extra_env
    if self.user_agent is not None:
        if self.bridge is None or self.config.user_agent is None:
            raise RuntimeError("User-agent trial requires an initialized bridge")

        running_agent = self.user_agent
        instruction = render_user_prompt(
            instruction,
            self.bridge.prompt(),
            template_path=self.config.user_agent.user_prompt_template_path,
            persona_path=self.config.user_agent.user_persona_path,
        )

        # ACPX launches and may restart the target from this ambient
        # environment. Apply target values last so the target always sees
        # its own resolved credentials when the two roles share a key.
        exec_env = {
            **self.user_agent.extra_env,
            **self.bridge.env(),
            **self.agent.extra_env_for_bridge(self.config.user_agent.bridge.kind),
        }

    try:
        plan = self._network_plan(step_cfg, warn_unknown_inference=True)
        step_name = step_cfg.name if step_cfg is not None else None
        with self.agent_environment.with_default_user(user):
            async with self._phase_network_policy(
                self.agent_environment,
                baseline_policy=plan.agent_env_baseline,
                phase_policy=plan.agent_phase,
            ):
                with self.agent_environment.scoped_exec_env(exec_env):
                    await self._configure_web_tools(plan.agent_phase)
                    with self._log_context(
                        "agent", self.agent_environment, step_name
                    ):
                        if load:
                            run = self.agent.load
                        elif resume:
                            run = running_agent.resume
                        else:
                            run = running_agent.run
                        from harbor.trial.sync_trajectory import sync_trajectory

                        async with sync_trajectory(
                            self.agent_environment,
                            running_agent,
                            self.paths.step_agent_dir(step_name)
                            if step_name is not None
                            else self.paths.agent_dir,
                            enabled=self.user_agent is None,
                        ):
                            await asyncio.wait_for(
                                run(
                                    instruction=instruction,
                                    environment=self.agent_environment,
                                    context=target.agent_result,
                                ),
                                timeout=timeout_sec,
                            )
    except asyncio.TimeoutError as exc:
        raise AgentTimeoutError(
            f"Agent execution timed out after {timeout_sec} seconds"
        ) from exc
    finally:
        if self.user_agent is not None:
            await self._close_bridge(user=user)
        target.agent_execution.finished_at = self._now()
        await self._emit(TrialEvent.AGENT_END)
```

- 默认用户、网络策略、命令环境变量和日志上下文作用于这次执行；sync_trajectory 包裹实际 run，具体同步机制暂缓。
- load/resume 选择不同方法，user-agent 分支还会改变运行角色和指令；本轮固定为普通主 Agent 执行。
- 执行段的超时转换为 AgentTimeoutError。其 finally 记录结束；前面的 AGENT_START 与记录初始化在 try 之外，不能泛化为所有前置异常都触发 AGENT_END。

</details>

## 我的直接表述（原话）

> 好的我差不多理解了
> 那么现在看一下这个run agent phase吧

“差不多理解”对应上一层 _run_agent；本函数的内部关系尚待反馈。

本轮追问：

> 好的 我差不多的理解是
> 使用emit部分的trial envent agent start的函数
> 这里其实我没有特别理解是在做什么?
> 这里是在给给定的instruction还有对应的环境然后和对应的context?
> 怎么有点像openai的opengym呢?
> anyway 那么这里需要看一下这里的这个run吗?
> 还是暂时不用?
> 你觉得呢?

助手区分生命周期回调与 run 的执行参数；Gym 的相似处仅是 Agent 使用环境，当前 Environment 提供命令与文件操作，不是 Gym 的 step(action) 交互接口。下一处建议 ClaudeCode.run，尚未开始该函数。

本轮回看结束段的复述：

> 好的 那么我们继续吧
> 下一个函数 我们需要看什么呢?
> 是看这个run agent phase?
> 然后看到的是这个trial event agent start的部分?
> 然后其他的内容呢?
> 选择制定的agent 还有换定变量
> 执行这里的环境变量?
> 以及对应的timeout部分
> 最后在执行以下这个结束的回调?
> 以及这里最终执行的很多部分?
> 是我的理解
> 还有什么是需要做的吗?
> 关于这个step?

助手校准：普通分支使用已选 Agent，设置执行命令的环境变量而不是“执行变量”；当前从整个 run 完成后回看 AGENT_END 与返回，不重新从 AGENT_START 展开。理解与收束状态仍待反馈。

## 尚不清楚

- 已进入 [ClaudeCode.run](../../agents/installed/claude_code.py/ClaudeCode.run.md) 查看三个参数的实际使用；具体命令执行后端仍未展开。
- _emit 的事件/回调用途已补充，完整注册链、网络策略和轨迹同步内部仍按需回查。

<details>
<summary>来源与验证</summary>

- 本地 `git show v0.25.0:src/harbor/trial/trial.py` 核对完整方法，调用方为 `single_step.py:74–86`。2026-11-14 回看 769–785 的等待与结束位置；Dressage 固定提交 plugin.py:707–715、821–845 及 gateway.py:308–350 用于核对正常 quiesce 的作用，不新建这些辅助卡。
- Harbor `_emit:590–599` 构造 TrialHookEvent 并依次 await self._hooks[event]。Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c` 的 plugin.py:408 注册 AGENT_START 回调，`_on_agent_start:694–705` 打开 turn、递增序号并设为 ACTIVE；这是两个固定版本的源码职责对照，不是运行兼容性证明。
- Harbor 的 `ClaudeCode.run` 实际定义于 installed/claude_code.py:2122–2233，本轮只定位下一入口，没有展开实现。
- `src/harbor/agents/base.py::BaseAgent.run` 明确要求把执行结果填入传入的 AgentContext；`src/harbor/models/agent/context.py` 定义用量、费用、model_usage、rollout_details 与 metadata 等可选字段。本轮只认记录职责，没有为这些类型另建卡。
- 本页为静态阅读，未运行 Agent、回调、模型或沙箱；前序环境可用仍是阅读假设。
- [Step 014 本次接续](../../../../../04-flow.md#run-agent-phase-entry)。

</details>
