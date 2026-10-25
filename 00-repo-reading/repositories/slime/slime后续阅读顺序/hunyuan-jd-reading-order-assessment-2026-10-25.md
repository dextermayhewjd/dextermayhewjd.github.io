# Slime 后续阅读顺序与腾讯混元岗位：逐项评估

记录日期：2026-10-25。

[返回后续阅读顺序](README.md) · [岗位对照与一个月安排](../../../../slime_photo/code-reading/job-alignment.md#next-month-job-plan-20261025) · [官方岗位](https://careers.tencent.com/jobdesc.html?postId=2061654749727600640)

## 1. 明确结论

**现有 README 的四个阅读主题都直接对应这个岗位，`generate_and_rm` 作为第一入口也合理。** 这是一条方向正确的源码阅读路线；要用于一个月内的岗位准备，还需要补准实际调度模式，并把测试、Trace 和 Kubernetes 的实践完成标准写具体。

用户当前计划一个月内投递或面试，已经用过 kubectl、部署过简单服务。建议继续利用已读的 Coding Agent 单题主线，把下一阶段集中在框架接入、验证和运行治理上。

本文件是新增的评估记录，保留原 README 和其他阅读方案，不据此替换原计划或宣告下一步已经开始。

## 2. 四个阅读主题怎样对应 JD

| README 内容 | 对应岗位要求 | 评估 |
| --- | --- | --- |
| 策略与评测接入 | 职责 2、3：可复用组件、不同 Agent 策略和评估逻辑接入；要求 5、6：工程能力与需求承接 | **直接对应，适合最先读。** 能把单题实现接到统一框架接口，进一步验证扩展契约 |
| 批量任务与并发控制 | 职责 4：并发、资源、稳定性与性能；要求 1：Python、asyncio 和并发处理 | **核心内容，必须保留。** 需要按实际运行模式选入口，并验证慢任务、取消及结果完整性 |
| Trace 与故障定位 | 职责 1、2、4：实验复现、日志追踪和链路治理；要求 2、5：核心链路与工程实践 | **直接对应。** 基本 Trace 应贯穿接入和并发阅读，专题深入以具体故障为对象 |
| 训练数据交接 | 职责 5：从训练视角推进工程落地；要求 4：了解至少一类训练或自动评估流程 | **直接对应，当前深度合理。** 先解释 Sample 怎样被消费，再按需要深入损失和并行实现 |

配套契约测试也选得合理，能回应接口验证与软件工程要求。Kubernetes 已在原 README 中列出；问题不是遗漏，而是安排仍较概括。

## 3. 需要明确修正的三处

### 3.1 批量调度：注明实际运行模式

当前示例的[启动脚本第 165–167 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/run_qwen38_27b_fully_async.sh#L165-L167)选用：

```text
--rollout-function-path slime.rollout.fully_async_rollout.generate_rollout_fully_async
--custom-generate-function-path examples.coding_agent_rl.generate.generate
```

原 README 主要安排的是 `sglang_rollout.generate_rollout_async`。它适合学习基础批量调度；若要解释当前示例的实际运行，还需要接上 [AsyncRolloutWorker._loop](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L178-L243)：该循环持续接纳任务、调用共同的 `generate_and_rm_group`，并根据完成队列控制继续取任务。

- “完整的 fully-async 文件暂缓”可以保留。
- 当前路径实际用到的任务接纳、完成队列和背压需要解释清楚。
- 阅读顺序可以由内向外；记录中要分清它与真实调用方向。

### 3.2 测试与 Trace：贯穿阅读，并形成验证结果

原 README 已列出[生成契约测试](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tests/plugin_contracts/test_plugin_generate_contracts.py)与[路径装载契约测试](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tests/plugin_contracts/test_plugin_path_loading_contracts.py)。这些包含无需 GPU 的替身测试，适合作为起点；保存或阅读测试文件本身不代表测试已运行。

建议将“能说明接口”的结束标准补充为：

- 接入一个范围小的自定义策略或评分逻辑，通过相关契约测试。
- 制造一次失败、超时或取消，检查返回状态、结果完整性与资源清理。
- 用 Trace 指出问题发生在哪个任务、哪个阶段，并保存能复现的输入和配置。

`trace_span` 已有阅读基础。后续更有价值的是沿真实问题使用它，而不是把重新读装饰器或上下文管理器当作整个观测能力的完成标准。

### 3.3 Kubernetes：从原则补成有限、可检查的实践

岗位明确要求容器与 Kubernetes，以及集群开发、部署、排障或性能优化经验。针对已有的基础部署经验，建议补齐一个有限案例：

- 部署任务 worker 和服务接口，说明它们怎样通过 Service 通信。
- 设置资源限制、任务超时和结果保存方式。
- 复现并排查一次 Pod、资源或服务连接故障，记录恢复过程。

这条实践可以从批量运行阶段同步推进。无 GPU 时可先使用 CPU 任务或可控模型服务替身；按实际环境描述验证结果，不把本地模拟当成真实 GPU 训练或生产集群经验。

## 4. 建议保留怎样的主顺序

**简短确认训练全景 → 策略/评测接入 → 实际模式下的批量调度 → 训练数据交接。**

- **测试与基本 Trace 全程配套。** 独立的 Trace 深入保留，但围绕失败、慢任务及实验复现展开。
- **Kubernetes 从批量阶段同步实践。** 不需要等所有源码读完才开始积累部署和排障证据。
- **训练详细阅读仍可放后面。** 开始前只需知道 `Sample → 训练 → 权重更新 → 下一轮生成` 的位置，不必先通读所有损失或 Megatron 底层。
- **Dressage 作为定点设计对照。** 带着具体的环境接口、阶段钩子或奖励抽象问题去比较；岗位没有指定必须掌握某一个开源框架。

这保留了原路线的主体，同时补上实际运行方式和可验证的结束条件。

## 5. 推荐的下一处入口

仍推荐 [generate_and_rm](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L338-L380)。它直接承接已经读过的 Coding Agent，适合先解决：

- 框架怎样找到并调用自定义 `generate`？
- 返回 `Sample` 或列表后，框架怎样接收？
- 已经有 `reward` 时是否再次评分，失败状态怎样传递？

`_generate` 中尚未集中回看的状态处理、失败返回与最终清理，可作为这项接口契约的必要回查。下一步具体范围仍在接续时确认；本次保存评估不自动创建新的阅读步骤。

## 依据与边界

- 官方职位：腾讯“混元 Agent 强化学习框架工程师”，`postId=2061654749727600640`。本轮于 2026-10-25 从官方接口取得内容，岗位更新日期为 2026-10-20，工作经验字段为一年以上。
- [取证元数据与岗位要点](../../../../slime_photo/code-reading/job-evidence/2026-10-25-tencent-2061654749727600640.json)保存接口来源与原响应校验值。
- Slime 源码固定为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。本次核对了上述代码与测试文件，没有运行新增实验、部署或训练。
- 这里评价的是阅读选题和准备方式，不使用没有分母的岗位覆盖百分比，也不据此判断具体面试必考或不考内容。
- 实际阅读进度继续见[唯一路线](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。
