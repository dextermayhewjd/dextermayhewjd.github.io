# SandboxFleet.run

> 继承快照：来自 [Step 000 原记录](../../../../../../../step-000-warmpool-reconcile/02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.run.md)。以下“当前／本轮”保留原步骤语境；本次继承不改变认识时间，也不表示重新阅读或掌握。

[返回 main](../../examples/run_swebench_fleet.py/main.md) · [SandboxFleet 类卡](../../../../../classes/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.md) · [下一层 run_naive](../strategies.py/run_naive.md) · [本步 scope](../../../../../../../step-000-warmpool-reconcile/01-scope.md#current-excerpt)

- 源码定位：[fleet.py:2060–2128](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L2060)。
- 首次接触：此前 Step 000 从 main 定位过该调用；2026-11-04 用户确认解析本方法并建立独立短期记录。
- 最近认识更新：2026-11-04，用户初步理解为让 Fleet 开始运行当前任务，同时明确表示细节混乱；完整 SWE-bench 与当前 probe 的区别由助手补充，尚待确认。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：main 已创建 Fleet、加载 Task 列表，接着传入单任务处理函数，请求执行这一批任务。
2. **具体内容**：选择策略和执行器，在缺少计划时生成计划，进入资源监控与运行记录的范围，调用策略函数并返回结果。当前选 naive、单轮、不复用环境、结束后清理的路径。
3. **建议构建的心智模型**：

   > run 是整批运行的编排入口。它接好处理函数、策略、执行器与运行条件，再把具体的准备、执行和清理交给选中的策略；自己接收整批结果并交回 main。

4. **调用代码**：main:92–93 的真实调用。

   ```python
   results = fleet.run(_record(swebench_probe), strategy=strategy,
                       concurrency=max_concurrent)
   ```

## 本场景的输入与输出

### 1. 进入时已经有什么

| 输入或已有状态 | 当前含义 |
| --- | --- |
| self | main 中的同一个 fleet，已有 config 和加载后的 tasks |
| process_fn | _record(swebench_probe) 返回的单任务回调，稍后接收 task 和 handle |
| strategy | 当前选用字符串 "naive" |
| concurrency | main 传入 max_concurrent；方法用 concurrency or self.config.max_concurrent 得到 conc |
| epochs | 未显式传入，默认 1，只运行一轮 |
| keep_warm | 未显式传入，默认 False，交给策略的 teardown 因而为 True |
| recycle | 未显式传入，默认 False，保留默认执行器 process_parallel |
| self.plan_ | 当前路径先前没有预拉取或调用 plan，初始为 None |

_record 的构造调用先发生，再进入 run。此时拿到的是函数对象，还没有通过它执行探针。reset 等复用参数仅在 recycle 分支使用，本轮不展开。

### 2. 先分清三个不同的函数角色

| 本方法中的名字 | 当前指向什么 | 负责哪一层 |
| --- | --- | --- |
| process_fn | _record 返回的回调 | 一条任务如何使用 handle、产生结果 |
| executor | process_parallel | 一批任务怎样领取环境、调用回调、释放并收集结果 |
| fn | run_naive | 环境准备、整批执行与清理的安排 |

局部变量 fn 来自 STRATEGIES[strategy]；这里的 fn 与 _record 内部也叫 fn 的嵌套函数不是同一角色。

<a id="run-core"></a>

### 3. 默认路径的核心代码与顺序

以下从原方法裁剪：保留真实变量、参数和调用。省略参数检查、recycle 分支、环境描述采集、日志及多轮分支；因为当前 epochs=1，直接保留该分支中的调用。资源计划、监控与报告上下文保留。

```python
conc = concurrency or self.config.max_concurrent
fn = STRATEGIES[strategy]
executor = process_parallel

if self.plan_ is None:
    self.plan()
expected = self.plan_.total_replicas if self.plan_ else None

with self.overcommit_guard(expected), self._obs.run(strategy) as report:
    self.report = report
    results = fn(self, process_fn, conc, teardown=not keep_warm,
                 executor=executor)

return results
```

1. **确定并发度（2091）**：用传入值或配置中的预算得到 conc，后续传给策略。
2. **选择策略函数（2092）**：STRATEGIES["naive"] 得到 run_naive。这里仅取得函数对象，还没有执行它。
3. **选择执行器（2093）**：executor 指向 process_parallel；recycle=False，所以不替换为复用执行器。
4. **补齐初始计划（2103–2104）**：如果 self.plan_ 为 None，调用 self.plan()，按任务镜像和配置生成资源计划。这次调用发生在进入 run_naive 之前；计划路径还包含 namespace 准备，不能将它当成绝对纯计算。
5. **取得计划副本数（2105）**：读取 total_replicas，作为资源监控的预期规模。它不是任务结果数量，也不是对 Ready 环境的实时计数。
6. **进入监控与记录范围（2106–2111）**：overcommit_guard 按配置监测资源超量；Observer.run 创建运行报告，保存为 self.report。原实现随后尝试采集环境描述，失败时记录日志并继续。
7. **调用策略（2112–2114）**：单轮路径调用 fn，也就是 run_naive，把 self、process_fn、conc、清理开关及 executor 交给它。
8. **退出上下文并返回（2127–2128）**：正常情况下，策略交回结果后退出运行记录与监控上下文，记录报告摘要，再把 results 返回 main。

第 7 项是本轮的主要下钻边界。run_naive 内怎样安排 setup、executor 和 teardown，继续使用[已有方法记录](../strategies.py/run_naive.md)；这里先看清交给它的内容。

### 4. 交给下一层的是什么

当前调用的实际关系为：

1. self 作为 run_naive 的 fleet 参数，仍是 main 创建的同一对象。
2. 任务列表没有作为单独参数传给 run_naive；它已在 self.tasks 中，策略之后通过 fleet.tasks 取得。
3. process_fn 原样继续传递，run 本身不在这里逐条调用它。
4. executor 也是作为函数值传递；它的调用由策略安排。
5. keep_warm=False 使 teardown=True；当前正常路径的环境清理由 run_naive 安排，完成后再返回结果。

### 5. 正常返回得到什么

1. 返回一轮的任务结果列表，当前默认执行器按输入任务顺序放置结果。元素来自单任务处理函数；单任务普通异常也可能作为结果元素保存，列表不是固定的 reward 数组。
2. main 用 results 接住返回值，随后打印 JSON。
3. Fleet 上保存了运行报告 self.report。报告用于记录这次运行，与作为业务返回值的 results 分开。

当前回调使用 SWE-bench probe，成功结果记录任务标识、镜像、集群、hostname 与输出文本，不代表已经执行了完整解题或评分。

<details>
<summary>本轮暂不展开的分支与实现</summary>

- 参数检查：未知策略或 epochs 小于 1 会报错。
- epochs 大于 1：多次调用策略，形成按轮组织的结果列表；清理和异常处理逻辑也随之变化。
- recycle=True：替换执行器，改变任务与环境的复用方式；策略选择仍独立存在。
- keep_warm=True：向策略传 teardown=False，保留预热环境供后续使用。
- plan、overcommit_guard、Observer.run、describe_environment：本轮只说明作用与调用位置，不为这些辅助调用新增方法卡。资源监控按配置和条件启用，触发时可进行清理并抛错；不能把进入上下文理解成所有配置下必定启动监控线程。
- 当前正常路径不覆盖所有失败：规划、准备、策略调用或上下文退出都可能抛错，不能保证每次调用都会交回结果列表。

</details>

## 我的直接表述（原话）

用户在推荐 run 作为下一入口后要求：

> 这里是在干嘛?
> 请解析了之后直接产生对应的short term memory吧

这是当时解析与建立记录的要求。随后用户给出高层理解：

> 好的
> 我大概理解了
> 虽然感觉很混乱
> 但是这里就是让这个fleet 开始运行和跑对应的这个swebench了对吗?
> 我可以简单理解为

用户把 run 联系到启动当前任务运行，但明确表示内部关系仍混乱。助手建议先保留“让 Fleet 开始执行已加载任务，具体动作由传入回调决定”的模型；当前 swebench_probe 只检查环境并返回信息，不等于完整解题与评分。上述边界尚未得到用户进一步确认。

## 尚不清楚

1. 用户明确表示内部关系仍混乱；process_fn、executor、fn 三种角色与实际调用时机尚未确认理解。
2. 资源计划怎样计算、监控阈值怎样生效、报告怎样累计，本轮只定位接口。
3. run_naive 内部的准备、执行、清理交接待接续；以前讨论过的执行器与回调记录可按问题回查，不自动当作本轮已掌握。

<details>
<summary>源码、参考与验证范围</summary>

- 固定提交：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1，本地 agent-sandbox checkout。
- 当前函数：fleet.py:2060–2128；调用方：examples/run_swebench_fleet.py:92–93；回调构造：同文件 116–123。
- 策略表：strategies.py:206–211；run_naive:82–97；默认执行器：process_parallel:34–79。
- 计划入口：fleet.py:810，内部 _plan 先进入 namespace 准备；资源监控：fleet.py:273；运行报告上下文：observability.py:288–306。
- [本轮分析与建卡](../../../../../../../step-000-warmpool-reconcile/04-flow.md#fleet-run-method-card)。
- 仅静态核对源码与裁剪片段，没有启动训练、执行探针或操作 Kubernetes 集群。

</details>
