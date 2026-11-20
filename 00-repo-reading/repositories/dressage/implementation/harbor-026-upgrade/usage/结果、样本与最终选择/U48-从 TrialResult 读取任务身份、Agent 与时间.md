# U48 · 从 TrialResult 读取任务身份、Agent 与时间

<a id="u48"></a>

[结果、样本与最终选择目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[artifacts.py 453–455](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L453-L455)

```python
task_name=_string_attr(trial_result, "task_name"),
task_checksum=_string_attr(trial_result, "task_checksum"),
agent_name=_nested_string_attr(trial_result, "agent_info", "name"),
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage artifacts.py 445–455](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L445-L455) · [Dressage artifacts.py 469–471](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L469-L471) | 在构造 bundle 时看输入 TrialResult 的 task、checksum、agent 名、started_at 和 finished_at。 |
| ② 结果　[Dressage artifacts.py 480–484](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L480-L484) · [Dressage rollout.py 653–660](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L653-L660) | 回读同一物理 ID 的 bundle，逐字段比较这五项。进入样本时再看被复制进 metadata 的三项身份字段。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/trial/result.py#L76) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/trial/result.py#L69-L129) | 读取 task_name、task_checksum、agent_info.name、started_at、finished_at | 用真实 TrialResult 及受控输入实测 | 写入 bundle 对应的任务身份、Agent 名及时间。尚未结束的时间允许为空 | 结果模型和消费字段已对源码。探测验证物理 ID，未逐项断言这些元数据 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/result.py#L82) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/result.py#L75-L169) | 读取 task_name、task_checksum、agent_info.name、started_at、finished_at | 用真实 TrialResult 及受控输入实测 | 写入 bundle 对应的任务身份、Agent 名及时间。尚未结束的时间允许为空 | 结果模型和消费字段已对源码。探测验证物理 ID，未逐项断言这些元数据 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/result.py#L105) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/result.py#L91-L189) | 读取 task_name、task_checksum、agent_info.name、started_at、finished_at | 用真实 TrialResult 及受控输入实测 | 写入 bundle 对应的任务身份、Agent 名及时间。尚未结束的时间允许为空 | 结果模型和消费字段已对源码。探测验证物理 ID，未逐项断言这些元数据 |

**接续**　重点回查 task_checksum。三版真实 Trial 初始化均发出 Task.checksum 弃用提示。 [artifacts.py 453-455](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L453-L455) · [artifacts.py 470-471](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L470-L471) · [0.18 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.18.0.txt) · [0.25 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.25.0.txt) · [0.26 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-output.txt) · [结果探测实际调用的范围](../../investigations/12-reward-validity/result_contract_probe.py) · [问题 08](../../investigations/08-trial-output-redaction/README.md) · [问题 12](../../investigations/12-reward-validity/README.md)
