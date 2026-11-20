# 22 · 同一个错误升级后会不会让 Harbor 重跑整个 Trial？

**当前判断**　在 Job 的 `retry.max_retries=1`、未指定异常过滤时，0.18/0.25 的非零退出会重试，0.26 保留第一次结果。配额耗尽时，0.18/0.25 保留第一次结果，0.26 允许重试。0.26 还会读取仅记录在 step 上的错误，所有记录都允许重试时才重跑整个题。Terminal-Bench 和 Tau³ 的 E2B Job 配方均给每个 Trial 一次 Harbor 重试机会，训练配置另有一次整组重试。[Terminal-Bench 配方](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/harbor_job_configs/terminal-bench-2-e2b.yaml#L7-L8) · [Tau³ 配方](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/harbor_job_configs/tau3-bench-e2b.yaml#L7-L8) · [训练配置](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dressage_profiles/training-bwrap.yaml#L55-L58)

**对应的三版用法表**　[U50 从 trial 与 step 的 exception_info 生成训练失败记录](../../usage/结果、样本与最终选择/U50-从%20trial%20与%20step%20的%20exception_info%20生成训练失败记录.md#u50) · [U53 get_result 与 write_job_manifest 对齐最终物理尝试](../../usage/结果、样本与最终选择/U53-get_result%20与%20write_job_manifest%20对齐最终物理尝试.md#u53) · [13 · 重试结束后选哪一份 bundle](../13-final-attempt/README.md) · [原套件覆盖范围](../original-test-audit.md#i22)

<a id="sources"></a>

## 两边的源码原文

**Harbor 0.18.0 / 0.25.0**　两版队列只检查顶层异常。[queue.py 第 205–208 行](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/queue.py#L205-L208)

```python
if result.exception_info is None:
    return result

if not self._should_retry_exception(result.exception_info.exception_type):
```

0.25 同一位置保留了这一判断，实际队列按 `RetryConfig` 的默认排除集合筛选，包含 `ApiUsageLimitError`。[0.25 队列](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/queue.py#L203-L209) · [0.25 默认配置](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/job/config.py#L292-L313)

**Harbor 0.26.0**　队列枚举顶层和各个 step 的记录。[queue.py 第 183–191 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/queue.py#L183-L191)

```python
exceptions = result.recorded_exceptions()
if not exceptions:
    return result

# A retry replays the entire trial, including earlier steps.
if not all(
    self._retry_config.is_retryable(error.exception_type)
    for error in exceptions
):
```

0.26 根据错误策略生成默认排除集合。显式 `exclude_exceptions` 优先，有 `include_exceptions` 时还要满足纳入条件。三个版本默认的 `max_retries` 都是 0，表中的差异要在配方启用重试时观察。[基线默认值](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/job/config.py#L280-L299) · [0.26 默认配置及筛选](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/job/config.py#L296-L326) · [0.26 的策略覆盖规则](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/job/config.py#L490-L505) · [配额耗尽](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/error_policy.py#L52-L62) · [非零退出和 Agent 超时](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/error_policy.py#L99-L105)

**Dressage 3e3142f**　bundle 的失败记录单独设置 `fatal` 和 `retryable`。[artifacts.py 第 1099–1101 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1099-L1101)

```python
fatal=True,
retryable=exception_type not in {"CancelledError", "AgentTimeoutError"},
details=details,
```

训练循环拿到失败的组后，依据 `group_retry < max_retries` 再次提交整组。因此一次失败可以同时具有三种观察结果，例如 0.26 的非零退出在 bundle 中标记为可重试、Harbor 默认不重跑物理 Trial、训练外层仍有资格重跑整组。[整组重试入口](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1113-L1127)

<a id="evidence"></a>

## 证据与验证范围

三个版本运行同一脚本，每个本地 Job 有一个逻辑 Trial。会恢复的错误只在第一次指定的 Agent 调用出现。表内数字是实际执行的物理 Trial 数，由不同 UUID、START / END 和 Store 提交次数核对。[0.18 原始输出](job-trial-output.txt#L1-L8) · [0.25](job-trial-output.txt#L9-L16) · [0.26](job-trial-output.txt#L17-L24)

| 首次运行的输入 | 0.18 | 0.25 | 0.26 | 0.26 的下游结果 |
| --- | ---: | ---: | ---: | --- |
| 单步正常 | 1 | 1 | 1 | 可训练，两段奖励为 0 和 0.75 |
| 两步题的第二步抛出 `RuntimeError`，顶层无异常 | 1 | 1 | 2 | 两步一起重跑，第一次 bundle 被取代，第二次的 UUID 与两段 Sample 一致 |
| 单步 `NonZeroAgentExitCodeError` | 2 | 2 | 1 | 最终 bundle 带致命异常，`retryable=True`，转换样本被拒 |
| 单步 `ApiUsageLimitError` | 1 | 1 | 2 | 第二次成功，manifest 与样本采用新 UUID |
| 两个 step 分别记录 `RuntimeError` 与 `AgentTimeoutError` | 1 | 1 | 1 | 后者在默认排除集合，整题不重跑，两条错误进入 bundle |
| 单步实际等待超时 | 1 | 1 | 1 | 记录 `AgentTimeoutError`，bundle 标记不可训练、不可重试 |
| Agent 运行期间取消 | 1 | 1 | 1 | 取消向外传播，CANCEL 后收到 END，Store 零次提交 |

**复现**　按[环境说明](../../tools/reproduce.md)选定一个版本，在 Dressage checkout 作为 `PYTHONPATH` 的环境中运行 `python "$notes_dir/investigations/22-retry-policy/probe.py"`。可追加 `step-retry` 或 `nonzero` 只跑一例。输出文件保留脚本的版本行和每例 JSON。运行了真实 `Job.create/run`、队列、SingleStepTrial / MultiStepTrial、六个插件回调、磁盘 Store、manifest 和样本转换。环境准备、日志传输、停止、Oracle 执行和 verifier 返回值使用离线夹具，Gateway 和 Proxy 使用记录对象，0.25 / 0.26 仅在进程内放行版本门禁。未运行 Slime 训练分区、远端沙箱、真实模型和打分脚本。[探测源码](probe.py)

## 处理与验收

升级需要明确采用 0.26 默认重试策略，还是为现有配方保留基线的排除名单。固定名单可控制异常类型，0.26 对 step 级错误的处理仍按新的整题规则执行。两种选择都应单独核对物理 Trial 数、最终 UUID、bundle 可训练性与训练整组重试次数。本页已核对前三项，整组重试仍有待从公开训练入口验证。[13 · 最终选择](../13-final-attempt/README.md#evidence)

[返回升级问题](../../README.md#investigations)
