# HarborArtifactStore._commit_attempt_once

- 代码归属：**Dressage**，`dressage/integrations/harbor/artifacts.py`。
- 源码入口：[artifacts.py:307](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:307)；本轮观察点：[构造 bundle:445](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:445)。
- 首次单独建卡：2026-11-16，Step 015。当前为局部阅读，尚无对此函数内部的个人复述；不标记完整读完。
- 本轮边界：**数据来源 → 构造 bundle → trainable 判断**。保存、清理与失败恢复仅定位。

[本步 scope](../../../../../../01-scope.md) · [返回 commit_attempt](HarborArtifactStore.commit_attempt.md) · [外层 _finalize_attempt](../plugin.py/DressageHarborPlugin._finalize_attempt.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Harbor 已给出这次 Trial 的执行与评测结果，插件委托 Store 提交这次尝试。`commit_attempt` 创建的提交 Task 执行本函数。
2. **具体内容**：结束 Proxy 会话并取得记录，提取 Harbor 评分、检查结果，构造 bundle；按 Store 模式保存，尝试清理 Proxy 中的记录，登记并返回 bundle。
3. **建议构建的心智模型**：

   > 按同一次尝试的身份，把“Harbor 评了多少分”和“Proxy 记录了哪些模型生成”整理成一份结果包，并标明它能否用于训练。

4. **调用代码**（调用方教学节选，参数省略）：

   ```python
   # commit_attempt 内：仅在没有对应提交 Task 时创建。
   task = asyncio.create_task(self._commit_attempt_once(...), ...)
   # 随后由 commit_attempt 等待 Task，返回这里产生的 bundle。
   ```

## 本场景的输入与输出

进入时已经有：`trial_result`（Harbor 的结果）、Trial/session 等身份、`proxy_client`，以及取消状态、已有失败和版本/策略要求。`trial_dir` 用于检查保存位置，不代表本函数会读取并打包该目录下的全部文件。

正常返回：一个 `HarborTrajectoryBundle`；Store 还会登记它，磁盘模式会写结果文件。发生提交错误时可能抛异常，不能假定一定返回成功结果。

### ① 先看结果包装了什么：445–472 行

教学节选：保留本轮三类数据和训练检查结果，省略其他必需参数，不能独立执行。

```python
bundle = HarborTrajectoryBundle(
    trial_id=trial_id,                 # 身份：哪次 Trial？
    session_id=session_id,             # 对应哪个 Proxy 会话？
    instance_id=instance_id,           # 对应哪个会话实例？
    rewards=rewards,                   # Harbor 给出的评分字典
    reward_key=self.reward_key,        # 选哪个评分项？
    reward=rewards.get(self.reward_key),
    segments=segments,                 # Proxy 给出的模型交互记录
    trainable_token_count=token_count, # 检查时统计的可训练 token 数
    failures=_deduplicate_failures(failures),
    warnings=warnings,
    trainable=False,                   # 初始值；下一段再判断
    ...
)
```

**bundle 在这里是一个结果对象，不是把日志、代码文件压缩成一个包。** Harbor 的文件产物仍有自己的收集与保存位置。

### ② 再向上对应两路数据的来源：391–443 行

下面按源码先后摘取关键语句；中间的保护条件、镜像写入与失败处理省略。

```python
trajectory_payload = await proxy_client.read_trajectory(
    trajectory_id=session_id,
    instance_id=instance_id,
    drain=False,
)
segments = _payload_segments(trajectory_payload)

rewards = _extract_rewards(trial_result)
failures.extend(_harbor_result_failures(trial_result))
validation_failures, warnings, token_count, versions = validate_attempt(...)
failures.extend(validation_failures)
```

- `segments`：来自 Proxy 返回值的 `data` 列表，保留其中的字典记录；这里不读取 Harbor 的 `agent/trajectory.json`。
- `rewards`：当前单步场景来自 `trial_result.verifier_result.rewards`。辅助函数也兼容从多步结果中倒序找评分，本轮不展开。
- `validate_attempt`：检查评分、模型记录及相关版本/身份要求，返回失败、提示、token 数和版本。本轮只认输入输出。

静态字段示例，不是运行结果，也不是完整可通过验证的输入：

```text
输入 / 来源                                bundle 中的字段
trial_id = "trial-A"                    → trial_id = "trial-A"
session_id = "session-A"                → session_id = "session-A"
Harbor rewards = {"reward": 1.0}         → rewards = {"reward": 1.0}
Store reward_key = "reward"              → reward_key = "reward", reward = 1.0
Proxy payload["data"] 中的字典记录        → segments = [这些模型记录]
```

### ③ 最后看能否用于训练：473–478 行

这是源码中的完整条件：

```python
bundle.trainable = (
    not cancelled
    and checkpoint is FinalizationCheckpoint.TRAJECTORY_SNAPSHOTTED
    and not any(failure.fatal for failure in bundle.failures)
    and token_count > 0
)
```

四项都成立才为 True：没有取消、已经取得轨迹快照、没有致命失败、有可训练 token。**有 bundle 不等于可训练；合法的 0 分也不等于不可训练。** `trainable` 也不代表已经被后续选入训练批次。

**本轮读到这里停。** 后面的保存与清理只保留交接：按模式保存 → 尝试 `drain=True` 清理 Proxy 记录 → 登记到 Store 的 `_bundles` → `return bundle`。具体实现暂不下钻。

返回路线：本函数返回 → `commit_attempt` 的等待得到 bundle → `_finalize_attempt` 执行：

```python
record.bundle = bundle
self._results[(record.trial_name, record.trial_id)] = bundle
```

## 我的直接表述（原话）

进入本卡前，对整体委派的理解：

> 简单来说是从这里的这个store中commit once
> 然后生成具体的这个bundle？

上述原话是对职责的初步理解，不代表已经理解内部字段与保存过程。

## 尚不清楚

- 用户此前不确定是否需要完整阅读本函数；本轮已确认只选读三处，并独立保存此卡。
- 具体字段关系尚待阅读反馈；验证算法、文件原子写入、重试与恢复暂不展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：Dressage `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`，`artifacts.py` 的 `_commit_attempt_once:307`，构造与判断 445–478，保存和返回 480–523。
- 数据提取辅助函数：`_payload_segments:1033`、`_extract_rewards:1056`。只核对本卡依赖的字段来源，未另行建卡。
- [详细字段示例](../../../../../../references/harbor-trajectory-bundle.md)按需查阅；本卡示例均为静态说明，未执行提交、Proxy 清理或训练。
- [本步讨论记录](../../../../../../04-flow.md)。代码块明确区分教学节选与完整条件。

</details>
