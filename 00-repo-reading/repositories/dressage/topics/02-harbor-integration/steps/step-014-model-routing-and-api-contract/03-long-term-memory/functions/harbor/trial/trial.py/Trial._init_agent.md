# Trial._init_agent

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/trial/trial.py/Trial._init_agent.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../step-012-task-agent-verifier/02-short-term-memory/functions/harbor/trial/trial.py/Trial._init_agent.md) 完整继承；复制不改变原认识时间或已掌握状态。

- 源码：[src/harbor/trial/trial.py · Trial._init_agent](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py)，Harbor v0.25.0，固定提交 fdba28fc411e47e8765420a1a063b4918fce3def。
- 首次单独展开：Step 012，2026-11-13，用户确认进入本函数。
- 最近认识更新：2026-11-13，用户已表述工厂按配置创建 Agent，并进一步明确当前只是对象初始化，不能据此认为容器内已完成安装；身份字段与具体工厂内部仍按原边界留白。

[Trial.__init__ 的组件准备](../../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/trial/trial.py/Trial.__init__.md) → **Trial._init_agent** → 返回构造器继续 _init_user_agent · [本步导航](../../../../../../step-012-task-agent-verifier/01-scope.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Trial 已保存运行安排和题目，准备日志、路径及超时等依赖，现在需要创建本次使用的主 Agent 对象。
2. **具体内容**：组合附加参数，将 config.agent 交给 AgentFactory，保存返回的对象，再设置会话和尝试身份、检查轨迹加载支持。
3. **建议构建的心智模型**：

   > 把“本次选好的 Agent 配置”交给工厂创建对象，保存为 self.agent，再把对象与这次尝试关联起来。

4. **调用代码**（Trial.__init__ 中的连续位置）：

   ```python
   self._init_agent()              # 当前展开：创建主 Agent 对象。
   self._init_user_agent()         # 返回后继续；本例未配置模拟用户。
   self._init_agent_environment()  # 环境入口交给 Step 013。
   ```

## 本场景的输入与输出

### 带着哪些已准备好的数据进入？

沿用 hello-world 静态例子。config 是 TrialConfig，task 是已经读好的题目；父构造器还准备了本次路径、身份、logger、超时和 skills 相关状态。当前问题是：运行安排里的 Agent 选择怎样变成 self.agent？

```text
self.config.agent
├─ name: claude-code
└─ model_name: anthropic/example-model   # 示意模型名，无真实调用
self.config.trial_name                  # 此次尝试的名称
self.task                               # hello-world 题目对象
self.paths.agent_dir                    # 本次 Agent 日志的目录位置
self.logger                             # 本次日志对象
self._id                                # 父构造器生成的尝试 UUID
```

为了先看正常创建路径，本例另假定没有附加 MCP、skills 或待加载轨迹；这些是假定的输入条件，不代表所有题目的默认状态。实际函数也支持这些可选能力，位置见下方表格与完整源码。

### 核心骨架：准备参数 → 创建对象 → 设置身份

以下是教学裁剪：保留真实方法签名、工厂实参、赋值与身份设置。省略附加参数的条件分支及末尾的轨迹支持检查；原函数没有删除这些逻辑。

```python
def _init_agent(self) -> None:
    extra_kwargs: dict[str, Any] = {}
    # 原码在这里按 Oracle / MCP / skills / 已有轨迹补充附加参数。

    self.agent = AgentFactory.create_agent_from_config(
        self.config.agent,             # [1] 运行安排里选定的 Agent 与模型配置。
        logs_dir=self.paths.agent_dir, # 本次 Agent 的日志位置。
        logger=self.logger,
        **extra_kwargs,
    )                                  # [2] 工厂返回的对象保存到当前 Trial。
    self.agent.session_id = f"{self.config.trial_name}__agent"
    self.agent.context_id = self._id     # [3] 关联这次尝试的身份。
    # 原码最后调用 _validate_load_trajectory_support()，此处省略。
```

1. **准备参数**：extra_kwargs 保存按需增加的构造参数。工厂同时收到主要的 config.agent 和这些附加项。本轮先认识来源，不下钻所有 helper。
2. **创建对象**：右侧工厂返回 Agent 对象，左侧 self.agent 保存它。本例选择名为 claude-code 的实现；具体类如何查找、构造参数怎样展开，仍在工厂内部，尚未精读。task.instruction 后面在执行阶段使用，本方法的核心创建调用没有将它作为 instruction 参数传入。
3. **设置身份**：session_id 按 trial_name 拼成带 __agent 后缀的会话名；context_id 使用当前 Trial 的 UUID。它们都写在创建出的 Agent 对象上。

### 原码中其余部分各负责什么？

| 位置 | 条件与作用 | 本轮阅读深度 |
| --- | --- | --- |
| Oracle 分支 | 为该 Agent 准备 task_dir、trial_paths 和 agent_timeout_sec | 当前 claude-code 场景不进入，只认分支 |
| merge_mcp_servers | 合并题目环境与本次 Agent 配置里的 MCP 定义，非空时传入 | 按参数准备看待，合并规则暂留白 |
| skills_dir | 父构造器准备的有效 skills 目录非空时传入 | 暂不追踪技能解析与安装 |
| _resolve_load_trajectory | 确定待加载的已有轨迹，存在时追加 load_trajectory 参数 | 本例假定没有待加载轨迹；解析内部不展开 |
| _validate_load_trajectory_support | 创建后检查轨迹加载支持等条件 | 本轮不展开检查与延迟报错分支 |

### 留下什么，返回哪里？

本方法正常返回 None；主要结果是更新当前 Trial 的状态。静态示意：

```text
self: SingleStepTrial
└─ agent: 工厂创建的主 Agent 对象
   ├─ session_id: <本次 trial_name>__agent
   └─ context_id: 与 self._id 相同的 UUID
```

返回 Trial.__init__ 后继续 _init_user_agent；本例 user_agent=None，然后到 _init_agent_environment 的环境入口。这里先建立 Agent 对象；Agent 的安装、执行和模型请求沿后续生命周期继续。本轮没有实际调用这些方法。

### 对象创建与环境内安装的时间顺序

当前 _init_agent 创建 Python 侧的 Agent 对象并保存配置、关联身份。它不代表目标容器里的 Agent CLI 已经安装完成。后面的环境准备由运行生命周期组织：

```text
Trial.__init__
  → _init_agent                    创建 Agent 对象（当前）
  → _init_agent_environment        创建环境对象的入口

后面队列调用 trial.run()
  → _prepare
      → _setup_agent_environment   启动并准备运行环境
      → _setup_agent
          → agent.setup(environment=...)  在环境中准备 Agent
```

上图按真实调用分段示意；初始化与 run 是不同阶段。对于当前关注的已安装型 CLI Agent，需要的安装或复用检查在其 setup 路径处理；镜像也可能预装 CLI，所以不能从当前对象初始化推断环境里一定有或一定没有它。具体安装实现仍按 Step 011 已有材料回查，不另建 helper 卡。

## 我的直接表述（原话）

用户在确认下一入口后要求：

> 好的 那么 我们来看一下这里的这个init agent 具体是什么样子的吧

用户随后表述：

> 好的 我简单理解一下
> 这里这个agent factory通过这里的config来生成需要的agent？
> 是我的理解
> 这里的mode 是factorymode
> 然后生成了这里的这个agent
> 是我的理解
> 还有什么需要做的或者我理解的吗？

用户已说清工厂根据配置创建 Agent 的主线。助手补充：这里可称工厂模式（factory pattern），是集中处理对象选择与创建的设计方式；本调用传的是 self.config.agent。Trial._init_agent 还负责将返回对象保存为 self.agent、写入 session_id/context_id，本方法正常返回 None。后两项用途尚未由用户独立复述，不代填为已掌握。


用户进一步确认对象与安装的边界：

> 但是这里应该不是完整的直接在容器里面已经安装好了这个agent吧？
> 只是吧需要的agent给初始化
> 我理解目前只是对象 不是别的内容

用户已明确当前是 Agent 对象初始化。助手核对后续 Trial._prepare → _setup_agent → agent.setup 的调用位置，并补充 CLI 是否已预装取决于环境，当前创建调用不证明安装状态。

## 尚不清楚

- AgentFactory 怎样按 name 或其他配置选择具体类并展开构造参数，当前保留工厂边界。
- MCP 合并、skills 目录准备及轨迹恢复的具体机制，当前只定位它们对参数的影响。
- Agent 安装、实际执行与模型调用，留在各自后续运行位置。

<details>
<summary>完整源码、来源与验证边界</summary>

当前方法依据官方固定提交读取，下面保留本方法完整源码，便于回查裁剪处：

```python
def _init_agent(self) -> None:
    extra_kwargs: dict[str, Any] = {}
    if self.config.agent.name == AgentName.ORACLE.value:
        extra_kwargs = {
            "task_dir": self.task.task_dir,
            "trial_paths": self.paths,
            "agent_timeout_sec": self._agent_timeout_sec,
        }
    mcp_servers = merge_mcp_servers(
        self.task.config.environment.mcp_servers, self.config.agent.mcp_servers
    )
    if mcp_servers:
        extra_kwargs["mcp_servers"] = mcp_servers
    if self._effective_skills_dir:
        extra_kwargs["skills_dir"] = self._effective_skills_dir
    self._resolve_load_trajectory()
    if self._load_trajectory is not None:
        extra_kwargs["load_trajectory"] = str(self._load_trajectory)
    self.agent = AgentFactory.create_agent_from_config(
        self.config.agent,
        logs_dir=self.paths.agent_dir,
        logger=self.logger,
        **extra_kwargs,
    )
    self.agent.session_id = f"{self.config.trial_name}__agent"
    self.agent.context_id = self._id
    self._validate_load_trajectory_support()
```

- [官方固定版本 trial.py](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py)：核对当前函数、父构造器及相邻的轨迹解析/检查接口。函数名与语句以此固定版本为准，网页文本行号与原文件行号不混用。
- 当前原本地 checkout 不可用；通过官方源码静态核对。示意模型名、路径占位和正常输出结构不代表实际运行。未创建真实 Agent、安装 CLI、启动环境或调用模型；工厂实现未在本轮下钻。
- 安装时序回查：[Step 011 的 Trial._prepare 卡](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md)，其中保留 BaseInstalledAgent.setup 与具体 CLI 安装入口的固定版本证据；本轮另核对了官方 trial.py 的 _setup_agent 调用位置。
- [Step 012 本次过程](../../../../../../step-012-task-agent-verifier/04-flow.md#init-agent-entry-20261113)。

</details>
