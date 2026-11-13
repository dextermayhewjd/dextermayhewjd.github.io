# 01 · Dressage Step 017：整合已有验证，形成可复跑的接入证据

[主题入口](../../README.md) · [项目进度](../../../../README.md) · [前一范围](../step-016-cancellation-and-retries/01-scope.md)

> 状态：2026-11-12 按真实调用交接调整。本页是已确认的后续 scope；本轮只更新范围与导航，尚未开始本步阅读或创建函数卡。 Harbor 入口统一依据 v0.25.0 发布版；没有运行任务、安装、模型或集群验证。

## 1. 阅读目标

**用固定任务、配置和版本复跑正常与故障路径，确认环境、模型、评测和结果对应一致，整理可以解释的证据。**

## 2. 指挥官、入口条件与边界

1. **执行入口**：沿用 [Job.run:1082](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1082) 与已有 Trial 生命周期；需要训练输出时再验证 Dressage 的 generate_rollout_harbor_sync，不另造调度器。
2. **前置核对**：选定 Harbor 版本、环境适配实现、模型/控制接口与凭据条件。复用 013–016 的局部证据；版本门禁或缺失实现尚未解决时，不宣称三方已接通。
3. **停止位置**：一份可复跑配置与结果记录，包含正常任务、一个相关失败/取消以及少量并发；多 Agent 与热领取在接口可用时加入，未完成项分别列出。
4. **不要求**：完整 GPU 训练、所有 Agent、所有隔离后端、多集群或性能最优。只有具备真实训练字段时才验训练产物，已有同等案例优先复用。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

沿用 Step 010、011 的整体主线，各步保持相同图形结构。**本步不是正常调用链中的新函数阶段，而是把前面已经明确的接口和局部验证串成一次复跑。** 具体入口与返回位置见 3.2；图中回调和 HTTP 均标明交互方式，不当作同一同步调用栈。

图内 **[本步·验收]** 标出要复跑和检查的节点；本步覆盖整条已有链，不对应一个新的业务函数。

```python
# 关系示意，不是可执行代码；标记的是本步观察位置。
Slime 的 rollout hook
  -> generate_rollout_harbor_sync                 # 训练入口；API-only 路线不必执行这里。
       -> _run_harbor_rollout -> _run_round -> _run_partition
            -> _CREATE_JOB(job_config)          # 创建 Job 时组成各次尝试的配置。
            -> plugin.on_job_start(job)          # 挂接路由配置与生命周期回调。
            -> Harbor Job.run  # [本步·验收入口] 固定版本与配置，复跑已有整条链。
                 -> _run_trials_with_queue -> TrialQueue -> Trial.run  # 队列交接后进入一次尝试。
                      -> _prepare                # 环境与 Agent 准备。
                           -> Environment.start  # [本步·验收] 就绪、命令、文件能力与回收证据。
                                -- 目标接缝 --> K8s 适配 -> Agent Sandbox -> Pod  # [本步·验收] 真实冷创建；按目标追加并发与热领取。
                           -> Agent.setup        # 环境就绪后准备已选定的 Agent。
                      -> _run
                           -> _run_agent         # 把题目交给 Agent，执行中请求模型。
                           -> _collect_artifacts # 收集产物；按评测模式安排环境停止。
                           -> _run_verifier  # [本步·验收] 题目检查与评分对应实际执行。
                      -> _finalize  # [本步·验收] 成功/失败的收尾与远端资源状态。
                           == END 事件 ==> plugin._on_end
                                            # 本步核对提交与资源释放的实际证据。
            <- JobResult  # [本步·验收] 汇总结果、错误与产物身份一致。
            -> plugin.on_job_end(...)           # 整份 Job 返回后的插件收尾。
            -> _bundle_samples                   # 训练路线的结果转换。
       <- Sample 组与 metrics
  <- RolloutFnTrainOutput

# Agent.run 期间的模型交互，不是等 Trial 结束才发请求：
Agent == HTTP ==> Gateway -> Dressage Proxy -> 模型服务  # [本步·验收] 真实模型请求与当前 trial/session 对应。
# 只做 API 评估时，调用方也可以从 Harbor Job 进入，不启动 Slime 训练。
```

