# SandboxFleet

[返回 run_naive](../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md#fleet-object-source) · [本步 scope](../../01-scope.md) · [本轮讨论](../../04-flow.md#sandbox-fleet-shape)

## 1. 对象职责

一个 SandboxFleet 实例管理一批任务所需的沙箱环境：保存配置和运行状态，通过方法发起环境准备、领取与释放。外部变量 fleet 指向这个 Python 对象；远端 Pod 由 Kubernetes 管理。

本轮从“构造对象”和“准备环境”两个时刻看这个类，先读[当前两个方法入口](#current-methods)。下面是刚构造后部分字段的结构示意，不是可执行代码。

```text
fleet: SandboxFleet
  config     -> FleetConfig
  registry   -> ClusterRegistry
  tasks      -> []
  plan_      -> None
  _handles   -> []
  _warmed    -> {}
```

## 2. 字段总览

构造函数显式初始化 28 个实例字段。先显示当前最相关的六项，其余辅助字段按需展开；字段出现在表中不代表其使用机制已经读懂。

<a id="core-fields"></a>

### 2.1 当前先认识的六个字段

| 字段 | 保存什么 | 本轮关联 |
| --- | --- | --- |
| config | FleetConfig 配置的副本，例如集群配置、资源规格和并发设置 | [__init__](2026-11-04-before-init-method-separation/SandboxFleet.__init__.md)复制配置并应用运行设置 |
| registry | ClusterRegistry，持有要操作的集群及其客户端 | [__init__](2026-11-04-before-init-method-separation/SandboxFleet.__init__.md)接收外部注册表或建立默认注册表 |
| tasks | 本批 Task 列表，刚构造时为 [] | [run_naive](../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md)通过 fleet.tasks 交给 executor |
| plan_ | 按镜像规划的集群、模板、池名和副本数量，刚构造时为 None | [setup](../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md)调用 plan 进行规划；计算细节待后续 |
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

### 3.1 当前需要读懂的两个方法

| 顺序与入口 | 围绕什么问题读 | 先读到哪里 |
| --- | --- | --- |
| 1. [SandboxFleet.__init__](2026-11-04-before-init-method-separation/SandboxFleet.__init__.md) | 执行 SandboxFleet(config) 时，管理对象里面建立了什么？ | 看清配置、客户端和初始状态；返回对象构造处 |
| 2. [SandboxFleet.setup](../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md) | 调用 fleet.setup() 时，怎样开始准备真实环境？ | 看清检查、规划、预热与等待；返回 run_naive 的 executor 调用前 |

setup 的[同号代码与说明](../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md#setup-numbered-flow)保留回查。用户已概括其主要职责，当前返回 [run_naive 的 executor 调用](../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md#fleet-executor-handoff)。

load_tasks 先作为两者之间的衔接：它把本批任务写入 tasks。preflight、plan、start_warmpools 先在 setup 中认识职责，内部机制随具体问题再展开。

<details>
<summary>3.2 其他操作目录：本轮按需定位</summary>

下表仅用于找方法。run 会选择策略，naive 策略再调用 setup，并把逐任务执行交给 executor。

| 方法 | 作用 |
| --- | --- |
| load_tasks | 把外部任务转换并保存到 tasks |
| plan | 按镜像规划集群与预热池数量，保存到 plan_ |
| acquire | 为一条任务领取环境，返回 SandboxHandle |
| release | 释放某个已领取句柄对应的环境 |
| teardown | 清理本次运行管理的资源 |
| run | 选择并调用策略，组织整批任务 |

</details>

### 3.3 接回当前的 run_naive

1. 调用方执行 SandboxFleet(config)，通过 __init__ 初始化 fleet。
2. 调用方通过 load_tasks 登记任务。
3. 调用 fleet.run 时，方法中的 self 指向同一对象。
4. run 选择 run_naive，把 self 作为第一个参数传入。
5. run_naive 通过这个对象调用 setup。
6. setup 正常返回后，run_naive 把同一对象交给 executor；默认 executor 使用它的 acquire 和 release。

对象始终是同一个，里面的管理状态会随操作变化。例如 tasks 可以从空列表变成 [t1, t2]；环境准备之后，也不代表已经为某条任务领取了 handle。

## 4. 我的直接表述（原话）

此前用户提出的初步理解，节选如下；完整上下文保留在 [flow](../../04-flow.md#setup-before-executor)：

> 好的 我的理解是fleet是sandboxfleet
> 用来管理对象
> 简单来说就是k8s起pod什么的对吗?

用户本次明确要求：

> 好的
> 那么我们现在单独看一下这里的fleet到底长什么样子吧

用户进一步明确本轮阅读重点：

> 那么是否考虑一下在这个class这里看一下这里暂时需要看懂函数的哪些function呢?
> 我需要知道的是这里在一开始init的时候会执行什么
> 以及这里的setup的时候在做什么

用户已概括 setup 的主要职责，完整原话见 setup 卡片；初始化及各字段使用细节尚无完整复述。

## 5. 尚不清楚

1. 字段中的数据怎样随 setup、acquire 和 release 改变。
2. setup 怎样把本地配置落实为远端环境。
3. executor 怎样利用该对象及返回的 handle 组织任务。

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

</details>
