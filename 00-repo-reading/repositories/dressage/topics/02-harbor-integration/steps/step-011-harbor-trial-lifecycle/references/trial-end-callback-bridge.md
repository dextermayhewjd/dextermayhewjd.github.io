# Step 011 · END 回调怎样接回 Dressage（旧说明保留）

> 2026-11-12：当前阅读改为 [scope 第 5 项的逐函数入口](../01-scope.md#end-hook-registration)。本页保留此前说明与来源，不再作为当前主线阅读入口。

[本步 scope 的第 5 项](../01-scope.md#end-hook-registration) · [返回 Trial._finalize](../02-short-term-memory/functions/harbor/trial/trial.py/Trial._finalize.md#finalize-mainline) · [形成过程](../04-flow.md#end-hook-reference-placement)

这份参考保存跨函数交接：插件登记 → Job/TrialQueue 传递与挂接 → Trial 发出 END → Dressage 回调。它不是单个 _finalize 函数的内部实现，也不表示整个 Step 011 已读完。

源码范围：Harbor v0.25.0 发布提交 fdba28fc411e47e8765420a1a063b4918fce3def；Dressage 固定提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。这里只核对接口连接，尚未运行验证两者兼容性。

## _emit(END)：把结束消息交给已经登记的回调

当前只回查 trial.py:590–599，不单独建卡：

```python
async def _emit(self, event: TrialEvent) -> None:
    # 包装“哪次尝试、什么事件、配置和结果是什么”。本次 event 是 END。
    hook_event = TrialHookEvent(
        event=event,
        task_name=self.task.name,
        config=self.config,
        result=self.result,
        lock=self._trial_lock,
    )
    for hook in self._hooks[event]:
        await hook(hook_event)  # 按登记顺序执行回调，等待当前回调返回。
```

本次不是打印一条“结束”日志，而是实际调用 END 对应的处理函数。回调可以更新进度、记录结果或做接入方的收尾。调用方若还没登记某个回调，这里不会凭空调用它。

<a id="end-hook-bridge"></a>

## END 怎样接回 Dressage：先登记，再随 Trial 结束调用

```text
运行前：on_job_start → Job → TrialQueue → 挂到每个 Trial 的 END 回调列表
结束时：Trial._finalize → _emit(END) → _safe 的 wrapper → plugin._on_end
```

下面分别是不同函数的源码片段，按注册和触发时机排列；不是拼成一段连续源码。

```python
# Dressage _run_partition:760–762：先登记，再运行整个 Job。
await plugin.on_job_start(job)
result = await job.run()          # 各个 Trial 的 END 回调在这次等待期间执行。
await plugin.on_job_end(result)   # 整份 Job 返回后的收尾，是另一个调用。
```

```python
# Dressage on_job_start:414；这里 self 是插件对象。
# _safe 返回一个包装回调，此时只登记，还没有运行 _on_end。
job.on_trial_ended(self._safe(self._on_end, "END"))
```

Job.on_trial_ended 把它作为 END 回调传给 Job.add_hook，再转交 TrialQueue.add_hook，保存在队列的 self._hooks[END] 列表。

```python
# TrialQueue._execute_trial_with_retries:201–203：每次创建 Trial 时挂接。
trial = await Trial.create(trial_config)
self._setup_hooks(trial)  # 将队列已登记的回调挂到这个 Trial 上。
result = await trial.run()

# _setup_hooks:122–124 的登记部分；这里 self 是 TrialQueue。
for event, hooks in self._hooks.items():
    for hook in hooks:
        trial.add_hook(event, hook)  # 存入 Trial 自己的回调列表。
```

```python
# Trial._emit:598–599；此时 self 是 Trial，本次 event 是 END。
for hook in self._hooks[event]:
    await hook(hook_event)  # 对 Dressage 这个 hook，进入 _safe 返回的 wrapper。

# Dressage._safe 的 wrapper:611，实际继续调用：
await callback(event)       # 本次 callback 就是之前登记的 self._on_end。
```

至此接回 [DressageHarborPlugin._on_end:742](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L742)。它接收该 Trial 的事件，找到对应记录并安排/等待本次尝试的收尾；内部产物与轨迹处理本轮暂不展开。回调返回后回到 _emit，再回到 _finalize 和 Trial.run。

本节只核对回调连接，不通读整个 on_job_start；也不把现有 Dressage 与 Harbor 0.25 的接口静态对照当作运行兼容性验证。


## 来源与阅读边界

- 回调连接来源：Dressage 固定提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c 的 rollout.py:760–762、plugin.py:414、604–637、742–749；Harbor v0.25.0 的 job.py:230–233、255–257，trial/queue.py:50–53、112–124、201–203，以及 Trial.add_hook:552–553。_safe 的正常路径 await 原回调，异常处理本轮省略。
- 2026-11-11 从 Trial._finalize 卡迁出，完整保留已发生的 _emit 回查与注册链讲解；迁移不表示新增个人理解。
- 当前停在接回 _on_end 的位置；插件配置准备、路由注入、轨迹与产物处理不在此展开。
- 回调结束后沿原路返回 _emit 和 _finalize；外层后续收尾仍见 [Trial._finalize 卡的返回段](../02-short-term-memory/functions/harbor/trial/trial.py/Trial._finalize.md#finalize-mainline)。
