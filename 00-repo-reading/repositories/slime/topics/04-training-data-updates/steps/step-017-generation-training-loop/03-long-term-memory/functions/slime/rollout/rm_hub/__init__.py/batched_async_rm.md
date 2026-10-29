# batched_async_rm

- Step 012 继承：来自 [Step 011 完整记录](../../../../../../../../../02-rollout-reward/steps/step-011-generate-and-rm-group/02-short-term-memory/functions/slime/rollout/rm_hub/__init__.py/batched_async_rm.md)；保留原话、未知、版本与认识日期，仅重算链接。

- Step 011 调取：从[本步长期快照](../../../../../../../../../02-rollout-reward/steps/step-011-generate-and-rm-group/03-long-term-memory/functions/slime/rollout/rm_hub/__init__.py/batched_async_rm.md)完整调取，供组级调用回顾；沿用原认识时间，未新增个人理解。

- Step 011 继承：来自 [Step 010 · 02-short-term-memory](../../../../../../../../../02-rollout-reward/steps/step-010-generate-and-rm/02-short-term-memory/functions/slime/rollout/rm_hub/__init__.py/batched_async_rm.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- 源码定位：[slime/rollout/rm_hub/__init__.py:99–110](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/rm_hub/__init__.py#L99-L110)。
- 首次接触：Step 010 父函数骨架中的评分调用；2026-10-26 按用户指定独立展开。
- 最近认识更新：2026-10-26，用户已表达自定义评分与逐项 async_rm 两条路径，并将后者联系到 rm_type；函数加载含义和单样本自定义优先级已补充，尚待反馈。

[generate_and_rm：筛选缺分样本](../../sglang_rollout.py/generate_and_rm.md#reward-list-branch) → **本函数：组织评分、返回奖励列表** → 父函数 369–371 写回并返回。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：生成结果需要补分时，父函数把筛选后的 Sample 列表交来；本场景仍是 group_rm=False、列表返回、无 ABORTED。
2. **具体内容**：有全局自定义评分路径时，把整个列表交给该函数；否则逐个调用 async_rm，并等待收集奖励列表。本函数不显式给 sample.reward 赋值。
3. **建议构建的心智模型**：

   > 批量评分的分派入口：先按“怎么组织调用”分类，再看单个样本“选哪种评分方式”；最后把奖励列表交回父函数。
   >
   > ```text
   > batched_async_rm：批量分派
   > ├─ 有全局 custom_rm_path
   > │   └─ 自定义评分函数处理整批 samples
   > └─ 没有全局 custom_rm_path
   >     └─ 每个 sample 进入 async_rm：单样本评分选择
   >         ├─ 样本有 custom_rm_path → 自定义评分函数
   >         └─ 否则 → rm_type 选择框架已有的评分方式
   > ```
   >
   > **第一层按调用粒度分**：整批交给自定义函数 / 逐个交给 async_rm。
   >
   > **第二层按评分来源分**：样本自己的自定义函数 / rm_type 指定的已有方式。

4. **调用代码**：

   ```python
   # generate_and_rm:366–370，省略追踪包装
   samples_need_reward = [sample for sample in samples if sample.reward is None]
   rewards = await batched_async_rm(args, samples_need_reward)
   for sample, reward in zip(samples_need_reward, rewards, strict=False):
       sample.reward = reward
   ```

## 本场景的输入与输出

**输入**：args 提供 custom_rm_path；samples 接收父函数的 samples_need_reward。当前调用没有额外 kwargs，本函数允许继续把它们传给评分函数。group_rm 已由父函数处理，此处不再判断。

**输出**：默认路径返回按输入顺序排列的奖励列表；自定义路径直接返回自定义函数的结果，要求它遵守批量评分接口。父函数负责把奖励与原来的缺分成员配对写回。

下面是完整函数，保留真实名称与参数：

```python
async def batched_async_rm(
    args,
    samples: list[Sample],
    **kwargs,
) -> list[int | float]:
    if args.custom_rm_path is not None:
        # Ensure the custom reward function is implemented in batch mode
        rm_function = load_function(args.custom_rm_path)
        return await rm_function(args, samples, **kwargs)
    tasks = [async_rm(args, sample, **kwargs) for sample in samples]
    rewards = await asyncio.gather(*tasks)
    return rewards
```

- **有 custom_rm_path（104–107）**：加载评分函数，整个 samples 列表传入一次，等待并直接返回结果。自定义函数需要支持批量输入；这里没有逐项调用或重新排序。
- **没有 custom_rm_path（108–110）**：每个 sample 创建一次 async_rm 调用。tasks 这个变量此时存的是协程对象；gather 调度并等待它们，成功时按传入顺序交回结果，完成先后不改变配对关系。

教学示意：samples=[A, B]。即使 B 先完成，只要走默认路径，返回列表仍是 [A 的奖励, B 的奖励]。这里不假设具体分数，也不表示实际运行过评分器。

### 本轮校准：自定义函数与 rm_type 不是完全互斥的两类

load_function 加载的是 Python 评分函数，不等于加载神经网络奖励模型。自定义函数可以调用模型，也可以执行规则或测试，具体由函数实现决定。

上方心智模型的分支图把“批量分派”和 async_rm 内部的“单样本评分选择”分成两层；后者是为理解交接所作的最小回查。

依据 async_rm:55–72 的入口优先级，完整独立调用还支持全局 args.custom_rm_path。沿当前批量默认分支进入时，该全局路径已知为 None，所以不会命中。rm_type 优先取 sample.metadata 中的值，再取 args.rm_type；本轮只校准选择关系，不展开各算法。

因此，“自行设置奖励方式 / 选择框架提供的评分方式”是可用的第一层理解；需要保留的补充是：逐样本的 async_rm 也能选择该样本的自定义评分函数。

**读完返回**：本函数 return rewards → 父函数 368 接住 rewards → 369–370 配对写回 → 371 返回完整 samples。

## 我的直接表述（原话）

用户此前对本函数与父函数的关系表达：

> 这里简单就是按照batched async rm给出这里的reward
> 然后给每一个sample贴上对吗
> 这是我对于这里的理解

助手已补准：写回的是父函数提前筛选的缺分成员。此表述不代表已理解本函数内部的分派或 gather。

用户本轮指定：

> 好的那么现在请先处理一下这里的batched async rm的部分吧

当时尚无内部机制反馈；本轮用户进一步表述如下。

> 这里就是两条路
> 要么是直接走load reward model的方式
> 要么就是通过async rm的方式
> 然后走async rm
> 里面有各种rm 的type
> 这是我对于这里的理解
>
> 也就是一个是自行设置了怎么给奖励
> 第二个更多的是通过rm type这里给出了一系列可能的奖励方式来处理这里的问题？
> 这是我的理解

已表达两条分派和自定义/内置评分的关系；助手补准加载对象为函数，以及 async_rm 的单样本自定义优先级，尚待用户反馈。

用户对展示方式的明确反馈：

> 我觉得心智模型用这个图配合类似的分类性质的话更加合适

据此将分支图移到 LLM 心智模型，并标明两层分类依据。这是呈现偏好，不作为用户已掌握全部分支、结果顺序或算法的证据。

## 尚不清楚

- 两条分派已获用户直接概括；函数加载与单样本自定义优先级的校准、协程列表和结果顺序仍待反馈。
- async_rm 的选择优先级已作最小回查，各评分器怎样算分，以及自定义评分如何保证结果数量与顺序，尚未展开。
- gather 的完整异常与取消机制不在本轮展开范围。

<details>
<summary>来源、验证与边界</summary>

- 固定源码提交 18868a79b0b083a093798a94ed0f8cb4f71b9c14，已核对本地 checkout；本函数 99–110，父函数 366–371。
- 选择优先级依据：[async_rm:55–72](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/rm_hub/__init__.py#L55-L72)。
- 本地 inspect.getdoc(asyncio.gather) 核对成功返回时保持输入顺序；仅为文档核对，没有运行真实评分、模型服务或训练。
- 空列表在默认路径得到空奖励列表；自定义路径仍调用自定义函数，由其遵守接口。本函数没有检查自定义返回数量或类型，也没有显式写入 sample.reward；自定义函数的内部副作用需另行核对。
- 源码注解为 list[int | float]；本轮不凭注解推断所有自定义实现都已满足该约定。
- [本轮形成过程](../../../../../../../../../02-rollout-reward/steps/step-010-generate-and-rm/04-flow.md#batched-async-rm-reading)。

</details>
