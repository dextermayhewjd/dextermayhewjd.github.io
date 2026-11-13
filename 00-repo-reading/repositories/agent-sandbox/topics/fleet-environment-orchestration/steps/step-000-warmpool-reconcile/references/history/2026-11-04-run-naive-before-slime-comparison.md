# run_naive

[main](../../02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md) → [SandboxFleet.run](../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.run.md) → **run_naive（当前）** · [返回 scope](../../01-scope.md#reading-navigation)

- 源码定位：[strategies.py:82–97](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L82)。
- 首次接触：Step 000，2026-11-04，用户确认从本函数开始，后来回查 Fleet 与调用方。
- 最近认识更新：此前用户已概括 setup 的主要职责并讨论 executor；本次要求重整本函数记录，尚无对本轮完整交接的新复述。
- 本次整理：2026-11-04，按短期记忆 skill 回到既有函数卡；旧场景、原话和未知保留，排版与源码核对不视为新增掌握。

<a id="strategy-position"></a>

当前 STRATEGIES 有四项：naive、sliding、pipelined、none；名称到函数的映射及区别见[四种策略简表](../../../../../../references/rl-batch-flow-and-entry.md#strategy-comparison)。本轮只展开 naive，其他项仅用于定位。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：外层 SandboxFleet.run 选中 naive 后，传入已有任务的 Fleet、单任务回调、并发度和执行器。
2. **具体内容**：先调用 setup 准备环境，再将整批任务交给 executor；退出时根据 teardown 清理本次运行资源。
3. **建议构建的心智模型**：

   > run_naive 是“先准备这一批需要的环境，再执行这一批任务”的简单编排。具体环境操作交给 Fleet，逐任务处理交给 executor；它自身不包含解题或评分逻辑。

4. **调用代码**：以下为 Fleet.run 中的真实语句，省略中间的计划与运行上下文，当前 strategy="naive"。

   ```python
   fn = STRATEGIES[strategy]
   executor = process_parallel
   results = fn(self, process_fn, conc, teardown=not keep_warm,
                executor=executor)
   ```

## 本场景的输入与输出

### 1. 输入：承接同一次 main → Fleet.run 调用

本次沿 SWE-bench 示例的默认 naive、epochs=1、recycle=False、keep_warm=False 路径。下面的参数来自外层运行，不另构造一套任务数量。

<a id="fleet-object-source"></a>

| 参数 | 本次来自哪里、表示什么 |
| --- | --- |
| fleet | 外层 Fleet.run 的 self；其中已有 config 和经 load_tasks 保存的 tasks |
| process_fn | main 的 _record(swebench_probe) 返回的单任务回调 |
| concurrency | 外层传入的 conc；脚本默认并发度为 1，可通过配置改变 |
| teardown | not keep_warm；当前为 True |
| executor | process_parallel；当前未启用复用执行器 |

进入前，外层 run 已在需要时生成初始计划，但这不表示所有环境已经 Ready。此处仍要调用 setup，完成它自己的检查、规划、预热和等待。

### 2. 输出与副作用

1. 正常路径将 executor 的整批结果列表交回 Fleet.run，后者退出自身运行上下文后再返回 main。
2. 当前 teardown=True：run_naive 在交回结果前先尝试清理本次运行管理的资源。
3. 默认执行器按输入任务顺序保存结果；结果来自 process_fn，单任务普通异常也可能作为结果元素返回。本例的成功结果是探针记录，不是统一奖励值。

<details>
<summary>保留此前的两任务教学场景</summary>

此前用 t1、t2 都需要 image-a、concurrency=2 的假设说明本函数；那是教学构造，没有运行集群。结果写作 [result_for_t1, result_for_t2]，仅表示默认执行器保持输入顺序。该例不代表当前脚本默认一次必有两条任务，也不意味着预热副本数一定等于任务数。

</details>

### 3. 本函数的真实主体

下面只省略原 docstring 和注释，保留真实签名、参数及 try/finally 关系。

```python
def run_naive(fleet, process_fn, concurrency, *, teardown=True,
              executor=process_parallel):
  try:
    fleet.setup()
    return executor(fleet, fleet.tasks, process_fn, concurrency)
  finally:
    if teardown:
      fleet.teardown()
```

1. **准备环境（93）**：调用 fleet.setup，按本批任务和配置准备镜像池，并等待所需就绪条件；正常返回后才进入执行器。
2. **执行任务并取得结果（94）**：把同一个 Fleet、fleet.tasks、process_fn 和并发度交给 executor。当前的 process_parallel 负责逐任务领取、调用回调、释放和汇总；这里先按接口理解。
3. **退出时清理（95–97）**：进入 finally，若 teardown 为 True 就调用 fleet.teardown。它清理整批运行管理的资源，与执行器里的单任务 release 分工不同。
4. **完成返回**：虽然 return 写在 finally 前，Python 会先取得 executor 的返回值，再执行 finally；清理正常结束后才把该结果交回外层 Fleet.run。

因此，不能把第 94 行理解为“立即返回，后面的清理不执行”。若 setup 或 executor 抛出异常，finally 仍会尝试清理；清理本身也可能失败，不能据此保证每次都正常返回列表。

<a id="fleet-executor-handoff"></a>

### 4. 从这里进入哪里，读完回哪里

| 调用 | 当前只需看清 | 回到哪里 |
| --- | --- | --- |
| [fleet.setup](../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md) | 把任务与配置落实为可领取环境；本轮不展开所有辅助方法 | 返回本函数，继续第 94 行 |
| [executor / process_parallel](../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/process_parallel.md) | 接收这批任务与回调，交回有序结果列表 | 回到 return 表达式，再执行 finally |
| [fleet.teardown 源码](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1835) | 按配置清理整批运行管理的资源 | 结束本函数，交回 Fleet.run:2113 |

本轮在这三个接口处停止。要知道题目到底怎样执行，应看 process_fn；改变预热策略不会自动把 probe 变成完整 Agent。

## 我的直接表述（原话）


<details>
<summary>此前关于基础策略和 fleet 来路的原话</summary>

用户确认从这里开始，并提出初步理解：

> 好的那么就从这里的native开始看一下吧
> 我可以理解为这里是k8s 在这个中间承担的最基础的创建然后运行的过程吗?
> 我可以这么理解吗?
> 这是最基本的basic的strategy?
> 所有后续的改进在这个基础之上衍生?

原话中的 native 对应当前讨论的 naive。以上保留为用户提出的理解与疑问，不将助手的校准代写成用户已经确认的结论。

随后用户追问：

> 那么这里的fleet是什么呢?
> 我其实没有特别理解
> 我的理解是
> 这里应该说的是准备pod 然后让executor直接去执行?
> 我不是特别理解了
> 请再看一下吧

</details>

此前用户进一步表述：

> 好的 我的理解是fleet是sandboxfleet
> 用来管理对象
> 简单来说就是k8s起pod什么的对吗?
> 然后是这里的executor
> 实质性
> 一开始的fleet里面只有一系列的config
> 但是当前需要executor来让他们真正的开始执行对吗?
>
> 虽然目前对于fleet和executor都不是特别理解
> 那么我们现在需要继续吗?
>
> 是我们先看一下fleet具体是怎么样子的
> 单独看一下这里的executor呢?


本次用户明确要求简要了解策略并整理本函数：

> 好的这里是否需要简单的给出这里的strategy一共有哪些内容?
> 同时看一下skill来生成一下这里的这个函数的理解吧

这是当前阅读和记录要求，尚无新的机制复述。

## 尚不清楚

1. 用户已用管理对象描述 Fleet；setup 准备环境与 executor 执行题目的边界，仍需结合本次代码确认。
2. Pod、领取后的 handle、批次编排与 Kubernetes 资源管理的完整关系，尚未确认理解。
3. setup 和执行器此前已有讨论，当前只回接接口；teardown 及更深层方法仍保留未知。
4. 目前只有静态源码与此前 Python 层替代环境实验，没有真实集群任务结果。
5. return 表达式与 finally 清理的先后关系，本次已明确解释，尚待用户反馈。

<details>
<summary>来源、历史与验证范围</summary>

- 固定提交：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 函数主体：strategies.py:82–97；策略表：206–211；外层调用：fleet.py:2091–2114，返回 main 的位置为 2128。
- setup 入口：fleet.py:1403–1423；默认执行器：strategies.py:34–79；单条任务领取与释放：48–54。
- [首次阅读](../../04-flow.md#run-naive-start)、[此前 Fleet 与执行器疑问](../../04-flow.md#fleet-and-executor)、[本轮策略概览与整理](../../04-flow.md#strategy-overview-and-naive-review)。
- [本次整理前的完整卡片](2026-11-04-run-naive-before-current-review.md)保留旧教学场景、原话和历史导航；[更早快照](2026-11-04-run-naive-before-consolidation.md)也继续保留。
- 本次仅静态核对，没有下载数据集、启动 Pod、执行探针或训练。

</details>