<a id="reading-navigation"></a>

### 3.2 本步骨架与阅读顺序

下面是普通单步任务的教学裁剪。按编号进入当前局部，弄清交接后回到真实调用方；前置回查、能力对照和验证不会冒写成一条连续执行栈。

```python
# 验证顺序，不是新增的源码调用栈。
[1] 复核已经选定的版本、配置和接口
[2] 复跑 013 的冷创建基线：文件/命令/Verifier/环境回收
[3] 复跑 014–015 的真实 Agent：模型请求/尝试身份/评分/轨迹
[4] 复跑 016 的一个故障：取消或失败/清理/最终结果选择
[5] 加少量并发；按目标验证换 Agent 与热领取
[6] 保存配置、源码版本、日志与结果；需要训练时再验真实 Sample 合同
# 任何失败回到对应步骤的实际接口修复，不另起泛读模块。
```

<a id="reading-sequence"></a>

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. 确认本次可执行范围 | [环境](../step-013-harbor-kubernetes-environment/01-scope.md) · [模型](../step-014-model-routing-and-api-contract/01-scope.md) · [结果](../step-015-harbor-results-and-samples/01-scope.md) | 列明已实现与未实现的接口，区分已有静态核对、替身测试和真实运行。 |
| 2. 环境与评分复跑 | [Job.run](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1082) → [Trial.run](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L601) | 用同一确定性任务确认文件、命令、评分和回收；这是复跑已有局部验证，不拖到此处才首次检查。 |
| 3. 真实 Agent 与轨迹 | [Agent 执行与模型请求](../step-014-model-routing-and-api-contract/01-scope.md) → [评测与结果](../step-015-harbor-results-and-samples/01-scope.md) | 用一个 trial/session 对齐请求、输出、评分和轨迹；模型连通不替代完整采集合同。 |
| 4. 故障与并发 | [取消/失败路径](../step-016-cancellation-and-retries/01-scope.md) · [Agent Sandbox 导航](../../../03-agent-sandbox/README.md) | 复跑一条故障、少量并发；预热要有热领取证据，不能只凭配置存在。 |
| 5. 整理证据与取舍 | 现有项目的运行配置、日志与结果；[Step 010 返回合同](../step-010-harbor-rollout-entry/01-scope.md) | 说明改动在哪里、为什么这样接、怎样验证及未完成边界；没有真实 token/logprob 不用占位值宣称可训练。 |

**验证从前面各步开始**：013 验环境，014 验请求，015 验结果，016 验故障，本步负责整合与复跑。步骤 scope 准备完毕不表示这些验证已经执行。

**岗位证据**：用一个有限的接口改动与正常/失败验证说明组件接入、资源管理和排障能力。无需为增加框架数量而重写已有 runner、预热或评测；Harbor 与旧 runner 不同时争夺同一任务的编排责任。

**读后接续**：根据复跑结果修复已定位的缺口，或结束本轮接入；更多 Agent、优化和更深实现只由具体需求触发。

<details>
<summary>源码版本、历史与验证边界</summary>

- Harbor 使用发布提交 fdba28fc411e47e8765420a1a063b4918fce3def（v0.25.0），本轮按本地 git show 定位相关符号；本地 main 与发布标签有差异，不混用。
- Dressage 源码仍为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，依赖和运行时门禁仍限定 Harbor 0.18。本文建立接口阅读路线，不表示已经完成升级；具体适配与验证见既有兼容性记录。
- 既有 Agent Sandbox 与 slime_api_data_collecting 的能力按原记录和当前实际分支核对；已有代码、接口声明与真实运行证据分别登记。
- [调整前 scope](references/history/2026-11-12-before-call-order-scope.md)完整保留。本次只改 scope 与导航，不将未读函数提前建卡或标为掌握。

</details>
