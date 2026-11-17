# 奖励处理扩展点：Slime 与 Dressage 的关系

记录日期：2026-11-17。用途：回顾已读代码、准备框架扩展类面试问题；不新增必读步骤，不代表完整训练已验证。

## 这次确认的理解

用户原话：

> 只需要这里有自定义的部分 那么就完全可以通过load function来自行加入是我的理解

核对后的表述：**框架在指定位置提供扩展入口，启动时按函数路径加载实现，运行时按照约定的输入输出调用它。Slime 提供入口，Dressage 提供针对分段轨迹的具体规则。**

`load_function` 负责找到函数；它本身不保证签名、返回结构或业务语义正确，也不会让一个函数自动出现在任意调用位置。兼容性仍需由调用合同和测试验证。

## 我们已经在哪里读过

| 内容 | 真实阅读记录 |
| --- | --- |
| 原始奖励、组内归一化、按 rollout 去重并映射回各 Sample | [Slime Step 016：BatchBuilder._post_process_rewards](../../../slime/topics/02-rollout-reward/steps/step-016-sample-to-train-data/02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder._post_process_rewards.md)；保留了用户“我差不多理解了”的反馈 |
| 组装训练字段、loss mask、按 rollout 汇总 mask 总和 | [Slime Step 016：BatchBuilder.convert](../../../slime/topics/02-rollout-reward/steps/step-016-sample-to-train-data/02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.convert.md)；具体损失归约当时留白 |
| 按已有边界切段、拼接训练数组 | [Dressage Step 007：分段函数卡](../../topics/01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/02-short-term-memory/functions/dressage/proxy/server.py/_split_session_into_lineage_segments.md)；边界产生和 TITO fallback 没有完整展开 |
| Segment 转 Sample、轨迹归属、末段奖励 | [Dressage Step 008：形成过程](../../topics/01-native-agent-rollout/steps/step-008-segments-to-samples/04-flow.md)；Step 015 又回看了 Harbor 的转换与奖励归属 |

此前助手将“没有完整精读 Dressage 的具体实现”说成“奖励广播这一类机制尚未读过”，范围过大。**Slime 中的基础机制已有阅读；Dressage 的 anchor 规则与 Prompt-Equal 是需要比较的差异，而不是重新学习整条奖励链。**

## 两个扩展入口，避免把调用关系串错

以下为本地 Slime `18868a79` 的教学节选，省略其他初始化与字段拼装。

```python
# 初始化时，按配置加载奖励后处理函数。
self.custom_reward_post_process_func = load_function(
    self.args.custom_reward_post_process_path
)

# _post_process_rewards：有自定义函数就直接交给它。
if self.custom_reward_post_process_func is not None:
    return self.custom_reward_post_process_func(self.args, samples)
```

该入口的合同是 `args, samples → raw_rewards, rewards`；两个结果列表都应与输入 Sample 按位置对应。没有配置时才使用内置规则。

另外，`BatchBuilder.convert` 也有**整个训练数据转换的扩展入口**。若配置了它，会直接调用自定义转换函数，不再执行默认 convert 的奖励调用与字段拼装。

Dressage `3e3142fe` 的 Harbor 训练示例同时配置：

```text
--custom-reward-post-process-path dressage.training.reward_post_process.reward_post_process
--custom-convert-samples-to-train-data-path dressage.rollout.convert_samples.convert_samples_to_train_data
```

其中 Dressage 的 `convert_samples_to_train_data` 内部直接导入并调用自己的 `reward_post_process`。所以不能把“两项配置”理解成奖励会被重复处理两次。

源码定位：[Slime 初始化](/home/hongshi/projects/slime/slime/data/batch_builder.py:39)、[奖励扩展入口](/home/hongshi/projects/slime/slime/data/batch_builder.py:207)、[整体转换扩展入口](/home/hongshi/projects/slime/slime/data/batch_builder.py:256)、[Dressage 训练示例](/home/hongshi/projects/Dressage/examples/harbor/run_harbor_training_qwen3.5_4b.sh:65)、[Dressage 自定义转换](/home/hongshi/projects/Dressage/dressage/rollout/convert_samples.py:89)。这两份 checkout 的版本不同，不将其描述为已经联合验证过的训练组合。

## Dressage 多出来的规则是什么

- **Anchor 与广播：**Slime 已读内置实现要求同一次 rollout 的各段原始奖励一致；Dressage 允许非末段为 0，先按 `parent_traj_id` 找到最大 `segment_index` 的 anchor，再处理并广播给兄弟段。原始奖励与处理后奖励分开，raw_rewards 不做同样广播。
- **Prompt-Equal：**Slime 已读默认转换按 rollout 汇总 mask；Dressage 在 GRPO / Reinforce++ baseline 分支按 `instance_id` 聚合同一题目的有效 mask，生成相应分母。`parent_traj_id`、`rollout_id`、`instance_id` 的职责不同，不能混用。
- **切段时机：**请求处理时记录边界，finalize 时按边界分段、组装记录；不能笼统描述为每次断裂立刻写出完整训练证据。

具体来源：[reward_post_process](/home/hongshi/projects/Dressage/dressage/training/reward_post_process.py:79)、[Prompt-Equal 分母](/home/hongshi/projects/Dressage/dressage/rollout/convert_samples.py:30)、[finalize 分段调用](/home/hongshi/projects/Dressage/dressage/proxy/server.py:2801)。本次为静态核对，没有新增训练运行证据。

## 面试时可以怎样说明

> 我会先找框架已经提供的扩展入口，确认调用时机、输入输出和默认行为，再通过配置加载自己的实现。比如 Slime 的奖励后处理入口可以接入 Dressage 的分段轨迹规则：先按原始轨迹选奖励锚点，再归一化并分配给各段。这样主流程仍由框架组织，策略可以替换。验证不能只检查函数能否导入，还要检查结果数量与顺序、分段归属，以及自定义转换是否绕过了默认处理。

这是可用于准备的工程案例，不是对具体面试题的预测。当前无 GPU 的 MiniMax 评测路径不执行这些训练广播与归一化规则；不能拿 API 或 Harbor Trial 成功代替训练正确性的证据。

## 回到当前实施目标

目标与停止条件沿用 [实施入口](../minimax-harbor/README.md) 和 decision-001；实时进度只看 Backlog。

- [MH-007](../minimax-harbor/backlog/tasks/mh-007%20-%20通过现有-Dressage-插件完成-MiniMax-单题-Harbor-Trial-验收.md)：单题 Harbor 基线及可控失败/超时清理。
- 随后将 Harbor 的 Environment 后端接到 Agent Sandbox，并核对冷创建、预热与少量并发、代表性任务和资源回收。
- [MH-004](../minimax-harbor/backlog/tasks/mh-004%20-%20核对-Slime-无-GPU-发起路径与实际版本.md)：最终从 Slime 无 GPU 发起的既定目标仍需完成，不因独立 Harbor 运行成功而自动满足。

不追加完整训练算法、调度器重写或通用 SDK 为本轮前置。
