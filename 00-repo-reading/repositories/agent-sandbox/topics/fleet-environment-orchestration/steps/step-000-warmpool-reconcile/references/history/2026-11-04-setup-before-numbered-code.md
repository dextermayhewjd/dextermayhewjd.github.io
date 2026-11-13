> 2026-11-04：为 setup 补齐代码内编号前的快照；相对链接按归档位置调整。

# SandboxFleet.setup

[SandboxFleet 类卡](2026-11-04-SandboxFleet-before-reactivation.md#current-methods) · [前面的初始化](2026-11-04-before-init-method-separation/SandboxFleet.__init__.md) · [返回 run_naive](../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md) · [本轮讨论](../../04-flow.md#fleet-init-and-setup)

- 源码定位：[fleet.py:1403](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1403)。
- 首次接触：Step 000，2026-11-04，用户明确要求查看 setup 的工作。
- 最近认识更新：本轮确定阅读问题；以下为助手核对的模型，尚待用户反馈。

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

外层 SandboxFleet.run 可能已经调用过 plan；setup 仍会调用 plan。不能据此假定每次进入 setup 时 plan_ 都为 None。

### 2. 正常返回后得到什么

1. 已完成本轮检查与规划，plan_ 保存资源安排。
2. 已经通过下游接口准备模板、预热池，并等待本场景所需的就绪条件；_warmed 等本地记录随准备过程更新。
3. 返回值是 self，仍为同一个管理对象。run_naive 没有接住这个返回值，而是继续使用原来的 fleet。
4. 此方法没有为各任务领取 handle，也没有运行 process_fn；这些交接属于后面的执行器。

### 3. setup 的执行顺序

下面为教学裁剪：省去清理状态重置细节与日志，保留真实调用顺序和可选分支。

```python
if self.config.install_teardown_hooks:
    self._install_teardown_hooks()
...
self.preflight()
self.plan()
if prepull and not self.prepull(wait=True):
    ...  # log a warning
self.start_warmpools(wait=True, create_budget=create_budget)
return self
```

1. **按配置注册退出清理**，第 1409–1410 行。安装退出与信号处理入口，以便后续清理资源。
2. **重置本轮管理状态**，第 1411–1416 行。重置清理标记、已删除 namespace 记录与 Claim 预留计数。
3. **检查运行条件**，第 1417 行。preflight 检查集群、资源类型和运行配置；按运行隔离配置，也可能在其内部准备 namespace。
4. **规划资源**，第 1418 行。plan 根据任务涉及的镜像安排集群和预热副本数，更新 plan_。
5. **按需预拉取镜像**，第 1419–1421 行。本场景 prepull=False，跳过这一步；它与后续创建运行中的沙箱是不同动作。
6. **准备并等待预热池**，第 1422 行。start_warmpools 使用计划，通过资源接口准备模板和预热池，并以 wait=True 等待就绪。Pod 的创建、调度和启动由下游控制器及 Kubernetes 推进。
7. **返回原对象**，第 1423 行。回到 run_naive:94，下一次调用才进入 executor。

本轮先看清这几个动作各自负责什么。下一层源码入口保留在下面，暂不展开其内部算法。

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

此前关于“是否直到 executor 才真正开始执行”的疑问见 [run_naive 原话记录](../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md)；本轮尚未收到对 setup 的技术复述。

## 尚不清楚

1. 检查、规划、预热这三个动作的职责边界，尚待用户反馈。
2. 副本数量怎样计算，以及模板和预热池怎样提交到 Kubernetes，尚未逐函数展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 主体：fleet.py:1403–1423；调用处：strategies.py:93–94。
- 静态回查了 preflight、plan、start_warmpools 和 _warm_entry 的交接，用于核对副作用与返回条件；不表示用户已读这些子函数。
- 没有执行集群或训练实验。
- 原始过程：[Step 000 · __init__ 与 setup](../../04-flow.md#fleet-init-and-setup)。

</details>
