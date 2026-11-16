# BaseInstalledAgent.setup

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../../step-014-model-routing-and-api-contract/02-short-term-memory/functions/harbor/agents/installed/base.py/BaseInstalledAgent.setup.md) 完整继承；不改变原认识时间或掌握状态。

- 源码：[installed/base.py:1126–1150](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/agents/installed/base.py#L1126)，Harbor v0.25.0，固定提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独展开：Step 014，2026-11-13。
- 最近认识更新：2026-11-13，用户将本函数概括为 Agent 的基本安装准备；具体 install 内部尚未展开。

[Trial._setup_agent](../../../trial/trial.py/Trial._setup_agent.md#setup-agent-mainline) → **当前 BaseInstalledAgent.setup** → self.install(environment) → 返回本函数。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Trial 把已准备的环境交给选定的 Agent。本轮沿用此前 claude-code 示例。
2. **具体内容**：准备环境中的安装目录和本地日志目录，委派具体安装，并按需查询版本。
3. **建议构建的心智模型**：

   > 父类组织共同准备步骤，具体 Agent 提供自己的 install。

4. **调用代码**（Trial._setup_agent:1885–1888）：

   ```python
   await asyncio.wait_for(
       self.agent.setup(environment=self.agent_environment),
       timeout=self._agent_setup_timeout_sec,
   )
   ```

## 本场景的输入与输出

`ClaudeCode` 继承 `BaseInstalledAgent`，没有重写 setup，所以调用来到这里；函数中的 `self` 仍是那个 ClaudeCode 实例。输入 `environment` 是上层传来的同一个环境。正常返回 None，产生目录/安装等副作用，并可能更新 `self._version`。

<a id="installed-agent-setup-mainline"></a>

主干节选：异常转换与版本探测折叠保留。

```python
async def setup(self, environment: BaseEnvironment) -> None:
    # 在目标环境里确保 /installed-agent 目录存在，以 root 执行。
    await environment.exec(
        command="[ -d /installed-agent ] || mkdir -p /installed-agent",
        user="root",
    )

    # 在运行 Harbor 的本地准备日志目录；不是上面的环境目录。
    setup_dir = self.logs_dir / "setup"
    setup_dir.mkdir(parents=True, exist_ok=True)

    await self.install(environment)  # 本例委派 ClaudeCode.install；内部下一层再读。
    # 原码随后：若尚无版本记录，尝试查询版本并保存到 self._version。
```

正常结束后返回 [Trial._setup_agent](../../../trial/trial.py/Trial._setup_agent.md#setup-agent-mainline) 的等待处，再由它补结束时间、返回 Trial._prepare。本轮先停在具体 install 的调用边界。

<details>
<summary>完整函数：异常转换与版本探测</summary>

```python
@override
async def setup(self, environment: BaseEnvironment) -> None:
    await environment.exec(
        command="[ -d /installed-agent ] || mkdir -p /installed-agent",
        user="root",
    )

    setup_dir = self.logs_dir / "setup"
    setup_dir.mkdir(parents=True, exist_ok=True)

    try:
        await self.install(environment)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Agent install failed: {exc}") from exc

    if self._version is None:
        version_cmd = self.get_version_command()
        if version_cmd:
            try:
                version_result = await environment.exec(command=version_cmd)
                if version_result.return_code == 0 and version_result.stdout:
                    self._version = self.parse_version(version_result.stdout)
            except Exception:
                pass  # Version detection is best-effort
```

</details>

## 我的直接表述（原话）

用户确认继续看 setup 做什么：

> 那么需要接下去序曲看这个setup具体要做什么吗?

本轮职责复述：

> 基本上就是安装agent的理解内容是我的理解?
> 完成对于一个agent最基本的安装?
> 是我的理解

助手校准：可以将 setup 理解为 Agent 的基本安装准备流程；它准备目录、委派 install 并按需记录版本，具体安装动作由 install 完成。本轮仍未进入 install 内部。

## 尚不清楚

- ClaudeCode.install 如何检查已有 CLI、怎样安装或配置，下一层再看。
- 版本查询命令与容错细节按需回查；实际运行与后端适配仍未验证。

<details>
<summary>来源与验证</summary>

- 本地 `git show v0.25.0` 核对 BaseInstalledAgent.setup 与 ClaudeCode 的继承关系；ClaudeCode 未定义 setup，其 install 由该类提供。
- claude-code 场景沿用 [Step 012 的 Trial.__init__ 记录](../../../../../../../step-012-task-agent-verifier/02-short-term-memory/functions/harbor/trial/trial.py/Trial.__init__.md)，不表示真实任务已启动。
- 代码节选保留原接口和实际语句；没有执行目录创建、安装或版本命令。
- [Step 014 本次接续](../../../../../../../step-014-model-routing-and-api-contract/04-flow.md#base-installed-agent-setup-entry)。

</details>
