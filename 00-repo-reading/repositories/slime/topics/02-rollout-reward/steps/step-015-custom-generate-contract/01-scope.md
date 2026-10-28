# 01 · 自定义 generate 的接口约定与接入验证

[本步入口](README.md) · [短期卡片](02-short-term-memory/overview.md) · [前序记录](03-long-term-memory/overview.md) · [理解过程](04-flow.md)

## 1. 阅读目标

**Goal：如果换成自己写的 Agent 生成函数，能说明框架怎样调用它、它应交回什么，以及怎样用一个最小测试检查接入是否正确。**

本步把已读的 Coding Agent generate（具体实现）与 generate_and_rm（框架调用方）接起来，从中提炼可复用的接入约定。前者提供一个真实案例，后者给出实际调用与结果处理的要求；最后用最小实现及测试核对两边是否配合。

完成时应能拿出三项具体结果：输入与调用方式的说明、返回数据及双方职责的说明、覆盖正常返回和一个错误／失败情形的验证证据。Sample 字段、评分分支和辅助函数都围绕这三项按需阅读。

前提：先看一个尚未完成的单 Sample，设置自定义生成路径，`evaluation=False`、`group_rm=False`，无额外结果改写 hook。准入成功，业务环境作为已有条件。评估参数仍保留在接口中；其他配置分支按需要对照。

## 2. 找到指挥官函数

**调用方锚点是 [generate_and_rm](/home/hongshi/projects/slime/slime/rollout/sglang_rollout.py:289)**：它选择生成函数、构造调用、等待结果，再处理 hook 和奖励。**接入方对照是 [coding_agent_rl.generate](/home/hongshi/projects/slime/examples/coding_agent_rl/generate.py:225)**：这是已经读过的真实 Agent 入口，正常路径把内层 `_generate` 的样本列表交回。

本步重点是两者交接的接口。`load_function`、Trace、准入与中止包装先保留用途；最后的测试用于验证实际行为，不是新的运行时组件。源码版本为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。

## 3. 核心骨架与阅读导航

### 3.1 整体位置

以下沿已读本地 worker 路径定位；不将其冒充 straw 默认分布式执行体。框架实际执行关系与本步阅读顺序分别展示。

```text
AsyncRolloutWorker._loop                       # 已读：持续调度
  ├─ 创建 generate_and_rm_group 的 Task
  │    ├─ 为组内 Sample 创建 generate_and_rm 的任务
  │    │    ├─ 准入、pacer、中止检查、DP 上下文
  │    │    ├─ 选择并调用自定义 generate         # 本步接口入口：338–344
  │    │    │    └─ coding_agent_rl.generate    # 真实接入方：225
  │    │    │         └─ _generate → 样本列表   # 已读 Agent 主线
  │    │    ├─ 等待返回、归还准入名额
  │    │    ├─ 继承上下文、应用样本 hook
  │    │    └─ group_rm=False 时按条件补奖励并返回
  │    └─ 汇总组结果；group_rm=True 时在组级评分
  └─ 登记完成回调 → output_queue → 获取完成结果   # 已读：group handoff
```

具体策略的内部模型/工具循环可由外部 CLI 推进；它们不由本步的调用适配代码逐次驱动。

### 3.2 本步局部骨架

下面是 `generate_and_rm:338–349` 的真实代码片段。它位于 DP 上下文内，执行后离开生成阶段，再接已读的样本处理和奖励判断。

```python
custom_func_path = sample.generate_function_path or args.custom_generate_function_path
generate_func = load_function(custom_func_path) if custom_func_path is not None else generate

if custom_func_path is not None and "evaluation" in inspect.signature(generate_func).parameters:
    generate_call = generate_func(args, sample, sampling_params, evaluation=evaluation)
else:
    generate_call = generate_func(args, sample, sampling_params)

if getattr(generate_func, "abort_mode", None) == "request":
    sample = await _run_request_abortable_generate(state, sample, generate_call)
else:
    sample = await _run_server_abort_generate(state, generate_call)
```

