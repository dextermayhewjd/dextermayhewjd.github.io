# SandboxFleet.__init__

[SandboxFleet 类卡](../../../../../classes/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.md#current-methods) · [返回 main](../../examples/run_swebench_fleet.py/main.md) · [本轮讨论](../../../../../../04-flow.md#fleet-init-method-separated)

- 源码定位：[fleet.py:139](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L139)。
- 首次接触：Step 000，2026-11-04，用户明确要求查看初始化过程。
- 最近认识更新：本轮确定阅读问题；以下为助手核对的模型，尚待用户反馈。

- 本次调取：2026-11-04 按用户确认从备用区移入本步 02/functions；沿用首次接触、原话与未知，不据迁移更新个人掌握状态。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：调用方构造 SandboxFleet 时，Python 对新实例执行初始化。
2. **具体内容**：建立该实例使用的配置、运行标识、集群客户端、放置策略和管理状态。
3. **建议构建的心智模型**：

   > 先得到一个能够管理集群、记录任务和环境状态的 Python 对象。它的任务、计划和领取记录从空状态开始，实际的预热准备由后续 setup 发起。

4. **调用代码**：main:84 的实际语句；config 是调用方已准备的 FleetConfig，registry 未显式传入。

   ```python
   fleet = SandboxFleet(config)
   ```

## 本场景的输入与输出

### 1. 输入

| 输入 | 本轮场景 |
| --- | --- |
| self | Python 新创建的 SandboxFleet 实例 |
| config | main 传入的配置对象，包含目标集群和运行设置 |
| registry | 未传入，取默认值 None；由本函数建立集群注册表 |

### 2. 初始化后得到什么

1. self.config 是输入配置的副本；随后写入运行标识相关设置。
2. self.registry 保存集群及其客户端，self.placement 保存放置策略。
3. tasks=[]、plan_=None、_handles=[]、_warmed={}；其余字段见类卡。
4. __init__ 本身隐式返回 None；外部的 SandboxFleet(...) 表达式得到初始化后的实例，并赋给 fleet。

默认构造路径会读取 Kubernetes 客户端配置并建立客户端对象；本次构造没有发起 Sandbox、预热池或 Pod 的创建。创建该对象本身也没有登记本批任务。

<a id="init-actions"></a>

### 3. 初始化按什么顺序执行

1. **复制配置（143–145）**：从传入的 config 取得配置，深复制到 self.config。后续修改本对象的配置，不直接改调用方的原配置。
2. **确定本次运行的标识与命名（149–156）**：取得或生成 run_id，写入资源标签，并通过 apply_run_isolation 调整配置中的名称。这一步处理的是配置，还没有创建 namespace。
3. **初始化清理记录和同步工具（157–171）**：建立 namespace 记录、退出处理状态和锁，供后续方法登记、同步和清理使用。这里的 _atexit_registered 为 False，还没有注册退出清理。
4. **取得集群注册表和客户端（176–199）**：有外部 registry 就使用它；当前 main 没传，因此调用 _default_registry。随后向相关客户端配置同步标签，并按隔离配置处理 namespace 名称。客户端供后续请求 Kubernetes 使用，此处没有创建沙箱环境。
5. **选择放置策略并初始化业务状态（200–219）**：get_placement 选择后续规划使用的策略；tasks、plan_、_handles、_warmed 等初始化为空状态，并建立相应计数和锁。选择策略不等于已经生成资源计划。
6. **建立运行观察与报告状态（220–223）**：创建 Observer，将 report 设为 None；若配置开启 tracing，再设置追踪支持。此时还没有任务执行结果或完成的报告。

<details>
<summary>对应的核心片段（教学裁剪）</summary>

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

</details>

<a id="config-initialization"></a>

### 4. 当前具体回查：配置怎样进入对象

以下为 fleet.py:143–145 的原始语句：

```python
src = config or FleetConfig()
self.config = (src.model_copy(deep=True) if hasattr(src, "model_copy")
               else src.copy(deep=True))
```

当前进一步回查构造入口的配置初始化（fleet.py:139–156）：

1. main 的 config 传入构造函数的同名形参；registry 未传，使用默认值 None。self 是正在初始化的新实例。
2. src = config or FleetConfig() 在本场景选用传入的配置；self.config 通过深复制保存该配置。
3. 随后构造函数会向 self.config.labels 写入本次运行标识，并应用运行隔离的命名设置。先复制可以避免这些修改直接改变调用方传入的配置对象。
4. 构造完成后，main 中的 fleet 指向该实例，因此构造函数里的 self.config 就是外部访问的 fleet.config。

读完返回 SandboxFleet(...) 的调用处。调用方随后用 load_tasks 登记任务；在当前主线中，fleet.run 选择 run_naive，再由 run_naive 调用 [setup](../../../../../../references/reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md)。

## 我的直接表述（原话）

本轮阅读要求，节选：

> 我需要知道的是这里在一开始init的时候会执行什么
> 以及这里的setup的时候在做什么

尚无用户对初始化实现的复述；完整原话见本轮讨论。

用户随后要求按类卡与方法卡的分工整理：

> 那么按照这个方式做修改吧

这是对记录归属的确认，不代表已经掌握初始化内部机制。

## 尚不清楚

1. 配置副本、集群客户端和远端环境的区别，尚待用户结合本轮材料确认。
2. 隔离命名、放置算法、锁和 tracing 的内部机制尚未展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 主体：fleet.py:139–223；_default_registry:422；集群客户端构造：cluster.py:56。
- 完整字段清单与既有认识见类卡，不在本函数重复展开 28 个字段。
- 本次只核对静态源码，没有构造真实客户端或执行集群操作。
- 原始过程：[Step 000 · __init__ 与 setup](../../../../../../04-flow.md#fleet-init-and-setup)。

- [调取前的方法记录](../../../../../../references/history/2026-11-04-before-init-method-separation/SandboxFleet.__init__.md)与[分离前的类卡](../../../../../../references/history/2026-11-04-before-init-method-separation/SandboxFleet.md)保存原版内容。

</details>
