# DressageHarborPlugin._on_cancel

- 源码：[Dressage plugin.py:731–740](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L731)，固定提交 3e3142fe。
- 首次单独展开：2026-11-16，Step 016 的 [2]；尚无个人复述。
- [scope [2]](../../../../../../01-scope.md#current-reading) → [Trial.run 的 CANCEL 通知](../../../../harbor/trial/trial.py/Trial.run.md#cancel-notify) → **当前回调** → [返回 [3] 关闭桥接与恢复输出](../../../../harbor/trial/trial.py/Trial.run.md#cancel-recover)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Harbor 已捕获取消并记录异常，现在通知此前登记的 Dressage 插件。
2. **具体内容**：找到这次尝试的记录，标记取消和异常状态；如果模型交互仍活跃，等待路由静止。
3. **建议构建的心智模型**：

   > 先标记这次尝试不能再按正常完成处理；最终关闭留给后面的 END 收尾。

4. **调用背景**（跨事件回调，不是 Trial.run 直接调用此方法）：

   ```python
   # 此前 on_job_start 注册了回调；当前不重复执行注册。
   job.on_trial_cancelled(self._safe(self._on_cancel, "CANCEL"))
   # Harbor Trial.run 中发出通知，经已登记回调来到这里。
   await self._emit(TrialEvent.CANCEL)
   ```

## 本场景的输入与输出

**输入**：event 携带被取消 Trial 的身份等信息；插件已有对应 AttemptRecord。它与上一步 Harbor 的 TrialResult 是不同对象。

**本段要解决的问题**：Harbor 已知道取消了，怎样让 Dressage 后续的模型路由和结果提交也知道？

下面保留全部业务语句，只改写末尾解释注释：

```python
async def _on_cancel(self, event: Any) -> None:
    record = self._record_for_event(event)  # 找到对应尝试的已有记录。
    if record is None:
        return
    record.cancel_requested = True        # END 收尾将据此跳过正常 bundle 提交。
    record.poisoned = True                 # 标记这次尝试处于异常状态。
    if record.phase is AttemptPhase.ACTIVE:
        await self._quiesce(record)        # 模型交互仍活跃时，让路由进入静止流程。
    # 此处不 finalize/read/close/rotate；最终清理由后面的 END 负责。
```

**前后变化**（教学场景：找到记录，原先两个标记均为 False）：

```text
record.cancel_requested: False → True
record.poisoned:         False → True
活跃的模型路由：         调用 _quiesce 并等待其处理
返回：                   None
```

回到 Trial.run 后，继续 `_close_bridge()`、`_recover_outputs()` 和 `raise`。后面的 finally 发出 END 时，`_finalize_attempt` 看到 cancel_requested，跳过训练 bundle 提交，但仍执行关闭尝试的 finally。

这里不是重新发送 Task.cancel，也不表示沙箱已删除。`_quiesce` 的排空细节暂不展开，实际资源状态需运行验证。

## 我的直接表述（原话）

用户理解异常记录后要求“那么继续吧”；尚无对当前回调的独立复述。

## 尚不清楚

- 回调包装 _safe、记录查找与 _quiesce 内部暂只认职责。
- 重复取消、排空失败和远端资源释放尚未验证。

<details>
<summary>来源与验证</summary>

- Dressage 固定提交：回调注册 plugin.py:413；当前函数 :731；END 提交分支 :751；_quiesce :821。
- Harbor Trial.run 的 CANCEL 发出点按 v0.25.0 发布提交核对；跨版本运行仍待验证。
- 本卡为静态代码讲解，未执行回调或发送取消。
- [本步过程](../../../../../../04-flow.md)。

</details>
