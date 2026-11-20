# U30 · END 前后的 Trial 目录及外部 bundle 路径

<a id="u30"></a>

[Trial 事件与目录目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[artifacts.py 1133](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1133)

```python
def _ensure_outside_trial_dir(path: Path, trial_dir: Path | None) -> None:
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor trial.py 667–676](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L667-L676) | 按同一 Trial 记录目录的无敏感信息测试标记、首次清理和 END 的先后。 |
| ② 结果　[Dressage artifacts.py 480–484](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L480-L484) · [Harbor trial.py 629–636](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L629-L636) | 看插件落盘的 bundle 路径是否位于 Trial 目录外。等外层 finally 后重新读取两个目录中的测试标记。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L386-L390) | Trial 输出目录与位于目录外的 Store 目标路径。需要脱敏的文件由 Harbor 处理 | 真实 Job 的 UTF-8 标记、外部 bundle 已读回 | 该收尾流程直接发 END | END 读取第一份文件及 Job 返回后读取 END 新建文件，两处均仍含标记 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L627) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L660-L667) | Trial 输出目录与位于目录外的 Store 目标路径。需要脱敏的文件由 Harbor 处理 | 真实 Job 的 UTF-8 标记、外部 bundle 已读回 | END 后在外层清理时扫描 jobs 目录 | END 时仍见第一份标记；Job 返回后 END 新建文件的标记已清理 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L667-L676) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L634) | Trial 输出目录与位于目录外的 Store 目标路径。需要脱敏的文件由 Harbor 处理 | 真实 Job 的 UTF-8 标记、外部 bundle 已读回 | 发 END 前扫描，外层退出时还有一次扫描 | END 时第一份标记已清理；Job 返回后 END 新建文件的标记也已清理 |

**接续**　三版均从 Trial 目录外读回 bundle。对目录内无效目标路径和公开字段分别验收。 [artifacts.py 1133-1143](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1133-L1143) · [plugin.py 778-782](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L778-L782) · [结果探测实际调用的范围](../../investigations/12-reward-validity/result_contract_probe.py) · [问题 08](../../investigations/08-trial-output-redaction/README.md) · [问题 11](../../investigations/11-trial-events/README.md)

[三版生命周期及替身范围](../../investigations/22-retry-policy/probe.py) · [三版运行输出](../../investigations/22-retry-policy/job-trial-output.txt)
