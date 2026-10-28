# Scope 完整候选：保留整体框架，只调整生成段详略

[当前正式 scope](../01-scope.md) · [此前局部提案原稿](scope-stage-navigation-proposal-before-full-options-2026-10-26.md)

2026-10-26，用户明确要看完整的大框架，不能只给 with 内的几个函数。下面两份候选都完整保留共享状态、受控生成、结果处理、评分交付；仅比较 with 主体如何表达。用户随后于 2026-10-26 确认采用 A，现已替换正式 scope 的核心骨架；B 保留为对照。

补充评估：[架构与认知科学视角](scope-architecture-cognition-review.md)。建议保留完整主体，以 A 为基础，让资源范围与执行分支可见，接口适配按需展开；此次按用户指定采用下方 A 的完整代码骨架，不额外改成 B。

## 1. 两个选项共用的目标、入口与边界

- **目标**：跟随一份输入任务，理解生成如何受控执行，以及结果如何后处理、补奖励并交付。
- **指挥官**：`slime/rollout/sglang_rollout.py::generate_and_rm`；调用者是 generate_and_rm_group，当前自定义实现是 Coding Agent generate。
- **阅读场景**：新输入 Sample、evaluation=False、生成后返回列表；保留中止与 group_rm 交付分支。
- **共同保留**：semaphore 的取得与 finally 归还、pacer、aborted、DP 上下文、任务归属继承、hooks、缺失奖励筛选、写回与返回。
- **教学裁剪**：代码不是独立运行脚本。省略日志、已完成输入的提前返回、部分续跑处理、单个 Sample 的结果分支。`...` 表示省略的参数；选项 A 的 `if ...` 是明确用旁注说明的条件占位，不是可直接执行的逻辑。

## 2. 选项 A：保留条件分支，简写条件与参数（推荐）

主体和现有结构基本一致。evaluation 是否支持、request/server 两种等待路径继续出现在代码里；省去长签名检查与重复参数。自定义/默认生成器的选择保留旁注，其完整判定继续从现有局部导航回查。

```python
# 1. 共享状态与输入上下文
state = GenerateState(args)
queue_input = copy.copy(sample)

# 2. 受控生成：获取名额、分批放行、检查中止
await state.semaphore.acquire()
try:
    await state.generation_pacer.wait()
    if state.aborted:
        sample.status = Sample.Status.ABORTED
        return sample

    with state.dp_rank_context() as _:
        generate_func = load_function(...)  # 本例用自定义生成器；无自定义时用 generate
        if ...:  # 自定义生成器的签名包含 evaluation
            generate_call = generate_func(..., evaluation=evaluation)
        else:
            generate_call = generate_func(...)

        if getattr(generate_func, "abort_mode", None) == "request":
            sample = await _run_request_abortable_generate(state, sample, generate_call)
        else:
            sample = await _run_server_abort_generate(state, generate_call)  # 当前
finally:
    state.semaphore.release()

# 3. 结果处理：保持任务归属，运行样本后处理
sample = inherit_queue_context(queue_input, sample)
sample = await apply_rollout_sample_hooks(..., sample)
sample = inherit_queue_context(queue_input, sample)

# 4. 评分与交付：只给缺失奖励的结果补分
if args.group_rm:
    return sample

samples = sample  # 当前阅读路径：生成器返回列表
if any(sample.status == Sample.Status.ABORTED for sample in samples):
    return samples

samples_need_reward = [sample for sample in samples if sample.reward is None]
rewards = await batched_async_rm(..., samples_need_reward)
for sample, reward in zip(samples_need_reward, rewards, strict=False):
    sample.reward = reward
return samples
```

- `if ...` 的真实条件是 `custom_func_path is not None and "evaluation" in inspect.signature(generate_func).parameters`；它判断接口是否接受该关键字，不是判断 evaluation 的真假。
- 当前路径选中 Coding Agent、传 evaluation=False，随后进入 server 等待支。
- 当阅读目标转到路径优先级或参数签名时，再在对应局部展开真实表达式。

