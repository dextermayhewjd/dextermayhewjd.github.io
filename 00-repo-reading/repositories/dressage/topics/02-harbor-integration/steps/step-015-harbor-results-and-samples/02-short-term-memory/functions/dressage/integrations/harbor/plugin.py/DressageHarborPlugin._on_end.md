# DressageHarborPlugin._on_end

- 代码归属：**Dressage**，路径中的 integrations/harbor 表示接入 Harbor，不是 Harbor 源码。
- 源码：[plugin.py:742](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:742)，提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- Harbor 事件侧对照：v0.25.0，`fdba28fc411e47e8765420a1a063b4918fce3def`。这是接口阅读对照，未验证两个版本运行兼容。
- 首次单独阅读：2026-11-16，Step 015；用户确认进入 _on_end，尚无本函数机制的个人复述。

[本步 scope](../../../../../../01-scope.md) · [前一阶段：Verifier.verify](../../../../harbor/verifier/verifier.py/Verifier.verify.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Harbor 的单次 Trial 进入收尾并发出 END 事件，调用提前登记的 Dressage 插件回调。不是整个 Job 返回后的 on_job_end。
2. **具体内容**：按事件身份找到尝试记录；若尚无收尾 Task 就创建一个；随后用 shield 等待同一个 Task。
3. **建议构建的心智模型**：

   > Harbor 通知“这次尝试结束了”，Dressage 找到对应记录，让这次尝试有且只有一个被复用的收尾任务。结果提交和资源关闭由收尾任务执行。

4. **调用交接**：

   ```text
   【Dressage：运行前】on_job_start 登记 _safe(_on_end, "END")
                          ↓
   【Harbor：尝试收尾】Trial._finalize
       → _emit(TrialEvent.END)
       → 把 TrialHookEvent 传给已登记回调
                          ↓
   【Dressage：当前】_on_end(event)
       → 创建或复用执行 _finalize_attempt(record, event) 的 Task
       → 等待 Task
   ```

## 本场景的输入与输出

### 先分清登记和执行：同一条回调如何接起来

1. **运行前登记**：Dressage 的 on_job_start 调用 `job.on_trial_ended(self._safe(self._on_end, "END"))`。传入的是回调，不是在这里执行 _on_end。Harbor 将它登记到 END 对应的回调中。
2. **运行到结束位置**：Harbor 的 Trial._finalize 调用 `await self._emit(TrialEvent.END)`。
3. **Harbor 真正调用回调**：_emit 创建带 result 的事件，然后执行 `for hook in self._hooks[event]: await hook(hook_event)`，经 _safe 包装进入 Dressage 的 _on_end。
4. **Dressage 安排收尾**：_require_record 查询已有尝试记录；create_task 调度 _finalize_attempt；最后等待收尾 Task。

这是显式的“登记 → 到达事件位置 → 遍历调用”流程，不是 Python 自动监控一个名叫 on_end 的函数。END 说的是这次 Trial，不是整个 Job。

依据：[Harbor Job.on_trial_ended](/home/hongshi/projects/harbor/src/harbor/job.py:255)、[Trial._emit](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:590)。

### 1. 事件不是只有一个 reward

Harbor 的 `_emit` 构造事件时带上当前 config、result、task_name 等信息。当前正常路径中，result 已包含前面写入的 verifier_result。取消或失败也可能到 END，不能把 END 等同于成功或高分。

下面只列相关字段，是对象示意，不是完整构造代码：

```text
event（Harbor TrialHookEvent）
├─ trial_name                    由 config 导出
├─ trial_id                      由 result.id 导出
└─ result                        Harbor TrialResult
   └─ verifier_result
      └─ rewards                 例如 {"reward": 1.0}

self._attempts[(trial_name, str(trial_id))]
└─ record（Dressage AttemptRecord）
   ├─ session_id / instance_id   对应 Proxy 会话等身份
   ├─ finalize_task              尚未创建时为 None
   └─ bundle                     后续收尾得到的结果
```

`_require_record` 使用事件的 trial_name、trial_id 查询已有记录，不在这里创建 AttemptRecord；找不到会报错。Harbor 的结果与 Dressage 的会话身份由此接到同一次尝试。

**本轮小回查：_require_record 为什么叫 require？**

```python
def _require_record(self, event: Any) -> AttemptRecord:
    record = self._record_for_event(event)  # 用事件中的 Trial 身份查询已有记录。
    if record is None:
        trial_name, trial_id = _event_key(event)
        raise KeyError(f"unknown Harbor attempt {trial_name}/{trial_id}")
    return record
```

其中 `_record_for_event` 只是 `self._attempts.get(_event_key(event))`；`_event_key` 返回字符串形式的 `(trial_name, trial_id)`。例如事件身份为 `("task-A", "id-123")`，就取回 `_attempts` 中同一键下的 AttemptRecord（名称与 ID 为示意值）。这份记录先前在 START 的 `_on_start` 创建并存入，此时并不新建、复制或更新它。

require 表达的是“这里必须有对应记录”：找到就返回，找不到就抛 KeyError，而不是继续拿 None 收尾。查到后，_on_end 才能使用其 finalize_task，并把同一 record 传给 _finalize_attempt。这里只需保留查询与存在性检查，不另建辅助函数卡。

### 2. 完整函数：定位 → 创建或复用 → 等待

保留真实函数体，增加注释：

```python
async def _on_end(self, event: Any) -> None:
    record = self._require_record(event)  # 找到这次 Trial 对应的记录。
    if record.finalize_task is None:
        record.finalize_task = asyncio.create_task(
            self._finalize_attempt(record, event),
            name=f"harbor-end-{record.trial_id}",
        )
    await asyncio.shield(record.finalize_task)
```

- 首次进入：创建 Task 并立即把引用保存在 record 上。
- 同一记录再次进入：复用已有 Task，不另启动一份提交。
- `await` 表明当前回调会等待，而不是创建后立即返回。
- `shield` 防止等待回调被取消时，取消沿此等待传播给收尾 Task；它不保证 Task 一定成功，也不阻止该 Task 被其他地方直接取消。Task 的错误仍可能传到等待者，外面的 `_safe` 包装如何处理本轮不展开。

**create_task 和 shield 的区别**：create_task 已把 _finalize_attempt 调度为可独立推进的任务；shield 负责随后等待时的取消传播边界，不负责启动它。

```text
正常：_on_end 等待 ──────────→ 收尾 Task 完成 → _on_end 返回
取消：_on_end 的等待被取消   收尾 Task 仍可继续
                             （不会因这次等待者取消而被连带取消）
```

shield 不会让 _on_end 忽略取消一直等下去，也不保证收尾永不失败。这里希望保存结果和关闭资源的工作不因回调等待者被取消就一同中断；后续任务管理仍由插件负责。

**正常返回 None**。即使收尾 Task 返回 bundle，这里也没有 `return await ...`，不会直接把 bundle 返回给 Harbor。

### 3. 下游收尾只认识交接，不展开全部实现

| 当前入口 | 实际负责的内容 |
| --- | --- |
| `_on_end` | 查询记录、确保复用同一个收尾 Task、等待 |
| `_finalize_attempt` | 接住 record 与 event，组织提交并做最终关闭 |
| `commit_attempt` 及其下游 | 取得 Proxy 轨迹，结合尝试结果进行校验和保存 |

正常、非取消路径下，`_finalize_attempt` 将 `event.result` 连同 record 的 trial/session 身份传入 `commit_attempt`。成功得到 bundle 后，会设置 `record.bundle`，并放入插件 `_results[(trial_name, trial_id)]`；finally 尝试关闭本次路由等资源，关闭失败还可能撤下或作废结果。因此不能仅凭 Task 被创建，就认为结果已保存或可用于训练。

取消路径不会照常生成训练 bundle，当前只标明边界。**这里读取的是 Dressage Proxy 轨迹，不是前面 Harbor 生成的 agent/trajectory.json。**

| 按需查看真实子函数 | 带着什么问题进入、读完回哪里 |
| --- | --- |
| [_require_record:894](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:894) | 如何按 Trial 身份找到记录；返回当前第一行，本文已解释到查询层 |
| [_finalize_attempt 函数卡](DressageHarborPlugin._finalize_attempt.md) | 当前继续：评分、Proxy 轨迹和保存结果如何接上；它在 Task 内运行，完成后解除当前等待 |

当前先读到“一个尝试对应一个被复用的收尾 Task”。不要把 Task 调度、结果持久化和整个 Job 返回混为一步。

### 4. 当前场景的状态变化

```text
进入前                         正常完成收尾后（提交及关闭成功）
record.finalize_task = None     record.finalize_task = 已完成的 Task
record.bundle 尚无结果          record.bundle = 本次 bundle
                               插件 _results 中可按 Trial 身份查到它

_on_end 的返回值：None
```

第二、三行变化是下游 _finalize_attempt 的副作用，不是 _on_end 直接赋值。此图为静态推演，未运行真实回调或存储。

## 我的直接表述（原话）

> 好的 那么看一下这个on end吧

用户本轮初步理解与追问（节选）：

> 在运行前on job start的时候久等极了dressage部分的on end
> 这样子的话 就能够在harbor结束的时候运行了？
> 然后trial finalize的时候出发了这个trial envent 的end
> 就会使用这个函数？
> 然后这个函数具体的功能就是
> 记录这个event？
> 然后在这里继续create这个task？
> 然后硬性这个finalize attempt？
> 然后这个task需要通过asyncio 的shield来运行是做什么呢？

助手校准：登记与 END 调用的方向正确；_require_record 是查询已有记录，不是记录事件。create_task 调度收尾，shield 控制等待时的取消传播。对这些修正的理解尚待反馈。

本轮用户已串起的关系（原话节选）：

> 这样子就穿起来了
> 也就是之前传入这的这个on end 会在trial的end部分运行
> 然后这里on end的部分里面有一个finalize attempt 是我的理解

用户进一步要求简单查看 _require_record；助手补充按身份查已有记录、缺失即报错，并保留 Task 调度与直接普通调用的区别。

## 尚不清楚

- _finalize_attempt 怎样把评分与 Proxy 轨迹交给提交层，后续可沿当前边界继续。
- bundle 的校验、保存与可训练条件，本轮未展开。
- _safe、取消与关闭失败的完整治理，本轮仅标边界。

<details>
<summary>来源与验证</summary>

- [回调注册](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:405)、[当前函数与下游](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:742)。
- [AttemptRecord](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:149)、[事件键](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:1239)。
- [Harbor Trial._finalize](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:660)、[_emit](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:590)、[TrialHookEvent](/home/hongshi/projects/harbor/src/harbor/trial/hooks.py:29)。
- [本步形成过程](../../../../../../04-flow.md)。静态源码阅读，不是跨版本集成或任务提交实测。

</details>


### 本轮 shield 理解反馈

用户表示：“也就是原来可以a或许不再等待了 但是b还是可以继续做这件事情 我可以这么理解吗？”助手确认其核心关系，并限定为 A 被取消时不把该取消传给 B；正常时 A 仍等待，直接取消 B 不受 shield 阻止。随后用户确认继续进入 _finalize_attempt。
