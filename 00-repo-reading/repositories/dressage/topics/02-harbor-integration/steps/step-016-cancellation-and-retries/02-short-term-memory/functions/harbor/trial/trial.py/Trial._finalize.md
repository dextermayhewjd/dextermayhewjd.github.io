# Trial._finalize（Harbor）

[当前 scope · 第 5 项](../../../../../01-scope.md) · [返回 Trial.run](Trial.run.md) · [源码 :660](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:660)

## 当前只看清三个问题

1. **前面已经停止过环境，为什么这里还要再调用？**
2. **这里是在收集输出，还是保存结果？**
3. **结果已经保存，为什么还要发 END？**

**进入位置**：同一次 Trial 收到取消，尝试恢复输出后，从 `Trial.run` 的 `finally` 进入这里。当前无 user-agent bridge。

> `_recover_outputs` 尽量把已有日志和文件收回来；`_finalize` 统一收尾环境、保存本次结果、通知相关组件结束。

<a id="finalize-mainline"></a>

## 核心代码：三个动作发生在哪里？

完整函数语句，只增加与下方标题对应的注释：

```python
async def _finalize(self) -> None:
    # ① 再次安排环境收尾
    try:
        await self._close_bridge()
    finally:
        await self._stop_agent_environment()

    # ② 保存已有的结果记录
    self.result.finished_at = self._now()
    self.paths.result_path.write_text(self.result.model_dump_json(indent=4))

    # ③ 通知已登记的回调
    await self._emit(TrialEvent.END)
```

## ① 再次安排环境收尾：为什么不是重复停止？

前面的输出恢复可能中途失败，尚未走到停止环境；所以共同收尾入口仍要安排停止。若此前已设置停止标记，`_stop_agent_environment` 会直接返回，避免重复委派后端。

当前无 bridge，`_close_bridge` 直接返回。外层 `finally` 让桥接关闭发生异常时，仍尝试停止环境。

<details>
<summary>补充：停止标记能保证什么，不能保证什么？</summary>

停止方法开头检查：

```python
if self._is_agent_environment_stopped:
    return
```

正常清理路径：首次执行后端 stop、设置标记；再次调用看到标记就返回。源码在停止异常或等待被取消时也设置标记，所以它不是失败重试机制，标记也不能证明远端环境已释放。

Trial 决定何时收尾，具体停止/删除由 `Environment.stop(delete=...)` 的后端实现负责。

</details>

## ② 保存结果：与 recover_outputs 收集输出有什么不同？

这里不重新下载日志或收集任务文件，而是把**已经存在的 `self.result`** 补上结束时间，写成结果 JSON。本次取消信息此前已由 `_record_exception` 记录在其中。

```text
_recover_outputs：从执行环境尽量收回已有日志、文件产物
_finalize：给现有 TrialResult 补结束时间，并写入 result.json
```

两者使用的是同一次 Trial；这里没有重新执行 Agent 或重新评测。写入 Harbor 的结果文件，也不等于提交了可训练的 Dressage bundle。

<a id="end-hook-bridge"></a>

## ③ 通知结束：为什么保存结果后还要发 END？

保存文件让结果留下来；`_emit(TrialEvent.END)` 则让**提前登记的其他组件执行自己的收尾**。它组装带有当前结果的事件，并逐个等待回调完成。

**END 只表示尝试结束，不表示成功。** 本次插件此前已收到 CANCEL；进入相应取消路径时，不会因收到 END 就正常提交训练 bundle。

<details>
<summary>补充：END 怎样接到 Dressage？</summary>

```text
Trial._finalize
  → _emit(TrialEvent.END)
      → 已登记的 _safe(_on_end, "END")
          → 收尾 Task 执行 _finalize_attempt
```

`_emit` 没有写死 Dressage 的函数名；插件提前登记了回调，才会发生这条调用。当前取消路径的 `_finalize_attempt` 根据取消标记跳过正常 bundle 提交，仍执行 finally 中的路由关闭。

</details>

## 读完返回哪里？

