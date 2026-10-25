# 骨架提取对照：按业务结果分块，保留关键交接

2026-10-25 的对照方案，用于继续审阅 [Step 010 当前 scope](../01-scope.md)。本稿只讨论骨架怎样提取，尚未替换正式 scope。

> 后续源码核对：本稿改善了数据交接，但仍缺少共享 state、准入和释放范围。完整函数还需结合[state 与执行结构](../../../../../../../../slime_photo/code-reading/chapters/03-strategy-evaluation/walkthrough.md#state-and-execution-skeleton)阅读，不能仅用下面三段代表全部职责。

## 1. 原来的方法在哪里

直接对应的是 [repo-reading-scope](../../../../../../../../.agents/skills/repo-reading-scope/SKILL.md)及其[剪枝方法](../../../../../../../../.agents/skills/repo-reading-scope/references/pruning-method.md)：找指挥官、按职责过滤、保留正常路径与真实交接，再有限下钻。

其中两项容易在压缩时丢掉：

- 第 3 节要求保留“关键返回值、await 和必要的上下文嵌套”；涉及当前数据交接时，允许保留少量必要参数。
- 局部导航规则要求在实际实现不清楚时补最少的来源关系，明确到底调用谁。

[代码阅读指南的方法二](../../../../../../../../00-repo-reading/code-reading-guide.md#方法二读代码时记录什么)另强调记录数据形态的变化。将这些规则用于当前函数，才有下面的候选写法；并不需要另创一套步骤格式。

## 2. 当前版本还缺什么

之前的 `_generate` 骨架中，`prepare_workspace`、`harness.run`、`run_evaluation` 等名字直接对应业务动作。当前函数多了动态选择与等待包装：`generate_func` 没有说明具体身份，`_run_server_abort_generate` 的名字也不直接告诉读者正在执行 Coding Agent。

此外，当前代码省略了这条关键实参：

```python
generate_call = generate_func(...)
sample = await _run_server_abort_generate(...)
```

第二行看不出如何使用第一行的 `generate_call`。同样，`batched_async_rm(...)` 与 `zip(...)` 全部省略参数，也会使待评分成员、返回分数和写回对象之间的关系变暗。

“取得函数 → 准备调用 → 等待返回”共同完成一次生成委派；如果先将这些准备语句拆成独立主阶段，读者需要自行重新组合。这里应先按结果分块，再在块内看具体语句。

## 3. 候选提取方法

1. **先说清这次调用的起点和终点。** 一份待生成的 Sample 进入，本例最终交回带奖励的样本列表。
2. **找造成业务结果变化的连续代码块。** 当前可分为“得到生成结果 → 样本后处理 → 补奖励并返回”。配置选择与异步等待归在生成块中。
3. **保留使块内、块间关系可见的语句和参数。** `generate_call` 交给等待包装器；`sample` 交给 hook；待评分成员交给 RM，返回分数写回这些成员。
4. **再折叠横跨主线的机制。** 限流、追踪、队列上下文和异常仍存在于真实代码，第一遍只说明边界。不能仅因函数名含 `abort` 就删除实际执行交接。

这是本函数的分块判断；阶段数量随职责变化，不把三段作为其他函数的固定模板。

## 4. Step 010 的候选骨架

沿用当前选定路径：新任务、`evaluation=False`、`group_rm=False`，Coding Agent 正常返回列表，hook 不改变返回形状。`custom_func_path` 已选为 `examples.coding_agent_rl.generate.generate`。

下面为教学裁剪，保留真实函数名和顺序；`...` 省略不影响当前交接的参数，`zip` 省略默认值 `strict=False`。

```python
# 1. 委派生成：一份待生成 Sample → Coding Agent 的结果列表
generate_func = load_function(custom_func_path)
generate_call = generate_func(...)
sample = await _run_server_abort_generate(..., generate_call)

# 2. 样本后处理：将刚收到的结果交给已配置的 hook
sample = await apply_rollout_sample_hooks(..., sample)

# 3. 补奖励并返回：只把缺奖励的成员送去评分，再写回这些成员
samples = sample
samples_need_reward = [sample for sample in samples if sample.reward is None]
rewards = await batched_async_rm(..., samples_need_reward)
for sample, reward in zip(samples_need_reward, rewards):
    sample.reward = reward
return samples
```

第 1 块的 `generate_func` 就是已读的 Coding Agent `generate`。等待包装器内部的核心语句是 `return await generate_call`，周围负责维护活跃生成计数；因此它承接并等待这次生成调用，不需要先展开整个取消机制。

第 3 块保留 `reward is None`，因为它决定谁需要评分。当前 Coding Agent 正常结果已带奖励时，待评分列表为空；源码仍会调用批量入口。其他分支与完整前提继续以当前 scope 的折叠说明为边界。

## 5. 如何判断这次是否提取清楚

读者应能直接沿变量回答：调用哪个生成器、`generate_call` 被谁等待、返回结果交给谁、哪些成员被评分、分数写回哪里。默认骨架无需先理解等待包装器的全部状态机制。

若采用本方案，正式 scope 仍保留阅读目标、指挥官、核心骨架三段；骨架中的分块与阅读导航对应。具体输入样本、完整分支和原话继续归函数卡片，不增加重复的完整函数讲解。

## 版本与依据

- 当前源码 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`：[生成调用与后处理](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L338-L355)、[奖励写回](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L361-L371)。
- [等待包装器 277–285 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L277-L285)已静态核对。本轮未执行生成任务；候选写法的可读性仍待实际反馈。
