# 12 · Harbor 认为分数有效时，Dressage 是否应采纳这个训练样本？

**当前判断**　四种相同输入在三个版本均得到相同的 Dressage 选分、失败码和可训练状态。带非零退出异常的 0.75 分，在 Harbor 0.25.0 的 `reward_valid` 为 False，在 0.26.0 为 True。普通 Agent 异常另有行为变化。真实 Trial 中，0.26 会为未分类的 RuntimeError 继续评分，bundle 从缺分变为有分，仍然拒绝训练。 [三版用法表](../../usage/结果、样本与最终选择/U50-从%20trial%20与%20step%20的%20exception_info%20生成训练失败记录.md#u50)

**对应的三版用法表**　[U49 从 verifier_result 或末尾 step 选择目标奖励](../../usage/结果、样本与最终选择/U49-从%20verifier_result%20或末尾%20step%20选择目标奖励.md#u49) · [U50 从 trial 与 step 的 exception_info 生成训练失败记录](../../usage/结果、样本与最终选择/U50-从%20trial%20与%20step%20的%20exception_info%20生成训练失败记录.md#u50) · [U51 commit_attempt 将 Harbor 结果与 Proxy 轨迹持久化](../../usage/结果、样本与最终选择/U51-commit_attempt%20将%20Harbor%20结果与%20Proxy%20轨迹持久化.md#u51) · [U58 Harbor Verifier 读取运行产生的 reward.json](../../usage/题目文件与可选后端/U58-Harbor%20Verifier%20读取运行产生的%20reward.json.md#u58) · [原套件在本问题测到了哪里](../original-test-audit.md#i12)

一个 Trial 可能既有 verifier 分数也有异常。升级时要确认这个分数是否统计、样本是否训练，各由谁决定。

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　bundle 可训练要求所有 failure 均非致命，还有 token 等条件。[artifacts.py 第 473–478 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L473-L478)

```python
bundle.trainable = (
    not cancelled
    and checkpoint is FinalizationCheckpoint.TRAJECTORY_SNAPSHOTTED
    and not any(failure.fatal for failure in bundle.failures)
    and token_count > 0
)
```

**Harbor 0.26.0**　`reward_valid` 检查分数和每个异常的策略。[result.py 第 142–148 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/result.py#L142-L148)

```python
def reward_valid(self) -> bool:
    if self.verifier_result is None or not self.verifier_result.rewards:
        return False
    return all(
        exception.policy.has_valid_reward
        for exception in self.recorded_exceptions()
    )
```

**Harbor 0.26.0**　默认策略允许这两种异常仍有有效分数。[error_policy.py 第 99–101 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/error_policy.py#L99-L101)

```python
ErrorPolicy(should_retry=False, should_grade=True, has_valid_reward=True): (
    "NonZeroAgentExitCodeError",
    "AgentTimeoutError",
```

**据此判断**　同一个有分数的 Trial 可以满足 Harbor 的评测规则，而 Dressage 对记录到的 Trial 或 step 异常会生成致命失败。因此需要在同一份结果上分别观察 `reward_valid` 和 `trainable`。

<a id="evidence"></a>

## 证据与验证范围

**失败规则原文 · Dressage 3e3142f**　Dressage 把记录到的 Harbor 异常标为 fatal。[artifacts.py 第 1095–1099 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1095-L1099)

```python
return AttemptFailure(
    code="HARBOR_TRIAL_EXCEPTION",
    stage=FailureStage.AGENT,
    message=_one_line(message),
    fatal=True,
```

**已有测试断言 · Dressage 3e3142f**　Dressage 的失败矩阵只读 bundle 的可训练状态和错误码。[test_data_path.py 第 162–163 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_data_path.py#L162-L163)

```python
assert bundle.trainable is expected_trainable
assert {failure.code for failure in bundle.failures} >= expected_codes
```

**同一对象在两侧的实际判断 · 0.26.0**　每个用例把一份 Harbor `TrialResult` 先交给 Harbor 的有效性判断，再交给 Dressage Store。正常输入还经过了落盘、读取 bundle、按片段生成样本和评测聚合。[0.26.0 输出第 3–7 行](result-contract-output.txt#L3-L7)

```text
normal: reward_valid=True selected=0.75 trainable=True failures=[]
two segment rewards=[{'reward': 0.0}, {'reward': 0.75, 'aux': 0.25}] | eval rewards=[0.75]
nonzero-exit: reward_valid=True selected=0.75 trainable=False failures=['HARBOR_TRIAL_EXCEPTION']
other-key: reward_valid=True selected=None trainable=False failures=['REWARD_MISSING']
step-only: reward_valid=False selected=0.75 trainable=True failures=[]
```

**怎么读 0.26 的结果**　同样是 0.75，Agent 非零退出时 Harbor 0.26 允许用它统计，Dressage 留下分数并拒绝训练。只有辅助分数键时 Harbor 0.26 也能统计，Dressage 找不到指定的 `reward`。第四例刻意只在最后一个 step 设置分数，观察 Dressage 的回退行为。Harbor 的正常多步流程会把所选分数写回顶层。 [多步结果赋值原行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/multi_step.py#L92)

**升级前的对照**　0.18.0 没有 `reward_valid` 字段。同一脚本、题目和四组评分输入经 Dressage 后，选分、可训练标志、失败码和两个片段的奖励均与 0.26.0 一致。两版运行也各给出一次 `Task.checksum` 的弃用提示，当前结果仍有该字段。[0.18.0 原始输出](result-contract-0.18.0.txt) · [0.26.0 原始输出](result-contract-output.txt)

**中间版本的实际输出 · 0.25.0**　同一份带分数的非零退出结果也经 Store 落盘回读。可以直接比较上文 0.26.0 的同名输入。 [0.25.0 输出第 5 行](result-contract-0.25.0.txt#L5)

```text
nonzero-exit: reward_valid=False selected=0.75 trainable=False failures=['HARBOR_TRIAL_EXCEPTION']
```

**这次跑到了哪里**　脚本用真实 Harbor `Trial.create` 创建本地 Oracle Trial，调用 `_init_result` 并主动触发一次 END，核对事件对象上的 Trial 名、物理 ID、目录。评分字段由探测设置，Proxy 和样本模板采用 Dressage 测试夹具。Store 与样本转换执行实际实现。真实 Agent、verifier、正常/取消时序和重试后的 JobResult 留给各自的入口验收。[探测源码](result_contract_probe.py) · [11 · 事件时序](../11-trial-events/README.md) · [13 · 最终 attempt](../13-final-attempt/README.md)

由真实 Job 运行两步题时，第一步收到 0.25，第二步收到 0.75，题目选择 final。0.26 的第二步首次报错后，队列整题重跑。第二次成功的最终 bundle 给两段 Sample 分别交付 0 和 0.75，评测按一条轨迹统计。单步超时则被三个版本记录为 `AgentTimeoutError`，即使夹具 verifier 给出 0.75，转换也拒绝该 bundle。分数均来自离线 verifier 夹具。[重试及超时矩阵](../22-retry-policy/README.md#evidence) · [0.26 两步重试](../22-retry-policy/job-trial-output.txt#L19) · [0.26 超时](../22-retry-policy/job-trial-output.txt#L23)

**相同故障是否走到 verifier。** 关闭物理重试，在单步 Oracle 夹具的 run 中抛普通 `RuntimeError`。0.18 和 0.25 发 AGENT_END 后直接收尾，bundle 为 `reward=None`、失败码同时含 `HARBOR_TRIAL_EXCEPTION` 和 `REWARD_MISSING`。0.26 捕获异常，未知错误的默认策略允许评分，真实 Trial 发 VERIFICATION_START，夹具返回 0.75；`reward_valid=True`，bundle 只剩 `HARBOR_TRIAL_EXCEPTION`，仍拒绝生成训练样本。[0.18 输出](lifecycle-rewards.txt#L3) · [0.25](lifecycle-rewards.txt#L6) · [0.26](lifecycle-rewards.txt#L9) · [0.26 单步 Agent 与 verifier](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/single_step.py#L75-L96) · [未知错误的默认策略](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/error_policy.py#L33-L35)

**末步没有评分时。** 两步任务使用 `final` 策略，第一步得到 0.25，末步 verifier 抛出 `RewardFileNotFoundError`。三个版本的真实 Trial 均得到 `verifier_result=None`，异常保存在末步。Dressage 向前找到第一步的 0.25，保存在 bundle 中供诊断，同时因末步异常拒绝训练。此时查看 bundle.reward 会看到前一步的成绩。[0.18 输出](lifecycle-rewards.txt#L2) · [0.25](lifecycle-rewards.txt#L5) · [0.26](lifecycle-rewards.txt#L8) · [Harbor final 的取值](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L924-L929) · [Dressage 选分](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1056-L1065)

用同一[离线探测](../22-retry-policy/probe.py)追加参数 `step-final-ungraded agent-runtime-error` 可复现上述两组。各版本均实际经过 Job、Trial、END、Store、manifest 及失败样本转换。两项均在夹具边界提供确定的故障或评分。[运行环境](../../tools/reproduce.md)

## 处理与验收

**下一步**　用环境内 verifier 实际产生的奖励重跑评分和最终选择对照。 [分数消费位置](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1056) · [13 · 最终选择](../13-final-attempt/README.md#evidence)

**通过条件**　正常样本保留目标分数，带异常的样本按现有训练规则标记，缺失指定键得到 `REWARD_MISSING`。若要放宽训练采纳条件，应把策略变更单独评审。

<a id="history"></a>

## 判断记录

- 2026-11-18　0.25 已有 ErrorPolicy 与 `reward_valid`。0.26 提供 `recorded_exceptions()` 和策略覆盖，并把有效性判断用于 Job 统计。升级没有确立放宽训练样本选择的需求。
- 2026-11-18　用相同输入复查了 0.18.0 与 0.26.0 的事件对象、奖励和落盘的 bundle。四例都保留现有采纳结果。分段样本的奖励和单条评测统计也符合当前转换。受限执行器中的初次探测停在异步磁盘写入等待，完整对照在本地放行的测试进程运行。[基线输出](result-contract-0.18.0.txt) · [目标输出](result-contract-output.txt)

- 2026-11-18　补验 0.25.0 四组受控输入。Harbor 对非零退出的分数有效性在中间版与目标版不同，Dressage 的选分、失败码、训练标记与两段样本均与既有两版吻合。 [中间版完整输出](result-contract-0.25.0.txt)

### 复查入口

- 复现与对照　[0.25 已有的有效性判断](https://github.com/harbor-framework/harbor/blob/v0.25.0/src/harbor/models/trial/result.py#L104-L130) · [Dressage 失败矩阵](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_data_path.py#L124)
- 完整调用与配置　[artifacts.py:1056](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1056-L1104) · [目标 reward 检查](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L864) · [result.py:127](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/models/trial/result.py#L127-L149) · [error_policy.py:95](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/models/trial/error_policy.py#L95-L125)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#training) · [返回问题索引](../../README.md#investigations)
