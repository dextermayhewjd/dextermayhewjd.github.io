# 调用上下文参考：从 _run_harbor_rollout 进入 _run_round

- 用户认可并确认纳入：2026-11-10。
- [原始函数卡](../../../../00-repo-reading/repositories/dressage/topics/02-harbor-integration/steps/step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_round.md#caller-context) · [格式讨论与确认](../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#run-round-caller-context-reference-applied)。
- 下方保存认可版本的完整卡片快照，仅重算相对链接；原卡仍是项目内持续维护的阅读记录，不因样例保存而更新学习进度。

## 何时参考

从父函数进入子函数时，读者知道函数名，却难以说明“为什么到这里、手里已有的数据是什么、读完回哪里继续”。此时先恢复最小调用现场，再展开实现。

已有面包屑参考侧重入口与返回导航；本例补充的是进入子函数时要带上的任务和数据语境。它沿用基础函数卡栏目，不另设平行模板。

## 参考哪些做法

1. **先恢复现场**：在“本场景的输入与输出”开头说明父函数正在做的事，附少量真实调用代码。需要追踪的实参明确写出，例如本例的 `retry_round=execution_round`。
2. **带一个问题进入**：本例是“给定 pending，怎样执行这一轮并交回 outcomes？”随后沿 `pending → partitions → nested → outcomes` 展开。
3. **说明真实执行关系**：本例区分内部包装 `run_partition`、顶层 `_run_partition`，以及定义、gather 调度、等待和返回。其他函数按自身机制解释，不强加并发内容。
4. **接回调用方**：说明结果由哪个变量接收，以及调用方随后怎样使用；不只写“返回父函数”。
5. **按需展开细节**：核心数据与交接默认可见，参数全集、辅助机制和完整源码可折叠，仍可回查。

四行表格和三段内部流程是本例的具体选择。短函数可用几句话完成上述交接；不要为了匹配版式增加段落或重复解释。用户原话、助手校准和未解决问题继续分开保存。

## 已认可的完整函数卡

---

# _run_round

- 源码：[dressage/integrations/harbor/rollout.py:903–980](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L903)。
- 首次单独展开：2026-11-10，初建于 Step 011；同日按用户确认归回 Step 010。此前仅定位职责与调用。
- 最近认识更新：2026-11-10，用户表述额度、分区执行与结果汇总的关系；执行时序和返回结构由助手补充校准。

[父函数第 3 段](../../../../00-repo-reading/repositories/dressage/topics/02-harbor-integration/steps/step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_harbor_rollout.md#pending-and-outcomes) → **_run_round** → [_run_partition](../../../../00-repo-reading/repositories/dressage/topics/02-harbor-integration/steps/step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#partition-mainline) · [本步导航](../../../../00-repo-reading/repositories/dressage/topics/02-harbor-integration/steps/step-010-harbor-rollout-entry/01-scope.md#reading-navigation)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`_run_harbor_rollout` 已经准备好本轮 `pending`，需要把这些工作交给 Harbor 执行。
2. **具体内容**：按运行配置分区，计算每区所需路由额度；在额度允许时运行各区，等待结果并合并成一份列表。
3. **建议构建的心智模型**：

   > 把本轮工作按运行配置分成几份，控制并发交给 _run_partition，再把各组结果收回来。

4. **调用代码**（父函数 1086 行，省略其他参数）：

   ```python
   outcomes = await _run_round(..., pending=pending, retry_round=execution_round)
   # 返回父函数后，才决定哪些组完成、哪些组需要重试或替换。
   ```

## 本场景的输入与输出

<a id="round-mainline"></a>
<a id="caller-context"></a>

### 从父函数带进来的上下文

我们停在 `_run_harbor_rollout` 第 3 段的 `outcomes = await _run_round(...)`。父函数已取到本批模板组并整理成工作，现在需要执行其中这一轮。

| 进入时带着的问题 | 当前答案 |
| --- | --- |
| 正在做什么？ | 执行当前批次中的一轮工作。 |
| 工作在哪里？ | `pending`，里面是一组组待执行的工作。 |
| 调用后要拿到什么？ | `outcomes`，每个工作组对应的结果或错误。 |
| 谁决定是否再跑？ | 父函数 `_run_harbor_rollout`。 |

**round 是批次内部的执行轮次，不是 Agent 的一轮对话。** 第一次的 `pending` 来自全部 `work`；之后可能是待重试组，或按失败策略选出的替换工作。

父函数源码阅读节选（1050–1131 行）：省略取组、循环、其他参数及失败处理，不作为可独立运行的代码。

```python
# 父函数已取得 source_groups，先整理这批工作。
work = _resolve_work(data_source, source_groups)
pending = list(work)
execution_round = 0

# 进入本批次的执行循环后，把这一轮工作交出去。
outcomes = await _run_round(
    pending=pending,
    retry_round=execution_round,
    # 其余参数省略。
)
execution_round += 1

# 后面仍由父函数检查 outcomes：
# 成功组存入 completed；仍允许重试的组放入 next_pending。
```

**带着这一个问题进入本函数：已经给你一份 pending，你怎样把这些工作执行一遍，再交回一份 outcomes？**

<details>
<summary>需要时核对：当前调用的参数与返回字段</summary>

- `pending` 是 `_GroupWork` 列表，每项保存原位置 `position`、Sample 模板 `templates`、运行规格 `spec` 及组/任务标识。
- `args`、`config`、`data_source`、`runtime` 来自父函数；`rollout_id` 标识批次，形参 `retry_round` 接收父函数的 `execution_round`。
- `evaluation` 选择训练/评估配置；`expected_weight_version` 传递期望权重版本。
- 返回 `list[_GroupOutcome]`，每项仍对应一个工作组，携带 Sample 或错误，以及版本、轨迹 bundle、路由摘要。
- 本函数按分区顺序展平结果；整个批次恢复原始组顺序由父函数负责。

</details>

### 1. 先看工作怎样分区（915 行）

```python
partitions = _partition_work(pending)  # 相同运行指纹的工作放在一起。
```

依据是 `item.spec.runtime_fingerprint`。这里改变的是工作的组织方式：partition 是一份工作集合，不是 Kubernetes 分区或一个 Pod。

静态例子：`pending` 有 A、B、C 三组；A/C 的运行指纹相同，B 不同，就会得到 `[[A, C], [B]]` 两个分区。下一步让每个分区分别执行。

### 2. 找到工作交给谁执行（943–972 行）

先看内部包装的正常路径。下列节选省略类型标注、其他参数和异常包装；额度准备放在后面的折叠区，完整原函数保留在文末。

```python
async def run_partition(partition, demand):
    await limiter.acquire(demand)  # 等本区所需的路由额度可用。
    try:
        return await _run_partition(
            partition=partition,
            # 其余参数省略。
        )
    finally:
        await limiter.release(demand)  # 结束后归还额度。
```

- 内部 `run_partition` 负责额度和错误包装；带下划线的顶层 `_run_partition` 负责创建并运行 Job，返回该分区的组结果列表。
- **读到 `class RouteCapacity` 或 `async def run_partition`，是在建立类或函数定义；方法和协程体还没有因此运行。** 这里先认识包装，下面的 `gather` 才安排各分区协程执行。

需要展开 Job 时进入 [_run_partition 函数卡](../../../../00-repo-reading/repositories/dressage/topics/02-harbor-integration/steps/step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#partition-mainline)。读完返回这里：先归还额度，结果交给下面的 `gather` 收集。

### 3. 安排执行、收齐结果并返回（974–980 行）

```python
# 为各分区创建协程，由 gather 安排执行并等待结果。
nested = await asyncio.gather(
    *(
        run_partition(partition, demand)
        for partition, demand in zip(partitions, demands)
    )
)
# 每区返回一份组结果列表；这里合成一份列表。
return [outcome for partition in nested for outcome in partition]
```

各协程开始后会先等待自己的额度，所以不代表所有 Job 都能同时运行。延续前面的静态例子：两个分区各自返回列表，展平后得到 `[A结果, C结果, B结果]`。

### 接回父函数：outcomes 接住了什么？

返回的是这轮各组的执行结果。父函数从 `execution_round += 1` 继续，逐组检查：成功的存入 `completed`；失败的记录错误，仍允许重试的放入 `next_pending`。随后由父函数决定继续、替换或结束，并在整批收束时恢复原始组顺序。

因此先沿这条数据线读通即可：

```text
pending → partitions → nested → outcomes
```

| 阅读交接 | 进入与返回位置 |
| --- | --- |
| 分区具体怎样运行 | 进入 [_run_partition](../../../../00-repo-reading/repositories/dressage/topics/02-harbor-integration/steps/step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#partition-mainline)，返回内部包装，再由 gather 收齐 |
| 本轮结果接下来怎样用 | 返回 [父函数第 3 段](../../../../00-repo-reading/repositories/dressage/topics/02-harbor-integration/steps/step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_harbor_rollout.md#pending-and-outcomes) 的 outcomes 赋值之后 |

<details>
<summary>按需回查：额度与失败边界</summary>

这部分在源码中位于内部包装定义之前。首读先看上面的工作流，需要理解并发限制时再展开。

```python
max_routes = int(config.gateway.limits.max_active_routes)
limiter = RouteCapacity(max_routes)
demands = [
    _partition_route_demand(partition, max_active_routes=max_routes)
    for partition in partitions
]
```

`demand = min(本区所有 templates 的数量之和, max_active_routes)`。额度按预计同时运行的 Trial 数计算，不是“一个 Job 占一个名额”。`RouteCapacity` 用 Condition 等可用额度足够时扣减，结束后归还并通知等待者；它不保证所有分区同时开始。

内部包装保留取消传播；普通异常转换为本区每个工作组的失败 outcome。失败包装不是自动重跑，重试策略仍在父函数。辅助源码：[_partition_work:413](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L413)、[_partition_route_demand:490](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L490)。

</details>

## 我的直接表述（原话）

> 好的
> 那么就看一下这里的这个run round 和这里的run partition吧

以上是本轮范围确认。随后用户对本函数的理解：

> 好的
> 我简单理解是这里像limiter acquire这里获取需要的额度
>
> 然后通过这里的run partition来直接运行这里的这个 run partition是我的理解
> 之后通过asyncio gather来获取 这里对应的这个结果，是我的理解
> 最后把这个结果汇总成为表格返还给这里的outcome

助手校准：`gather` 安排各个内部 `run_partition` 协程执行并等待结果；每个协程内部先通过 `limiter.acquire(demand)` 等待并占用额度，再调用顶层 `_run_partition`，结束时在 finally 中归还额度。并非所有分区先执行完，才由 gather 接手。`nested` 是各分区的结果列表组成的列表，最后展平为 `list[_GroupOutcome]`，由父函数的 `outcomes` 接住；不是表格，也不是一个单独的 outcome。用户已表达主干关系，不据此认定 Condition 或 Job 内部机制已掌握。

## 尚不清楚

- 本轮先沿工作分区与返回交接阅读；Condition 的具体等待机制未展开。
- 一个分区怎样创建 Job、怎样将结果归回工作组，接到下一张函数卡。

<details>
<summary>完整源码与验证依据（903–980 行）</summary>

Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`；2026-11-10 按本地源码静态核对。以下保留原函数；未运行 Harbor Job、模型或沙箱。卡内省略参数的片段仅用于阅读导航。

```python
async def _run_round(
    *,
    args: Any,
    config: Any,
    data_source: Any,
    pending: Sequence[_GroupWork],
    runtime: Any,
    rollout_id: int,
    retry_round: int,
    evaluation: bool,
    expected_weight_version: str | None,
) -> list[_GroupOutcome]:
    partitions = _partition_work(pending)
    max_routes = int(config.gateway.limits.max_active_routes)

    class RouteCapacity:
        def __init__(self, capacity: int) -> None:
            self.capacity = capacity
            self.available = capacity
            self.condition = asyncio.Condition()

        async def acquire(self, weight: int) -> None:
            async with self.condition:
                await self.condition.wait_for(lambda: self.available >= weight)
                self.available -= weight

        async def release(self, weight: int) -> None:
            async with self.condition:
                self.available += weight
                self.condition.notify_all()

    limiter = RouteCapacity(max_routes)
    demands = [
        _partition_route_demand(
            partition,
            max_active_routes=max_routes,
        )
        for partition in partitions
    ]

    async def run_partition(
        partition: Sequence[_GroupWork],
        demand: int,
    ) -> list[_GroupOutcome]:
        await limiter.acquire(demand)
        try:
            try:
                return await _run_partition(
                    args=args,
                    config=config,
                    data_source=data_source,
                    partition=partition,
                    runtime=runtime,
                    rollout_id=rollout_id,
                    retry_round=retry_round,
                    evaluation=evaluation,
                    expected_weight_version=expected_weight_version,
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # retry every group in the failed job
                return [
                    _GroupOutcome(
                        work=item,
                        error=exc,
                    )
                    for item in partition
                ]
        finally:
            await limiter.release(demand)

    nested = await asyncio.gather(
        *(
            run_partition(partition, demand)
            for partition, demand in zip(partitions, demands)
        )
    )
    return [outcome for partition in nested for outcome in partition]
```

形成过程：[Step 011 本次回查](../../../../00-repo-reading/repositories/dressage/topics/02-harbor-integration/steps/step-011-harbor-trial-lifecycle/04-flow.md#round-and-partition)。


本次上下文讲解：[Step 010：从父函数携带上下文进入](../../../../00-repo-reading/repositories/dressage/topics/02-harbor-integration/steps/step-010-harbor-rollout-entry/04-flow.md#caller-context-for-run-round)。
</details>
