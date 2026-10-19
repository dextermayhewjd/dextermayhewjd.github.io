# 第 7 章 训练交接、策略版本与权重更新

[阅读路线](../../repo-reading-route.md) · [总目录](../../README.md)

**目录 ID：** `07-training-handoff`
**产物状态：** planned
**学习状态：** 统一见[阅读路线的当前接续](../../repo-reading-route.md#当前接续)。

**问题：** 生成的轨迹怎样被训练消费，更新后的模型怎样继续服务下一轮任务，如何保留一致性？

**前置：** 02、03、05、06；了解 Sample、结果传输与模型服务。

**图文对照：** 4.2、5.1、7.8；7.9 与 SFT 作为第二遍。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 生成、训练、保存与更新主循环 | [train.py · train](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/train.py#L13) | trace | 第一遍读职责与顺序；Megatron 张量并行和全部算法推导后置。 |
| 模型训练消费 | [slime/backends/megatron_utils/actor.py · MegatronTrainRayActor.train_actor](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/actor.py#L449) | trace | 定位 reward、advantage、logprob、mask 的消费；不能假设所有字段在生成阶段已经算好。 |
| 权重发布 | [slime/backends/megatron_utils/actor.py · MegatronTrainRayActor.update_weights](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/actor.py#L628) | trace | 暂停/版本/内存或磁盘更新；与 GPU/模型服务生命周期共同理解。 |
| 共同 checkpoint | [slime/data/checkpoint.py · save_checkpoint](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/checkpoint.py#L39) | trace | 模型/优化器状态与数据进度共同恢复；仅完成一次训练不等于可恢复 checkpoint。 |
| SFT 样本生成 | [slime/rollout/sft_rollout.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sft_rollout.py#L1) | locate | 审核后的轨迹可重新编码用于 SFT；需要概率信息的 RL 不能只用最终文本补齐。 |

**章内顺序：**

1. 画 train() 的生成 → 训练 → 数据完成确认 → checkpoint → 暂停与权重更新 → 继续生成。
2. 从 Sample 跟到 actor 的数据读取与 train_actor，说明 tokens、loss_mask、reward、rollout_log_probs 与 advantage 的用途和产生位置。
3. 追一个策略版本跨越生成与训练的情景，分清异步旧策略数据和 SGLang/Megatron 数值不一致两类问题。
4. 第二遍按具体算法读 loss.py 与 examples/train_infer_mismatch_helper/；权重传输细节再读 update_weight/ 与 delta-weight-sync 文档。

**验收问题：** 更换 Agent 策略为什么可能影响训练数据合同？哪些数据必须在生成时保留？异步生成与训练更新如何协调？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](../../repo-reading-route.md#当前接续)。
