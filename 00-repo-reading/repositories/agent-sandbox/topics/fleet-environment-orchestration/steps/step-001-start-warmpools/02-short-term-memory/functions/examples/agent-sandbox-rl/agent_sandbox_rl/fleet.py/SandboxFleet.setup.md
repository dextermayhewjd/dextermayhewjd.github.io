# SandboxFleet.setup

[Step 001 scope](../../../../../../01-scope.md#reading-navigation) → [run_naive](../../../../../../03-long-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md) → **SandboxFleet.setup** → [start_warmpools（本次接续）](SandboxFleet.start_warmpools.md)

- 源码定位：[fleet.py:1403](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1403)。
- 首次接触：Step 000，2026-11-04，用户明确要求查看 setup 的工作。
- 最近认识更新：Step 001，2026-11-04，用户按 hooks、preflight、plan、start_warmpools 复述 setup；明确不清楚 plan 是否属于策略，清理触发与预热条件仍需校准。

- 本次调取：Step 001 按用户要求先看调用方 setup，复制自 [Step 000 的已有记录](../../../../../../../step-000-warmpool-reconcile/references/reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md)。首次接触、原话与未知保留；本轮新增表述见下方原话区。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：run_naive 在调用执行器之前，先对同一个 fleet 调用 setup。
2. **具体内容**：组织运行前检查、资源规划、可选的镜像预拉取，以及预热池准备和就绪等待。
3. **建议构建的心智模型**：

   > setup 使用已有配置和任务，推进真实的环境准备。正常返回时仍是同一个 fleet 对象，后续执行器再为具体任务领取环境。

4. **调用代码**：来自 run_naive 的当前两次交接。

   ```python
   fleet.setup()
   return executor(fleet, fleet.tasks, process_fn, concurrency)
   ```

## 本场景的输入与输出

### 1. 输入

当前采用首次运行、自建预热池的正常路径，adopt_existing=False。

| 输入 | 本轮场景 |
| --- | --- |
| self | 已初始化的 fleet；tasks 中已有本批任务，尚未为任务领取 handle |
| prepull | False；本次不先做独立的镜像预拉取 |
| create_budget | None；继续沿用配置里的预热创建预算 |

相关配置 install_teardown_hooks 默认是 True，因此当前默认路径会执行下面的 [1]。prepull 默认是 False，因此 [5] 的分支会跳过。

外层 SandboxFleet.run 可能已经调用过 plan；setup 仍会调用 plan。不能据此假定每次进入 setup 时 plan_ 都为 None。

本例的 tasks 已由 main 里的 fleet.load_tasks(SweBenchSource(...)) 提前加载。setup 使用已有任务规划环境，不在这里创建 Source 或调用 source.load()。

### 2. 正常返回后得到什么

1. 已完成本轮检查与规划，plan_ 保存资源安排。
2. 已经通过下游接口准备模板、预热池，并等待本场景所需的就绪条件；_warmed 等本地记录随准备过程更新。
3. 返回值是 self，仍为同一个管理对象。run_naive 没有接住这个返回值，而是继续使用原来的 fleet。
4. 此方法没有为各任务领取 handle，也没有运行 process_fn；这些交接属于后面的执行器。

<a id="setup-current-flow"></a>
<a id="setup-numbered-flow"></a>

### 3. setup 完整源码：按执行顺序逐段对照

这里保留函数签名和全部执行语句，仅替换注释并增加空行。代码与下方说明统一使用 [1]–[7]；这些编号是本函数内部的七段，不是七个必须深入的子函数。当前从 run_naive 的 setup() 进入，prepull=False。

```python
def setup(self, prepull: bool = False,
          create_budget: int | None = None) -> "SandboxFleet":
    # [1] register exit cleanup
    if self.config.install_teardown_hooks:
        self._install_teardown_hooks()

    # [2] reset state for this run
    self._torndown = False
    self._deleted_namespaces.clear()
    with self._lock:
        self._claims_reserved = 0

    # [3] check prerequisites
    self.preflight()

    # [4] plan resources
    self.plan()

    # [5] optionally pre-pull images
    if prepull and not self.prepull(wait=True):
        logger.warning("pre-pull did not finish within its budget; the warm pools "
                       "start anyway and pull what is missing")

    # [6] prepare pools and wait
    self.start_warmpools(wait=True, create_budget=create_budget)

    # [7] return the same fleet
    return self
```

1. **[1] teardown hooks（1409–1410）**：配置启用时，向 Python 进程登记退出清理回调，并尝试安装 SIGINT、SIGTERM 的处理器。这里提前安排“进程退出时怎样收尾”，不立即清理资源，也不是监听 Kubernetes 资源删除事件。
2. **[2] 重置本轮状态（1411–1416）**：把 _torndown 设为 False，清空已删除 namespace 的本地记录，在锁内将 Claim 预留计数归零。这些操作重置管理记录，不是在此处删除 namespace 或创建环境。
3. **[3] preflight（1417）**：确认运行所需的集群、资源类型和配置等条件，正常返回后继续。
4. **[4] plan（1418）**：用已有任务与配置形成资源计划，写入 self.plan_。虽然 Fleet.run 可能已经生成初始计划，这里仍会调用 plan。
5. **[5] 可选预拉取（1419–1421）**：当前 prepull=False，跳过此分支。启用时调用 self.prepull(wait=True)；若返回未完成，记录警告后仍继续预热。镜像预拉取是可选动作，不是控制 [6] 是否执行的开关。
6. **[6] start_warmpools（1422）**：将实际预热和就绪等待交给这个方法；wait=True，create_budget 沿用 setup 的参数。这是下一处要进入的调用。
7. **[7] return self（1423）**：前面的调用正常完成后，返回同一个 Fleet 对象。run_naive 没有另接一个新对象，而是继续把原来的 fleet 交给 executor。

当前默认路径执行 [1]–[4]，跳过 [5]，再执行 [6]–[7]。先沿完整顺序看一遍；下一次下钻停在 **[6] start_warmpools**，其余调用先保留接口理解。

<a id="plan-vs-strategy"></a>

#### 3.1 当前要分清：资源计划与运行策略

| 概念 | 决定什么 | 当前对应 |
| --- | --- | --- |
| plan / self.plan_ | 每个镜像放在哪个集群、使用哪个模板和池、目标备用副本数是多少 | plan 产生 FleetPlan，条目包含 cluster、image、template、pool、replicas、tasks |
| strategy | 按什么节奏准备这些环境并执行任务 | naive 先准备全批；sliding 分镜像窗口；pipelined 重叠准备与执行 |

1. 策略已由外层 Fleet.run 选中；[4] 计算资源安排，不在这里重新选择 naive 或其他策略。
2. [4] 给出计划，[6] 根据计划组织实际预热。计划存在不等于环境已经就绪；正常返回前需完成 [6] 要求的等待。

#### 3.2 辅助实现与来源：需要时再展开

<details>
<summary>[1] 中“注册”的一行源码依据</summary>

_install_teardown_hooks 在 fleet.py:367 使用：

```python
atexit.register(self._safe_teardown)
```

传入的是回调函数，登记给 Python 的退出处理机制。该辅助方法还会处理信号入口；其完整实现暂不作为新的阅读单元。

</details>

<details>
<summary>下一级源码入口与返回位置</summary>

| 调用 | 入口 | 返回后继续 |
| --- | --- | --- |
| preflight | [fleet.py:624](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L624)，经 _preflight:780 | setup:1418 的 plan |
| plan | [fleet.py:810](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L810)，经 _plan:815 | setup:1419 的可选预拉取 |
| start_warmpools | [fleet.py:1144](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1144)，经 _warm_entries 和 _warm_entry | setup:1423 返回 self |

自建池的 _warm_entry 在准备资源后调用 wait_for_pool_ready；未能在时限内就绪会抛出 FleetError。这里的“正常返回”不包含准备失败的情况。资源采用已有池、创建分批预算与各类失败处理留待对应问题。

</details>

## 我的直接表述（原话）

本轮阅读要求，节选：

> 我需要知道的是这里在一开始init的时候会执行什么
> 以及这里的setup的时候在做什么

此前关于“是否直到 executor 才真正开始执行”的疑问见 [run_naive 原话记录](../../../../../../03-long-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md)。下面保留顺序核对及随后的职责复述。

本轮用户进一步反馈：

> 好的 那么我们来看一下这里的这个sandboxfleet到底做了什么吧
> 我其实只是想要知道这里在setup的过程中到底做了什么是我会比较想要知道的
> 先注册?
> 还是做什么?
> 我不是特别理解这里的执行顺序
> 这里的1-7 在代码侧没有很好的对应起来

随后用户概括：

> 简单来说这里的内容是这个
> 这里有推出时候需要执行的部分
> 这里也有关于namespace
> 和清楚标记的部分
> 还有查看所需要的资源类型和运行配置是否是符合要求的部分
> 以及规划资源要使用什么集群预热多少副本的部分
> 也有可以选择预先拉去镜像的部分
> 也有预热池准备就绪的部分
>
> 这么看下来这里的sandboxfleet的内容还是特别的多了
>
> 那么我们返回去看一下这里的executor的部分吧

助手补充区分：第 [2] 项清空的是本地保存的已删除 namespace 记录，并非在这一行删除 namespace；清理标记也是本地状态重置。

本次在 Step 001 中明确选择先打开 setup：

> 好的那么看一下吧
> 这里我是在fleet.setup()
> 中遇到的这个fleet start warmpools对吧
> 那么我是否可以理解为这里我需要掀开一个这里的这个fleet setup
> 然后在考虑一下别的部分呢?
> 掀开第一个函数卡吧

用户确认的是先看调用方的阅读顺序；不据此认为完整准备机制已经理解。

本次用户按顺序复述并提出 plan 的疑问：

> 好的我简单理解一下这里的setup吧
> 这里的set up其实需要考虑一下teardown hooks
> 我的理解是删除的时候需要做的事情
> 这里在运行的时候初始化的时候先做这件事情其实也挺好的
> 然后考虑一下这里的preflight的内容
> (关于集群)
> 然后再看一下这里的这个plan我不知道是什么
> 人物配置的plan
> 是native 或者其他strategy的plan吗?
> 然后就是这里的start warmpools
> 我的理解应该是需要考虑加入预热的情况下的操作
>
> 我的理解准确吗?

助手的上述澄清与个人原话分开保存，尚未收到用户对 plan/strategy 区别的新确认。

本次版式反馈：用户认可 preflight、plan、start_warmpools 与 return self 的逐项解释，并要求第 3 部分完整展开源码；该反馈不作为新的技术理解确认。详见 [本次重构记录](../../../../../../04-flow.md#setup-section3-unified)。

用户随后反馈并要求进入下一部分：

> 好的 我觉得这里的逻辑没有问题
> 那么我们是否考虑做下一个部分的内容呢?

这次反馈支持沿第 [6] 项继续到 start_warmpools，不据此推断每个辅助方法的内部机制均已掌握。

## 尚不清楚

1. 用户已能概括主要职责；退出回调、namespace 记录和状态重置的具体实现尚未深入阅读。
2. 副本数量怎样计算，以及模板和预热池怎样提交到 Kubernetes，尚未逐函数展开。
3. plan 的资源安排与 strategy 的执行节奏、退出清理回调与资源删除事件的区别，本次已说明，仍待反馈。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 主体：fleet.py:1403–1423；调用处：strategies.py:93–94。
- 静态回查了 preflight、plan、start_warmpools 和 _warm_entry 的交接，用于核对副作用与返回条件；不表示用户已读这些子函数。
- 没有执行集群或训练实验。
- 原始过程：[Step 000 · __init__ 与 setup](../../../../../../../step-000-warmpool-reconcile/04-flow.md#fleet-init-and-setup)。
- 本轮对应关系修订：[Step 000 · setup 的同号代码与说明](../../../../../../../step-000-warmpool-reconcile/04-flow.md#setup-numbered-code)。
- [编号前的卡片快照](../../../../../../../step-000-warmpool-reconcile/references/history/2026-11-04-setup-before-numbered-code.md)。

- [Step 001 本次打开调用方](../../../../../../04-flow.md#setup-first-card)。原 Step 000 记录和本步 03 继承快照未改。

- [第 3 部分重构前的完整卡片](../../../../../../references/history/2026-11-04-setup-before-unified-section3.md)保留此前的简版与折叠完整版；本次合并为单一源码对照。

</details>
