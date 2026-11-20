# 18 · 随仓两份 Job YAML 还能得到相同的任务、Agent 和环境配置吗？

**当前判断**　保留原来的两份 Job YAML。三个版本均能解析出相同的 dataset、Agent 模型名和 E2B 后端。

**对应的三版用法表**　[U06 JobConfig.model_validate 读取随仓 Job YAML](../../usage/启动与配置/U06-JobConfig.model_validate%20读取随仓%20Job%20YAML.md#u06) · [U57 Harbor Task 读取 Dressage 生成的题目目录](../../usage/题目文件与可选后端/U57-Harbor%20Task%20读取%20Dressage%20生成的题目目录.md#u57) · [原套件在本问题测到了哪里](../original-test-audit.md#i18)

升级后旧合同测试在校验 YAML 之前就失败，需要单独判断示例配置的含义是否变化。

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　数据源把解析出的 YAML 映射交给 Harbor 的模型。[data_source.py 第 602–603 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L602-L603)

```python
try:
    return job_config_type.model_validate(dict(payload))
```

**Harbor 0.26.0**　`JobConfig` 的原注释及默认值说明省略 `schema_version` 的文档如何读取。[config.py 第 401–407 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/job/config.py#L401-L407)

```python
class JobConfig(BaseModel):
    # Unversioned documents are permanently version 1. Future versions must
    # dispatch/migrate missing versions as v1 before applying current defaults.
    schema_version: Literal[1] = Field(
        default=1,
        description="Serialized document schema version. Omission denotes the legacy version 1 format.",
    )
```

**据此判断**　版本断言失败与两份 YAML 的字段能否被解析是两项判断。读回 dataset、模型名和后端，才能判断示例是否需要改写。

<a id="evidence"></a>

## 证据与验证范围

**已存输出**　给 0.26 的 `JobConfig` 两份随仓示例，展示读回的名称、dataset、模型、后端及摘要。[job-config-output.txt 第 9–11 行](job-config-output.txt#L9-L11)

```text
Harbor 0.26.0 | n_samples=2 seed=7 shuffle=False
tau3-bench-e2b | sierra-research/tau3-bench | Qwen/Qwen3.5-4B | e2b | 9780cd6492be13
terminal-bench-2-e2b | terminal-bench/terminal-bench-2 | Qwen/Qwen3.5-4B | e2b | eaa28aafd82982
```

三版都读回相同的关键配置，末列摘要另在问题 19 审查。这里的解析实验不包含 dataset 下载与云端运行。

## 处理与验收

**下一步**　把安装版本断言与两份 YAML 的字段测试分开，让失败信息指明是选错包，还是同一份配置的含义发生变化。[问题 04](../04-version-checks/README.md)

**通过条件**　目标版对两份 YAML 分别返回预期的 dataset、模型名、环境类型。沙箱实际启动归入问题 16，序列化摘要归入问题 19。[问题 16](../16-e2b-template/README.md) · [问题 19](../19-checkpoint-digests/README.md)

<a id="history"></a>

## 判断记录

- 2026-11-18　0.18.0、0.25.0、0.26.0 对两份随仓 YAML 都通过 `JobConfig.model_validate`。0.26 为 JobConfig、TrialConfig、JobResult、TrialResult 增加默认 `schema_version`。解析成功后仍需考虑 checkpoint 摘要。

### 复查入口

- 复现与对照　[Terminal-Bench 输入](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/harbor_job_configs/terminal-bench-2-e2b.yaml) · [τ³-bench 输入](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/harbor_job_configs/tau3-bench-e2b.yaml) · [探测脚本](probe.py) · [逐版字段输出](job-config-output.txt)
- 完整调用与配置　[data_source.py:562](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L562-L605) · [test_contracts.py:165](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_contracts.py#L165) · [models/job/config.py:404](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/models/job/config.py#L404)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#job) · [返回问题索引](../../README.md#investigations)
