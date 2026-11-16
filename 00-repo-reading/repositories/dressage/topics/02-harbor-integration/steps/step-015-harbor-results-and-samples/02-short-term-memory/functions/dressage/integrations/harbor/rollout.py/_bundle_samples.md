# _bundle_samples

- 代码归属：Dressage，源码 [rollout.py:624](/home/hongshi/projects/Dressage/dressage/integrations/harbor/rollout.py:624)。
- 首次单独接触：2026-11-16，Step 015；已确认进入本函数，尚无个人复述，不标记掌握。
- [本步 scope](../../../../../../01-scope.md)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`_run_partition` 在 Job 返回、插件收尾之后，按 Trial 名称与最终尝试 ID 取回 bundle，需要将其转换成 Sample 列表。
2. **具体内容**：拒绝不可训练的 bundle；委托展开模型记录；检查指定奖励是有限数值；给各个 Sample 添加 Harbor 来源信息，将完整奖励字典放到最后一个 Sample；返回列表。
3. **建议构建的心智模型**：

   > 将一次尝试的结果包变成一组 Sample：模型记录提供生成内容，原始模板提供样本基础，bundle 补上来源身份和最终奖励。

4. **调用代码**（外层正常路径节选）：

   ```python
   bundle = plugin.get_result(trial_name, str(final_result.id))
   # 外层检查 bundle 存在后：
   converted = _bundle_samples(
       template=template, bundle=bundle, args=args, reward_key=reward_key,
   )
   outcome.samples.extend(converted)
   ```

## 本场景的输入与输出

**带着什么进来？** `template` 是外层为该 Trial 保留的原始样本模板；`bundle` 是已提交的尝试结果；`args` 继续传给展开函数；`reward_key` 指定需要检查的评分项，例如 `"reward"`。

**得到什么？** 正常返回 `expanded`，即转换后的 Sample 列表。它不是重新调用模型，也不重新运行评测。不可训练的 bundle 或不合格的指定奖励会抛错，由外层处理组失败。

### ① 模型记录先展开成 Sample

前置条件是 `bundle.trainable` 为 True。满足后执行：

```python
expanded = expand_segments_to_samples(
    template,
    list(bundle.segments),
    args=args,
    session_id=bundle.session_id,
    instance_id=bundle.instance_id,
)
```

这里委托已有的转换函数处理 segments，得到 `expanded`。此前 Step 008 已涉及此转换；本轮按用户问题调取 [expand_segments_to_samples 函数卡](../../../rollout/multi_segment.py/expand_segments_to_samples.md)，具体输入输出可直接展开下面的例子；需要内部代码时再进入子函数卡。

<details>
<summary>展开具体例子：一个 segment 怎样变成一个 Sample？</summary>

以下按源码静态推导，只展示相关字段，不是运行输出。token ID 为示意数值，不代表下方中文的真实编码。本例不截断、不启用 routing replay，也不提供版本数组。

**调用前：原始模板保留题目，bundle.segments 提供已经生成好的记录。**

```python
# template 的字段视图
template.index = 7
template.prompt = "计算 1+1"
template.metadata = {}
template.reward = None

# bundle 的相关字段视图
bundle.session_id = "session-A"
bundle.instance_id = "instance-A"
bundle.segments = [{
    "uid": "seg-0",
    "segment_index": 0,
    "tokens":         [101, 102, 201, 202],
    "full_loss_mask": [  0,   0,   1,   1],
    "full_logprobs":  [0.0, 0.0, -0.3, -0.1],
    "messages": [{"role": "assistant", "content": "答案是2"}],
    "extra_info": {},
    "finish_reason": "stop",
}]
```

**调用后：expanded 是含一个新 Sample 的列表，原模板不被修改。**

```python
# expanded[0] 的结果字段视图，不是额外执行这些赋值
index = 7
prompt = "计算 1+1"                       # 模板保留
rollout_id = 7                            # 来自 template.index
tokens = [101, 102, 201, 202]              # 完整序列
response = "答案是2"                      # 来自最后一条 assistant 消息
response_length = 2
loss_mask = [1, 1]
rollout_log_probs = [-0.3, -0.1]
reward = None                            # 尚未执行下面第②段
# metadata 节选
metadata = {
    "session_id": "session-A",
    "instance_id": "instance-A",
    "parent_traj_id": "session-A",
    "segment_index": 0,
    "segment_count": 1,
}
```

