# run_naive

[main](../../examples/run_swebench_fleet.py/main.md) → [SandboxFleet.run](../fleet.py/SandboxFleet.run.md) → **run_naive（当前）** · [返回 scope](../../../../../../01-scope.md#reading-navigation)

- 源码定位：[strategies.py:82–97](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L82)。
- 首次接触：Step 000，2026-11-04，用户确认从本函数开始，后来回查 Fleet 与调用方。
- 最近认识更新：2026-11-04，用户已概括准备、经 executor 执行、清理与返回的主线；领取对象、清理对象和各策略共性的层次仍需澄清。
- 本次整理：2026-11-04，按短期记忆 skill 回到既有函数卡；旧场景、原话和未知保留，排版与源码核对不视为新增掌握。

<a id="strategy-position"></a>

当前 STRATEGIES 有四项：naive、sliding、pipelined、none；名称到函数的映射及区别见[四种策略简表](../../../../../../../../../../references/rl-batch-flow-and-entry.md#strategy-comparison)。本轮只展开 naive，其他项仅用于定位。

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

### 2. 输出与副作用：同一个 Fleet，另有一份执行结果

| 跟踪对象 | 进入 run_naive 时 | 正常返回时（当前 teardown=True） |
| --- | --- | --- |
| fleet | 已有配置和任务的管理对象 | 仍是同一个对象；本函数不以它作为返回值 |
| 沙箱环境 | 初始计划已存在，尚需完成本次准备 | 经历准备与使用，并已执行整批清理流程 |
| 任务结果 | 尚未通过本次 executor 取得 | executor 返回的列表，经本函数交给外层 Fleet.run 的 results |

本例成功结果的单项结构如下，只展示字段，省略号表示未实际取得的值；不是运行输出，也不表示一批只会有一项。

```python
{
    "instance_id": ...,
    "image": ...,
    "cluster": ...,
    "hostname": ...,
    "output": ...,
}
```

这些字段由传入的回调组织，output 是探针输出文本。run_naive 透传执行器的列表，不负责生成奖励。默认执行器保持输入任务顺序，单任务普通异常也可能作为对应的列表元素。

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

1. **配置与任务 → 可领取的环境（93）**：fleet.setup 使用同一对象已有的配置和任务完成准备及等待。它正常返回后，控制流才到下一行；此处没有接收 setup 的返回值，也没有创建第二个 Fleet 对象。
2. **任务与回调 → 结果列表（94）**：executor 接收 fleet、fleet.tasks、process_fn、concurrency，组织逐条任务并交回结果。run_naive 把这个调用直接放在 return 后面，没有在自身函数中声明一个 results 局部变量。
3. **结果已经取得 → 先执行清理（95–97）**：Python 在完成返回前先进入 finally。当前 teardown=True，于是调用同一对象的 fleet.teardown，清理整批运行管理的资源；这与执行器内部的单任务 release 分开。
4. **清理正常结束 → 结果交回调用方**：待返回的列表交给外层 Fleet.run:2113 的 results，随后再由外层返回 main。清理不是另一个结果，也不会把返回值改成 Fleet 对象。

因此，不能把第 94 行理解为“立即返回，后面的清理不执行”。若 setup 或 executor 抛出异常，finally 仍会尝试清理；清理本身也可能失败，不能据此保证每次都正常返回列表。

<a id="fleet-executor-handoff"></a>

### 4. 从这里进入哪里，读完回哪里

| 调用 | 当前只需看清 | 回到哪里 |
| --- | --- | --- |
| [fleet.setup](../../../../../../references/reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md) | 把任务与配置落实为可领取环境；本轮不展开所有辅助方法 | 返回本函数，继续第 94 行 |
| [executor / process_parallel](../../../../../../references/reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/process_parallel.md) | 接收这批任务与回调，交回有序结果列表 | 回到 return 表达式，再执行 finally |
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

用户本次要求参照既有 Slime 材料改进写法：

> 你这里对于short term memory的构建方法是否可以参考一下slime或者别的地方呢?

本次按该要求改进同一对象、环境副作用与返回值的区分；这是记录方法反馈，不记作新增源码理解。

用户本次对 run_naive 的完整概括：

> 好的 我大概的理解就是这里的确保这里的fleet是可以领取的
> 然后通过executor 的方式
> 把这里的任务通过并行的方式来执行
> 最后考虑如何返还和清理这里的运行的配置内容
> 是我对于这里的run naive的理解
> 应该是所有strategy的最大公约数的或者共有的一个步骤吧
> 是我的理解

用户已经联系了准备、执行、清理和返回。助手校准：可领取的是沙箱环境，不是 Fleet 对象；executor 按并发度组织任务，默认实现的并发度不大于 1 时顺序处理；teardown 清理本次运行管理的资源，不是单纯清除 config。各策略具有相近职责与一致调用接口，但 run_naive 不是其他策略共同调用的基类或公共实现。上述校准尚待用户反馈。

## 尚不清楚

1. 用户已概括准备、执行、清理的顺序；“可领取的是环境”与“清理的是运行资源”的对象边界仍待确认。
2. Pod、领取后的 handle、批次编排与 Kubernetes 资源管理的完整关系，尚未确认理解。
3. setup 和执行器此前已有讨论，当前只回接接口；teardown 及更深层方法仍保留未知。
4. 目前只有静态源码与此前 Python 层替代环境实验，没有真实集群任务结果。
5. return 表达式与 finally 清理的先后关系，本次已明确解释，尚待用户反馈。
6. 策略共有职责、共同接口与复用同一个实现的区别，用户以“最大公约数”提问，尚待确认。

<details>
<summary>来源、历史与验证范围</summary>

- 固定提交：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 函数主体：strategies.py:82–97；策略表：206–211；外层调用：fleet.py:2091–2114，返回 main 的位置为 2128。
- setup 入口：fleet.py:1403–1423；默认执行器：strategies.py:34–79；单条任务领取与释放：48–54。
- [首次阅读](../../../../../../04-flow.md#run-naive-start)、[此前 Fleet 与执行器疑问](../../../../../../04-flow.md#fleet-and-executor)、[本轮策略概览与整理](../../../../../../04-flow.md#strategy-overview-and-naive-review)。
- [本次整理前的完整卡片](../../../../../../references/history/2026-11-04-run-naive-before-current-review.md)保留旧教学场景、原话和历史导航；[更早快照](../../../../../../references/history/2026-11-04-run-naive-before-consolidation.md)也继续保留。
- 本次仅静态核对，没有下载数据集、启动 Pod、执行探针或训练。

- 本次写法参考（仅作记录格式参考，非 Agent Sandbox 源码证据）：
  - [Slime 的 E2BSandbox.__aenter__：同一对象的输入、状态变化与返回去向](../../../../../../../../../../../slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md)。
  - [BaseAdapter._run_turn：连续代码后的数据交接与局部回查](../../../../../../../../../../../../../.agents/skills/repo-reading-short-term-memory/references/base-adapter-run-turn.md)。
  - [SunabakoSandbox.__init__：短函数保留完整代码与紧邻说明](../../../../../../../../../../../slime/topics/01-coding-agent-rl/steps/step-006-agent-sandbox/02-short-term-memory/functions/examples/coding_agent_rl/sunabako_sandbox.py/SunabakoSandbox.__init__.md)。
- [对照修改前的卡片](../../../../../../references/history/2026-11-04-run-naive-before-slime-comparison.md)保存原文；scope、其他函数卡和个人认识时间保持原状。

</details>
