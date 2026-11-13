# SandboxFleet

[返回 main](main.md) · [本步 scope](../../../01-scope.md#current-excerpt) · [本次调取](../../../04-flow.md#sandboxfleet-class-reactivated)

- 源码定位：[fleet.py:136](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L136)。
- 首次接触：Step 000，2026-11-04，先通过 run_naive 认识此对象，随后建立类卡。
- 最近认识更新：沿用此前“管理对象”的初步表述；配置复制与对象状态为助手核对，尚待用户反馈。
- 本次调取：按用户要求从备用区移入本步 02；移动与排版不代表新的掌握。

## 1. LLM 整理：使用场合、对象职责与心智模型

1. **使用场合**：main 执行 SandboxFleet(config)，得到后续加载任务、准备及管理环境所用的对象。
2. **具体内容**：保存配置、集群客户端、任务与环境管理状态；通过方法组织准备、领取、释放和清理。当前看 __init__ 怎样建立这个管理对象：先了解初始化的完整职责，再具体理解配置复制。
3. **建议构建的心智模型**：

   > fleet 指向当前 Python 进程中的沙箱管理对象。它保存“按什么配置、管理哪些任务、环境准备到哪一步”的信息；远端 Pod 由 Kubernetes 管理。

4. **调用代码**：以下是 main:84 的真实语句。

   ```python
   fleet = SandboxFleet(config)
   ```

## 2. 本场景：输入与对象状态

输入是 main 已准备的 config；registry 未显式传入。构造完成后，表达式得到 SandboxFleet 实例，赋给 fleet；__init__ 本身返回 None。

当前配置关系：传入的 config 经深复制保存为 self.config。构造完成后，外部的 fleet.config 就是这个属性。复制使后续添加运行标签、调整命名时不直接修改调用方配置。

下面是刚构造后的部分字段，属于对象结构示意，不是可执行代码。当前没有通过此构造创建远端 Sandbox、WarmPool 或 Pod，也尚未加载本批任务。

```text
fleet: SandboxFleet
  config     -> FleetConfig
  registry   -> ClusterRegistry
  tasks      -> []
  plan_      -> None
  _handles   -> []
  _warmed    -> {}
```

构造函数显式初始化 28 个实例字段。先显示当前最相关的六项，其余辅助字段按需展开；字段出现在表中不代表其使用机制已经读懂。

<a id="core-fields"></a>

### 2.1 六个字段：当前重点看 config 与 tasks

| 字段 | 保存什么 | 本轮关联 |
| --- | --- | --- |
| config | FleetConfig 配置的副本，例如集群配置、资源规格和并发设置 | [__init__](SandboxFleet.__init__.md)复制配置并应用运行设置 |
| registry | ClusterRegistry，持有要操作的集群及其客户端 | [__init__](SandboxFleet.__init__.md)接收外部注册表或建立默认注册表 |
| tasks | 本批 Task 列表，刚构造时为 [] | [run_naive](../../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md)通过 fleet.tasks 交给 executor |
| plan_ | 按镜像规划的集群、模板、池名和副本数量，刚构造时为 None | [setup](../../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md)调用 plan 进行规划；计算细节待后续 |
| _handles | 本对象登记的已领取沙箱句柄，刚构造时为 [] | handle 用于操作某个远端环境；列表维护过程待后续 |
| _warmed | 镜像到本对象登记的预热副本数，刚构造时为 {} | setup 的预热过程会维护它；这是本地记录，不能直接当成 Kubernetes 实时 Ready 数量 |

1. config 说明准备依据。
2. tasks 说明要处理哪些任务。
3. plan_ 说明准备怎样安排资源。
4. _handles 和 _warmed 保存执行期间的管理记录。

<details>
<summary>2.2 其余 22 个实例字段：本轮仅供定位</summary>

| 字段 | 初始形态或用途 |
| --- | --- |
| run_id | 配置中的运行 ID 或生成的 ID，用于标识本次运行资源 |
| _shared_run_id | 是否由调用方提供 run_id |
| _created_namespaces | 本次创建的集群/namespace 记录，初始 set() |
| _deleted_namespaces | 清理过程中已删除的 namespace 记录，初始 set() |
| _namespaces_set_up | 已完成配置钩子的 namespace 记录，初始 set() |
| _namespaces_ensured | 是否完成 namespace 准备，初始 False |
| _ns_lock | 保护 namespace 准备与回滚过程的锁 |
| _prev_handlers | 保存被替换的信号处理器，初始 {} |
| _atexit_registered | 是否注册退出清理，初始 False |
| _torndown | 标记已进入清理流程，用于防止重复清理，初始 False |
| _teardown_lock | 保护 teardown 调用的锁 |
| _sweep_lock | 保护资源清扫与核验配合的锁 |
| placement | 根据配置选择的镜像放置策略对象 |
| _claims_reserved | 已预留的在途或持有 Claim 数量，初始 0 |
| _ondemand | acquire 过程中按需准备的集群/镜像记录，初始 set() |
| _adopted_pools | 接入已有预热池的记录，初始 set() |
| _adopted_templates | 接入已有模板的记录，初始 set() |
| _lock | 保护并发管理记录的锁 |
| _guard_active | 资源超量守护是否已运行，初始 False |
| _guard_lock | 保护守护状态的锁 |
| _obs | 按配置创建的 Observer，汇集运行观察信息 |
| report | 运行报告，初始 None |

这里只核对构造函数中直接写入 self 的字段，不把方法的局部变量或 observer 这样的计算属性重复计入。

</details>

## 3. 这个对象提供哪些操作

<a id="current-methods"></a>

### 3.1 __init__ 做什么：建立可供后续操作的管理对象

<a id="init-actions"></a>

执行 main 中的 SandboxFleet(config) 时，Python 会对新实例调用 __init__。下面按源码执行顺序说明它建立什么，对应 fleet.py:139–223；这些是构造函数内的职责段，不是额外的六个函数。

1. **复制配置（143–145）**：从传入的 config 取得配置，深复制到 self.config。后续修改本对象的配置，不直接改调用方的原配置。
2. **确定本次运行的标识与命名（149–156）**：取得或生成 run_id，写入资源标签，并通过 apply_run_isolation 调整配置中的名称。这一步处理的是配置，还没有创建 namespace。
3. **初始化清理记录和同步工具（157–171）**：建立 namespace 记录、退出处理状态和锁，供后续方法登记、同步和清理使用。这里的 _atexit_registered 为 False，还没有注册退出清理。
4. **取得集群注册表和客户端（176–199）**：有外部 registry 就使用它；当前 main 没传，因此调用 _default_registry。随后向相关客户端配置同步标签，并按隔离配置处理 namespace 名称。客户端供后续请求 Kubernetes 使用，此处没有创建沙箱环境。
5. **选择放置策略并初始化业务状态（200–219）**：get_placement 选择后续规划使用的策略；tasks、plan_、_handles、_warmed 等初始化为空状态，并建立相应计数和锁。选择策略不等于已经生成资源计划。
6. **建立运行观察与报告状态（220–223）**：创建 Observer，将 report 设为 None；若配置开启 tracing，再设置追踪支持。此时还没有任务执行结果或完成的报告。

**完成后的交接**：main 得到 fleet，里面已有配置、客户端和初始管理状态；任务、计划和已领取环境仍为空。接下来 main 才调用 load_tasks；环境准备由后续 setup 发起。

当前先把以上六项理解到职责与结果，具体源码展开仍集中在配置复制。完整调用片段和参数含义见 [__init__ 方法记录](SandboxFleet.__init__.md)。类卡保留“初始化怎样建立对象”的概览，方法卡保留实现细节；setup 的已有记录继续按需回查。

读完返回 [main 的构造调用](main.md)，不继续进入 setup。

<details>
<summary>3.2 其他操作目录：本轮按需定位</summary>

下表仅用于找方法。run 会选择策略，naive 策略再调用 setup，并把逐任务执行交给 executor。

| 方法 | 作用 |
| --- | --- |
| [setup](../../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md) | 组织环境检查、规划、预热与等待；已有记录按需回查 |
| load_tasks | 把外部任务转换并保存到 tasks |
| plan | 按镜像规划集群与预热池数量，保存到 plan_ |
| acquire | 为一条任务领取环境，返回 SandboxHandle |
| release | 释放某个已领取句柄对应的环境 |
| teardown | 清理本次运行管理的资源 |
| run | 选择并调用策略，组织整批任务 |

</details>

<details>
<summary>3.3 后续主线：同一个对象怎样继续被使用</summary>

1. 调用方执行 SandboxFleet(config)，通过 __init__ 初始化 fleet。
2. 调用方通过 load_tasks 登记任务。
3. 调用 fleet.run 时，方法中的 self 指向同一对象。
4. run 选择 run_naive，把 self 作为第一个参数传入。
5. run_naive 通过这个对象调用 setup。
6. setup 正常返回后，run_naive 把同一对象交给 executor；默认 executor 使用它的 acquire 和 release。

对象始终是同一个，里面的管理状态会随操作变化。例如 tasks 可以从空列表变成 [t1, t2]；环境准备之后，也不代表已经为某条任务领取了 handle。

</details>

## 4. 我的直接表述（原话）

此前用户提出的初步理解，节选如下；完整上下文保留在 [flow](../../../04-flow.md#setup-before-executor)：

> 好的 我的理解是fleet是sandboxfleet
> 用来管理对象
> 简单来说就是k8s起pod什么的对吗?

此前用户明确要求：

> 好的
> 那么我们现在单独看一下这里的fleet到底长什么样子吧

此前用户进一步明确当时的阅读重点：

> 那么是否考虑一下在这个class这里看一下这里暂时需要看懂函数的哪些function呢?
> 我需要知道的是这里在一开始init的时候会执行什么
> 以及这里的setup的时候在做什么

用户已概括 setup 的主要职责，完整原话见 setup 卡片；初始化及各字段使用细节尚无完整复述。

本次用户要求保存类级短期记忆：

> 那么是否考虑以下构建一个这个class的short term memory呢?

当前已讲解 config 与 self.config 的关系，尚无用户对此的新复述；不据保存请求推断已经理解。

用户随后指出类卡还需要解释初始化的行为：

> 是否应该考虑一下这个class的init是在做什么这件事情呢?

据此补充初始化的职责顺序；这些说明仍属于助手核对，不代表用户已掌握各项机制。

## 5. 尚不清楚

1. 字段中的数据怎样随 setup、acquire 和 release 改变。
2. setup 怎样把本地配置落实为远端环境。
3. executor 怎样利用该对象及返回的 handle 组织任务。
4. 当前配置复制与 self / fleet 的关系已由助手解释，仍待用户反馈。

## 6. 来源

<details>
<summary>固定源码、记录来源与核对范围</summary>

- [类定义与构造函数：fleet.py:136](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L136)。
- 字段核对范围：__init__ 的 139–223 行，28 个直接写入 self 的实例字段。
- 方法定位：load_tasks:429、plan:810、setup:1403、acquire:1426、release:1663、teardown:1835、run:2060。
- 本地仓库：/home/fredkeira/projects/agent-sandbox；固定提交 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 首次接触：Step 000 中先通过 run_naive 的参数认识该对象，2026-11-04 按用户要求建立独立类卡。
- 最近认识更新：沿用本步用户的“管理对象”初步表述；字段与方法说明为助手静态核对，尚待阅读反馈。
- 没有运行集群实验；仅按用户明确指定的范围建立 __init__ 和 setup 的方法卡，其余操作目录不表示已逐项阅读。

- [调取前的完整类卡](../2026-11-04-SandboxFleet-before-reactivation.md)保留原版式、原话、来源及当时的 init/setup 阅读安排。

</details>