本次从 full_loss_mask 中第一个 1（位置 2）开始取回复区间，因此 response_length 为 `4 - 2 = 2`，mask 和 logprobs 取后两项，tokens 保留完整序列。一般情况下，response_length 不等于 mask 中 1 的数量。

如果有两个 segment，就分别复制模板，返回两个 Sample。随后继续本卡第②段：由 `_bundle_samples` 补 Harbor 来源信息，并把最终奖励字典放到最后一个 Sample。

</details>

### ② 每个 Sample 补上来源，最后一个接最终奖励

教学裁剪：保留代表性 metadata，省略其他来源字段和奖励合法性检查。

```python
rewards = dict(bundle.rewards)
# 源码检查 rewards[reward_key] 的值：必须是有限数值，且不能是 bool。
for index, sample in enumerate(expanded):
    metadata = _metadata(sample)
    metadata.update({
        "harbor_job_id": bundle.job_id,
        "harbor_trial_name": bundle.trial_name,
        "harbor_trial_id": bundle.trial_id,
        "harbor_rewards": rewards,
        "harbor_reward_key": reward_key,
        # 其余字段包括任务、Agent、路由、尝试序号、权重版本和实例身份。
    })
    sample.reward = (
        rewards if index == len(expanded) - 1 else {reward_key: 0.0}
    )
return expanded
```

两类字段用途不同：**metadata 记录结果来自哪次执行；sample.reward 是分配给这个 Sample 的奖励。** 每个 Sample 的 metadata 都能保留完整评分，但其 sample.reward 不一定相同。

静态示例：假设展开后有 3 个 Sample，且 `bundle.rewards={"reward": 1.0}`、`reward_key="reward"`：

```text
展开后              本函数补写的 sample.reward
Sample 0        →   {"reward": 0.0}
Sample 1        →   {"reward": 0.0}
Sample 2        →   {"reward": 1.0}   ← 最后一个接到最终奖励
```

这不是又评分三次，也不是把 1 分平均拆开；函数把已有的最终奖励字典放在最后一个 Sample 上。此例只演示奖励赋值，不承诺任意三个输入 segment 都必然产生三个 Sample。

### ③ 返回外层，继续组检查

`return expanded` 后，外层用 `outcome.samples.extend(converted)` 将结果加入对应组。后续还会检查组内轨迹数量，以及配置要求下的权重版本一致性，再登记成功组的最终结果；**本函数转换成功不等于整组已经选用**。

本轮停在返回 Sample 列表，组检查接下来再看，不在本卡展开。

## 我的直接表述（原话）

尚无针对本函数的个人复述。用户确认继续：

> 好的 那么我们继续吧
> 看一下吧 当前除了这个plugin on job end之外还有什么是我需要做的呢？
> 我的意思是
> 应该需要看一下 下一个部分了对吗？

本轮具体 Sample 示例之后，用户反馈：

> 好的 我觉得差不多了
> 那么看一下下一个部分吧
> 还有什么需要单独看一下的吗？

接续本卡第②段的来源信息和奖励赋值；不将上述反馈记为已掌握全部展开机制。

## 尚不清楚

- 本轮优先理解：为什么取回 bundle 后还要做 Sample 转换，来源字段与奖励各放在哪里。
- 展开函数已按具体字段示例回查；完整可选分支仍未展开。外层组检查和最终清单随后接续。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：Dressage `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`，`rollout.py:624–674`；外层调用与接收位于 802–827 附近。
- `plugin.py:256` 的 get_result 仅从 `_results` 按身份取回 bundle；它对应前面 _finalize_attempt 的登记，不重新提交结果。
- [前序转换范围](../../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/01-scope.md)。
- [本步讨论过程](../../../../../../04-flow.md)。以上是静态源码核对与教学示例，未运行训练或转换实验。

</details>
