# 13 · 同一 Trial 重试后，最终是哪份 bundle 进入训练？

**当前判断**　真实 Harbor 队列生成了同名不同 ID 的两次尝试，插件的 Job 结束入口、最终 manifest 和按所选 bundle 生成的两段 Sample 均采用第二个 ID。训练分区推迟到整组校验后的 manifest 仍待公开入口联测。

**对应的三版用法表**　[U22 Job.run 将本次 Job 的最终结果交给插件与分区](../../usage/Job%20与%20Agent%20路由/U22-Job.run%20将本次%20Job%20的最终结果交给插件与分区.md#u22) · [U53 get_result 与 write_job_manifest 对齐最终物理尝试](../../usage/结果、样本与最终选择/U53-get_result%20与%20write_job_manifest%20对齐最终物理尝试.md#u53) · [U54 _bundle_samples 将一次尝试的分段奖励送入训练样本](../../usage/结果、样本与最终选择/U54-_bundle_samples%20将一次尝试的分段奖励送入训练样本.md#u54) · [原套件在本问题测到了哪里](../original-test-audit.md#i13)

同一 Trial 名下可以积累两份尝试的 bundle。训练要能说明最终采用哪份，以及组校验失败时怎么办。

<a id="sources"></a>

## 两边的源码原文

**Harbor 0.26.0**　队列重试会重新创建 Trial，并可返回成功的那次结果。[queue.py 第 178–185 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/queue.py#L178-L185)

```python
for attempt in range(self._retry_config.max_retries + 1):
    trial = await Trial.create(trial_config)
    self._setup_hooks(trial)
    result = await trial.run()

    exceptions = result.recorded_exceptions()
    if not exceptions:
        return result
```

**Dressage 3e3142f**　按最终 `TrialResult` 的 id 取 bundle。[rollout.py 第 802–803 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L802-L803)

```python
bundle = plugin.get_result(trial_name, str(final_result.id))
if bundle is None:
```

**Dressage 3e3142f**　整组检查通过的 `final_keys` 才进入最终选择。[rollout.py 第 853–858 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L853-L858)

```python
selected_keys = [
    key
    for outcome in outcomes_by_position.values()
    if outcome.succeeded
    for key in outcome.final_keys
]
```

**据此判断**　同一个任务可能产生多次物理尝试。一次成功保存只说明 bundle 存在，训练接入还要对照最终 Trial 身份与组的结果。

<a id="evidence"></a>

## 证据与验证范围

**已有测试断言 · Dressage 3e3142f**　合成的两次尝试中，旧尝试被取代，新尝试可训练。[test_data_path.py 第 228–231 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_data_path.py#L228-L231)

```python
manifest = json.loads(path.read_text())
attempts = {item["trial_id"]: item for item in manifest["attempts"]}
assert attempts[first.trial_id]["superseded"] is True
assert attempts[second.trial_id]["trainable"] is True
```

三版的正常 Job 都按最终 UUID 取回磁盘 bundle。0.26 的 step-only RuntimeError 和配额错误各触发一次重试，第一次 bundle 为 superseded、不可训练，第二次选中且可训练；两段 Sample 的 `harbor_trial_id` 均与第二次 UUID 一致。0.18 和 0.25 的非零退出用例也观察到同样的两次尝试选择。探测直接调用插件默认的 `on_job_end` 和样本转换，Proxy 轨迹、Sample 模板及评分采用夹具。[0.18 非零退出](../22-retry-policy/job-trial-output.txt#L4) · [0.25 非零退出](../22-retry-policy/job-trial-output.txt#L12) · [0.26 两步重试](../22-retry-policy/job-trial-output.txt#L19) · [重试策略](../22-retry-policy/README.md#evidence)

## 处理与验收

**下一步**　让公开训练入口接住一组有多个逻辑 Trial 的 Job，覆盖整组校验失败及最终选择为空的分支，核对 manifest 与实际返回训练批次。 [Job 结束入口](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L420-L437) · [转 Sample](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L624-L675) · [写 manifest](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L537)

**通过条件**　两次尝试都可追溯，返回的 Sample 和 manifest 选择最终成功的 ID。在组校验失败的用例中，manifest 的最终选择不含该组的 key。已保存且未被选择的 bundle 应为 `superseded=True`、`trainable=False`。[最终选择的标记](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L566-L589)

<a id="history"></a>

## 判断记录

- 2026-11-18　源码复核确认取消影响样本可训练性，`superseded` 由最终选择决定。现有用例覆盖合成结果，目标版真实 Trial 到训练 Sample 的交接仍需验收。

### 复查入口

- 复现与对照　[manifest 用例](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_data_path.py#L201) · [重试用例](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_execution.py#L215)
- 完整调用与配置　[artifacts.py:256](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L256) · [按最终 ID 取 bundle](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L795-L814) · [组校验与 manifest](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L840-L875) · [queue.py:172](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/trial/queue.py#L172-L205) · [汇总结果](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/job.py#L1176-L1181) · [写回 JobResult](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/job.py#L1214-L1220)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#training) · [返回问题索引](../../README.md#investigations)
