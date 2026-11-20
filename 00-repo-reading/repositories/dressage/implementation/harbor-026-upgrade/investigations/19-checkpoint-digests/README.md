# 19 · 升级后，旧数据源 checkpoint 还能被正确识别吗？

**当前判断**　已使用真实 save/load。两题样例在 0.26 的两个哈希种子下都能恢复；用 0.26 读取 0.18 的同输入 checkpoint 会在 source_digest 校验处拒绝。[五次恢复](#checkpoint-replay)

**对应的三版用法表**　[U10 Job 配置摘要写入 checkpoint 并在 load 时比较](../../usage/启动与配置/U10-Job%20配置摘要写入%20checkpoint%20并在%20load%20时比较.md#u10) · [原套件在本问题测到了哪里](../original-test-audit.md#i19)

同一道题、同一份 Job 配置在另一个进程里恢复时，Dressage 需要识别它是否属于原数据源。

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　source 摘要把脱敏后的 Job 配置与采样参数一起哈希。[data_source.py 第 829–837 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L829-L837)

```python
def _source_digest(job_config: Any, *, n_samples: int, seed: int, shuffle: bool) -> str:
    return _fingerprint(
        {
            "job": _redact_public(_dump_model(job_config, reveal_sensitive=True)),
            "n_samples_per_prompt": n_samples,
            "rollout_seed": seed,
            "rollout_shuffle": shuffle,
        }
    )
```

**Harbor 0.18.0**　旧版的排除异常字段是集合。[config.py 第 288–291 行](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/job/config.py#L288-L291)

```python
exclude_exceptions: set[str] | None = Field(
    default_factory=lambda: {
        "AgentTimeoutError",
        "VerifierTimeoutError",
```

**Harbor 0.26.0**　0.26 仍声明集合，使用默认策略生成排除项。[config.py 第 304–308 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/job/config.py#L304-L308)

```python
exclude_exceptions: set[str] | None = Field(
    default_factory=default_retry_exclusions,
    description="Exception types to NOT retry on. Takes precedence over "
    "include_exceptions.",
)
```

**据此判断**　先固定 Harbor 版本、YAML 和 rollout seed，再改变 Python 哈希种子。这样可以区分同一版本的序列化差异与升级引入的差异，避免把每个摘要变化都归因于 0.26。

<a id="evidence"></a>

## 证据与验证范围

**已存输出**　0.18.0，同一个 τ³-bench Job，Python 哈希种子为 1。[hash-seed-output.txt 第 1–3 行](hash-seed-output.txt#L1-L3)

```text
PYTHONHASHSEED=1
Harbor 0.18.0 | n_samples=2 seed=7 shuffle=False
tau3-bench-e2b | sierra-research/tau3-bench | Qwen/Qwen3.5-4B | e2b | b6447bc4c6232c
```

**已存输出**　同版同一输入，只把 Python 哈希种子换成 2。[hash-seed-output.txt 第 6–8 行](hash-seed-output.txt#L6-L8)

```text
PYTHONHASHSEED=2
Harbor 0.18.0 | n_samples=2 seed=7 shuffle=False
tau3-bench-e2b | sierra-research/tau3-bench | Qwen/Qwen3.5-4B | e2b | 928c61d50d89fc
```

**字段对照原文**　逐字段比较定位到了哪一项。[hash-seed-output.txt 第 11 行](hash-seed-output.txt#L11)

```text
Harbor 0.18.0 | changed JobConfig dump fields for tau3-bench-e2b: retry.exclude_exceptions
```

0.25 也观察到这种差异。0.26 在所测两个种子下摘要相同，固定种子跨版比较仍有差异。现有输出止于摘要计算，旧 checkpoint 的结论需要实际执行 `load`。

<a id="checkpoint-replay"></a>

## 两次保存，五次独立进程恢复

每个进程用同两条本地 Task 配置、固定 Job 名、每题 2 条 Sample、rollout seed 7。保存前领取一组。下表的“种子”指 Python 的哈希种子。0.26 的探测只在进程内放行原版本门槛。实验经过真实的 `HarborDataSource.get_samples/save/load`，覆盖的是训练数据源游标。[探测](checkpoint_probe.py) · [逐进程输出](checkpoint-output.txt)

| 写入 → 读取 | 写入种子 → 读取种子 | load 的结果 |
| --- | --- | --- |
| 0.18 → 0.18 | 1 → 1 / 1 → 2 | 相同种子恢复 cursor=1、sample index=2；换种子在 source_digest 处拒绝。 |
| 0.18 → 0.26 | 1 → 1 | 在 source_digest 处拒绝。registry 摘要也改变；拒绝后新实例的 cursor 和 index 都是 0。 |
| 0.26 → 0.26 | 1 → 1 / 1 → 2 | 两次均恢复 cursor=1、sample index=2。0.26 会排序序列化重试异常集合。[序列化原文](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/job/config.py#L319-L321) |

发布时应让使用旧 checkpoint 的人知道本例会停在何处。若承诺跨版继续同一次训练，需要验证任务注册表、顺序、游标和下一组身份；只改摘要会失去这项保护。

## 处理与验收

**下一步**　让两个进程针对同一配置执行真实的 `save` 和 `load`。先固定 Harbor 版本并改变 Python 哈希种子，再固定种子并改变 Harbor 版本。分别记下 source 和 registry 标识以及任何拒绝原因。[已有漂移测试](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_data_path.py#L400)

**通过条件**　同版恢复能读回预期 cursor 和任务身份。跨版按维护者确认的兼容范围记录成功恢复、可解释的拒绝或经验证的迁移结果。以真实 `load()` 的可观察结果判定旧 checkpoint 的恢复行为。[端到端 checkpoint 用例](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_gated_e2e.py#L142)

<a id="history"></a>

## 判断记录

- 2026-11-18　下表保留第一次观察到的前缀，随后归档的[另一轮输出](../18-example-configs/job-config-output.txt)在 0.18 和 0.25 得到不同的值。0.26 新增默认字段也是一个已知的跨版输入差异。

| 随仓 Job | Harbor 0.18.0 | Harbor 0.25.0 | Harbor 0.26.0 |
| --- | --- | --- | --- |
| terminal-bench-2-e2b | `10dc1bcdefa215` | `5ad32833f41bae` | `eaa28aafd82982` |
| tau3-bench-e2b | `fcfdd07989fbb9` | `0ccb8257941113` | `9780cd6492be13` |

- 2026-11-18　迁移笔记时将 `PYTHONHASHSEED` 分别固定为 1 和 2，每种配置各运行两次。相同版本、相同种子的两次输出一致；只换种子就能复现旧版摘要差异。审查 PR 时先做同版跨进程恢复，再控制种子做跨版恢复。上述实验只计算 source 摘要，尚未执行 `load` 或验证 registry 摘要。[本轮对照](hash-seed-output.txt)

### 复查入口

- 复现与对照　[计算脚本](../18-example-configs/probe.py)
- 完整调用与配置　[data_source.py:829](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L829-L854) · [data_source.py:357](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L357-L416) · [0.25 config.py:300](https://github.com/harbor-framework/harbor/blob/v0.25.0/src/harbor/models/job/config.py#L300) · [0.26 重试配置](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/models/job/config.py#L299-L307) · [0.26 JobConfig](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/models/job/config.py#L401-L410)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#checkpoint) · [返回问题索引](../../README.md#investigations)
