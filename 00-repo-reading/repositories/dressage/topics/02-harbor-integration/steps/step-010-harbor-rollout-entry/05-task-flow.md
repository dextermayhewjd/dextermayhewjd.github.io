# 05 · Step 010：从批量 rollout 入口定位 Harbor 执行

> 最终收束（2026-11-11）：用户确认 Step 010 主线结束。首次总结之后，又补读了数据源配置/spec 来源、模板组到工作项、按指纹分区、Job 配置与插件交接、结果归组、重试及批次返回；记录见[函数索引](02-short-term-memory/overview.md)。最终得到 Sample 组与 metrics，训练路径由外层包装交回 Slime。以下正文保留首次总结的历史粒度，“当时未展开”不表示本次补读未发生；全部异常与内部算法仍未通读，未运行集群或训练实验。

> Slime 反复发起批次请求；Dressage 数据源提供 Harbor 任务模板，批次函数组织执行与结果检查；下游创建 Harbor Job、挂接插件，最终将样本组与指标交回外层。

[本步 scope](01-scope.md) · [函数记录](02-short-term-memory/overview.md) · [形成过程](04-flow.md#transition-step011)

## 1. 本步位置

当前路径是 Slime 的批量 rollout hook，不是此前原生单任务 blackbox_dispatch.generate。任务来源由 Harbor JobConfig 指定，通过 Dressage HarborDataSource 取得本批模板组。

## 2. 已读主干与下游交接

```python
generate_rollout_harbor_sync
└─ run(_run_harbor_rollout(...))
   ├─ 准备配置、Proxy 能力与 Gateway runtime
   ├─ get_samples / _resolve_work  # 准备本批 work。
   ├─ pending → _run_round        # 执行与失败组去向由父函数组织。
   │             └─ run_partition → _run_partition
   │                  ├─ _CREATE_JOB(job_config)
   │                  ├─ _PLUGIN_FACTORY(...)
   │                  ├─ plugin.on_job_start(job)
   │                  ├─ await job.run()
   │                  └─ plugin.on_job_end(result)
   ├─ completed → ordered       # 恢复组顺序，检查有效性与版本。
   └─ return ordered, metrics
```

这是跨函数关系示意，非可执行代码。父函数六段已介绍；_run_round、_run_partition 的整体实现只作职责与关键调用定位，不能算作已深读。

进入：[批量入口卡](02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/generate_rollout_harbor_sync.md)；[批次父函数卡](02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_harbor_rollout.md)。

## 3. 本步结果与边界

ordered 保留 Sample 组结构，metrics 保存统计。训练返回由外层包装为 RolloutFnTrainOutput；evaluation 分支使用相应评估返回。有效组不等于高分组，权重版本检查不等于更新模型权重。

Slime 外层决定何时发起下一批；本函数内部的 pending 管理本批重试或替换后的工作，不能把两种循环混为一谈。

## 4. 本轮收束与下一步

2026-11-10 用户要求折叠第 3 段并开始 Step 011。本轮在批次父流程与 Job/插件最小交接层次收束，以下留作按需回查：Gateway 内部、数据源细节、容量调度、_run_partition 的完整结果合并与失败处理。未运行训练、Job 或集群。

下一步从 Harbor 的 Trial.run 看一次任务尝试。它位于 Job 的调度之下，不是 _run_round 函数体内的一个代码分段。

<details>
<summary>源码与验证</summary>

Dressage 固定版本 3e3142fe8ea07e4504c3b20a936a4c201a3de44c；rollout.py:1026–1277、675 起、903 起。Slime 批次循环按子模块 aaf5c209 核对；Harbor 采用 0.18.0 固定提交 527d50deb63a5d279e8c20593c18a2cbc7f61f9e。均为静态阅读，不作端到端兼容验证结论。

</details>
