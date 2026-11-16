# Trial._prepare（Harbor）

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../step-014-model-routing-and-api-contract/02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md) 完整继承；不改变原认识时间或掌握状态。

- Step 014 调取：2026-11-13，从 [Step 013 完整记录](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md) 调取；下方历史原话与认识时间保留。本步从第 652 行进入 _setup_agent。

- 本步调取：2026-11-13，从 [Step 013 前序快照](../../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md) 完整调入；保留 Step 011 的原话、认识时间与未知。本步先接环境启动，现继续健康检查的调用位置。

- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

- 源码：[src/harbor/trial/trial.py:641–658](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L641)，Harbor v0.25.0，提交 fdba28fc411e47e8765420a1a063b4918fce3def。
- 首次单独展开：Step 011，2026-11-11。
- 本轮范围：沿此前普通 Trial 场景，user_agent=None；先看准备阶段的编排，不展开环境后端或各类 Agent 的安装实现。

[Trial.run 的准备阶段](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#prepare-call) → **Trial._prepare** · [本步导航](../../../../../../step-013-harbor-kubernetes-environment/01-scope.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Trial.run 已初始化本次结果并发出 START，需要先把运行环境和 Agent 准备好，再进入任务执行。
2. **具体内容**：检查准备前提，启动环境、做健康检查并按需上传 skills；准备选定的 Agent，最后记录流访问资料和 Agent 信息。
3. **建议构建的心智模型**：

   > 把这一次尝试需要的环境和 Agent 准备好，让 Trial.run 可以继续安排任务执行。

4. **调用代码**（Trial.run:606–609）：

   ```python
   await self._prepare()  # 准备环境与 Agent，正常返回 None。
   if not self.config.install_only:
       # 后续执行：运行 Agent → 上传日志、收集产物 → 评测。
       # 独立环境评测可先停 Agent 环境；共用环境评测后再停。
       await self._run()  # 更新 self.result，正常返回 None。
   # 随后进入 Trial.run 的 finally，调用 _finalize 收尾。
   ```

## 本场景的输入与输出

### 从 Trial.run 带进来的上下文

Trial、Agent 和环境对象已经创建，self.result 已初始化。这里实际准备运行环境；正常返回 None，随后 Trial.run 继续决定是否执行 _run。

<a id="prepare-mainline"></a>

### 准备主干：解释直接跟着代码读

普通场景节选：user_agent=None，省略对应的两个分支；其他执行顺序与 finally 保留。

```python
# 检查前提：已有错误就抛出，并确认 Agent 支持当前要求。
if self._task_trajectory_error is not None:
    raise self._task_trajectory_error
self._validate_agent_capabilities()

# 实际启动运行环境，不只是检查配置。
await self._setup_agent_environment()
try:
    await self.agent_environment.run_healthcheck()  # 健康检查正常返回。
    await self._upload_injected_skills()           # 已讨论：上传配置的技能目录。

    # Agent 已选定；按配置的用户调用它的 setup。
    # Claude/Codex 会检查已有 CLI，不满足版本要求时在环境中安装。
    with self.agent_environment.with_default_user(self.task.config.agent.user):
        await self._setup_agent()
finally:
    # 若启用了环境 stream，保存访问资料用于排查。
    self._write_stream_handle()

self.result.agent_info = self.agent.to_agent_info()  # 记录准备后的 Agent 信息。
# 正常返回 None；回到 Trial.run 后才进入任务执行。
```

<a id="prepare-healthcheck-call"></a>
<a id="prepare-skills-call"></a>
<a id="prepare-agent-call"></a>

| 按需查看真实子函数 | 本轮先知道什么、返回哪里 |
| --- | --- |
| [本步 _setup_agent_environment 卡片](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/trial/trial.py/Trial._setup_agent_environment.md) | 进入环境启动流程；返回 _prepare:647，继续健康检查与 skills 上传 |
| [BaseEnvironment.run_healthcheck](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.run_healthcheck.md#healthcheck-loop) | self.agent_environment 已启动；当前沿 while True 看检查执行、结果与退出。正常返回 _prepare:648，继续 _upload_injected_skills |
| [Trial._upload_injected_skills](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/trial/trial.py/Trial._upload_injected_skills.md#upload-skills-mainline) | 健康检查已正常返回；把本地技能目录放入环境，返回后进入默认用户上下文与 _setup_agent |
| [当前：Trial._setup_agent](Trial._setup_agent.md#setup-agent-mainline) | 委派选定 Agent 的 setup；返回 _prepare 的用户上下文，接着执行 finally 和信息记录 |

技能上传的用途已讨论，当前回到默认用户上下文；下一处建议进入 _setup_agent，按既有分工属于 Step 014。准备阶段整体返回后，执行细分仍可回查 [SingleStepTrial._run](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run.md#single-step-run-mainline)；该阶段已读主干，收尾见 [Trial._finalize](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial._finalize.md)。这些执行与收尾操作不属于 _prepare 函数体，也不是当前要跳转的入口。

### Step 013 的交接记录（历史）

技能上传用途已讨论，当前回到 `_prepare:649` 的 `with_default_user(...)`：临时设置环境操作的默认用户，退出后恢复。本例 user_agent=None，随后执行 `_setup_agent()`；这是 Step 014 的建议入口，尚未开始该步。_prepare 最后还会记录 stream 访问资料与 Agent 信息，当前只认用途。


### Step 014 的当前交接

环境与技能准备完成后，当前 user_agent=None，进入 [Trial._setup_agent](Trial._setup_agent.md#setup-agent-mainline)。它正常返回后，退出默认用户上下文，继续 _write_stream_handle 与 agent_info 记录，再由 _prepare 返回 Trial.run。本轮只展开 _setup_agent。

## 我的直接表述（原话）

用户在 Trial.run 中已表示准备环境与对应 Agent 是一个阶段，本轮确认继续：

> 好的 那么 我们继续吧
> 是先看一下这里的prepare吗?
> 那么生成对应的short term函数卡片吧

本轮复述与疑问：

> 检查agent的ability
> 还有是检查这里的启动环境和检查健康
> 然后就是传入对应的skill
> 选定特定的agent
> set up agent
> 记录星系
> 感觉就是在sandbox中准备的东西?
> 还是说只是检查配置里面有没有
> 并不是在sandbox里面直接安装?

助手校准：_prepare 同时包含本地前提检查、环境启动和文件上传等实际操作；Agent 已在此前选定。对 ClaudeCode/Codex，setup 会沿 install 路径检查并按需在目标环境安装 CLI。用户是否理解这一区别尚待反馈。

## 尚不清楚

- 环境对象如何选定具体后端，以及 start 怎样真正启动沙箱，后续按需下钻。
- 已定点核对 ClaudeCode/Codex 的 setup → install 与按需安装关系；具体安装脚本、依赖及运行配置尚未系统阅读。
- 健康检查当前进入循环主体，执行与重试关系仍待用户反馈；user_agent/bridge、skills 上传和 stream 资料的内部机制，本轮只认职责。

<details>
<summary>完整函数、来源与验证</summary>

以下为 v0.25.0 发布版完整函数，保留本轮未选中的 user_agent 分支。

```python
async def _prepare(self) -> None:
    if self._task_trajectory_error is not None:
        raise self._task_trajectory_error
    self._validate_agent_capabilities()
    await self._setup_agent_environment()
    try:
        await self.agent_environment.run_healthcheck()
        await self._upload_injected_skills()
        with self.agent_environment.with_default_user(self.task.config.agent.user):
            if self.user_agent is not None:
                await self._setup_user_agent()
            await self._setup_agent()
            if self.user_agent is not None:
                await self._setup_bridge()
    finally:
        # if fails, can be used for debugging
        self._write_stream_handle()
    self.result.agent_info = self.agent.to_agent_info()
```

- 主函数与调用者通过本地 git show v0.25.0 核对；[能力检查:1752](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L1752)、[skills 上传:1818](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L1818)、[环境启动:1845](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L1845)、[stream 资料写出:1866](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L1866)、[Agent setup:1880](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L1880)用于确认被调用方法的职责。
- 安装依据：[BaseInstalledAgent.setup:1126](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/agents/installed/base.py#L1126) → [ClaudeCode.install:635](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/agents/installed/claude_code.py#L635) / [Codex.install:653](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/agents/installed/codex.py#L653)。setup 通过环境 exec 准备目录并委派 install；已有 CLI 满足要求则复用，否则执行安装。其他 Agent 的 setup 行为由具体实现决定。
- 补充边界：with_default_user 提供默认用户，具体执行命令仍可显式指定用户；环境启动在 try 前，finally 不覆盖函数内所有失败。stream 资料记录不是模型轨迹采集，准备耗时由相关 setup 包装写入现有 result。
- 未切换本地 main、运行 Job、创建环境或安装 Agent。源码职责核对不等于已完成后端适配验证。
- [本步形成过程](../../../../../../step-011-harbor-trial-lifecycle/04-flow.md#trial-prepare-reading)。

</details>
