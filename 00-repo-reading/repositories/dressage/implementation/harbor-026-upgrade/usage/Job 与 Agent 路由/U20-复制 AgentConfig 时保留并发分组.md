# U20 · 复制 AgentConfig 时保留并发分组

<a id="u20"></a>

[Job 与 Agent 路由目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[plugin.py 353–355](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L353-L355)

```python
agent.concurrency_group = (
    "dressage:" + hashlib.sha256(original_key.encode()).hexdigest()[:24]
)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage plugin.py 344–355](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L344-L355) | 复制前记下 `original_agent.concurrency_key`、`n_concurrent` 和显式分组。 |
| ② 结果　[Harbor queue.py 104–110](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/queue.py#L104-L110) | 从 Harbor 队列读取注入后 Trial 的 `concurrency_key`，比较两条本应同组的 Trial 实际得到的键。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/trial/config.py#L148-L163) | `n_concurrent`、`concurrency_group`、`concurrency_key` 或 model_dump，复制的是该 Trial 的 AgentConfig | 源码可接收 | 必要时给副本补稳定的分组名。临时 Job 会重新校验分区 Agent 配置 | 源码追到字段赋值。多 Trial 同组并发效果待测 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/config.py#L194-L209) | `n_concurrent`、`concurrency_group`、`concurrency_key` 或 model_dump，复制的是该 Trial 的 AgentConfig | 源码可接收 | 必要时给副本补稳定的分组名。临时 Job 会重新校验分区 Agent 配置 | 源码追到字段赋值。多 Trial 同组并发效果待测 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/config.py#L195-L210) | `n_concurrent`、`concurrency_group`、`concurrency_key` 或 model_dump，复制的是该 Trial 的 AgentConfig | 源码可接收 | 必要时给副本补稳定的分组名。临时 Job 会重新校验分区 Agent 配置 | 源码追到字段赋值。多 Trial 同组并发效果待测 |

**接续**　只有需要验证并发分组时，观察两个 Trial 的分组身份和实际并发上限。 [plugin.py 344-355](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L344-L355) · [compat.py 206-223](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L206-L223) · [rollout.py 548](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L548) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [问题 09](../../investigations/09-trial-plan/README.md) · [问题 07](../../investigations/07-agent-routing/README.md)
