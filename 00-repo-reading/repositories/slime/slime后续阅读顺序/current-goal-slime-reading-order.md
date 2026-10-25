# 当前目标推进的slime阅读顺序

目标：对齐腾讯混元 Agent 强化学习框架工程师岗位，在已读完 Coding Agent 单题正常主线的基础上，继续学习**框架接入 → 评分扩展 → 批量调度 → 训练交接**。

[返回目录](README.md) · [岗位对应与评估依据](hunyuan-jd-reading-order-assessment-2026-10-25.md)

## 建议阅读顺序

| 顺序 | 模块与入口 | 读到能说明什么为止 |
| --- | --- | --- |
| 1. 框架怎样调用 Agent | [slime/rollout/sglang_rollout.py：generate_and_rm](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L289-L380) | 自定义 generate 怎样装载、调用；Sample 或列表怎样交回；已有 reward 时怎样处理 |
| 2. 评分逻辑怎样接入 | [slime/rollout/rm_hub/__init__.py：async_rm、batched_async_rm](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/rm_hub/__init__.py#L55-L110) | 单条与批量评分如何调用，自定义评分器接在哪里；先读接口，再选一个实现 |
| 3. 多条轨迹怎样组织 | [slime/rollout/sglang_rollout.py：generate_and_rm_group](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L388)，按需回查 GenerateState | 同一道题的多次采样如何并发、汇总和整组评分；并发限制与取消怎样影响结果 |
| 4. 持续生成怎样调度 | [slime/rollout/fully_async_rollout.py：AsyncRolloutWorker](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L82) | 沿 _loop、_make_done_cb、get_completed_groups 看任务生产、完成队列、背压与结果消费 |
| 5. Sample 怎样成为训练输入 | [slime/data/batch_builder.py：BatchBuilder.convert](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/batch_builder.py#L256)，连接 [RolloutManager._generate](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L335) | tokens、reward、logprob、mask 如何交成训练数据，哪些字段必须保持一致 |
| 6. 生成与训练怎样闭环 | [train.py：train](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/train.py#L13) | 生成结果怎样交给训练，训练后怎样更新生成侧权重；先看控制与数据交接 |

- **1、2 对应策略与评测接入**，最能承接已经读过的 Coding Agent。
- **3、4 对应并发、资源与稳定性治理**。当前示例实际使用 fully-async，第 4 项的关键路径需要覆盖。
- **5、6 对应训练视角与工程交接**。具体损失、并行通信和优化器内部按需后置。

## 当前第一步

先读 `generate_and_rm`，围绕三个问题：**谁调用我们的 Agent？返回值要满足什么？奖励由谁负责？**

```text
generate_and_rm
  → 选择 custom_generate_function_path
  → 调用已读的 coding_agent_rl.generate
  → 接住 Sample / Sample 列表
  → 判断是否还需要评分
```

## 贯穿主线的配套

- **测试与 Trace**：从第 1 项配套现有 `tests/plugin_contracts/`；到并发部分，选一个超时或取消案例，验证结果并定位问题。
- **Kubernetes**：从第 3、4 项同步实践。在已有简单部署经验上，重点补资源限制、服务连接和故障恢复。
- **Dressage**：遇到具体接口或评测抽象问题时做定点对照。

记录于 2026-10-25，源码基准为 Slime `18868a79`。本页保存选读路线，实际开始位置仍以[唯一路线](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)为准。
