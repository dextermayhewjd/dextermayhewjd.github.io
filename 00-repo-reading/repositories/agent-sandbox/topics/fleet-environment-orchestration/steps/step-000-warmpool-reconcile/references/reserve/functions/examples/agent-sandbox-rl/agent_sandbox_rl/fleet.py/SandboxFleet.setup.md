# SandboxFleet.setup

[SandboxFleet 类卡](../../../../../../../02-short-term-memory/classes/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.md#current-methods) · [前面的初始化](../../../../../../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.__init__.md) · [返回 run_naive](../../../../../../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md) · [本轮讨论](../../../../../../../04-flow.md#fleet-init-and-setup)

- 源码定位：[fleet.py:1403](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1403)。
- 首次接触：Step 000，2026-11-04，用户明确要求查看 setup 的工作。
- 最近认识更新：用户已概括退出处理、namespace/标记记录、条件检查、资源规划、可选预拉取和预热就绪等职责，并要求返回 executor；具体机制仍保留未知。

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

<a id="setup-numbered-flow"></a>

### 3. setup 的执行顺序：代码与说明同号对应

下面保留 setup 的函数签名和全部执行语句，仅移去原 docstring 与注释，加入 [1]–[7] 路标。下方同号说明只解释对应的一段代码。各调用正常返回后，才继续执行下一段。

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

1. **[1] 注册退出清理**：对应 _install_teardown_hooks，第 1409–1410 行。它向 Python 进程登记退出清理回调，并安装 SIGINT、SIGTERM 的处理器。这里注册的是“退出时怎样收尾”，不是向 Kubernetes 注册 Pod；登记时也不会立刻清理资源。
2. **[2] 重置本轮状态**：对应三处状态修改，第 1411–1416 行。清除“已清理”标记、清空已删除 namespace 的记录，并把 Claim 预留计数归零。这些是管理对象的本地记录。
3. **[3] 检查运行条件**：对应 preflight，第 1417 行。检查集群、资源类型和运行配置；按运行隔离配置，也可能先在其内部准备 namespace。
4. **[4] 规划资源**：对应 plan，第 1418 行。根据任务中的镜像安排集群和预热数量，将规划保存在 plan_ 中。
5. **[5] 可选预拉取**：对应 if prepull，第 1419–1421 行。当前 prepull=False，直接跳过；开启时才预拉取镜像，未在预算内完成会记录警告并继续。
6. **[6] 准备并等待预热池**：对应 start_warmpools，第 1422 行。使用计划准备模板和预热池；下游控制器及 Kubernetes 推进 Sandbox、Pod 的创建与启动；wait=True 要求本次调用等待相应就绪条件。
7. **[7] 返回同一个对象**：对应 return self，第 1423 行。setup 正常结束，回到 run_naive:94，下一次调用才进入 executor。

当前默认路径按编号看是：执行 [1]–[4]，跳过 [5]，再执行 [6]–[7]。[1]–[2] 是本地收尾安排和状态准备；本轮创建预热环境的主要交接在 [6]。

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

此前关于“是否直到 executor 才真正开始执行”的疑问见 [run_naive 原话记录](../../../../../../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md)。下面保留顺序核对及随后的职责复述。

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

## 尚不清楚

1. 用户已能概括主要职责；退出回调、namespace 记录和状态重置的具体实现尚未深入阅读。
2. 副本数量怎样计算，以及模板和预热池怎样提交到 Kubernetes，尚未逐函数展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 主体：fleet.py:1403–1423；调用处：strategies.py:93–94。
- 静态回查了 preflight、plan、start_warmpools 和 _warm_entry 的交接，用于核对副作用与返回条件；不表示用户已读这些子函数。
- 没有执行集群或训练实验。
- 原始过程：[Step 000 · __init__ 与 setup](../../../../../../../04-flow.md#fleet-init-and-setup)。
- 本轮对应关系修订：[Step 000 · setup 的同号代码与说明](../../../../../../../04-flow.md#setup-numbered-code)。
- [编号前的卡片快照](../../../../../../history/2026-11-04-setup-before-numbered-code.md)。

</details>
