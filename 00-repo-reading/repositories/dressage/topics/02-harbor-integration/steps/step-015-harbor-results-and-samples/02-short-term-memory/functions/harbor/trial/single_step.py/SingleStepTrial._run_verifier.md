# SingleStepTrial._run_verifier

- 代码归属：**Harbor**，不是 Dressage 的 reward/Proxy 逻辑。
- 源码：[single_step.py:88](/home/hongshi/projects/harbor/src/harbor/trial/single_step.py:88)，Harbor v0.25.0，提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独展开：2026-11-16，Step 015；用户确认建立本函数卡；本轮已复述评测执行、结果与结束时间，独立环境和框架的区别由助手校准。
- 本轮范围：是否评测、选择环境、写回结果；测试命令与奖励文件解析仍留给下游。只核对静态源码，未运行评测。

[本步 scope](../../../../../01-scope.md) · [返回 SingleStepTrial._run](SingleStepTrial._run.md) · [前一函数：产物收集](SingleStepTrial._collect_artifacts.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Agent 执行、日志与产物收集之后，父函数安排本次尝试的评测；SEPARATE 模式下父函数已先停止 Agent 环境。
2. **具体内容**：检查评测开关，记录开始事件与时间，选择共享或独立评测环境，把下游返回值写入本次结果，最后补结束时间。
3. **建议构建的心智模型**：

   > 这一层安排“要不要评、在哪里评、结果放哪里”；具体怎样测试和算分由下游 Verifier 执行。

4. **调用代码**（父函数中的当前交接）：

   ```python
   if mode == VerifierEnvironmentMode.SEPARATE:
       await self._stop_agent_environment()

   await self._run_verifier()  # 当前入口。

   if mode == VerifierEnvironmentMode.SHARED:
       await self._stop_agent_environment()
   ```

## 本场景的输入与输出

### 1. 接住什么，交回什么

本函数只有 self，没有新传入 Sample 或 reward。对象已经持有题目、评测配置、环境、产物目录和 self.result。

| 已有信息 | 当前用途 |
| --- | --- |
| `self.config.verifier.disable` | 是否直接跳过本次评测 |
| `self.task.config` | 解析共享/独立评测模式，并取得运行用户 |
| `self._verifier_timeout_sec` | 传给下游的评测超时限制 |
| `self.paths.artifacts_dir` | 独立环境分支使用的已收集产物目录 |
| `self.result` | 存放评测时间与 VerifierResult |

**正常返回 None**。评分结果不是当前函数的返回值，而是写在 `self.result.verifier_result` 上；外层 Trial.run 最终返回整份 TrialResult。

### 2. 核心骨架：先看三个分支

教学裁剪：省略事件与计时、用户与超时参数；真实代码见下一节。

```python
if self.config.verifier.disable:
    return

if mode == VerifierEnvironmentMode.SEPARATE:
    self.result.verifier_result = await self._run_separate_verifier(...)
else:
    self.result.verifier_result = await self._run_shared_verifier(...)
```

| 分支 | 在哪里运行 | 如何取得待评测内容 |
| --- | --- | --- |
| disable=True | 不执行 | 此函数不新建评测时间、不触发开始事件、不写入新评分 |
| SHARED | 原 Agent 环境 | 环境中仍有 Agent 执行后的文件；不是必须从本地产物重新恢复 |
| SEPARATE | 独立评测环境 | 下游把已收集产物上传到评测环境，再执行评测 |

两条执行分支都返回 VerifierResult，写入同一个字段。不是先共享评测，再独立评测，也不是评分两次。

### 3. 完整函数：结果与时间分开记录

以下保留真实函数体，只增加注释。

```python
async def _run_verifier(self) -> None:
    if self.config.verifier.disable:
        return

    await self._emit(TrialEvent.VERIFICATION_START)
    self.result.verifier = TimingInfo(started_at=self._now())
    mode = resolve_task_verifier_mode(self.task.config)
    user = self.task.config.verifier.user
    try:
        if mode == VerifierEnvironmentMode.SEPARATE:
            self.result.verifier_result = await self._run_separate_verifier(
                key="trial",
                timeout_sec=self._verifier_timeout_sec,
                artifacts_dir=self.paths.artifacts_dir,
                user=user,
            )
        else:
            self.result.verifier_result = await self._run_shared_verifier(
                timeout_sec=self._verifier_timeout_sec,
                user=user,
            )
    finally:
        self.result.verifier.finished_at = self._now()
```

- `self.result.verifier`：时间记录，表示这次评测何时开始、何时结束。
- `self.result.verifier_result`：实际评测结果，包含 rewards。
- 进入 try 后，即使下游评测抛出异常，也会补结束时间；本函数没有捕获并吞掉该异常。await 未正常返回时，该次赋值不会完成，不能把有结束时间当成有评分。

### 4. 最小数据变化

假设此前两字段均为 None，评测开启，SHARED 分支正常返回 `VerifierResult(rewards={"reward": 1.0})`。下面是构造的对象字段示意，不是实测输出；reward 名称及数值取决于实际评测。

```text
调用前 self.result                    调用后 self.result
verifier = None                       verifier = TimingInfo(
                                          started_at=开始时间,
                                          finished_at=结束时间)
verifier_result = None                verifier_result = VerifierResult(
                                          rewards={"reward": 1.0})

_run_verifier() 的返回值：None
```

这里没有展示“1.0 怎样算出来”。那是后续 Verifier 运行题目检查、读取评分结果的内容，不由本函数推算，也不能从 Agent 自己打印的“修复完成”推出。

### 5. 读到哪里停、回到哪里

| 按需查看真实子函数 | 带着什么问题进入、读完回哪里 |
| --- | --- |
| [Trial._run_shared_verifier:982](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:982) | 本轮代表路径：如何把原环境交给 Verifier；返回本函数的 verifier_result 赋值处 |
| [Trial._run_separate_verifier:1013](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:1013) | 按需：如何在独立环境恢复产物并评测；同样返回赋值处，当前不展开环境生命周期 |

当前先停在“下游返回 VerifierResult”。返回 `_run` 的第 51 行调用之后，SHARED 模式停止 Agent 环境；随后 `_run` 返回 Trial.run，继续外层收尾。当前不新建下游函数卡。

**本轮继续：**已建立 [Verifier.verify 函数卡](../../verifier/verifier.py/Verifier.verify.md)，沿上面共享分支及超时包装进入，查看测试脚本如何提供评分。它不是本函数的直接子调用。

## 我的直接表述（原话）

用户确认本轮记录范围：

> 好的那么请单独生成一下这个函数的short term memory吧

本轮复述（原话）：

> 我简单的理解是这里要么是单独重新创建一个框架
> 然后考虑验证
> 运行对应的验证方式？
> 然后写一下时间
> 这里面有具体的某一个verifier
> 通过这个具体的verfier运行了之后拿到这里的这个result作为结果是我的理解
> 同时给出这里的这个verifier的结束时间

助手校准：SEPARATE 准备的是独立评测环境，不是新建一套框架；SHARED 复用 Agent 环境。当前函数记录开始时间，再委派对应分支；具体 Verifier 的创建和运行位于下游。正常取得 VerifierResult 后写入 self.result.verifier_result，finally 补结束时间。进入 try 后即使评测异常，也会记录结束时间，因此有结束时间不代表成功取得评分。用户已表达执行、结果及结束时间的关联，对上述校准尚待反馈。

## 尚不清楚

- 题目测试具体怎么执行、评分从哪个文件读取，下一处再看 Verifier 的核心动作。
- 独立评测环境的准备与产物恢复细节，当前只知道交接职责。
- 评测失败、超时的外层归档与回调细节，当前不展开。

<details>
<summary>来源与验证</summary>

- [本函数与父函数](/home/hongshi/projects/harbor/src/harbor/trial/single_step.py:88)。
- [共享分支](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:982)、[独立分支](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:1013)：两者返回 VerifierResult，后者使用 upload_artifacts 恢复产物。
- [VerifierResult 字段](/home/hongshi/projects/harbor/src/harbor/models/verifier/result.py:4)：rewards 为可空的名称到数值的字典。
- [TrialResult](/home/hongshi/projects/harbor/src/harbor/models/trial/result.py:86)：verifier_result 与 verifier 是不同字段。
- [本步形成过程](../../../../../04-flow.md)。未执行评测或运行模型；字段例子为教学构造。

</details>
