# SandboxFleet.__init__

[SandboxFleet 类卡](SandboxFleet.md#current-methods) · [接着看 setup](../../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md) · [本轮讨论](../../../04-flow.md#fleet-init-and-setup)

- 源码定位：[fleet.py:139](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L139)。
- 首次接触：Step 000，2026-11-04，用户明确要求查看初始化过程。
- 最近认识更新：本轮确定阅读问题；以下为助手核对的模型，尚待用户反馈。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：调用方构造 SandboxFleet 时，Python 对新实例执行初始化。
2. **具体内容**：建立该实例使用的配置、运行标识、集群客户端、放置策略和管理状态。
3. **建议构建的心智模型**：

   > 先得到一个能够管理集群、记录任务和环境状态的 Python 对象。它的任务、计划和领取记录从空状态开始，实际的预热准备由后续 setup 发起。

4. **调用代码**：采用默认创建 registry 的分支，cfg 已是调用方准备的 FleetConfig。

   ```python
   fleet = SandboxFleet(config=cfg)
   ```

## 本场景的输入与输出

### 1. 输入

| 输入 | 本轮场景 |
| --- | --- |
| self | Python 新创建的 SandboxFleet 实例 |
| config | 已提供的 cfg，包含目标集群和运行设置 |
| registry | 未传入，取默认值 None；由本函数建立集群注册表 |

### 2. 初始化后得到什么

1. self.config 是输入配置的副本；随后写入运行标识相关设置。
2. self.registry 保存集群及其客户端，self.placement 保存放置策略。
3. tasks=[]、plan_=None、_handles=[]、_warmed={}；其余字段见类卡。
4. __init__ 本身隐式返回 None；外部的 SandboxFleet(...) 表达式得到初始化后的实例，并赋给 fleet。

默认构造路径会读取 Kubernetes 客户端配置并建立客户端对象；本次构造没有发起 Sandbox、预热池或 Pod 的创建。创建该对象本身也没有登记本批任务。

### 3. 初始化按什么顺序执行

1. **取得并复制配置**，第 143–145 行。未传配置时使用 FleetConfig()；复制后在 self.config 上调整。
2. **确定运行标识和命名设置**，第 149–156 行。取得或生成 run_id，添加运行标签，应用运行隔离相关的命名规则。
3. **初始化清理与同步状态**，第 157–171 行。建立 namespace 记录、退出处理状态和锁。
4. **取得集群注册表**，第 176–199 行。使用调用方提供的 registry，或经 _default_registry 建立默认注册表；向相关客户端配置同步标签与 namespace。
5. **建立放置策略和业务记录**，第 200–219 行。取得 placement，初始化任务、计划、句柄、预热记录和相应同步状态。
6. **建立观察对象**，第 220–223 行。创建 Observer，初始化 report；配置开启 tracing 时再做相应设置。

下面只摘出与当前对象模型直接相关的连续片段，其他语句用省略号标记；不是完整构造函数。

```python
src = config or FleetConfig()
self.config = (src.model_copy(deep=True) if hasattr(src, "model_copy")
               else src.copy(deep=True))
...
self.registry = (registry if registry is not None
                 else self._default_registry(self.config))
...
self.placement = get_placement(self.config.placement)
self.tasks: list[Task] = []
self.plan_: FleetPlan | None = None
self._handles: list[SandboxHandle] = []
...
self._warmed: dict[str, int] = {}
...
```

读完返回 SandboxFleet(...) 的调用处。调用方随后用 load_tasks 登记任务；在当前主线中，fleet.run 选择 run_naive，再由 run_naive 调用 [setup](../../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md)。

## 我的直接表述（原话）

本轮阅读要求，节选：

> 我需要知道的是这里在一开始init的时候会执行什么
> 以及这里的setup的时候在做什么

尚无用户对初始化实现的复述；完整原话见本轮讨论。

## 尚不清楚

1. 配置副本、集群客户端和远端环境的区别，尚待用户结合本轮材料确认。
2. 隔离命名、放置算法、锁和 tracing 的内部机制尚未展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 主体：fleet.py:139–223；_default_registry:422；集群客户端构造：cluster.py:56。
- 完整字段清单与既有认识见类卡，不在本函数重复展开 28 个字段。
- 本次只核对静态源码，没有构造真实客户端或执行集群操作。
- 原始过程：[Step 000 · __init__ 与 setup](../../../04-flow.md#fleet-init-and-setup)。

</details>
