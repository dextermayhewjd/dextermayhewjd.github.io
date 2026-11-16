# DressageHarborPlugin._finalize_attempt

- 代码归属：**Dressage**，`dressage/integrations/harbor/plugin.py`。
- 源码：[plugin.py:751](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:751)，提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次单独阅读：2026-11-16，Step 015；用户确认进入本函数，尚无本函数的个人机制复述。
- 当前范围：组织提交、登记 bundle、最终关闭；commit_attempt 内部暂作黑箱。静态核对，未运行提交或资源关闭。

[本步 scope](../../01-scope.md) · [返回 _on_end](../../02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_end.md)

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

下面按正常路径摘出三个动作；`...` 省略调用参数，`finally` 仅展示原函数片段，完整代码与分支保留在后面的折叠区。

### ① 委托保存这次尝试的结果

```python
bundle = await self._artifact_store.commit_attempt(...)
```

可以读成：

> “请根据这次任务的身份、Harbor 给出的结果，以及对应的 Proxy 会话，完成结果提交；完成后，把整理好的结果包交给我。”

这里先把 bundle 理解为**“这次尝试整理后的结果包”**。不用现在记住它的所有字段。

注意：具体怎样读取轨迹、怎样保存，是 commit_attempt 的工作。当前函数是在安排别人完成它。

### ② 记住这个结果包在哪里

```python
record.bundle = bundle
self._results[(record.trial_name, record.trial_id)] = bundle
```

第一行：

> “在这次尝试自己的记录上，挂上结果。”

第二行：

> “在插件的查询表里登记：以后拿这个 Trial 的名字和 ID，就能找到结果。”

就像同一份文件，既放进个人档案，也登记到检索目录。这里两个位置指向同一个对象，不是又生成两份结果。

### ③ 结束这次尝试使用的模型访问通道

```python
finally:
    closed = await self._close_attempt(record)
```

可以读成：

> “无论前面的提交顺利与否，最后都要尝试关闭这次路由。”

<details>
<summary>参数为什么这么多：按职责回查完整参数</summary>

参数不全是最终要记录的数据，其中还包括校验条件和执行依赖。

当前传入的 `record` 是 Dressage 的尝试记录，`event.result` 是 Harbor 的执行与评测结果。下面保留此前的关键参数节选，其他必需参数仍省略，不可直接复制运行：

```python
bundle = await self._artifact_store.commit_attempt(
    # 这份结果属于哪次尝试、哪个模型会话？
    trial_name=record.trial_name,
    trial_id=record.trial_id,
    session_id=record.session_id,
    instance_id=record.instance_id,

    # Harbor 给出了什么执行、评测结果？
    trial_result=getattr(event, "result", None),

    # 提交层通过什么访问模型记录？
    proxy_client=self._proxy_client,
    # 其余参数见后面的完整原函数。
)
```

正常提交并关闭成功时，本函数返回 bundle，_on_end 仅等待而不直接向 Harbor 返回这个 bundle。`return bundle` 不会跳过 finally。bundle 也不直接等于 event.result 或 Harbor 的 agent/trajectory.json。


| 职责 | 原调用中的参数 | 来源或用途 |
| --- | --- | --- |
| 标识这次尝试 | job_id、trial_name、trial_id、session_id、instance_id、attempt_ordinal | 插件与 record；关联作业、尝试、Proxy 会话 |
| 执行结果与状态 | trial_result、failures、cancelled | event.result 和 record；提供结果与失败/取消信息 |
| 校验条件 | expected_weight_version、routing_guarantee、task_network_class | record 或插件配置；传给提交层判定 |
| 操作工具与位置 | proxy_client、trial_dir | 插件客户端；_trial_dir(event) 计算本次目录 |
| 额外标注 | label | 本次固定传 None，暂不展开下游含义 |

此前卡片把全部参数与分支同时展示，增加了理解负担。当前正文仅保留三个动作，主要交接参数在本折叠区回查，完整实参保留在原函数中。

**设计疑问（未下结论）：**这个接口把身份、状态、策略、依赖混在一个长参数列表中。若相同身份字段总是一起传递，可以研究是否收拢为明确的数据对象；需要查看其他调用方和约束后判断，不能只把长列表藏进一个大对象。此处不修改产品源码。

</details>

<details>
<summary>提交前分支：ACTIVE、取消与 BROKEN</summary>

开头的真实业务分支必须保留：

