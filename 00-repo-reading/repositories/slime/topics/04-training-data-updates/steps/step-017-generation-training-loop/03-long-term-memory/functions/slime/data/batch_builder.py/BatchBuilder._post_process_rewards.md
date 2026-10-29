# BatchBuilder._post_process_rewards

- 源码定位：[slime/data/batch_builder.py:207](/home/hongshi/projects/slime/slime/data/batch_builder.py:207)，固定版本 `18868a79`，由助手核对。
- 首次接触：Step 016，2026-10-28；此前作为 convert 的配套调用，本轮单独展开。
- 最近认识更新：Step 016，2026-10-28；用户在算法与输出对照讲解后明确反馈“我差不多理解了”，要求保存并回到父函数继续看拼装。
- 导航：[convert 父卡：奖励交接](BatchBuilder.convert.md#reward-preparation) · [读完返回字段拼装](BatchBuilder.convert.md#rewards-to-field-lists) · [scope 第三个阅读入口](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/01-scope.md#reading-order)。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据固定源码与已有测试整理，作为理解参考。

1. **使用场合**：convert 已进入默认转换路径，拿到带有 reward 的 Sample 列表，在组装 train_data 前准备原始奖励与训练用奖励。

2. **具体内容**：先允许自定义后处理接管；否则提取已有分数。指定算法且启用 rewards_normalization 时，按独立 rollout 的结果计算 prompt 组内统计，再把处理后的分数对应回每份 Sample；其他情况直接返回原始分数。

3. **建议构建的心智模型**：

   > 按配置处理已有分数，同时保持输出与输入 Sample 一一对应。
   >
   > ```text
   > _post_process_rewards(samples)
   > ├─ 有 custom_reward_post_process_func → 整批交给自定义后处理
   > └─ 无自定义后处理 → 提取 raw_rewards
   >     ├─ 指定算法 + rewards_normalization=True
   >     │    └─ rollout 去重 → 按 prompt 组处理 → 映射回每份 Sample
   >     └─ 其余情况 → 原样返回
   > ```
   >
   > 第一层选择自定义或内置处理，第二层选择是否执行组内归一化。它交回两个奖励列表，完整训练字段字典仍由 convert 组装。

4. **调用代码**（convert:263–266）：

   ```python
   raw_rewards, rewards = self._post_process_rewards(samples)
   assert len(raw_rewards) == len(samples)
   assert len(rewards) == len(samples)
   ```

## 本场景的输入与输出

构造一个 prompt 组中的两次不同 rollout，已有评分分别为 1 和 3。以下为静态推导，非本轮 PyTorch 执行输出；数值公式同时对照已有 test_grouped_rewards.py 中的预期值。

```python
samples = [
    Sample(group_index=0, rollout_id=10, index=100, reward=1.0),
    Sample(group_index=0, rollout_id=20, index=101, reward=3.0),
]
# custom_reward_post_process_func=None，reward_key=None
```

<a id="algorithm-outputs"></a>

### 算法与开关改变哪份返回值

所有表中情形的 `raw_rewards` 都为 `[1.0, 3.0]`；变化的是第二项 `rewards`。

| 条件 | 处理方式 | 返回的 rewards |
| --- | --- | --- |
| rewards_normalization=False，任意算法 | 直接使用原分数 | `[1.0, 3.0]` |
| 算法不在源码列出的四种中 | 直接使用原分数 | `[1.0, 3.0]` |
| grpo / gspo / cispo，开启 rewards_normalization，关闭 grpo_std_normalization | 每个分数减去所在组均值 | `[-1.0, 1.0]` |
| grpo / gspo / cispo，两个开关均开启 | 去均值，再除以组内标准差加 1e-6 | 约 `[-0.7071, 0.7071]` |
| reinforce_plus_plus_baseline，开启 rewards_normalization | 只去均值，不进入标准差分支 | `[-1.0, 1.0]` |

本例均值为 2，去均值后为 `[-1, 1]`，默认样本标准差为 `sqrt(2)`。所以标准化结果是 `[-1, 1] / (sqrt(2) + 1e-6)`。[PyTorch std 文档](https://docs.pytorch.org/docs/2.14/generated/torch.std.html)说明默认 correction=1；本仓库测试 62–64 行也使用相同分母。

精确算法名是 `reinforce_plus_plus_baseline`；不能将它泛化为所有 REINFORCE++ 模式。GRPO、GSPO、CISPO 在这个函数中共用同一分支，它们的完整训练算法差异不由此函数实现。

### 把源码顺序翻译成五个动作

1. **208–209：允许自定义后处理接管。** 有函数就传入 args、整批 samples 并直接返回，下面的内置规则全部跳过。
2. **211：取出已有分数。** 调用 sample.get_reward_value(args)；reward_key 为空时取整个 reward，否则从 reward 字典选择该 key。内置路径不在这里调用 reward model，也不写回 Sample.reward。
3. **212–241：判断是否需要组内处理，并准备统计单位。** 算法在四种名单内且开启 rewards_normalization 才进入。先把同一次 rollout 的多份 Sample 合并成一份结果，再根据 group_index 分组。
4. **242–251：计算处理后的分数。** 每组先去均值；GRPO / GSPO / CISPO 且开启 grpo_std_normalization、组内独立 rollout 多于一个时，再除以标准差加 1e-6。
5. **252 或 254：按输入顺序交回两项奖励。** 归一化路径用 sample_rollouts 把各 rollout 的结果映射回每份 Sample；未进入归一化则返回 raw_rewards, raw_rewards。

核心数值计算是下面两段源码；第二段只有满足上述标准化条件时才执行：

```python
centered = rewards[positions] - rewards[positions].mean()
# 满足标准化条件时：
centered = centered / (centered.std() + 1e-6)
```

<a id="rollout-to-sample"></a>

### group、rollout 和 index 为什么都出现

| 字段／变量 | 在这里的作用 |
| --- | --- |
| group_index | 哪些 rollout 属于同一个 prompt 组，在组内计算均值和标准差 |
| rollout_id | 哪些 Sample 来自同一次 rollout，统计时只计一次 |
| index | 缺少 rollout_id 时作为回退标识；两者都缺少时按输入位置区分 |
| sample_rollouts | 每份输入 Sample 对应哪个去重后的 rollout，用于恢复输出顺序和数量 |

例如第一条 rollout 拆出两份 Sample，第二条拆出一份，仍取同组原分数 1 与 3：

```text
输入 samples 的归属：  rollout 10, rollout 10, rollout 20
raw_rewards：          [1,          1,          3]
统计时使用的分数：     [1, 3]       → 均值 2
只去均值后的 rewards：[-1,         -1,          1]
```

这避免把拆成更多 Sample 的 rollout 在组内统计中重复计权。最终返回值仍是两个与原 samples 等长、同顺序的列表，不返回一份 index 表，也不会把重复片段从原 samples 中删除。

### 当前需要注意的边界

- **单个独立 rollout 的组**：开启归一化时去均值结果为 0，并跳过标准差除法。组内分数全部相同时，也会得到全 0。
- **标识一致性**：在归一化分支中，group_index 必须全部提供或全部不提供；同一个 rollout 的片段必须具有相同的 group_index 和结果分数，否则报错。
- **旧输入兼容**：全部缺少 group_index 时，若独立 rollout 数等于 n_samples_per_prompt × rollout_batch_size，按原顺序每 n_samples_per_prompt 个组成一组；否则将它们放在同一组处理。
- **返回交接**：回到 convert:263，raw_rewards 写入初始 raw_reward 字段，rewards 写入 rewards 字段。convert 后续还可能用 metadata.raw_reward 覆盖 raw_reward，那是父函数的后续行为。

## 我的直接表述（原话）

> 这里简单来说就是保留每一个sample group中的index 和reward的要求的部分对吧
> 还有什么需要特别注意以下的地方吗？
> 我感觉更多的是根据这里的grpo gspo cispo或者reinforce ++ 的奖励特征或者算法来构建对应的需要的reward或者reward 对应的位置？
> 你能否简单帮我梳理一下这里的post process rewards 这里到底是在做什么
> 或者如果根据选择不同的算法 一般情况下 会出现怎样的 返回的rewards呢？
> 这样子是否会简单和清晰很多
> 直接把这里的逻辑翻译完就行

用户已经将分组、标识、奖励与算法联系起来。助手补充“按 rollout 去重统计、处理奖励、再映射到 Sample”的职责，以及算法开关与数值输出对照。

讲解后的明确反馈，2026-10-28：

> 好的 那么按照这个方式写入吧
> 我差不多理解了
> 那么请继续吧
> 我们是否需要回到上一步了呢？
> 看一下这里的后续是如何拼装的？

据此记录为对上述讲解“大致理解”，继续回到 convert；不要求重新复述，也不把这次反馈扩大为整个训练算法或全部异常分支已经掌握。

## 尚不清楚

- 标识一致性校验与旧输入回退规则已列出，但尚无用户单独展开这些边界的表述。
- 归一化分支没有在本轮实际运行；大致理解的反馈不作为测试通过的证据。
- 不展开完整 GRPO / GSPO / CISPO 的 loss；自定义奖励后处理的具体实现尚未选定。

<details>
<summary>来源、验证与完整例子</summary>

- [Step 016 本轮形成过程](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#post-process-algorithm-outputs)。
- [理解反馈与返回父函数](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#return-from-rewards-to-assembly)。
- 固定源码：batch_builder.py:207–254、263–266；types.py:270–271。完整函数未运行，示例是基于源码的构造与静态推导。
- [已有分组奖励测试](/home/hongshi/projects/slime/tests/test_grouped_rewards.py:48)：包含分组打乱和不等数量片段、单 rollout 组、标识冲突、旧输入与关闭归一化。仅阅读代码，未运行 pytest。
- 归一化示例的除法用标准库算术核对，约为 ±0.7071062812；它不是 PyTorch 运行证据。PyTorch 默认标准差约定核对于上面的 2.14 文档，不据此声称本地安装了这一版本。
- 之前 convert 的单样本例子实际运行过关闭归一化的分支；不将其扩展为本卡所有分支都已验证。

</details>
