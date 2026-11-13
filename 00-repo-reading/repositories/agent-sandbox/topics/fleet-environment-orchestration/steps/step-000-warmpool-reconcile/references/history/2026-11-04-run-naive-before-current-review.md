# run_naive

[本步 scope](../../01-scope.md) · [函数索引](../../02-short-term-memory/overview.md) · [本轮讨论](../../04-flow.md#run-naive-start)

当前 Step 000 只看准备、执行、清理三次交接；下面的认识时间和原话保留此前讨论来源。

- 源码定位：[strategies.py:82](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L82)，由助手核对。
- 首次接触：Step 000，2026-11-04，用户确认从本函数开始。
- 最近认识更新：Step 000，用户已概括 setup 的主要职责，要求回到本函数的 executor 调用；当前进入 process_parallel 主干。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：SandboxFleet.run 选择 naive，处理一批已登记的任务。
2. **具体内容**：组织环境准备、整批任务执行和可选清理。
3. **建议构建的心智模型**：

   > run_naive 安排三个阶段：准备、执行、清理。资源操作交给 fleet，逐任务处理交给 executor。

4. **调用代码**：外层按策略名取得本函数，并传入同一个管理对象 self。当前选择非 recycle、单轮、结束后清理的路径。

   ```python
   fn = STRATEGIES[strategy]
   executor = process_parallel
   results = fn(self, process_fn, conc, teardown=not keep_warm,
                executor=executor)
   ```

## 本场景的输入与输出

### 1. 输入

教学场景：任务 t1、t2 均使用 image-a；strategy="naive"、epochs=1、recycle=False、keep_warm=False。尚未运行真实集群任务。

<a id="fleet-object-source"></a>

| 参数 | 本场景中的含义 |
| --- | --- |
| fleet | 程序中的 SandboxFleet 管理对象，保存两条任务及运行配置，通过接口管理远端沙箱 |
| process_fn | 接入方的单任务处理函数，接收 task 和 handle |
| concurrency | 2，交给执行器的任务并发度 |
| teardown | True，结束时做整批清理 |
| executor | process_parallel，在 Python 调用程序中组织任务执行 |

外部 fleet.run 中的 self 作为第一个参数传入本函数，因此这里使用的仍是调用方创建的同一个 fleet 对象。

本步把 fleet 按接口理解为保存任务与配置、提供准备和清理方法的管理对象。

### 2. 输出

正常返回默认执行器的结果列表，位置对应输入任务；具体任务结果尚未取得，以下仅表示顺序。

```python
results = [result_for_t1, result_for_t2]
```

当前 teardown=True，返回前还会调用 fleet.teardown。

### 3. 本函数的三个阶段

下面是实际函数主体，省略 docstring 与原注释。

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

1. 准备：fleet.setup 根据配置发起实际环境准备，并等待预热池就绪；当前正常路径中，环境启动已经发生在这一阶段。
2. 执行：executor 接到同一个 fleet、任务列表、处理函数和并发度，开始组织题目处理。
3. 清理：退出时进入 finally，按 teardown 决定是否清理，然后完成返回。

<a id="fleet-executor-handoff"></a>

#### 3.1 本步只看 executor 的接口

当前 executor 的实现名是 process_parallel。本步先看它从 run_naive 接走什么、交回什么，不在这里继续展开内部循环。

1. 传入：同一个 fleet、它保存的任务列表、处理函数和并发度。
2. 交回：按输入位置排列的整批结果。
3. 返回后：本函数进入 finally，根据 teardown 决定整批清理。

<details>
<summary>备用查阅：对象来路与子函数返回点</summary>

1. 调用方创建对象并登记任务，随后调用它的 run 方法。下面按公开接口简写，变量由调用方提供。

   ```python
   fleet = SandboxFleet(config)
   fleet.load_tasks(tasks)
   results = fleet.run(process_fn, strategy="naive")
   ```

2. run 中的 self 就是这个对象，再被传给 run_naive。构造函数初始化管理状态，本场景由 setup 发起环境准备。
3. 默认执行器的单任务核心现在由 [process_parallel 函数卡](../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/process_parallel.md)承接；本页保留调用和返回位置。
4. [SandboxFleet 类卡](../../02-short-term-memory/classes/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.md)已调回本步短期记忆，用于理解管理对象。

| 需要展开时进入 | 读完回到这里 |
| --- | --- |
| [SandboxFleet.setup](../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md) | strategies.py:94，环境准备调用结束后交给执行器 |
| [process_parallel](../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/process_parallel.md) | strategies.py:95，取得批次结果后进入 finally |
| [SandboxFleet.teardown:1835](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1835) | fleet.py:2113，完成本次策略调用 |

</details>

<a id="strategy-position"></a>

naive 可作为学习基线。其他策略的[对照资料](../../../../../../references/rl-batch-flow-and-entry.md#strategy-comparison)保留备用，不列入当前阅读范围。

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

本轮用户进一步表述：

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

## 尚不清楚

1. 用户已用管理对象描述 fleet；setup 发起环境准备与 executor 开始题目处理的分界，仍需继续核对。
2. 对 Pod 资源、领取后 handle、批次编排与 Kubernetes 资源管理的关系，仍未确认完整理解。
3. setup 已做职责概括；默认执行器开始主干阅读，fleet.teardown 及更深层方法仍保留为后续问题。
4. 当前尚未使用真实 process_fn，也未取得真实集群运行结果。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 函数主体：strategies.py:82–97；并列策略表：206–211；其他策略入口：134、191、199。
- 外层选择与调用：fleet.py:2091–2114；单轮结果返回：2128。
- fleet 的对象来源：fleet.py:136 的 SandboxFleet 与公开使用示例；传入 run_naive 的 self 位于 fleet.py:2113。
- 默认执行器的必要交接：strategies.py:48–54；acquire 接口位于 fleet.py:1426，release 接口位于 fleet.py:1663；单个环境的操作句柄见 handles.py 中的 SandboxHandle。
- 输入例子为教学构造；调用关系、参数和返回结构经静态源码核对，没有运行 Kubernetes 或训练实验。
- 原始讨论：[Step 000 · 确认开始 run_naive](../../04-flow.md#run-naive-start)。
- 本轮追问：[Step 000 · fleet 与 executor 的交接](../../04-flow.md#fleet-and-executor)。
- 最新表述与下一入口建议：[Step 000 · 环境启动与任务执行](../../04-flow.md#setup-before-executor)。

- 计数边界：任务数、执行并发度和预热副本数不同，副本数由 Fleet 规划。
- 异常边界：默认执行器可将单任务异常放入相应结果位置；本页主线假定准备与清理均正常结束。
- 调整前的完整卡片：[历史快照](2026-11-04-run-naive-before-consolidation.md)。

</details>
