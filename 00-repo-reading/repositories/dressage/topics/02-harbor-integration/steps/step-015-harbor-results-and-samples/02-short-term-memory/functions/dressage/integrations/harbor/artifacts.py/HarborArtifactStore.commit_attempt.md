# HarborArtifactStore.commit_attempt

- 代码归属：**Dressage**，不是 Harbor 核心库。
- 源码：[artifacts.py:256](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:256)，提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次单独建卡：2026-11-16，Step 015；用户已要求补齐这一层交接，尚无本函数机制的个人复述。
- 本轮边界：查找、创建/复用提交 Task、等待并返回 bundle；下游只选读数据汇合，不完整精读持久化和恢复。

[本步 scope](../../../../../../01-scope.md) · [返回 _finalize_attempt](../plugin.py/DressageHarborPlugin._finalize_attempt.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：_finalize_attempt 已接到 Harbor 的结果，带着本次身份和 Proxy 客户端调用这里，等待提交后的 bundle。
2. **具体内容**：用 Trial 名称与 ID 查提交任务；已有则复用，没有则创建 _commit_attempt_once 的 Task 并保存；通过 shield 等待并返回其结果。
3. **建议构建的心智模型**：

   > 同一次尝试复用同一个提交任务，等它完成，把结果包返回给调用者。具体提交在 _commit_attempt_once 中执行。

4. **调用位置**（调用方节选，省略实参）：

   ```python
   bundle = await self._artifact_store.commit_attempt(...)
   record.bundle = bundle
   self._results[(record.trial_name, record.trial_id)] = bundle
   ```


下一处局部阅读：[\_commit_attempt_once：数据来源、结果包与 trainable](HarborArtifactStore._commit_attempt_once.md)。

## 本场景的输入与输出

### ① 按这次尝试的身份查找提交任务

```python
key = (str(trial_name), str(trial_id))
task = self._commit_tasks.get(key)
```

可以读成：

> 这次 Trial 是否已经启动过提交？先查一下登记的任务。

_trial name_ 相同不代表同一次实际尝试，重试可能生成新的 trial_id，所以这里使用两者组成键。`self._commit_tasks` 保存的是 **Task**，不是 bundle；不要与插件 `_results` 的结果查询表混淆。

### ② 没有就创建，有就直接复用

下面是实际代码的教学裁剪，只将内部参数列表写成 `...`；完整转发在文末。

```python
if task is None:
    task = asyncio.create_task(
        self._commit_attempt_once(...),
        name=f"harbor-artifact-{trial_id}",
    )
    self._commit_tasks[key] = task
```

可以读成：

> 第一次来就启动提交工作，并记住这个 Task。以后同一个键再来，等待已经登记的 Task。

这只是当前 Store 对象内的任务复用，不代表这一层已经实现跨进程、跨重启的全部幂等保障。同一键再次调用也不会在这里比较新参数或自动重建失败 Task；不能把复用理解成“每次重新提交一次”。

<details>
<summary>它把哪些参数交给实际提交函数？</summary>

| 输入类别 | 主要参数 | 当前层怎么处理 |
| --- | --- | --- |
| 作业、尝试与会话身份 | job_id、trial_name、trial_id、session_id、instance_id、attempt_ordinal | 多个 ID 转为字符串，继续传入 |
| Harbor 结果与状态 | trial_result、failures、cancelled | 结果直接传入，failures 转为 list |
| 版本与策略 | expected_weight_version、routing_guarantee、task_network_class、label | 继续传入下游 |
| 客户端与目录 | proxy_client、trial_dir | 客户端继续传入；目录存在时转成绝对 Path |

这一层不读取奖励文件、不解析 token、不打包 Harbor 的产物目录。trial_dir 在下游用于 bundle 保存路径检查，详见上层卡的现有说明。

</details>

### ③ 等待提交任务，并把 bundle 返回

```python
return await asyncio.shield(task)
```

可以读成：

> 等提交任务完成，把它产生的结果包返回。当前等待者被取消时，不要因此连带取消提交任务。

正常返回值是 **HarborTrajectoryBundle**。与 _on_end 的区别是：这里有 `return`，会将 Task 的结果交还给 _finalize_attempt。

```text
_finalize_attempt 的收尾 Task
  → await commit_attempt(...)
      → 创建或复用另一个提交 Task
          → _commit_attempt_once(...) 生成 bundle
      ← return await shield(task) 返回 bundle
  → record.bundle = bundle
  → 插件查询表登记 bundle
  → finally 关闭本次路由
```

这两个 Task 负责不同范围：外层组织整次收尾，内层组织结果提交。shield 不保证任务一定成功；下游异常可向上传播，等待者取消时也不保证等待者能拿到返回值。

### 本函数的输入与输出，收束起来看

- 输入：同一次尝试的身份、Harbor 结果、Proxy 客户端及提交条件。
- 副作用：首次调用为该键创建并登记提交 Task。
- 正常输出：下游 Task 返回的同一个 bundle，不在此重新构造。
- 读完回到：_finalize_attempt 中的 `bundle = await ...`，接着登记结果。

| 按需继续 | 从哪里进入 | 读到哪里停 |
| --- | --- | --- |
| 结果包怎样构造 | [scope 3.2 的数据交接](../../../../../../01-scope.md#bundle-handoff)；[实际子函数 _commit_attempt_once:307](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:307) | 只看身份、评分与 segments 的汇合及 trainable 条件；完整存储/恢复暂不展开 |

## 我的直接表述（原话）

用户指出调用链中的缺口：

> 不对啊
> 这里3.2的内容中其实写了commit attempt
> 我是否还是需要看一下呢？

随后确认建立记录：

> 那么是否考虑构建一下一个short term function
> 然后考虑一下在这里的scope中写清楚呢？

本轮记录的是已确认的阅读入口，尚无对本函数机制的个人复述。与 _on_end 的相似性属于助手核对说明，不自动视为掌握。

## 尚不清楚

- 下游完整提交、持久化、失败恢复仍未精读；本轮不要求展开。
- 结果包的数据汇合与 trainable 条件已有局部说明，理解程度仍待反馈。
- 本轮未运行重复调用、取消或真实提交实验。

<details>
<summary>固定版本完整函数：保留全部转发参数</summary>

```python
async def commit_attempt(
    self,
    *,
    proxy_client: ProxyClientProtocol,
    job_id: str,
    trial_name: str,
    trial_id: str,
    session_id: str,
    instance_id: str,
    attempt_ordinal: int,
    trial_result: Any,
    failures: Sequence[AttemptFailure] = (),
    cancelled: bool = False,
    expected_weight_version: str | None = None,
    routing_guarantee: Literal["configure_only", "enforced"],
    task_network_class: Literal["public", "restricted"],
    label: Any | None = None,
    trial_dir: str | Path | None = None,
) -> HarborTrajectoryBundle:
    """Finalize, snapshot, validate, persist, then drain one attempt.

    The key includes the actual Harbor ``trial_id`` because retries reuse a
    logical TrialConfig/trial name while creating a new physical Trial.
    """

    key = (str(trial_name), str(trial_id))
    task = self._commit_tasks.get(key)
    if task is None:
        task = asyncio.create_task(
            self._commit_attempt_once(
                proxy_client=proxy_client,
                job_id=str(job_id),
                trial_name=str(trial_name),
                trial_id=str(trial_id),
                session_id=str(session_id),
                instance_id=str(instance_id),
                attempt_ordinal=attempt_ordinal,
                trial_result=trial_result,
                failures=list(failures),
                cancelled=cancelled,
                expected_weight_version=expected_weight_version,
                routing_guarantee=routing_guarantee,
                task_network_class=task_network_class,
                label=label,
                trial_dir=Path(trial_dir).resolve() if trial_dir else None,
            ),
            name=f"harbor-artifact-{trial_id}",
        )
        self._commit_tasks[key] = task
    return await asyncio.shield(task)
```

</details>

<details>
<summary>来源与验证</summary>

- [当前函数及实际提交函数](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:256)。
- [调用方 _finalize_attempt](/home/hongshi/projects/Dressage/dressage/integrations/harbor/plugin.py:751)。
- [本步讨论](../../../../../../04-flow.md)。仅静态源码核对，无真实存储或跨版本集成验证。

</details>
