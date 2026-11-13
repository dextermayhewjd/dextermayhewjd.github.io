> 2026-11-04：收拢默认展开内容之前的函数卡。原话、认识时间与源码归属按原记录保留，相对链接已调整。

# run_naive

[本步 scope](../../01-scope.md) · [函数索引](../../02-short-term-memory/overview.md) · [本轮讨论](../../04-flow.md#run-naive-start)

- 源码定位：[strategies.py:82](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L82)，由助手核对。
- 首次接触：Step 000，2026-11-04，用户确认从本函数开始。
- 最近认识更新：Step 000，用户进一步追问 fleet 的含义及它与 executor 的交接；下文校准尚待用户反馈，不记为已掌握。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据当前调用场景和源码整理，作为理解参考。

1. **使用场合**：SandboxFleet.run 选择 strategy="naive" 时调用本函数。当前只看单轮、非 recycle、结束后清理的正常路径。

2. **具体内容**：本函数组织环境准备、整批任务执行和可选的整批清理。默认执行器 process_parallel 负责每条任务的领取与释放；Kubernetes 资源管理发生在下游。

3. **建议构建的心智模型**：

   > run_naive 是训练侧使用环境的一种朴素批次策略。它把准备、执行和清理按明确的阶段接起来，可以作为学习基线；它不是 Kubernetes 自身的调度算法，也不是其他全部功能的父实现。

4. **调用代码**：下面摘自 SandboxFleet.run 的当前分支，省去检查、规划和报告包装。当前 strategy="naive"、keep_warm=False、recycle=False、epochs=1。

   ```python
   fn = STRATEGIES[strategy]
   executor = process_parallel
   results = fn(self, process_fn, conc, teardown=not keep_warm,
                executor=executor)
   ```

## 本场景的输入与输出

### 1. 输入

采用已经配置并登记两条任务的 Fleet，以下为教学构造，没有执行集群任务。

<a id="fleet-object-source"></a>

#### 1.1 fleet 是怎样来到这里的

fleet 是 SandboxFleet 类的一个 Python 实例，运行在调用程序中。它保存这一批任务和运行配置，并提供准备环境、领取环境、释放环境等操作。Pod 是它通过 Kubernetes 管理的远端资源。

下面按仓库公开接口简写使用关系，config、tasks、process_fn 已由调用方准备。

```python
fleet = SandboxFleet(config)
fleet.load_tasks(tasks)
results = fleet.run(process_fn, strategy="naive")
```

1. 调用方创建 fleet 对象。
2. 调用方把任务登记到这个对象中。
3. 调用 fleet.run 时，方法内部的 self 就是这个 fleet。
4. fleet.run 选择 run_naive，将 self 作为第一个参数传入。因此 run_naive 中的 fleet 仍指向同一个管理对象。

SandboxFleet 构造函数初始化配置、任务容器等状态；本场景随后由 setup 发起环境准备。这里先认识对象身份和用途，构造函数的其他字段按需回查。

#### 1.2 run_naive 收到的参数

| 参数 | 本场景取值与意义 |
| --- | --- |
| fleet | 已持有任务与资源配置的 SandboxFleet；任务 t1、t2 均使用 image-a，metadata 为各自的题目数据 |
| process_fn | 接入方提供的函数，接收 task 与 handle，返回该任务的结果 |
| concurrency | 2，传给执行器的任务并发度 |
| teardown | True，本次结束时执行整批清理 |
| executor | 默认的 process_parallel |

task 的镜像数量、预热池的副本数量和任务并发度是不同概念。naive 准备本批涉及的各镜像池，具体副本数仍由 Fleet 规划；这里不假定两条任务必然对应两个预热副本。

### 2. 输出

1. 正常返回默认执行器产生的结果列表，顺序对应输入任务。下列名称是占位，未获得真实任务结果。

   ```python
   results = [result_for_t1, result_for_t2]
   ```

2. 默认执行器已经处理每条任务的领取与释放。单任务发生异常时，它可以把异常对象放到该任务的结果位置；本轮先看成功路径。
3. 当前 teardown=True，返回调用方之前已经调用 fleet.teardown。假定清理也正常结束；清理抛错等路径暂不展开。

### 3. 本轮直接看的函数主体

下面保留源码的签名和执行语句，只省略 docstring 与原注释。

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

1. 第 93 行先调用 fleet.setup，进入本批镜像池的准备过程。准备内部怎样协调 Kubernetes，暂时只保留接口。
2. 第 94 行将同一个 fleet、它的任务列表、处理函数和并发度交给 executor。默认执行器允许任务并发，因此 naive 不表示逐条串行执行。
3. 第 95–97 行在退出时进入 finally。当前开启清理，先调用 fleet.teardown，再把第 94 行取得的结果交回外层。

<a id="fleet-executor-handoff"></a>

#### 3.1 setup 之后，executor 怎样取得环境

第 94 行传给 executor 的是 fleet 管理对象、任务列表、处理函数和并发度。setup 没有在这里返回并传递一份 Pod 列表。

默认 executor 是运行在 Python 调用程序中的 process_parallel。下面摘录它内部处理单条任务的核心代码，省略监控和异常包装；这是该任务回调中的 return，不是整个批次立即结束。

```python
handle = fleet.acquire(task)
try:
    return process_fn(task, handle)
finally:
    fleet.release(handle)
```

1. 领取环境。executor 对当前 task 调用 fleet.acquire，取得对应的 SandboxHandle。
2. 处理任务。executor 把 task 和 handle 交给 process_fn。
3. 使用远端环境。process_fn 可以通过 handle.exec 等接口把命令送入对应 Pod；具体任务逻辑由接入方提供。
4. 释放环境。当前任务退出时，executor 调用 fleet.release(handle)。默认路径释放相应 Claim，不是把用过的环境直接放回备用池。

这里先把 handle 理解成“访问某一个已领取沙箱的操作句柄”。同一 fleet 可以管理多条任务和多个环境，每条任务得到自己的 handle。executor 负责组织任务执行，具体发往 Pod 的操作通过 handle 完成。

| 需要展开时进入 | 读完回到这里 |
| --- | --- |
| [SandboxFleet.setup:1403](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1403) | strategies.py:94，环境准备调用结束后交给执行器 |
| [process_parallel:34](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L34) | strategies.py:95，取得批次结果后进入 finally |
| [SandboxFleet.teardown:1835](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1835) | fleet.py:2113，完成本次策略调用 |

<a id="strategy-position"></a>

### 4. naive 与其他策略的关系

1. 在学习上，可以先用 naive 看清不重叠的准备、执行、清理阶段。
2. 在当前源码中，naive、sliding、pipelined、none 都由 STRATEGIES 表按名称选择，是并列函数。
3. 没有依据把它们说成全部继承 run_naive，或据此推断仓库的历史演化顺序。

| 策略 | 当前实现主要改变什么 |
| --- | --- |
| naive | 先准备本批所有涉及的镜像池，再交给执行器运行任务 |
| sliding | 每次准备并处理一个镜像窗口，随后移到下一窗口 |
| pipelined | 当前镜像窗口执行时，提前准备下一窗口 |
| none | 按单镜像、单副本池的窗口按需推进；名称不表示完全不使用预热池 |

recycle 是另一项配置：它可以替换执行器、改变任务与环境的复用关系，而不是新的预热策略。隔离、运行时和控制器优化也分别位于自己的职责层。本轮只核对这些关系，不展开它们的实现。

## 我的直接表述（原话）

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

## 尚不清楚

1. fleet 作为 Python 管理对象、Pod 作为远端资源，以及 executor 通过领取取得 handle 的关系，尚待用户反馈。
2. 对“批次编排策略”和“Kubernetes 资源管理”的区分，尚待用户反馈。
3. fleet.setup、默认执行器、fleet.teardown 的内部实现尚未完整逐函数阅读；本次只补充默认执行器与 fleet 的必要交接。
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

</details>
