# 01 · Dressage Step 016：回看一次取消或失败，核对清理与结果归属

[主题入口](../../README.md) · [项目进度](../../../../README.md) · [前一范围](../step-015-harbor-results-and-samples/01-scope.md) · [下一范围](../step-017-integration-validation/01-scope.md)

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

**当前：[3] 关闭桥接、恢复输出。** 从 Trial.run 的取消分支进入；本轮只看一次取消且清理正常完成的路径，不重读准备阶段或 asyncio 内部。下方与本步函数卡使用同一套 [1]–[6] 编号。

```python
# 已完成结果初始化和 START 通知；本轮省略普通 Exception 分支与日志。
try:
    await self._prepare()
    if not self.config.install_only:
        await self._run()               # 假设在这里收到一次取消。
except asyncio.CancelledError as exc:
    self._record_exception(exc)         # [1] 记录取消原因。
    await self._emit(TrialEvent.CANCEL)  # [2] 通知取消回调。
    await self._close_bridge()          # [3] 关闭桥接、恢复已有输出。
    await self._recover_outputs()       # 单步实现还会收集产物并停止环境。
    raise                              # [4] 继续传播，但先经过 finally。
finally:
    try:
        await self._finalize()          # [5] 主要收尾与 END 通知。
    finally:
        try:
            self._scrub_jobs_dir()      # [6] 尝试脱敏，随后关闭日志。
        finally:
            self._close_logger_handler()
# 原函数末尾还有 return self.result；取消路径不走这个正常返回。
```

<a id="reading-sequence"></a>

| 阅读顺序与入口 | 函数卡定位 | 本轮看清什么、返回哪里 |
| --- | --- | --- |
| **[1] 记录取消原因 · 已讨论** | [Trial._record_exception 函数卡](02-short-term-memory/functions/harbor/trial/trial.py/Trial._record_exception.md) | 看 exc 怎样变成 exception_info，并写入 traceback 文件；已有记录则保留。读完返回 Trial.run 的 [2]，不继续下钻格式化。 |
| **[2] 通知取消回调 · 已讨论** | [DressageHarborPlugin._on_cancel 函数卡](02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_cancel.md) | 只追 _on_cancel 的取消标记及必要 quiesce，返回 [3]；不扩展通用分发机制。 |
| <a id="current-reading"></a>**[3] 关闭桥接、恢复输出 · 当前** | [Trial.run：[3] 两个清理调用](02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#cancel-recover) | 无 bridge 时关闭调用直接返回；单步恢复包括输出同步、产物收集和停止环境。正常完成后接 [4]，不下钻传输实现。 |
| **[4] 继续传播取消** | [Trial.run：[4] raise](02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#cancel-reraise) | 重抛前进入 finally 的 [5]，不走正常返回。 |
| **[5] 主要收尾与 END** | [Trial.run：[5] _finalize](02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#cancel-finalize) | 接清停止环境、END 与插件取消分支；跳过训练 bundle 提交，仍尝试关闭，然后接 [6]。 |
| **[6] 脱敏与日志关闭** | [Trial.run：[6] 嵌套 finally](02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#cancel-final-cleanup) | 前项清理失败仍尝试后项；都正常完成时，取消继续向上传播。 |

编号是同一条取消路径的观察点；[2]、[5] 内部经已登记回调连接 Dressage 插件。骨架表示教学裁剪，不保证所有清理调用都成功；清理异常可能改变最终传播的异常。

**停止位置**：能说明“取消被接住后仍会向上传播、最终清理由谁承担、取消尝试为何不进入正常训练 bundle 提交”。到这里即可转向实践；不要求读完所有关闭函数。再次取消或清理异常可能改变结果，源码存在 finally 不等于已证明远端资源释放成功。

<details>
<summary>后续按需：普通失败重试与实际取消验证</summary>

- **普通失败重试是另一种情景**：`TrialQueue._execute_trial_with_retries`（Harbor `queue.py:194`）检查返回结果的 exception_info 与策略，必要时创建新尝试；本轮外部取消不自动进入这条重试路径。
- **实际验证留到接入时**：参考 [环境合同](../step-013-harbor-kubernetes-environment/01-scope.md)、[结果合同](../step-015-harbor-results-and-samples/01-scope.md)，运行一条正常任务作对照，再取消一次，观察进程/环境、路由和最终结果。没有运行条件时明确留作待验，不以更多源码分支代替验证。
- **接续 [Step 017](../step-017-integration-validation/01-scope.md)**：在可运行的接入中检验上述清理责任与结果边界；遇到实际失败，再回到对应实现。

</details>

<details>
<summary>源码版本、历史与验证边界</summary>

- Harbor 使用发布提交 fdba28fc411e47e8765420a1a063b4918fce3def（v0.25.0），本轮按本地 git show 定位相关符号；本地 main 与发布标签有差异，不混用。
- Dressage 源码仍为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，依赖和运行时门禁仍限定 Harbor 0.18。本文建立接口阅读路线，不表示已经完成升级；具体适配与验证见既有兼容性记录。
- 既有 Agent Sandbox 与 slime_api_data_collecting 的能力按原记录和当前实际分支核对；已有代码、接口声明与真实运行证据分别登记。
- [调整前 scope](references/history/2026-11-12-before-call-order-scope.md)完整保留。本次只改 scope 与导航，不将未读函数提前建卡或标为掌握。

</details>