## 3. 选项 B：完整框架中只展示当前执行路径，旁边列出分支

外层四部分与选项 A 完全一致。with 主体只展示当前 Coding Agent/server 路径，把另外的选择列在紧邻代码的说明中，适合先顺着一条路径读。

```python
# 1. 共享状态与输入上下文
state = GenerateState(args)
queue_input = copy.copy(sample)

# 2. 受控生成：获取名额、分批放行、检查中止
await state.semaphore.acquire()
try:
    await state.generation_pacer.wait()
    if state.aborted:
        sample.status = Sample.Status.ABORTED
        return sample

    with state.dp_rank_context() as _:
        generate_func = load_function(...)  # 本例选中 Coding Agent
        # 按签名传参：支持 evaluation 时传入，本例为 False
        generate_call = generate_func(...)
        sample = await _run_server_abort_generate(state, generate_call)  # 当前
finally:
    state.semaphore.release()

# 3. 结果处理：保持任务归属，运行样本后处理
sample = inherit_queue_context(queue_input, sample)
sample = await apply_rollout_sample_hooks(..., sample)
sample = inherit_queue_context(queue_input, sample)

# 4. 评分与交付：只给缺失奖励的结果补分
if args.group_rm:
    return sample

samples = sample  # 当前阅读路径：生成器返回列表
if any(sample.status == Sample.Status.ABORTED for sample in samples):
    return samples

samples_need_reward = [sample for sample in samples if sample.reward is None]
rewards = await batched_async_rm(..., samples_need_reward)
for sample, reward in zip(samples_need_reward, rewards, strict=False):
    sample.reward = reward
return samples
```

紧邻保留三个选择，不把当前路径冒充全部实现：

| 选择点 | 当前路径 | 其他路径 |
| --- | --- | --- |
| 生成器来源 | load_function 取得 Coding Agent generate | 没有自定义路径时用默认 generate；自定义路径本身优先取 Sample 配置，再取全局配置 |
| evaluation | 签名支持，传 evaluation=False；简写参数中包含该项 | 不支持时不传这个关键字 |
| 等待方式 | _run_server_abort_generate | abort_mode == request 时走 _run_request_abortable_generate |

## 4. 两个选项怎样选

| 比较项 | A：保留分支的简写 | B：当前路径与旁注 |
| --- | --- | --- |
| 大框架 | 四部分全部保留 | 四部分全部保留 |
| with 内部 | evaluation 与等待方式仍显示 if/else | 只显示当前三步调用，分支见紧邻说明 |
| 优点 | 主体仍能看见路径选择，兼顾当前阅读与分支定位 | 主线更短，便于跟随一次具体执行 |
| 代价 | 比 B 多几行控制结构 | 查另一条路径要看旁边的表格 |

当前更推荐 A：用户已明确希望分支可见，同时认可现有主体；A 只精简过长条件和实参，不改变整体表达方式。B 保留作完整对照，不能单独拿出其中三行替代大框架。

## 5. 两者共同的阅读导航与停止位置

1. state 与 Sample 定位沿用当前卡片；semaphore、pacer、DP 上下文继续从对应方法卡回查。
2. 当前观察点仍是 [_run_server_abort_generate](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/_run_server_abort_generate.md)：登记活跃计数、等待、finally 减回。
3. 方法返回后，先离开 DP 上下文，再归还 semaphore 名额，随后进入结果处理和评分。
4. 单样本返回、另一取消机制及远端中止继续保留为后续问题；候选呈现不代表这些已读完。

源版本仍为 Slime `18868a79`。A 已按用户确认应用到正式 scope，B 未应用；此次未改动函数卡、学习状态或 Hugo。此前只给局部示意的原稿完整保留在本文件顶部的历史链接。
