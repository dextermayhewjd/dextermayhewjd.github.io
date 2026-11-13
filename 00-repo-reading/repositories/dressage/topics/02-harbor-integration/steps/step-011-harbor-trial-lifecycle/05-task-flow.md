# 05 · Step 011：Harbor 完成一次任务尝试，再把结果交回 Dressage

> Job 安排多个 Trial；每个 Trial 准备环境与 Agent，执行任务和评测，收尾并返回 TrialResult。Job 汇总成 JobResult，Dressage 再把尝试结果与轨迹整理回原工作组。

[本步 scope](01-scope.md) · [函数记录](02-short-term-memory/overview.md) · [形成过程](04-flow.md#step011-first-pass-closure)

## 1. 本步在任务中的位置

Step 010 已读的 _run_partition 为当前 partition 创建 Job 与插件。本步从它的 `await job.run()` 进入 Harbor，沿普通单步任务、install_only=False、无 user-agent bridge 的正常路径阅读。

```python
# 调用方：Dressage._run_partition，rollout.py:760–762。
await plugin.on_job_start(job)  # 运行前配置插件、登记生命周期回调。
result = await job.run()        # 本步展开这里；最终接住 JobResult。
await plugin.on_job_end(result) # 整个 Job 返回后的插件收尾。
```

Harbor 源码采用 v0.25.0 发布版；Dressage 调用方仍是其固定 0.18 依赖版本的源码。这里接清接口职责，不表示两个版本已经完成运行适配。

## 2. 已读部分怎样完成交接

以下为正常执行关系图，包含 Task 内部调用，不是可执行代码。队列内部已定位的包装只保留名称。

```text
Job.run
├─ 建立 JobResult，准备汇总本 Job 的结果
├─ await _run_trials_with_queue
│  ├─ submit_batch：按剩余 TrialConfig 返回协程
│  ├─ TaskGroup：创建 Task，等待这批任务完成
│  │  └─ 每个 Task 执行队列包装，创建 Trial、挂接回调，再运行 Trial.run
│  │     ├─ 建立 TrialResult，通知 START
│  │     ├─ await _prepare：检查前提，启动环境，准备已选定的 Agent
│  │     ├─ await SingleStepTrial._run
│  │     │  ├─ 运行 Agent，按需上传日志，收集产物
│  │     │  └─ 按共享/独立环境安排评测与 Agent 环境停止
│  │     ├─ finally：await _finalize，处理环境、保存结果、通知 END
│  │     │  └─ 回到 Trial.run，继续脱敏与关闭日志
│  │     └─ return TrialResult：经队列包装交回对应 Task
│  └─ 收集各个 Task 的结果，返回 list[TrialResult]
└─ 合并已有结果与本次结果，计算统计，return JobResult

_run_partition 接住 JobResult，继续 on_job_end 和组结果整理
```

函数入口：[Job.run](02-short-term-memory/functions/harbor/job.py/Job.run.md#job-mainline) → [队列提交与等待](02-short-term-memory/functions/harbor/job.py/Job._run_trials_with_queue.md#queue-mainline) → [Trial.run](02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#normal-lifecycle)。

Trial 内部：[准备](02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-mainline) → [执行与评测](02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run.md#single-step-run-mainline) → [收尾](02-short-term-memory/functions/harbor/trial/trial.py/Trial._finalize.md#finalize-mainline)。

回调与普通返回分开理解：插件在运行前登记函数，Trial 执行到对应事件时调用它们；_on_end 发生在单个 Trial 收尾期间，on_job_end 是整个 Job 返回之后的另一调用。回调不是挂在 result 上自动触发，result 是事件携带的数据。回调传递细节仍可按需回查，不作为本步结束门槛。

## 3. 结果的含义与去向

| 从哪里交出 | 交出什么 | 谁接着使用 |
| --- | --- | --- |
| _prepare / SingleStepTrial._run / _finalize | 正常返回 None；更新现有 Trial 的状态、结果或产物 | Trial.run 继续下一个阶段 |
| Trial.run | 这一次尝试的 TrialResult | 队列包装处理，最终交回该 Task |
| _run_trials_with_queue | 按提交顺序组成的 TrialResult 列表 | Job.run 合并与统计 |
| Job.run | 整份 JobResult，包含尝试结果与统计 | Dressage._run_partition |
| _run_partition | 原分区顺序的 _GroupOutcome 列表，带 Samples 或错误 | _run_round 与外层批次逻辑 |

接回 [Step 010 第 4 部分](../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#collect-outcomes)：用最终 TrialResult 匹配插件的轨迹 bundle，结合模板转换 Sample；检查父轨迹数量及可选单版本要求，再登记最终选用产物，按原组位置返回。

ArtifactStore 管理尝试产物和最终选用状态；组错误仍保存在返回的 outcome 中。结果处理成功不等于答对题，奖励为零的正常轨迹也可以参与后续处理。当前只确认这些交接，不重复展开转换和写文件实现。

## 4. 本步收束与下一步

2026-11-12 按用户请求收束 **Step 011 的首轮职责与正常返回阅读**。已读部分足以连接准备、执行、收尾及结果归组；未展开的回调细节、重试、具体环境后端、Agent/Verifier 内部继续保留为未知，不能据此宣称已掌握或已运行整套系统。

下一步仍是 **Step 012：用一个任务例子区分 Task、Agent、Verifier 的替换位置**，而不是直接跳过它。只需看清题目/工作区与环境要求、Agent 选择、验证规则和评分产物之间的接口；本步已读的生命周期、安装入口与执行顺序直接复用。之后再到 Step 013 对照环境接口与现有 Agent Sandbox 适配器。

Step 012 目前仍只有预备 scope，旧链接依据 0.18；正式进入时先对照 0.25 校准相关入口。本次不预建其函数卡或继承目录，也不启动框架升级或集群实验。

<details>
<summary>源码、记录与验证范围</summary>

- Harbor 发布版提交 fdba28fc411e47e8765420a1a063b4918fce3def：job.py:1082、1229；trial/queue.py:194、239、253；trial/trial.py:601、641、660；trial/single_step.py:37。具体固定源码链接见上面的函数卡。
- Dressage 固定提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c：integrations/harbor/rollout.py:675–900，artifacts.py:537 起；采用已有读取结果核对结果归组、组检查与产物选用。
- 已保存的用户复述包括 Job 结果汇总、队列协程/Task 等待、Trial 生命周期、执行与评测、最终产物记录。对回调存储和触发仍有明确疑问，按当前范围保留，不抹去这些记录。
- 全部为静态源码阅读与文档校对；本步没有运行 Job、Agent、Verifier、模型、Kubernetes 或训练实验，也没有证明 Dressage 与 Harbor 0.25 兼容。

</details>