```python
if record.phase is AttemptPhase.ACTIVE:
    await self._quiesce(record)  # 路由还在活动中，先收束模型请求再提交。
if record.cancel_requested:
    return None                 # 取消的尝试不走正常提交，但仍执行 finally 关闭。
if record.phase is not AttemptPhase.BROKEN:
    record.phase = AttemptPhase.FINALIZING  # 正常进入收尾；保留已有 BROKEN 状态。
```

- 若路由还处于 ACTIVE，先委派 quiesce 收束；内部如何等待请求暂不展开。
- 若这次已取消，跳过结果提交，但仍会进入 finally 关闭。
- BROKEN 不会被改写为 FINALIZING；这里也没有因此直接跳过 commit_attempt。不能把所有失败状态都看成取消分支。


取消路径返回 None，异常可能向上传播；无论哪种路径，都不能把“有 END”理解成“成功得到可训练结果”。

</details>

<details>
<summary>关闭之后：凭据轮换，以及失败时如何撤下结果</summary>

```python
closed = await self._close_attempt(record)  # 尝试关闭本次路由，得到是否成功。
if closed:
    self._rotate_slot_after_end(record)  # 有对应槽位时轮换凭据。
else:
    # 关闭未成功：不要让后续从正常结果表中取走这次结果。
    self._results.pop((record.trial_name, record.trial_id), None)
    # 如果已经有 bundle，再尝试 invalidate_bundle，将该结果标记为不可用。
```

这里关闭的是 record.handle 所代表的路由/尝试句柄，**不是再运行一次 Harbor 的容器停止流程**。

| 关闭结果 | 后续处理 |
| --- | --- |
| 成功 | record 进入 CLOSED；调用凭据槽位轮换逻辑，有对应槽位时更新它 |
| 失败 | 从插件结果表移除这次结果；若已有 bundle，尝试将其作废 |

关闭失败分支没有直接写 `return None`，也没有清空 record.bundle。因此不能只看 Task 返回了 bundle 就判断结果可用；它可能已从查询表撤下或被作废。作废失败会记录 warning，完整治理本轮不展开。


</details>

<details>
<summary>按需继续：子函数与返回位置</summary>

先能连贯说明“委托提交 → 登记结果 → 关闭通道”，再沿当前问题选择是否深入。

| 按需查看真实子函数 | 进入的问题与返回位置 |
| --- | --- |
| [commit_attempt:256](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:256) | 结果包具体怎样产生和保存；读完回到②登记 bundle |
| [_close_attempt:853](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:853) | 需要时再看具体关闭方式；读完回到③的 closed 分支 |

正常完成后回到 [_on_end](../../02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_end.md) 的 shield 等待处。此处没有新增下游函数卡。


</details>

## 我的直接表述（原话）

> 好的 那么看一下这个finalize attempt吧

本轮反馈（原话）：

> 我没有很懂
> 这里到底在做什么？
> 你可以简单和我说一下吗？
> 我知道这里是在finalize attempt
> 但我不知道这里具体是在做什么这件事情

> 可以在这里的代码旁边写清楚注释吗？
> 否则 我实在是看不明不白

前轮助手将三项动作写在代码旁。随后用户认可按动作解释的形式，并提出保留源码和关键参数：

> 我觉得这样子就好很多

> 对的 但是也要结合原来的这个代码不能完全离开代码也不太好
> 主要是这里的这个参数确实是代表了具体的需要记录的内容
> 但是我觉得这里参数膨胀了 其实不太好 这个代码写的

本轮按用户确认改为三个动作，每段保留代码、自然语言解释及执行后的变化；参数按职责分组，完整参数和分支折叠。用户认可解释形式，不据此标记全部机制已掌握。

本轮进一步纠正（原话）：

> 但是这样子其实是太散了 我觉得这个形式不是很好为什么不能直接用这个呢？

用户明确要求直接采用其贴出的三段说明。正文已按该文本保留短代码和解释，不再插入展开参数、阶段小结与额外过渡；参数和返回细节移到折叠区。

## 尚不清楚

- commit_attempt 如何取得并保存具体的 bundle，当前明确作为黑箱。
- bundle 可训练性的完整判断与字段，尚未展开。
- quiesce、路由关闭和凭据轮换内部实现，本轮只知用途。
- 长参数列表是否需要按身份/策略分组设计，尚未核对其他调用方，保留为设计疑问。

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
- [本步讨论](../../04-flow.md)。示意流程未经实际提交或关闭验证，不将静态阅读视为集成成功。

</details>
