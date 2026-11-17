# 01 · Dressage Step 016：回看一次取消或失败，核对清理与结果归属

[主题入口](../../../../README.md) · [项目进度](../../../../../../README.md) · [前一范围](../../../step-015-harbor-results-and-samples/01-scope.md) · [下一范围](../../../step-017-integration-validation/01-scope.md)

> 状态：2026-11-16 用户确认开始快速阅读。当前只沿 Trial.run 的单次外部取消路径，接 CANCEL 标记、finally/END 清理和不提交训练 bundle 的边界；普通失败重试按需，尚无运行验证。

## 1. 阅读目标

**在已经走通的正常主线上选一次可控取消，观察异常怎样传播，环境、路由和产物怎样收尾。**

## 2. 指挥官、入口条件与边界

1. **入口**：回到 [Trial.run:601](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L601) 的运行中阶段及 CancelledError 分支；先选一项 Trial 运行期间取消其 Job 调用的情景，不同时展开所有超时和重试。
2. **已有输入**：正常环境、Agent 执行及结果路径已能定位；Step 013 的基本 stop/超时合同已有验证或明确待验证项，Step 015 已知训练与评测结果边界。
3. **停止位置**：能区分取消请求、调用栈退出、后台清理完成和远端资源释放；核对被取消尝试是否被错误选作可训练结果。
4. **额外分支**：如要验证重试，另选一种返回 TrialResult.exception_info 的普通执行失败。外部取消重新抛出，不画成进入队列重试循环的必然下一步。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

沿用 Step 010、011 的整体主线，各步保持相同图形结构。**本步回到同一任务运行中的一个故障点；先选外部取消，普通失败重试是另一条按需路径。** 具体入口与返回位置见 3.2；图中回调和 HTTP 均标明交互方式，不当作同一同步调用栈。

图内 **[本步·故障回看]** 标出本步观察的运行点与收尾位置；完整正常主线保留作对照，不表示取消后仍会走完正常返回。

```python
# 关系示意，不是可执行代码；标记的是本步观察位置。
Slime 的 rollout hook
  -> generate_rollout_harbor_sync                 # 训练入口；API-only 路线不必执行这里。
       -> _run_harbor_rollout -> _run_round -> _run_partition
            -> _CREATE_JOB(job_config)          # 创建 Job 时组成各次尝试的配置。
            -> plugin.on_job_start(job)          # 挂接路由配置与生命周期回调。
            -> Harbor Job.run  # [本步·故障回看] 在一项 Trial 运行期间取消 Job 调用。
                 -> _run_trials_with_queue -> TrialQueue -> Trial.run  # 队列交接后进入一次尝试。
                      -> _prepare                # 环境与 Agent 准备。
                           -> Environment.start
                                -- 目标接缝 --> K8s 适配 -> Agent Sandbox -> Pod  # 待对齐/验证。
                           -> Agent.setup        # 环境就绪后准备已选定的 Agent。
                      -> _run
                           -> _run_agent  # [本步·故障回看] 取消从运行点传播，进入 Trial.run 的异常路径。
                           -> _collect_artifacts # 收集产物；按评测模式安排环境停止。
                           -> _run_verifier      # 使用题目的验证规则取得评分。
                      -> _finalize  # [本步·故障回看] 核对取消后的环境停止；不重新阅读正常路径。
                           == END 事件 ==> plugin._on_end  # [本步·故障回看] 与更早的 CANCEL 标记配合，核对最终清理。
                                            # 本步沿取消分支核对清理，不把它当作自动重试。
            <- JobResult  # 正常路径背景；本次取消通常沿异常传播，不能预设返回 JobResult。
            -> plugin.on_job_end(...)           # 整份 Job 返回后的插件收尾。
            -> _bundle_samples                   # 训练路线的结果转换。
       <- Sample 组与 metrics
  <- RolloutFnTrainOutput

# Agent.run 期间的模型交互，不是等 Trial 结束才发请求：
Agent == HTTP ==> Gateway -> Dressage Proxy -> 模型服务
# 只做 API 评估时，调用方也可以从 Harbor Job 进入，不启动 Slime 训练。
```

