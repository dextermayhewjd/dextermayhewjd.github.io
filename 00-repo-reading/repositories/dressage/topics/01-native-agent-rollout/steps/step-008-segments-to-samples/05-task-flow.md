# 05 · Step 008：一条任务轨迹的各段怎样交成 Sample 列表

> 从本次 trajectory_payload 取出已分好的段，为每段复制原任务模板，写入训练字段、文本与来源，再补原轨迹归属和奖励字段；最终 Sample 列表返回 generate 的 result。

[本步 scope](01-scope.md) · [本步函数卡](02-short-term-memory/overview.md) · [形成过程](04-flow.md#close-step008) · [项目唯一进度](../../../../README.md)

## 1. 本步在任务中的位置

Step 007 已通过 Proxy 收尾并取得本次执行的 trajectory_payload。本步不重新采集 API，也不重新将 StepRecord 切段；输入是已发布、已取回的轨迹段和原任务 sample。

本步从 generate:322 开始，停在 :331 的 result 赋值完成。Sample 真正返回外部前的 finally 属于 Step 009。

## 2. 已读部分怎样完成交接

下面是正常路径关系示意，使用代码注释标出数据变化；不是可直接运行的程序。

```python
generate
  segments = trajectory_payload.get("data") or []  # 取本次轨迹的段列表。
  result = multi_segment.expand_segments_to_samples(sample, segments, ...)
    # 按 segment_index 排序，准备同一轨迹的身份信息。
    for each segment:
      sample = copy.deepcopy(template_sample)     # 每段一份独立副本。
      sample.rollout_id = rollout_id              # 来自模板 index。
      -> write_sample_from_segment(sample, ...)
           # 取得一致的 token/mask/logprob 数组，按配置处理长度/版本。
           # 保留完整 tokens，定位响应起点，写入后缀 mask/logprob。
           # 填写 response、会话/任务/段资料和状态。
         <- 同一个 sample 副本已写好
      sample.metadata["parent_traj_id"] = sid     # 各段仍属于同一原轨迹。
      sample.metadata["segment_index"] = ...
      if not last segment:
        sample.reward = 0.0                       # 当前不计算任务奖励。
      out.append(sample)
    return out
  # result 已接住 Sample 列表，本步到此停止。
```

对应卡片：[generate 取段与接收列表](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)、[逐段组织](02-short-term-memory/functions/dressage/rollout/multi_segment.py/expand_segments_to_samples.md)、[单段字段转换](02-short-term-memory/functions/dressage/rollout/artifacts/samples.py/write_sample_from_segment.md)。

## 3. 最终结果的含义与去向

| 数据 | 在这里的含义 |
| --- | --- |
| result | 本次轨迹各段对应的 Sample 列表，不是系统中的全部任务轨迹 |
| sample.tokens | 当前段保留的完整序列，含输入上下文 |
| response_length | 从第一个输出 token 到序列末尾的长度，可能包含后续工具上下文 |
| loss_mask / rollout_log_probs | 对应响应后缀的训练位置与 logprob；本轮以内存列表路径为例 |
| response | 从消息中选取的 assistant 内容或回退文本，不是在此解码整个训练序列 |
| parent_traj_id / segment_index | 原轨迹归属与段号，使分段不被误当成独立答题 |

沿用本卡人工 token 示例：tokens=[10,11,20,30,40]、整段 mask=[0,0,1,0,1]，写入的 response_length=3、loss_mask=[1,0,1]。两次模型输出之间的上下文仍在响应区间内，但 mask 为 0。

若一条轨迹分成两个段，且模板 reward=None，则两个 Sample 的 parent_traj_id 相同、segment_index 不同；非末段 reward 被设为 0.0，末段仍为 None。若模板已有奖励值，末段保留该值。完整奖励计算和传播不在本函数发生。

## 4. 首轮收束与 Step 009 的衔接

2026-11-08 用户概括按 segment 填写模板并返回 Sample，要求保存 task flow 并进入 Step 009。本轮按正常主线收束；“每段复制模板副本”和“处理本次轨迹”已作澄清，不推断已掌握所有扩展路径。

保留边界：复杂截断、版本屏蔽、TransferQueue、专家回放、完整奖励归一化及传播未深入。数据长度校验、文本与训练数组区别、本地裁剪与状态判断区别已在函数卡说明；本轮不为填满细节继续下钻。

下一步回到 generate 的 return result，沿 finally 看 Proxy 上下文与沙箱回收责任。Step 009 先读正常返回，取消和失败随后按既定范围逐段看。

<details>
<summary>来源与验证</summary>

- Dressage 固定版本：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- generate:322–331；multi_segment.py:118–192；artifacts/samples.py:291–418。
- 用户原话和校准保留在函数卡及 04-flow 中。
- 数组转换用源码抽取函数和构造样本做过局部验证；状态枚举/传输边界使用替身。未运行实际模型、训练或端到端流水线。

</details>
