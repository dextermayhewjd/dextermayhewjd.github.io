# RL batch demand：全流程与首读入口核对

[项目入口与唯一进度](../README.md#current-reading) · [四项目标与材料范围](rl-environments-and-jd.md#learning-scope) · [本次讨论](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/04-flow.md#full-batch-entry-audit)

2026-11-04，根据用户要求对照既有 reference，重新核对 RL batch demand 的全流程。源码固定为 `37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1`，本次核对时工作区干净；下文是静态源码审阅，不是集群或训练运行结果。

## 1. 先区分整体骨架与首个深入函数

1. [剪枝方法](../../../../.agents/skills/repo-reading-scope/references/pruning-method.md)要求先定位组织当前任务的函数，提取正常主线。
2. [先核心、后补前置](../../../../.agents/skills/repo-reading-order/references/inside-out-method.md)要求在已有骨架上，按当前问题选择深入点；不能仅因某节点出现在图的前面就先读它。
3. [Coding Agent 的 Step 0 样例](../../../../.agents/skills/repo-reading-scope/references/coding-agent-scope.md)先用 generate 建立整体轮廓；后续才按具体问题选择局部调用。

因此，“先在 Fleet 层建立批次全貌”有依据；“必须先深入 LookaheadWarmer.add”不能由 reference 推出。此前从 WarmPool controller 改到 LookaheadWarmer.add，仍然过早选择了一个局部机制。

## 2. 原图合并了两种用法

RL batch demand 是图中对训练侧输入的概括，不是仓库里的一个函数名。仓库提供环境编排接口，具体训练器的取批次、Agent 循环、评分和训练消费由接入方负责。

1. **一批已有任务交给 Fleet 执行。** 调用方使用 SandboxFleet.run，Fleet 选择策略并组织预热、任务执行和清理。
2. **训练器保留自己的批次循环。** 调用方直接使用 Fleet 的资源与领取接口；需要提前为后续批次预热时，可以加用 LookaheadWarmer。

LookaheadWarmer.add 不是 SandboxFleet.run 的固定前置。原图的 SandboxFleet / LookaheadWarmer 可用于粗略定位训练侧，但需要上述用法说明，不能当成完整的实际调用链。

依据：[RL 接入文档](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/examples/rl_integration.md#L1)与 [LookaheadWarmer 的模块说明](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/lookahead.py#L14)。

## 3. 用一条真实的正常路径建立批次骨架

建议先采用一批已知任务的最小场景：strategy="naive"、recycle=False、epochs=1、keep_warm=False。环境正常准备完成，每条任务单独领取与释放。这是用来建立关系的源码基线，不是大规模训练的性能配置建议。

### 3.1 调用方交入批次

1. 训练侧提供本批任务。题目采样和每题 rollout 数量由训练侧决定。
2. 调用方通过 fleet.load_tasks 登记任务。Task 保留 id、image、metadata；题目语义由接入方解释。
3. 调用方调用 fleet.run，并提供 process_fn。run 选择 naive 策略，将工作交给 run_naive。

### 3.2 准备环境

1. run_naive 调用 fleet.setup。
2. Fleet 按镜像等信息规划资源，并检查运行条件。详细检查与规划算法第一轮折叠。
3. Fleet 通过 Resources 准备 SandboxTemplate。
4. Fleet 通过 Resources 创建或协调 SandboxWarmPool，写入备用目标。
5. WarmPool controller 根据目标协调 Sandbox CR。
6. 核心 Sandbox controller 协调 Pod 等子资源。
7. Kubernetes 调度并运行环境，状态通过相应资源被观察到；当前选择环境准备成功的正常路径。

第 4–7 项跨 Kubernetes API 与控制器事件发生，不是 Python 对 Go 函数的直接同步调用。

### 3.3 执行每条任务

run_naive 的默认 executor 是 process_parallel；它按并发设置为任务运行下列流程。

1. fleet.acquire 为当前任务申请环境。它使用 SDK 创建 Claim，并取得对应 Sandbox 的连接信息。
2. process_fn 收到 task 和 handle。
3. 接入方在 process_fn 中完成题目初始化。
4. 接入方运行 Agent 的交互循环。
5. 接入方收集结果，并按需要完成评分。
6. process_parallel 在 finally 中调用 fleet.release，释放当前任务持有的环境。
7. process_parallel 汇集各任务结果。

第 3–5 项是回调应承担的业务职责，不是本包内置的统一 Agent 或评分实现。任务之间可以并发；单个任务内部的领取、使用、释放仍保持上述关系。

### 3.4 清理与返回

1. run_naive 在 finally 中调用 fleet.teardown，清理该运行管理的剩余资源。
2. 批次结果经过 fleet.run 返回调用方。
3. 训练框架决定怎样消费结果。轨迹字段、样本过滤、分组和策略更新不由这套环境编排接口自动完成。

默认路径下，单任务 release 与整批 teardown 是不同层次的清理。keep_warm=True 等其他设置会改变整批清理时机，暂不混入本次基线。

## 4. 最适合先打开的骨架

整体入口是 [SandboxFleet.run:2060](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L2060)，naive 路径的实际编排在 [run_naive:82](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L82)。

以下为 run_naive 在 teardown=True 时的教学裁剪，省略参数。executor 的默认实现是 [process_parallel:34](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L34)。

```python
try:
    fleet.setup()          # prepare environments
    return executor(...)   # run tasks and collect results
finally:
    fleet.teardown()       # clean up before returning
```

第一轮先看清三个调用的职责，并定位 executor 中的单任务领取、回调执行与释放。达到“能把本批任务从环境准备接到结果返回”就停，不逐项下钻所有配置与辅助函数。

## 5. 持续批次预热放回哪里

1. 当问题进入“当前批次还在执行，怎样提前准备下一批”时，选择外部训练循环加 LookaheadWarmer 的用法。
2. 训练器通过 add 提供已经知道的批次需求；Warmer 据此调整需要的预热数量。
3. Warmer 调用 Fleet 的 warm_image、set_pool_replicas 或 unwarm_image，仍接入同一套 Kubernetes 资源协调。
4. 任务的领取、交互与释放继续由训练侧通过 Fleet 或相应适配层驱动，add 不执行 rollout。
5. finish 更新该批次在预热需求中的记录，不等于释放某个已领取的 Sandbox；单条任务仍要完成自己的 release。

这个机制直接服务于既定的持续训练目标，但它覆盖的是预热需求支路。应先让它接回完整任务主线，再决定是否深入其数量合并和保留策略。

<a id="strategy-comparison"></a>

## 6. 按需对照：naive 与其他策略

此处承接 run_naive 函数卡中的策略比较，供相关问题出现时回查，不增加新的阅读步骤。

1. 在学习上，可以先用 naive 看清不重叠的准备、执行、清理阶段。
2. 在当前源码中，naive、sliding、pipelined、none 都由 STRATEGIES 表按名称选择，是并列函数。
3. 没有依据把它们说成全部继承 run_naive，或据此推断仓库的历史演化顺序。

STRATEGIES 当前注册四种名称，映射到下列函数。这里比较的是同一批已知任务中镜像池的准备节奏；镜像窗口不等于训练器预测出来的新批次。

| 策略名 | 对应函数 | 最简区别 |
| --- | --- | --- |
| naive | run_naive | 先准备本批涉及的全部镜像池，再执行整批任务，最后按开关清理 |
| sliding | run_sliding | 按镜像窗口逐组准备、执行、撤下，再推进下一组 |
| pipelined | run_pipelined | 当前窗口执行时，后台提前准备下一窗口，重叠准备与执行 |
| none | run_none | 每次一个镜像、一个副本的池，按需逐组推进；仍会使用并等待这个池 |


recycle 是另一项配置：它可以替换执行器、改变任务与环境的复用关系，而不是新的预热策略。隔离、运行时和控制器优化也分别位于自己的职责层。本轮只核对这些关系，不展开它们的实现。

源码依据：固定版本 strategies.py:134、191、199、206–211，以及 fleet.py:2092–2102。

本页保留入口核对的依据。用户随后确认从 run_naive 开始，当前说明见 [Step 000 scope](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/01-scope.md)和 [run_naive 函数卡](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md)；实时进度以项目入口为准。


<a id="unique-images-and-provisioning-boundary"></a>

## 7. 每个任务独有镜像时，这套结构解决什么

用户指出：如果每个任务都需要不同镜像，单纯解释“按镜像分别建池”没有回答架构价值。这里必须区分环境供给机制与训练需求调度。

1. **当前结构主要解决已知需求的环境供给与生命周期**：Task 指明所需镜像；plan 将镜像需求和配置转成池的放置与副本目标；预热路径准备这些环境；Claim 支持领取，控制器维持备用数量，释放和 teardown 处理生命周期。
2. **start_warmpools 只组织已决定目标的提交**：读取已有计划，按目标副本数分波并等待。它不读取每道题的训练进度，也不判断某个镜像未来是否还会用到。wave 控制准备过程的集中冲击，不是下一批任务选择，也不限制最终所有池的总常驻数量。
3. **全异镜像、每题仅一次时**：不同任务不能从同一个镜像池互换环境，池化的持续供给收益减弱。当前默认 sizing 对每个只有一条任务的镜像规划一个副本。假设有 100 条这样的任务、任务并发为 10，naive 仍规划 100 个单副本池，并在执行器开始前等待整批准备完成；它不会自动只预热接下来 10 条任务。
4. **预热收益有边界**：任务领取时能减少基础环境的冷启动等待，不意味着整批总时长一定更短，也不会免除独有环境的首次创建成本。每种镜像只用一次时，为它长期维持备用数通常价值有限；领取后池控制器还可能补充再无任务使用的备用环境，直到相应池被缩减或整批清理。
5. **用户期待的是另一层决策**：根据待执行、正在执行、已结束以及未来已知批次决定哪些镜像应保留、各要多少，并受资源预算约束。这需要训练侧需求管理。sliding/pipelined 对有限已知任务提供窗口调度；LookaheadWarmer 接收训练侧显式报告的批次需求和结束事件，但不能据此称当前 naive 或 start_warmpools 已自动理解训练进度。

因此，当前阅读对象适合学习“需求目标如何落地成 Kubernetes 环境，以及如何控制创建节奏”。不能将它直接当作完整的 Agentic RL 环境需求调度器。对于同镜像持续有多次领取、同题多条 rollout 或反复批次，备用池更容易体现作用；对于全异且单次的环境，按需创建或窗口化准备可能更匹配，须结合实际负载判断。

源码依据固定在 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1：fleet.py 的 _plan:815 起与 start_warmpools:1144–1192；sizing.py 的 compute_replicas:28–55；strategies.py 的 run_naive:82–97 与窗口策略；lookahead.py 的模块说明及 add/finish。上述 100/10 是静态说明用的输入，不是真实集群实验或性能结论。