<a id="reading-navigation"></a>

### 3.2 本步骨架与阅读顺序

**当前先看第 1 项 Trial.run 的取消分支**：从执行中的 `_run()` 回到 `except CancelledError`，接清记录、CANCEL 通知与 raise，再进入 finally；不从头重读准备阶段。

下面是普通单步任务的教学裁剪。按编号进入当前局部，弄清交接后回到真实调用方；前置回查、能力对照和验证不会冒写成一条连续执行栈。

```python
# 本步是回看另一种情景，不是正常结果之后才执行的新阶段。
[1] Job / Trial 正在执行时，调用方发出取消
  -> Trial.run 的 except CancelledError
       -> 记录异常
       == CANCEL ==> plugin._on_cancel   # 标记本次尝试，必要时停止路由接纳。
       -> 关闭 bridge、恢复可取输出
       -> raise                           # 继续传播取消。
  -> finally: Trial._finalize
       -> 环境停止与 END
       == END ==> plugin._on_end -> _finalize_attempt
            -> 取消分支不生成训练 bundle
            -> finally: _close_attempt
  -> 上层收到取消，走各自 finally / 中止处理

# [2] 按需另选普通失败场景；不要与上面的取消画成同一条路径。
TrialQueue._execute_trial_with_retries
  -> result = await trial.run()
  -> 检查 result.exception_info 和重试策略
       -> 允许时重新 Trial.create(...)，形成新的物理尝试
# [3] 对照实际资源、日志与最终选用状态，验证清理和结果归属。
```

<a id="reading-sequence"></a>

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| <a id="current-reading"></a>**1. Trial.run 的取消分支 · 当前** | [本步 Trial.run 函数卡](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#trial-cancellation) | 先读 except 中的记录、CANCEL、恢复输出与 raise；再接 finally。CANCEL/END 回调按 1a 回查后返回这里；本轮不重读正常准备与执行。 |
| 1a. 只追相关插件收尾 | [_on_cancel:731](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L731) → [_finalize_attempt:751](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L751) | 区分 CANCEL 标记与 END 最终清理；只看取消分支和 _close_attempt，不重新遍历正常提交。 |
| 2. 普通失败重试 · 按需 | [_execute_trial_with_retries:194](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/queue.py#L194) | 仅在选择重试案例时，看返回异常结果后的条件、次数与新 trial_id；不把取消当作自动重试。 |
| 3. 验证资源与结果 | [环境合同](../../../step-013-harbor-kubernetes-environment/01-scope.md) · [结果合同](../../../step-015-harbor-results-and-samples/01-scope.md) | 观察环境资源、路由、日志与最终产物；检查错误分类、重复提交和旧尝试是否误选，记录真实证据或明确未验证。 |

**本步局部验证**：只选择一个可复现故障，一次正常结果作对照。若只发出了取消而未观察资源消失，不能写“已证明不泄漏”；若无运行条件，就保留待验条件，不继续枚举源码分支代替验证。

**读后接续**：把正常与故障的小验证带到 [Step 017](../../../step-017-integration-validation/01-scope.md)复跑；不再新增一套通读队列或控制器的前置课程。

<details>
<summary>源码版本、历史与验证边界</summary>

- Harbor 使用发布提交 fdba28fc411e47e8765420a1a063b4918fce3def（v0.25.0），本轮按本地 git show 定位相关符号；本地 main 与发布标签有差异，不混用。
- Dressage 源码仍为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，依赖和运行时门禁仍限定 Harbor 0.18。本文建立接口阅读路线，不表示已经完成升级；具体适配与验证见既有兼容性记录。
- 既有 Agent Sandbox 与 slime_api_data_collecting 的能力按原记录和当前实际分支核对；已有代码、接口声明与真实运行证据分别登记。
- [调整前 scope](2026-11-12-before-call-order-scope.md)完整保留。本次只改 scope 与导航，不将未读函数提前建卡或标为掌握。

</details>
