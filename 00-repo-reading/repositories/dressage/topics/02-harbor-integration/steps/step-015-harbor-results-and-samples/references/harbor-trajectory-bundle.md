# HarborTrajectoryBundle：身份、评分和 Proxy 轨迹怎样放到一起

[当前主线：scope 3.2 结果包构造](../01-scope.md#bundle-handoff) · [返回 _finalize_attempt](../02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._finalize_attempt.md)

**代码归属：Dressage。** 本轮只查看结果包字段、构造处和 trainable 条件，不完整展开 commit_attempt、持久化或恢复逻辑，不将此说明当作这些函数已读完的记录。

源码版本：`3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。所有数值样例是静态教学构造，未运行真实任务或训练。

## ① 先看三份信息从哪里来

```text
_finalize_attempt 的 record
  └─ Trial / session / instance 身份 ─────────┐
                                             │
Harbor event.result                          ├→ HarborTrajectoryBundle
  └─ verifier_result.rewards ─────────────────┤
                                             │
Dressage Proxy 的 read_trajectory 返回值      │
  └─ payload["data"] → segments ──────────────┘
```

record 并非整个复制进 bundle，而是把身份等字段传给提交层。实际文件产物仍在 Harbor 的 artifacts 目录中，这个对象不把目录里的代码文件整体打包进去。

对应的真实准备语句节选：

```python
# 使用当前尝试的会话身份，向 Proxy 取模型轨迹；不是读取 Harbor 的 trajectory.json。
trajectory_payload = await proxy_client.read_trajectory(
    trajectory_id=session_id,
    instance_id=instance_id,
    drain=False,
)
segments = _payload_segments(trajectory_payload)  # 提取返回值 data 列表中的字典。
rewards = _extract_rewards(trial_result)         # 本次单步场景取 verifier_result.rewards。
```

以上省略读取条件和错误处理。取回后还会验证评分、轨迹身份/完整性、token 数组与版本等，不能把“读到了数据”直接视为“可以训练”。

## ② 构造处：每组数据放进哪些字段

真实构造调用节选，省略元信息、策略、失败记录与时间等必需/可选参数，不能直接当作完整构造示例运行：

```python
bundle = HarborTrajectoryBundle(
    # 归属：以后按这些身份对上同一次尝试及其 Proxy 会话。
    trial_name=trial_name,
    trial_id=trial_id,
    session_id=session_id,
    instance_id=instance_id,

    # 评分：保留全部评分，并选出本次使用的那一项。
    rewards=rewards,
    reward_key=self.reward_key,
    reward=rewards.get(self.reward_key),

    # 模型轨迹：分段 token、mask、logprob 等记录。
    segments=segments,
    trainable_token_count=token_count,
    # 其余参数见原函数构造处。
)
```

例如，假设 Harbor 返回的评分为 `{"reward": 1.0}`，配置 reward_key 为 `"reward"`，则：

```python
# bundle 的部分字段视图，不是完整对象构造或完整 JSON。
rewards = {"reward": 1.0}  # 全部评分的字典。
reward_key = "reward"    # 本次选择的评分名称。
reward = 1.0             # 从字典中取出的该项值。
```

segments 中的一段可能包含以下字段。数字为教学值，仅展示对齐关系；省略身份、完整性与版本等信息，不声称这个片段可以独立通过验证：

```python
{
    "tokens": [101, 102, 501, 502],
    "full_loss_mask": [0, 0, 1, 1],
    "full_logprobs": [0.0, 0.0, -0.1, -0.2],
}
```

三组数组沿同一 token 序列对齐；mask=1 的位置是此处统计的可训练 token。此片段贡献 2 个，整个 bundle 的 trainable_token_count 统计全部 segments。mask=0 位置的 0.0 只是例子里的占位值，不是模型实际计算概率的证据。如何生成这些数组沿用前面的 Proxy 阅读，不在这里重讲。

## ③ trainable：有结果包，不代表当前数据就合格

构造之后的真实条件：

```python
bundle.trainable = (
    not cancelled
    and checkpoint is FinalizationCheckpoint.TRAJECTORY_SNAPSHOTTED
    and not any(failure.fatal for failure in bundle.failures)
    and token_count > 0
)
```

可以读成：这次没有取消，已取到轨迹快照，没有致命失败，并且有参与训练的 token。这里的 failures 包括前面收集/校验产生的问题，不只检查一次命令是否报错。

| 例子 | 此处会怎样看待 |
| --- | --- |
| reward=0，但评分合法、轨迹完整、其他条件满足 | 不会仅因低分被判为不可训练 |
| reward=1，但轨迹不完整或数组校验失败 | 不能仅因高分就通过，需要看致命失败记录 |
| 已取消、没取到轨迹或没有可训练 token | 不满足上述 trainable 条件 |

这里评价的是训练数据是否满足条件，不是 Agent 是否答对题。

**还有一个后续边界：** 类定义中 `superseded=True` 是初始值，结果选用阶段再决定选择哪次尝试。即使当前算出 trainable=True，也不能说它已经被最终选用或送进训练；后续提交、清理和结果选用还可能使结果失效。该区别用于接回 scope 第 4 项，不在本轮展开全部选用逻辑。

## 当前读到这里即可

能说清身份来自 record、评分来自 Harbor、segments 来自 Proxy，以及低分不等于坏数据，就可以返回 _finalize_attempt 的 `record.bundle = bundle`，再接后续结果选用。原始文件产物、Harbor 的 ATIF 轨迹与这个结果包继续分开理解。

<details>
<summary>源码入口与验证边界</summary>

- [字段定义](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:123)。
- [Proxy 读取与提取](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:389)、[构造与 trainable 判断](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:445)。
- [评分和轨迹验证](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:846)，本轮仅核对输入输出及判断依据，不逐项精读。
- [_payload_segments](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:1033)、[_extract_rewards](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:1056)。
- [后续结果选用标记](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:568)。
- [本步讨论](../04-flow.md)。代码节选不代表完整提交实现，未运行模型、提交或训练。

</details>
