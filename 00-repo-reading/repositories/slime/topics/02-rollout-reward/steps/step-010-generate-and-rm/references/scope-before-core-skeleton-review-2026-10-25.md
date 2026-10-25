# 01 · 阅读范围：生成接入与奖励归属

[步骤入口](../README.md) · [本步函数记录](../02-short-term-memory/overview.md) · [上一主题](../../../../01-coding-agent-rl/README.md)

## 1. 阅读目标

- **整体目标**：理解自定义 Agent 怎样接入 Slime 的生成与评分流程。
- **本步问题**：框架怎样选中已读的 Coding Agent `generate`，它返回后是否还要再评分？
- **阅读范围**：先跟一个新 `Sample` 的正常训练路径，再对照返回一个或多个样本时的奖励判断。

## 2. 指挥官函数

- **本步入口**：[sglang_rollout.py::generate_and_rm](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L289-L380)，串起生成函数选择、等待、样本后处理与评分。
- **调用者**：`generate_and_rm_group:425` 为每个待生成 Sample 创建本函数的任务；本步只定位这一交接。
- **已读下游**：`examples/coding_agent_rl/generate.py::generate → _generate`，负责一次 Coding Agent 任务；此次从框架调用侧接回它。

## 3. 给出真正干活的核心骨架

### 3.1 整体位置：从框架进入，再从结果返回

```text
generate_and_rm_group
  └─ generate_and_rm                         ← 本步书签
       ├─ 选择生成函数 → 通过包装器等待结果
       │    └─ Coding Agent generate → _generate
       │         └─ 单题执行、评测、导出 Samples  ← 前一主题
       ├─ 继承任务上下文、执行样本 hook
       └─ 判断是否补评分 → 将结果交回 group
```

- **这次新增的关系**：已读的 `generate` 是框架可以装载的一种生成实现。
- **结果边界**：生成实现可以交回一个 `Sample` 或 `list[Sample]`；外层接住结果后才决定是否补评分。

### 3.2 局部骨架：选中、等待、判断奖励

以下为新任务正常路径的教学裁剪。`evaluation=False`，`group_rm=False`；省略限流、暂停、追踪与异常处理，保留两种等待入口。完整返回分支见代码后的要点。

```python
# 338–344：选择实现，准备本次异步调用
custom_func_path = sample.generate_function_path or args.custom_generate_function_path
generate_func = load_function(custom_func_path) if custom_func_path is not None else generate
generate_call = generate_func(...)  # 是否传 evaluation，取决于源码中的签名检查

# 346–349：通过对应包装器等待生成结果
if getattr(generate_func, "abort_mode", None) == "request":
    sample = await _run_request_abortable_generate(...)
else:
    sample = await _run_server_abort_generate(...)

# 353–355：后处理；随后才判断奖励
sample = inherit_queue_context(...)
sample = await apply_rollout_sample_hooks(...)
sample = inherit_queue_context(...)

# 361–380：下面只展示未中止、非组评分路径
if isinstance(sample, list):
    samples = sample
    samples_need_reward = [sample for sample in samples if sample.reward is None]
    rewards = await batched_async_rm(...)
    for sample, reward in zip(samples_need_reward, rewards, strict=False):
        sample.reward = reward
    return samples
else:
    if sample.reward is None:
        sample.reward = await async_rm(...)
return sample
```

- **实现选择**：单个样本的路径优先于全局配置；都没有时使用同文件的默认 `generate`。
- **等待边界**：`generate_call` 是准备好的异步调用；返回后，`sample` 可以已经变成列表。
- **奖励判断**：检查 `reward is None`。`0.0` 也是已有奖励；列表只将缺奖励的成员交给批量入口。即使列表中没有缺项，源码仍会以空列表调用批量入口，不能概括成完全跳过该函数。
- **其他返回**：`group_rm=True` 时在这里交回，由调用者处理组评分；ABORTED 结果在本函数的相应检查处直接返回。已有完成结果的前置返回及这些分支保留为边界，本轮不展开机制。

### 3.3 阅读顺序：每次只展开一个交接

**① 先看生成实现怎样被选中（338–344）。**

```text
示例配置：examples.coding_agent_rl.generate.generate
  → load_function 取得函数对象
  → generate_func(args, sample, sampling_params, evaluation=...)
  → 返回本次 generate_call，交给后面的 await 包装器
```

- 先分清路径字符串、函数对象与本次异步调用；这里选中的是上一主题读过的实现。
- 读到“已准备好调用哪个函数”即可，随后回到 `346–349` 的等待。

**② 接生成返回值，再判断评分（346–380）。**

- 看包装器如何把结果交回 `sample`；其内部取消机制暂不下钻。
- 接清 hook 位于奖励判断之前，再区分单样本、列表与组评分。
- 用 Coding Agent 已在内部赋 reward 的正常结果，对照尚无 reward 的结果；具体评分算法留给 `rm_hub`。

**停止位置**：能说明“谁选择生成实现、结果以什么形状交回、谁补缺失奖励”后，回到 `generate_and_rm_group`。本步不展开组并发、队列确认、训练消费或所有失败清理。

## 版本说明

- 源码固定为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；本步卡片使用这一版本。
- [函数卡片](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md)保留场景与返回边界；[04-flow](../04-flow.md#topic-two-start)保存本次开始阅读的实际过程。
