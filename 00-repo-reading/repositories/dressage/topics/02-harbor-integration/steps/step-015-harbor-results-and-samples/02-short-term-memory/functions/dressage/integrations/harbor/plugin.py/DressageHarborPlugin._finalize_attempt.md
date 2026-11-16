# DressageHarborPlugin._finalize_attempt

- 代码归属：**Dressage**，`dressage/integrations/harbor/plugin.py`。
- 源码：[plugin.py:751](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:751)，提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次单独阅读：2026-11-16，Step 015；用户确认进入本函数，尚无本函数的个人机制复述。
- 当前范围：组织提交、登记 bundle、最终关闭；commit_attempt 内部暂作黑箱。静态核对，未运行提交或资源关闭。

[本步 scope](../../../../../../01-scope.md) · [返回 _on_end](DressageHarborPlugin._on_end.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Harbor 发出单次 Trial 的 END 后，Dressage 的 _on_end 创建收尾 Task；该 Task 实际执行本函数。
2. **具体内容**：处理提交前状态，把尝试身份与 Harbor 结果交给提交层，登记返回 bundle，并在 finally 关闭本次路由；关闭失败时撤下可查询结果并尝试作废 bundle。
3. **建议构建的心智模型**：

   > 把这次尝试的结果交出去、保存查找入口，再收好本次路由。提交完成还要经过关闭，不能只把它理解为存一个结果。

4. **调用代码**（来自 _on_end）：

   ```python
   record.finalize_task = asyncio.create_task(
       self._finalize_attempt(record, event),
       name=f"harbor-end-{record.trial_id}",
   )
   # _on_end 随后通过 shield 等待这个 Task。
   ```

## 本场景的输入与输出

### 1. 两份输入怎样接起来

| 输入 | 来自哪里 | 当前用途 |
| --- | --- | --- |
| `record: AttemptRecord` | Dressage 已保存的本次尝试记录 | 提供 trial/session/instance 身份、状态、失败记录与路由句柄 |
| `event` | Harbor END 事件 | 提供 `event.result`（含评测结果）及用于定位本次目录的配置 |

`event.result` 不是只有 reward，record 也不是 Sample。提交时把两份信息交给同一个 commit_attempt，才能关联这次 Harbor 尝试与其 Proxy 会话。

正常非取消、提交及关闭成功时返回 **HarborTrajectoryBundle**，并更新 `record.bundle`、插件 `_results`。取消路径返回 None；异常可以向上传播。调用者 _on_end 不把这个返回值继续返回给 Harbor。

<details>
<summary>record 从哪里来？当前位置在 Trial.run 的哪一段？</summary>

正常路径的顺序：

```text
【Harbor】Trial.run
  ├─ 初始化 self.result
  ├─ 发出 START →【Dressage】_on_start 创建 AttemptRecord，放入 _attempts
  ├─ _prepare
  ├─ _run：Agent 执行 → 日志与产物 → 评测写入 self.result
  ├─ finally: Trial._finalize
  │    └─ 发出 END，event.result 指向当前 Harbor self.result
  │         →【Dressage】_on_end 按 Trial 身份取回已有 record
  │              → Task 执行 _finalize_attempt(record, event)  ← 当前
  └─ 完成其他清理，return self.result
```

因此当前在正常路径中是 _run 之后、Trial.run 返回之前；失败路径也可能进入 finally，不要求 _run 成功结束。

record 是 Dressage 在 START 时建立并维护的尝试记录，不是 Harbor 的 TrialResult，也不是产物文件。在此实现中，创建时 `record.session_id = trial_id`，配合 instance_id 关联 Proxy 会话；record.handle 指向本次路由句柄。

- Harbor 的 `event.result`：本次执行、评分、时间及异常等结果信息。
- Harbor 的 `<trial_dir>/artifacts/`：之前收集的实际任务文件，独立保存在磁盘。
- Dressage 的 `record`：哪次 Trial 对应哪个 Proxy 会话、当前路由状态，以及收尾 Task/结果包引用。

commit_attempt 使用 record 的身份参数和 event.result，而 trial_dir 仅作前述路径检查；不是把三者视为同一个容器。

来源：[Trial.run](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:601)、[Dressage _on_start](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:639)、[AttemptRecord 字段](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:149)。

</details>

### 2. 核心骨架：先看正常路径

Agent 已执行完，Harbor 已形成结果。这里接着做“提交 → 登记 → 关闭”。

教学裁剪：展开本轮重要的真实参数，暂省略版本与策略参数、前置状态分支及关闭失败处理；不是可直接运行的完整调用，完整原函数在末尾。

```python
try:
    record.phase = AttemptPhase.FINALIZING
    trial_dir = _trial_dir(event)  # 从 Harbor 事件定位这次尝试的本地目录。

    # ① 委托提交：关联这次尝试、Harbor 结果和 Proxy 会话，取得结果包。
    bundle = await self._artifact_store.commit_attempt(
        proxy_client=self._proxy_client,  # 提交层通过它向 Proxy 取得记录。

        # 这份结果属于哪个作业、哪次尝试？
        job_id=self._job_id or "unknown",
        trial_name=record.trial_name,
        trial_id=record.trial_id,
        attempt_ordinal=record.attempt_ordinal,  # 尝试序号。

        # 需要关联哪份 Proxy 会话？
        session_id=record.session_id,
        instance_id=record.instance_id,

        # Harbor 给出了什么结果？本次还有哪些失败/取消状态？
        trial_result=getattr(event, "result", None),  # 含前面获得的评测结果。
        failures=record.failures,
        cancelled=record.cancel_requested,
        trial_dir=trial_dir,  # 用于检查 bundle 不能写入此目录；不是把产物文件传进去。
        # 暂省略 expected_weight_version、routing_guarantee、
        # task_network_class、label；来源见下一节与完整原函数。
    )

    # ② 登记：两个位置指向同一个结果包，方便后续查询。
    record.bundle = bundle
    self._results[(record.trial_name, record.trial_id)] = bundle
    return bundle  # 先执行 finally，再完成返回。
finally:
    # ③ 关闭：结束本次模型访问通道。
    closed = await self._close_attempt(record)
    if closed:
        self._rotate_slot_after_end(record)
    # 关闭失败分支见第 5 节。
```

**① 可以读成：**“请根据这次任务的身份、Harbor 给出的结果，以及对应的 Proxy 会话完成提交；完成后，把结果包交给我。”bundle 先理解为这次尝试整理后的结果包。具体读取与保存由 commit_attempt 完成。

**② 可以读成：**“在当前尝试上挂好结果，同时让插件以后能按 Trial 身份查到它。”这里不是生成两份结果。

**③ 可以读成：**“无论前面的提交顺利与否，最后都尝试关闭这次路由。”

```text
_on_end 创建的 Task 开始执行
  → 提交前整理状态
  → commit_attempt：交出身份 + Harbor 结果，取得 bundle
  → 把 bundle 记在 record 和插件查询表中
  → finally：关闭本次路由
  → Task 完成，_on_end 的等待才结束
```

`return bundle` 不会跳过 finally：关闭逻辑先执行，再完成本次返回。

### 3. 提交前与提交时：交出去的是什么

开头的真实业务分支必须保留：

```python
if record.phase is AttemptPhase.ACTIVE:
    await self._quiesce(record)
if record.cancel_requested:
    return None
if record.phase is not AttemptPhase.BROKEN:
    record.phase = AttemptPhase.FINALIZING
```

- 若路由还处于 ACTIVE，先委派 quiesce 收束；内部如何等待请求暂不展开。
- 若这次已取消，跳过结果提交，但仍会进入 finally 关闭。
- BROKEN 不会被改写为 FINALIZING；这里也没有因此直接跳过 commit_attempt。不能把所有失败状态都看成取消分支。

提交层接收的关键字段如下，全部出自真实调用；完整参数在折叠源码中：

| 传入字段 | 值的来源 |
| --- | --- |
| `job_id` | 插件的作业 ID，缺失时传 "unknown" |
| `trial_name`, `trial_id`, `attempt_ordinal` | record：这是哪次尝试及其序号 |
| `session_id`, `instance_id` | record：关联哪份 Proxy 会话 |
| `trial_result` | `getattr(event, "result", None)`：Harbor 执行及评测结果 |
| `failures`, `cancelled` | record：当前失败与取消状态 |
| `trial_dir` | `_trial_dir(event)`：本次目录；提交层用来检查 bundle 保存路径位于其外，不用它打包产物 |
| `proxy_client` | 插件持有的客户端：由提交层向 Proxy 取资料 |
| `expected_weight_version` | 优先 record 的版本，否则读取插件 training 配置，供下游校验 |
| `routing_guarantee` | 插件 security 配置，默认 "configure_only" |
| `task_network_class` | record 的任务网络类别 |
| `label` | 当前传 None |

这些参数不全是待保存数据：proxy_client 是操作工具，版本与路由策略是下游判断的条件。当前把 commit_attempt 理解为“提交这次结果并取得 bundle”。bundle 不是直接等于 event.result，也不是 Harbor 的 agent/trajectory.json；内部的轨迹读取、校验和保存下一层再看。

**这里是否包含实际产物文件？** 没有把它们装入 bundle。需要区分两个位置：

```text
Harbor 收集的任务文件：<trial_dir>/artifacts/app/calc.py 等
    来源：前面的 _collect_artifacts

Dressage 的 HarborTrajectoryBundle：身份、评分、Proxy segments、状态等
    来源：当前 commit_attempt
```

`trial_result=event.result` 提供 Harbor 结果信息，提交层从中提取评分、任务/Agent 信息、时间及失败信息；它不是代码文件的内容。`proxy_client` 用于取得 Proxy 模型轨迹，可能包含模型交互文本，但这不等于归档整个产物目录。

源码中 `trial_dir` 在磁盘保存路径上交给 `_ensure_outside_trial_dir(output_path, trial_dir)`，防止 bundle 保存到 Harbor 的 Trial 目录内；不表示读取或复制该目录。这里的 ArtifactStore “artifact” 指它保存的结果包，与 Harbor collect_artifacts 的任务文件不是同一对象。

依据：[bundle 构造及保存路径检查](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:441)、[目录检查实现](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:1133)。此前“这次尝试的结果包”是职责概括，不应理解成包含所有运行产物文件的压缩包。

本轮已补充 [结果包字段、来源与 trainable 判断](../../../../../../references/harbor-trajectory-bundle.md)。这里只选读数据交接，不表示已精读 commit_attempt 内部。

### 4. 提交返回后：在哪里找到结果

```python
record.bundle = bundle
self._results[(record.trial_name, record.trial_id)] = bundle
return bundle
```

这是两个内存登记位置，不是这里又执行两次落盘：

```text
record.bundle ───────────────────┐
                                ├→ 同一个 bundle
self._results[(名称, Trial ID)] ─┘
```

record 保留本次尝试的结果，插件查询表供之后按 Trial 身份查找。真正保存由前面的提交层负责；这里先不展开 bundle 的全部字段。

### 5. finally：结束的是 Dressage 本次路由

```python
closed = await self._close_attempt(record)
if closed:
    self._rotate_slot_after_end(record)
else:
    self._results.pop((record.trial_name, record.trial_id), None)
    # 如果已有 bundle，再尝试 invalidate_bundle。
```

这里关闭的是 record.handle 所代表的路由/尝试句柄，**不是再运行一次 Harbor 的容器停止流程**。

| 关闭结果 | 后续处理 |
| --- | --- |
| 成功 | record 进入 CLOSED；调用凭据槽位轮换逻辑，有对应槽位时更新它 |
| 失败 | 从插件结果表移除这次结果；若已有 bundle，尝试将其作废 |

关闭失败分支没有直接写 `return None`，也没有清空 record.bundle。因此不能只看 Task 返回了 bundle 就判断结果可用；它可能已从查询表撤下或被作废。作废失败会记录 warning，完整治理本轮不展开。

### 6. 读完回哪里

| 按需查看真实子函数 | 进入的问题与返回位置 |
| --- | --- |
| [commit_attempt 函数卡](../artifacts.py/HarborArtifactStore.commit_attempt.md) | 下一层候选：身份、评分与 Proxy 轨迹如何提交；返回第 4 节登记 bundle |
| [_close_attempt:853](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:853) | 当前只知道关闭本次句柄并报告成功/失败；返回 finally 的分支 |

当前先能说明“提交 → 登记 → 关闭”即可，返回 _on_end 的 shield 等待处。取消、作废与凭据轮换只保留边界，不追加必读函数卡。

## 我的直接表述（原话）

> 好的 那么看一下这个finalize attempt吧

尚无本函数的个人机制复述；上面是助手依据固定版本源码整理。

本轮补充要求（原话）：

> 稍微膨胀一下这里的这个artifact store commit attempt吧
> 主要需要记录这里的这个参数比较重要

据此只在连续骨架中展开身份、结果、状态及操作依赖参数，其余参数保留来源表和完整源码，不新增阅读阶段。

本轮定位问题（原话）：

> 那么这个record和刚才的两个部分的关系具体是什么呢？
> 我其实不是特别理解
> 这里是在我们刚才说的_run结束之后的内容对吗？
> 也就是tria run这里的这个finalize部分？

助手核对 START 创建 record、END 取回 record 的时序，并区分 Harbor 结果、磁盘产物与 Dressage 尝试记录；理解反馈待续。

## 尚不清楚

- commit_attempt 如何取得并保存具体的 bundle，当前明确作为黑箱。
- bundle 可训练性的完整判断与字段，尚未展开。
- quiesce、路由关闭和凭据轮换内部实现，本轮只知用途。

<details>
<summary>固定版本完整函数体</summary>

```python
async def _finalize_attempt(
    self,
    record: AttemptRecord,
    event: Any,
) -> HarborTrajectoryBundle | None:
    try:
        if record.phase is AttemptPhase.ACTIVE:
            await self._quiesce(record)
        if record.cancel_requested:
            # CANCEL is followed by END in Harbor.  END is still the sole
            # cleanup owner, but cancelled sessions are diagnostics-only
            # and must never be finalized/read into a training bundle.
            return None
        if record.phase is not AttemptPhase.BROKEN:
            record.phase = AttemptPhase.FINALIZING

        if self._artifact_store is None or self._proxy_client is None:
            raise RuntimeError("artifact dependencies were not initialized")
        trial_dir = _trial_dir(event)
        bundle = await self._artifact_store.commit_attempt(
            proxy_client=self._proxy_client,
            job_id=self._job_id or "unknown",
            trial_name=record.trial_name,
            trial_id=record.trial_id,
            session_id=record.session_id,
            instance_id=record.instance_id,
            attempt_ordinal=record.attempt_ordinal,
            trial_result=getattr(event, "result", None),
            failures=record.failures,
            cancelled=record.cancel_requested,
            expected_weight_version=(
                record.expected_weight_version
                if record.expected_weight_version is not None
                else _config_get(
                    self.config, "training.expected_weight_version", None
                )
            ),
            routing_guarantee=str(
                _config_get(
                    self.config,
                    "security.routing_guarantee",
                    "configure_only",
                )
            ),
            task_network_class=record.task_network_class,
            label=None,
            trial_dir=trial_dir,
        )
        record.bundle = bundle
        self._results[(record.trial_name, record.trial_id)] = bundle
        return bundle
    finally:
        closed = await self._close_attempt(record)
        if closed:
            self._rotate_slot_after_end(record)
        else:
            self._results.pop((record.trial_name, record.trial_id), None)
            if record.bundle is not None and self._artifact_store is not None:
                failure = record.failures[-1]
                try:
                    await self._artifact_store.invalidate_bundle(
                        record.bundle,
                        failure,
                    )
                except Exception:
                    logger.warning(
                        "failed to invalidate bundle after route close failure",
                        exc_info=True,
                    )
```

</details>

<details>
<summary>来源与验证</summary>

- [本函数](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:751)、[_on_end](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:742)。
- [关闭与轮换](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:853)、[目录定位](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:1243)。
- [本步讨论](../../../../../../04-flow.md)。示意流程未经实际提交或关闭验证，不将静态阅读视为集成成功。

</details>