本函数正常返回 `None` → 回到 `Trial.run` 脱敏、关闭日志 → 本次取消继续向上传播。它不是在这里返回 TrialResult。

<details>
<summary>补充：正常结束与清理异常的区别</summary>

正常执行路径中，Trial.run 完成后续清理才返回 TrialResult；当前取消路径中则继续传播 CancelledError。

以上假设清理正常完成。若关闭或写结果时抛错，后面的 END 不保证执行，最终传播的异常可能改变；Trial.run 的外层嵌套 finally 仍会尝试后续清理。结果 JSON 在 END 之前写入，不预设回调没有后续副作用。

</details>

<details>
<summary>我的直接表述与尚未解决的问题（供回顾与 LLM 接续）</summary>

**2026-11-17 最新直接表述**：

> 这么看下来来这里的重复部分是由的
> 但是和之前的不易uyangde是之前还有回收日志和文件产物
> 但是当前就没有了
> 直接收集一下这里的result
> 这里不再从环境里收集是我的理解
> 有什么收集什么

助手校准：已区分从环境恢复输出与保存已有结果；此处更准确是“补结束时间并序列化已有 self.result”，不是重新收集结果。用户认可标题更清楚并要求继续，返回 Trial.run 第[6]的最终清理。

**当前状态**：已讨论共同收尾和重复停止的原因，未将本次格式整理视为新增掌握。当前入口以页首为准，以下历史“下一步”不是阅读指令。

Step 016 当前问题（2026-11-17，节选）：

> 这里的这个finalize 到底是在做什么呢？
> 为什么我在scope这里点及_finalize还是跳转回了一开始的部分

本轮补清同一次 Trial 的取消恢复与共同收尾，并修正 scope 直接指向本卡；尚未确认内部内容已理解。以下保留历史原话。


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

Step 015 本轮追问：

> 那么我们是否应该考虑先看一下这里的这个_finalize呢
> 否则直接到这里的这个 _emittrial envent end 我其实也不明白这里到底是啥对吧

本轮先补齐 Harbor 收尾到 END 回调的中间动作，未把旧阅读记录视为当前已理解。

**当前未知与边界**：具体后端回收未实测；再次取消、清理失败与插件取消分支的完整行为未逐项验证。

**此前记录的未知（保留历史语境，不作为新的必读清单）**：

- END 的注册和触发链已静态核对，用户是否接清尚待反馈；_on_end 内部的轨迹与产物处理还未展开。
- bridge 的用途与关闭机制、停止失败与取消传播，当前不展开。

**本次格式反馈（2026-11-17）**：

> 很多记录历史是为了留给llm看的
> 我需要看的部分很少

用户先确认按“默认简短主干、按需解释、历史接续记录”分层整理，随后指出关键关注点仍不显眼：

> 就没有一下子列清楚我这一个函数卡片到底需要关注什么问题

因此改为页首列出三个问题，正文以对应动作/问题作为标题，关键解释默认可见；补充机制、个人记录与历史继续折叠。不增加阅读范围或标记掌握。

</details>

<details>
<summary>历史变化、源码版本与验证依据</summary>

- 首次单独展开：Step 011，2026-11-11；Step 015 回查正常收尾到 END；2026-11-17 在 Step 016 调取，讨论取消场景与重复停止。本次只是结构整理，不重置既有认识日期。
- [分层整理前完整快照](../../../../../references/history/2026-11-17-finalize-before-layered-card.md)：保留全部原文、继承链、旧导航和来源；其中的旧阅读安排不是当前指令。
- 固定版本：Harbor v0.25.0，`fdba28fc411e47e8765420a1a063b4918fce3def`。
- 源码位置：`trial.py` 中 `_finalize:660`、`_emit:590`、`_close_bridge:2007`、`_stop_agent_environment:2039`；`Trial.run` 的取消与 finally 分支见 601–631。
- 本文完整函数与本地源码静态核对；未运行 Job、模型、容器或 Kubernetes，未证实远端资源释放或跨版本插件兼容性。
- [本步讨论过程](../../../../../04-flow.md)。

</details>
