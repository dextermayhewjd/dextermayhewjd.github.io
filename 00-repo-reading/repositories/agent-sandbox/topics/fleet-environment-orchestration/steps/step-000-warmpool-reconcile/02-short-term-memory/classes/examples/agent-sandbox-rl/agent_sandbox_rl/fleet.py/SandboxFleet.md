# SandboxFleet

[返回 main](../../../../../functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md) · [本步 scope](../../../../../../01-scope.md#current-excerpt) · [本次调取](../../../../../../04-flow.md#sandboxfleet-class-reactivated)

- 源码定位：[fleet.py:136](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L136)。
- 首次接触：Step 000，2026-11-04，先通过 run_naive 认识此对象，随后建立类卡。
- 最近认识更新：2026-11-04，用户初步理解为记录任务与环境的对象；“本 Fleet 的管理范围”与“整个集群”的区别仍待确认。
- 本次调取：按用户要求从备用区移入本步 02；移动与排版不代表新的掌握。

## 1. LLM 整理：使用场合、对象职责与心智模型

1. **使用场合**：main 执行 SandboxFleet(config)，得到后续加载任务、准备及管理环境所用的对象。
2. **具体内容**：保存配置、集群客户端、任务与环境管理状态；通过方法组织准备、领取、释放和清理。构造时建立初始状态，load_tasks 随后登记任务；具体初始化与加载过程分别由方法卡记录。
3. **建议构建的心智模型**：

   > fleet 指向当前 Python 进程中的沙箱管理对象。它保存“按什么配置、管理哪些任务、环境准备到哪一步”的信息；远端 Pod 由 Kubernetes 管理。

一个实例围绕交给它的任务与所管理的沙箱维护状态，可以使用多个配置集群；它不是整个集群全部任务、Pod 或应用的清单。tasks 保存任务数据，_handles 等字段记录环境管理状态，不能直接将 tasks 理解为“已经启动的任务”。除了保存状态，类的方法也会组织环境准备、领取和释放。

4. **调用代码**：以下是 main:84 的真实语句。

   ```python
   fleet = SandboxFleet(config)
   ```

## 2. 本场景：输入与对象状态

输入是 main 已准备的 config；registry 未显式传入。构造完成后，表达式得到 SandboxFleet 实例，赋给 fleet；__init__ 本身返回 None。

当前配置关系：传入的 config 经深复制保存为 self.config。构造完成后，外部的 fleet.config 就是这个属性。复制使后续添加运行标签、调整命名时不直接修改调用方配置。

<a id="config-vs-tasks"></a>

**config 与 tasks 的分工**：

1. config 是运行规则与资源配置：可使用哪些集群和 namespace、环境模板、并发预算、每个镜像池的副本上限、就绪等待时间等。它描述这次怎样管理环境，不列出具体要处理的题目。
2. tasks 是具体工作数据：每条 Task 的 id、所需 image 和 metadata。load_tasks 从来源取得这些记录，再保存到 fleet.tasks。
3. __init__ 根据 config 初始化管理对象，准备客户端、策略和空的管理记录；后续 load_tasks 才装入任务。环境规划与准备会共同使用运行配置和任务需求，初始化并不等于环境已经创建。

当前 main:79–82 明确构造 FleetConfig(clusters=clusters, max_concurrent=max_concurrent, max_warmpool_size=max_pool, window_size=window, ready_timeout=ready_timeout, template=template)；dataset、split、limit、offset 则在下一处调用中交给 SweBenchSource。以上为助手据调用现场说明，未将全部 FleetConfig 字段纳入本轮阅读。

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
| config | FleetConfig 配置的副本，例如集群配置、资源规格和并发设置 | [__init__](../../../../../functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.__init__.md)复制配置并应用运行设置 |
| registry | ClusterRegistry，持有要操作的集群及其客户端 | [__init__](../../../../../functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.__init__.md)接收外部注册表或建立默认注册表 |
| tasks | 本批 Task 列表，刚构造时为 [] | [load_tasks](../../../../../functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.load_tasks.md)写入；[run_naive](../../../../../functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md)通过 fleet.tasks 交给 executor |
| plan_ | 按镜像规划的集群、模板、池名和副本数量，刚构造时为 None | [setup](../../../../../../references/reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md)调用 plan 进行规划；计算细节待后续 |
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

### 3.1 初始化摘要与方法入口

<a id="init-actions"></a>

__init__ 根据配置建立本地管理对象所需的运行标识、集群客户端和初始状态；完成后由 main 中的 fleet 引用。字段含义与初始值见上方对象状态，任务加载和远端环境准备发生在后续调用中。

1. 构造过程回查：[SandboxFleet.__init__](../../../../../functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.__init__.md#init-actions)，查看初始化顺序、分支与副作用。
2. 初始化局部回查：[配置复制](../../../../../functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.__init__.md#config-initialization)，查看 config 怎样成为 self.config，以及为什么复制。
3. 任务加载回查：[SandboxFleet.load_tasks](../../../../../functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.load_tasks.md)，看任务列表怎样写入同一对象。
4. 当前具体阅读：[SandboxFleet.run](../../../../../functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.run.md)，看策略选择与整批运行的交接。
5. 读完返回 [main 的相应调用](../../../../../functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md)，继续沿调用方主线；setup 的已有记录按需回查。

<details>
<summary>3.2 其他操作目录：本轮按需定位</summary>

下表仅用于找方法。run 会选择策略，naive 策略再调用 setup，并把逐任务执行交给 executor。

| 方法 | 作用 |
| --- | --- |
| [setup](../../../../../../references/reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md) | 组织环境检查、规划、预热与等待；已有记录按需回查 |
| [load_tasks](../../../../../functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.load_tasks.md) | 把外部任务转换并保存到 tasks |
| plan | 按镜像规划集群与预热池数量，保存到 plan_ |
| acquire | 为一条任务领取环境，返回 SandboxHandle |
| release | 释放某个已领取句柄对应的环境 |
| teardown | 清理本次运行管理的资源 |
| [run](../../../../../functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.run.md) | 选择并调用策略，组织整批任务 |

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

此前用户提出的初步理解，节选如下；完整上下文保留在 [flow](../../../../../../04-flow.md#setup-before-executor)：

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

用户本次给出的初步理解：

> 好的我大概理解了 这里的sandboxfleet大概就是用来记录一系列的和fleet相关的
> 或者说用来记录一个集群到底有哪些人物,开启了什么人物和环境
> 这样子的一个对象?

助手按上下文将“人物”理解为“任务”，原话保留。用户已经把它联系到任务与环境记录；助手进一步澄清：其范围是本 Fleet 管理的任务与沙箱，可跨集群，不代表整个集群的全部对象；它还提供主动的管理方法。这些澄清尚未收到用户确认。完整过程见 [管理范围的澄清](../../../../../../04-flow.md#fleet-managed-scope)。

用户随后用控制角色作类比，并要求继续：

> 好的 有点类似于k8s的master node的感觉
> 那么继续吧

这个类比只适用于“统一管理”的直觉。助手澄清：Fleet 是应用侧 Python 对象，通过 Kubernetes API 管理本身负责的沙箱；它不是 Kubernetes 控制面，也不承担集群的调度与协调循环。用户要求继续，不作为该边界已经掌握的证据。

## 5. 尚不清楚

1. 字段中的数据怎样随 setup、acquire 和 release 改变。
2. setup 怎样把本地配置落实为远端环境。
3. executor 怎样利用该对象及返回的 handle 组织任务。
4. 当前配置复制与 self / fleet 的关系已由助手解释，仍待用户反馈。
5. 本 Fleet 的管理范围与整个集群的区别，以及任务数据与任务启动状态的区别，已提示但尚未确认。

## 6. 来源

<details>
<summary>固定源码、记录来源与核对范围</summary>

- [类定义与构造函数：fleet.py:136](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L136)。
- 字段核对范围：__init__ 的 139–223 行，28 个直接写入 self 的实例字段。
- 方法定位：load_tasks:429、plan:810、setup:1403、acquire:1426、release:1663、teardown:1835、run:2060。
- 本地仓库：/home/fredkeira/projects/agent-sandbox；固定提交 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 首次接触：Step 000 中先通过 run_naive 的参数认识该对象，2026-11-04 按用户要求建立独立类卡。
- 最近认识更新：2026-11-04 的任务与环境管理对象复述，详见原话区；具体字段机制与管理范围的澄清仍待反馈。
- 没有运行集群实验；已有 __init__、setup 方法记录，本次按用户要求补入 load_tasks 方法卡。其他操作目录不表示已逐项阅读。

- [调取前的完整类卡](../../../../../../references/history/2026-11-04-SandboxFleet-before-reactivation.md)保留原版式、原话、来源及当时的 init/setup 阅读安排。

</details>
