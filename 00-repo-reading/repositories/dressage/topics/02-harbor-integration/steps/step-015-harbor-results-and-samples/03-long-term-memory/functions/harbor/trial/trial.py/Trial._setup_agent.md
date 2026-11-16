# Trial._setup_agent

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../step-014-model-routing-and-api-contract/02-short-term-memory/functions/harbor/trial/trial.py/Trial._setup_agent.md) 完整继承；不改变原认识时间或掌握状态。

- 源码：[trial.py:1880–1894](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L1880)，Harbor v0.25.0，固定提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独展开：Step 014，2026-11-13。
- 最近认识更新：2026-11-13，用户已确认这里委派 Agent 的 setup；下一层继续看实际实现。

[Trial._prepare 的调用处](Trial._prepare.md#prepare-agent-call) → **当前 _setup_agent** → [BaseInstalledAgent.setup](../../agents/installed/base.py/BaseInstalledAgent.setup.md#installed-agent-setup-mainline)→ 返回 _prepare。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：环境已准备好，需要让已选 Agent 完成自身运行准备。
2. **具体内容**：给准备期间的环境命令补入变量，限时等待 Agent.setup，并记录准备耗时与日志。
3. **建议构建的心智模型**：

   > Trial 组织准备过程，具体 Agent 决定需要准备什么。

4. **调用代码**（_prepare:649–654，保留当前 user_agent=None 分支）：

   ```python
   with self.agent_environment.with_default_user(self.task.config.agent.user):
       await self._setup_agent()  # 用配置的默认用户进入准备过程。
   ```

## 本场景的输入与输出

已有 `self.agent`（选定的 Agent）和 `self.agent_environment`（前一步准备的同一个环境）。本函数无额外参数；正常返回 None，并更新 `self.result.agent_setup` 的开始/结束时间。

<a id="setup-agent-mainline"></a>

正常路径裁剪：先看实际委派，外围日志、计时与超时异常转换在下方完整源码中保留。

```python
# 准备期间，环境执行的命令临时带上 Agent 的附加环境变量。
with self.agent_environment.scoped_exec_env(self.agent.extra_env):
    await asyncio.wait_for(
        self.agent.setup(environment=self.agent_environment),  # 具体准备由这个 Agent 完成。
        timeout=self._agent_setup_timeout_sec,                 # 限制准备阶段的等待时间。
    )
```

返回 [Trial._prepare](Trial._prepare.md#prepare-agent-call) 后退出默认用户上下文，再记录 stream 访问资料与 Agent 信息。此处尚未调用 Agent.run；实际准备步骤进入 [BaseInstalledAgent.setup](../../agents/installed/base.py/BaseInstalledAgent.setup.md#installed-agent-setup-mainline) 查看。

<details>
<summary>完整函数：日志、计时和超时转换</summary>

```python
async def _setup_agent(self) -> None:
    self.result.agent_setup = TimingInfo(started_at=self._now())
    try:
        with self.agent_environment.scoped_exec_env(self.agent.extra_env):
            with self._log_context("agent_setup", self.agent_environment):
                await asyncio.wait_for(
                    self.agent.setup(environment=self.agent_environment),
                    timeout=self._agent_setup_timeout_sec,
                )
    except asyncio.TimeoutError as exc:
        raise AgentSetupTimeoutError(
            f"Agent setup timed out after {self._agent_setup_timeout_sec} seconds"
        ) from exc
    finally:
        self.result.agent_setup.finished_at = self._now()
```

</details>

## 我的直接表述（原话）

> 好的 那么看一下这里的这个step014吧

本轮职责复述：

> 这里是调用了agent 的setup这个function?
> 是我的理解

这一委派关系与源码一致；当前沿此前 claude-code 示例进入其继承的 BaseInstalledAgent.setup。

## 尚不清楚

- 已定位 claude-code 继承的 [BaseInstalledAgent.setup](../../agents/installed/base.py/BaseInstalledAgent.setup.md)；内部准备步骤继续在子卡阅读。
- 命令环境变量与日志上下文内部暂缓；具体沙箱后端仍未验证。

<details>
<summary>来源与验证</summary>

- 本地 `git show v0.25.0:src/harbor/trial/trial.py` 核对主函数及 _prepare 调用位置。
- `BaseEnvironment.scoped_exec_env` 为本环境当前上下文内的 exec 命令叠加环境变量，退出后恢复；此处不展开 ContextVar 实现。
- 当前按环境接口可用的假设继续阅读；尚未执行安装、运行模型或验证 Agent Sandbox 适配。
- [Step 014 开始记录](../../../../../../step-014-model-routing-and-api-contract/04-flow.md#step014-start)。

</details>