本步对照的 Coding Agent 声明了 `evaluation`，没有设置 `abort_mode="request"`，因此先走第一条传参分支和第二条等待分支。两项判断的用途不同；包装器内部沿用已有记录，暂不重新下钻。

<a id="reading-order"></a>

### 3.3 固定阅读顺序

| 阅读步骤 | 入口 | 本段问题与停止位置 |
| --- | --- | --- |
| **第一步：框架怎样调用** | [generate_and_rm：调用约定](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md#step015-call-contract)，源码 338–349 | 把函数路径、函数对象、本次调用和返回结果分开；先对齐调用处与接收方签名。读到等待后的结果交回父函数为止。 |
| **第二步：实现怎样交回结果** | [Coding Agent generate 的返回来源](02-short-term-memory/functions/examples/coding_agent_rl/generate.py/generate.md#returned-samples)：内层 326 导出、367 返回，外层 230–231 交回，再接父函数 349、353–380；配套 [Sample 字段视图](02-short-term-memory/classes/slime/utils/types.py/Sample.md#step015-field-view) | 先看一个任务的轨迹怎样交成 Sample 列表，再观察其中一份样本的够用结构，优先追踪 status、reward 的用途。finish_session 先按已读接口作为黑箱，不重读消息树、分段或完整 Agent 流程。 |
| **第三步：怎样验证接入** | [测试卡：最小 custom_generate → 框架调用 → 结果断言](02-short-term-memory/functions/tests/plugin_contracts/test_plugin_generate_contracts.py/test_custom_generate_function_path_supports_user_override.md#minimal-generate)，对应源码 74–80、148–162，按需看其两个断言函数 | 将接收参数、填充结果、返回 Sample 与框架调用连起来；用最小输入观察返回及副作用，再检查一个错误／失败情形。说明测试覆盖边界，不通读 fixtures 或整份测试文件。 |

第一步是本轮带读入口。三步编号保留，完成其中一段不会删去它；实时进度以唯一路线为准。本步卡片包含调用方、真实生成实现、Sample 类和一个正常路径测试；材料展开不等于已掌握或测试已通过。

第二步内部按“够用的字段结构 → 字段从哪里来、回到父函数后怎样使用 → 按需补查完整定义”推进。类卡保存字段含义，函数卡保存写入和读取的过程；训练消费只先定位用途，后续再进入 BatchBuilder。不单独为 Sample 开新 step，也不预先逐项讲解全部字段。

此前提出的 finish_session 末尾只作为返回字段不清楚时的回查入口，不是进入验证前必须展开的新单元。后续围绕最小 custom_generate 与调用测试理解接入；其中的固定 token、文本和分数是测试替身数据，不能当成完整 Agent 实现或一般训练样本构造规则。

注意：现有测试对形参名称和单个 Sample 返回的断言，比真实 Coding Agent 入口更窄。第三步需要核对这个差别，不能把测试文件当成覆盖所有合法接入形式的规范；本轮尚未运行它。

第三步中的“错误情形”指接入约定出错，不自动等同于主动中止。回看 [_run_server_abort_generate](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/_run_server_abort_generate.md#step015-abort-name) 是为了定位等待和错误传播；其名字包含 abort，但正常生成也会进入。真正的 abort 入口目前只作区别定位，完整取消、服务端停止与收尾不在本轮展开。

本步原定停止于“接口约定明确、最小接入有验证证据”。2026-10-28 用户明确认为可等待要求已清楚，不需要通过 async def / def 反例继续讲解或测试；取消这一阅读候选。已有契约测试的实际运行仍未完成，保留为实践缺口，不把这个已取消的演示当作继续源码阅读的前置。该调整不代表测试已通过或全部接入要求已验证。

下一处建议接回既定主线的 [BatchBuilder.convert](/home/hongshi/projects/slime/slime/data/batch_builder.py:256)，回答“生成后的 Sample 怎样成为训练数据”；本轮只定位候选，不创建新 step 或预填函数认识。Trace、完整训练、队列持久化、全部 reward 类型与分布式恢复不在本步展开。
