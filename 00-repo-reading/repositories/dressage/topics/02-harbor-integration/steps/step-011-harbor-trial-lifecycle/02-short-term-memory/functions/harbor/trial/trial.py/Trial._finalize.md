# Trial._finalize（Harbor）

- 源码：[src/harbor/trial/trial.py:660–667](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L660)，Harbor v0.25.0，提交 fdba28fc411e47e8765420a1a063b4918fce3def。
- 首次单独展开：Step 011，2026-11-11。
- 本轮范围：沿前面普通任务的正常收尾路径，先看环境、结果落盘与结束通知；无 user-agent bridge，不展开清理重试或事件回调内部。

[Trial.run 的 finally](Trial.run.md#finalize-call) → **Trial._finalize** · [本步导航](../../../../../01-scope.md#current-reading)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Trial.run 进入 finally，调用本函数为这次尝试收尾；本轮从 _run 执行与评测正常结束的位置接入。
2. **具体内容**：关闭 bridge、处理 Agent 环境停止，补结束时间、将当前结果写入文件，再执行 END 事件回调。
3. **建议构建的心智模型**：

   > 收好这次尝试的环境和结果，通知已登记的回调：这次尝试结束了。

4. **调用位置**：Trial.run:622–624 的 finally 中执行 `await self._finalize()`。本函数正常返回 None；外层随后继续脱敏、关闭日志，最终返回 TrialResult。

## 本场景的输入与输出

### 从 _run 回到收尾时，已经有什么？

self.result 已保存这次执行与评测的信息，产物已在前面的执行阶段收集；Agent 环境也可能已经处理过停止。本函数继续使用同一个 Trial 对象和结果记录。

这里不重新执行任务、计算奖励或创建新的结果对象。它更新结束时间并写文件，正常返回 None；**返回 TrialResult 的仍是外层 Trial.run。**

<a id="finalize-mainline"></a>

### 收尾主干：解释直接跟着代码读

以下保留完整函数执行语句，只添加注释：

```python
async def _finalize(self) -> None:
    try:
        await self._close_bridge()  # 关闭可选 bridge；本轮没有 bridge，直接跳过。
    finally:
        # 检查已停止标记；未标记时调用环境 stop，已有标记就跳过。
        await self._stop_agent_environment()

    self.result.finished_at = self._now()  # 给现有结果补上结束时间。
    self.paths.result_path.write_text(
        self.result.model_dump_json(indent=4)
    )  # 将本次 TrialResult 写成 JSON 文件。

    # 带上当前 Trial 的配置与结果，依次等待已登记的 END 回调执行。
    await self._emit(TrialEvent.END)
    # 正常返回 None，交回 Trial.run 的 finally。
```

前面 _run 已经调用过环境停止，这里通过标记避免重复操作；如果此前没有走到停止位置，收尾阶段仍会尝试停止。**END 表示尝试结束，不表示答对题或获得正奖励。**

<a id="end-hook-bridge"></a>

_emit(END) 把当前 Trial 的配置和结果交给已登记的 END 回调，并依次等待回调返回。注册与跨库交接另见 [scope 第 5 项的函数入口](../../../../../01-scope.md#end-hook-registration)。

### 返回后：还有哪些工作属于 Trial.run？

下面是父函数在 finally 内部及其后续的真实代码片段（623–631 行）：

```python
try:
    await self._finalize()         # 当前函数正常完成后，从这里继续。
finally:
    try:
        self._scrub_jobs_dir()     # 对落盘文本中的敏感值脱敏。
    finally:
        self._close_logger_handler()  # 关闭日志处理器。

return self.result                # 正常路径下，外层才返回 TrialResult。
```

| 需要回查的入口 | 先知道什么、回来哪里 |
| --- | --- |
| [_stop_agent_environment:2039](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L2039) | 检查标记、委派环境 stop；回到 _finalize 补结束时间 |
| [_emit:590](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L590) | 构造 TrialHookEvent 并 await 对应回调；返回后本函数结束 |

本卡先停在 _finalize 的收尾与返回；跨函数注册和调用关系沿 [scope 第 5 项](../../../../../01-scope.md#end-hook-registration)逐函数展开。

## 我的直接表述（原话）

用户确认继续收尾：

> 好的那么看一下这里的这个trial finalize吧
> 看一下还有什么是需要我来看一下的

本轮复述与疑问：

> 好的 我差不多理解了
> 那么现在看一下
> 还有什么是需要我来了解的吗
> 干视觉这里都是在最后的收尾工作
>
> close bridge
> stop agent enironment
> 还有给出这里的时间等一系列内容
> 还有什么是我特别需要注意的吗?
>
> 以及这里的emit?
>
> 感觉这里差不多就只有这些内容了吧?
> 还有什么吗?

助手核对：用户已认出收尾主线，本轮补清 _emit 构造事件并逐个 await 已登记回调；END 不代表任务成功。_finalize 可先停在这个深度，具体清理内部暂缓。事件机制说明尚待用户反馈。

## 尚不清楚

- END 的注册和触发链已静态核对，用户是否接清尚待反馈；_on_end 内部的轨迹与产物处理还未展开。
- bridge 的用途与关闭机制、停止失败与取消传播，当前不展开。

<details>
<summary>来源与验证边界</summary>

- 通过本地 git show v0.25.0 核对 [完整 _finalize](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L660)、[外层 finally](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L622)、[_close_bridge:2007](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L2007)、[_stop_agent_environment:2039](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L2039)、[_emit:590](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L590)。
- _emit 构造包含 config/result 等信息的 TrialHookEvent，按注册顺序 await 回调；不是只发出一个后台通知就立即返回。注册链另见独立参考，具体回调内部本轮未展开。
- _stop_agent_environment 的标记用于避免重复处理；异常分支也可能设置标记并记录错误，因此不能只看标记就保证远端资源已成功释放。stop 的删除行为由 config.environment.delete 决定。
- _finalize 的 try/finally 保证关闭 bridge 后尝试环境停止；不保证任何异常下都能继续写文件或执行 END。外层 Trial.run 还有自己的嵌套 finally 来尝试脱敏和关闭日志。
- TrialResult 在 END 回调之前写入文件；本轮只说明实际先后，不预设回调没有其他副作用。
- 未运行 Job、模型、Verifier、容器或 Kubernetes；源码核对不等于资源释放或插件兼容性实测。
- [本步形成过程](../../../../../04-flow.md#trial-finalize-reading)。

</details>
