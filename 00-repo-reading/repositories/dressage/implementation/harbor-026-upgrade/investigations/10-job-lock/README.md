# 10 · Dressage 重建临时 Job 后，Harbor 还能生成 lock.json 吗？

**当前判断**　本地题目能构造 v3 Job lock，保留临时 Job 配置。远程数据集的任务解析仍待验证。

**对应的三版用法表**　[U12 model_validate 重建每个分区的临时 JobConfig](../../usage/Job%20与%20Agent%20路由/U12-model_validate%20重建每个分区的临时%20JobConfig.md#u12) · [U18 Job._init_job_lock 使用解析记录生成 lock](../../usage/Job%20与%20Agent%20路由/U18-Job._init_job_lock%20使用解析记录生成%20lock.md#u18) · [原套件在本问题测到了哪里](../original-test-audit.md#i10)

Dressage 会按训练分区重建 Job，需要确认 Harbor 用新配置还能找到每个任务的解析记录。

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　临时 Job 用展开的任务取代 dataset 列表。[rollout.py 第 562–563 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L562-L563)

```python
"datasets": [],
"tasks": temporary_tasks,
```

**Harbor 0.26.0**　构造 lock 时按任务 ID 取下载记录，缺记录会报错。[lock.py 第 669–673 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/job/lock.py#L669-L673)

```python
task_id = task_config.get_task_id()
try:
    return task_download_results[task_id]
except KeyError:
    raise ValueError(f"Task {task_id.get_name()!r} was not resolved.") from None
```

**据此判断**　临时配置会改写任务来源。判断是否影响 lock，要看 Harbor 能否用生成的任务 ID 找到同一份解析记录。

<a id="evidence"></a>

## 证据与验证范围

**基线输出**　同一本地题目创建 Job，在内存中构造 lock。[job-lock-output.txt 第 1–2 行](job-lock-output.txt#L1-L2)

```text
Harbor 0.18.0
claude-code | MiniMax-M3 | Job.create succeeded | lock schema 2
```

**0.26 输出**　同一 Agent／模型和输入路径，调用 `_init_job_lock`。[job-lock-output.txt 第 11–12 行](job-lock-output.txt#L11-L12)

```text
Harbor 0.26.0
claude-code | MiniMax-M3 | Job.create succeeded | lock schema 3
```

本地任务在 0.25 和 0.26 都得到 schema 3。远程 dataset 下载与 `Job.run` 实际写出的 lock 文件仍待检查。

## 处理与验收

**下一步**　用真实本地任务检查 lock 的任务身份和 schema。若 PR 承诺远程 dataset 输入，再用该来源运行 `Job.run()` 并读取落盘的 `lock.json`。[已有临时 Job 合同](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_execution.py#L456)

**通过条件**　每份 Trial 对应预期任务，目标版写出的 lock 可解析为 schema 3。远程输入的下载记录能按相同任务 ID 找回。

<a id="history"></a>

## 判断记录

- 2026-11-18　在同一种本地输入上，0.18 生成 v2 lock，0.25 与 0.26 均生成 v3。直接探测停在 lock 构造，后续完整 Job、远程任务和重试需各自验收。

### 复查入口

- 复现与对照　[Job 探测](probe.py) · [lock 输出](job-lock-output.txt)
- 完整调用与配置　[rollout.py:505](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L505-L579) · [job.py:961](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/job.py#L961) · [lock.py:356](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/models/job/lock.py#L356) · [任务 ID 查找](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/models/job/lock.py#L665-L673)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#job) · [返回问题索引](../../README.md#investigations)
