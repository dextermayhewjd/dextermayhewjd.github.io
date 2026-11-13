# SingleStepTrial._run（Harbor）

- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

- 源码：[src/harbor/trial/single_step.py:37–54](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L37)，Harbor v0.25.0，提交 fdba28fc411e47e8765420a1a063b4918fce3def。
- 首次单独展开：Step 011，2026-11-11。
- 最近认识更新：2026-11-11，用户复述 Agent 执行、日志上传、产物收集、评测和返回父函数的主线；调用与定义、停止时机由助手校准。
- 本轮范围：普通单步任务，install_only=False，沿执行与评测的正常交接；不展开 Agent、Verifier 和文件传输内部。

[Trial.run 的执行位置](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#run-call) → **SingleStepTrial._run** · [本步导航](../../../../../../step-011-harbor-trial-lifecycle/01-scope.md#current-reading)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：_prepare 已准备好环境与 Agent，Trial.run 现在调用 self._run，执行本次任务尝试。
2. **具体内容**：运行 Agent，将日志按需传回环境、收集产物，进行评测，并按评测模式安排 Agent 环境停止。
3. **建议构建的心智模型**：

   > 让 Agent 做任务，收好执行产物，再安排评测；环境用完后停止。

4. **调用代码**（Trial.run:606–609）：

   ```python
   await self._prepare()              # 前一个阶段已经完成。
   if not self.config.install_only:
       await self._run()              # 当前进入 SingleStepTrial._run。
   # 本次调用返回后，Trial.run 进入 finally 完成收尾。
   ```

## 本场景的输入与输出

### 为什么从 Trial.run 来到这个类？

本轮任务没有配置多个工作步骤，Trial.create 选用 SingleStepTrial。它继承 Trial.run，并实现自己的 _run；因此父函数里的 self._run() 会执行这里的代码。**run 管整次尝试的生命周期，_run 管准备完成后的执行阶段。** single-step 不限制 Agent 内部调用模型或工具的次数。

调用时 self 已持有题目、Agent、运行环境与本次结果记录；不再传入另一份题目。正常返回 None，执行与评测信息写入现有 self.result，产物写入本次尝试的产物目录；最后返回 TrialResult 的仍是外层 Trial.run。

<a id="single-step-run-mainline"></a>

### 执行主干：解释直接放在代码旁边

下面保留本函数完整执行语句，只调整注释；子函数的超时、失败与清理实现暂不展开。

```python
async def _run(self) -> None:
    # SHARED：沿用 Agent 环境评测；SEPARATE：在独立环境评测。
    mode = resolve_task_verifier_mode(self.task.config)

    await self._run_agent()          # 调用并等待 Agent 执行，不是在此定义方法。
    await self._upload_agent_logs()  # 按需把本地 Agent 日志传回运行环境。

    # 收集任务产物，供后续评测与记录使用。
    # SEPARATE 若需采集辅助服务产物，会先尝试停止主服务再采集。
    await self._collect_artifacts(
        stop_main_before_sidecars=(mode == VerifierEnvironmentMode.SEPARATE)
    )

    # 独立环境评测：Agent 环境已用完，可以先停止。
    if mode == VerifierEnvironmentMode.SEPARATE:
        await self._stop_agent_environment()

    await self._run_verifier()       # 执行评测，写入 self.result.verifier_result。
                                    # 若配置禁用评测，子函数直接返回。

    # 共用环境评测：评测还要用原环境，所以评测后再停止。
    if mode == VerifierEnvironmentMode.SHARED:
        await self._stop_agent_environment()
    # 正常返回 None，回到 Trial.run 的 finally。
```

这里先抓住 **Agent 执行 → 日志与产物 → 评测**。环境停止分别放在评测前或后，是因为评测是否还需要原环境；停止不自动等于删除资源，具体保留/删除由环境配置决定。

| 按需查看真实子函数 | 带着什么问题进入、读完回哪里 |
| --- | --- |
| [_run_agent:74](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L74) | 题目怎样交给 Agent 执行；返回第 41 行，继续日志与产物 |
| [_run_verifier:88](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L88) | 怎样选择评测环境并写回结果；返回第 53 行，继续环境停止分支 |

本轮只读本函数的组织顺序；上述子函数暂不建卡。正常返回后接回 [Trial.run 的 finally](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#normal-lifecycle)，完成后续收尾和最终结果返回。

## 我的直接表述（原话）

用户确认继续：

> 好的 那么先看一下这里的这个run吧
> 生成一下合适的short term memory吧

本轮复述：

> 也就是这里直接是定义这个run agent
> 并且吧agent 日志传到运行环境里面
> 然后考虑的是手机人物产物
> 如果agent 环境用完停止
> 然后使用这里的这个 verifier来评测
> 然后在返回none?
> 回到trial run的finally
> 感觉就是agent 运行时候的一系列内容
> 别的内容不是特别多
> 关于执行和上传的
> 都是运行时候的产物是我的理解

助手校准：await self._run_agent() 是调用并等待执行；def 才是定义方法。运行后处理日志与任务产物，再安排评测；SEPARATE 可先停 Agent 环境再评测，SHARED 在原环境评测后才停。正常返回 None，但执行与评测信息已写入 self.result，外层 Trial.run 继续 finally。校准内容尚待用户反馈。

## 尚不清楚

- 当前 Agent 怎样真正执行题目、产生输出，尚未进入 _run_agent 内部。
- Verifier 怎样运行检查并计算奖励，尚未进入 _run_verifier 内部。
- 产物具体包括哪些文件、独立评测怎样取得它们，以及辅助服务采集，当前只识别职责。

<details>
<summary>来源与验证</summary>

- 按本地 git show v0.25.0 核对 [SingleStepTrial._run 完整源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L37)；父函数为 [Trial.run:606–609](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L606)，普通任务的实现选择见 [Trial.create:505–525](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L505)。
- [_upload_agent_logs:834](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L834) 将本地日志按需上传回环境，已挂载路径会跳过重复上传；[_collect_artifacts_phased:1623](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L1623) 分主服务和辅助服务采集；这里只核对职责，不展开全部路径。
- [_run_verifier:88](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L88) 检查 disable，并将评测结果写入 self.result.verifier_result。共享环境分支使用 agent_environment；独立环境分支见 [Trial._run_separate_verifier:1013](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L1013)。
- [_stop_agent_environment:2039](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L2039) 有已停止检查，调用环境 stop 时传入 config.environment.delete；与上层 finalize 再次收尾并不等同于重新执行整个任务。
- 原函数不会直接把结果列表交给队列；它更新当前 Trial，外层 Trial.run 最后返回 TrialResult。执行完成也不等于题目答对，失败与取消仍有上层处理。
- 仅静态源码核对，没有运行 Agent、Verifier、模型、容器或 Kubernetes。
- [本步形成过程](../../../../../../step-011-harbor-trial-lifecycle/04-flow.md#single-step-run-reading)。

</details>
