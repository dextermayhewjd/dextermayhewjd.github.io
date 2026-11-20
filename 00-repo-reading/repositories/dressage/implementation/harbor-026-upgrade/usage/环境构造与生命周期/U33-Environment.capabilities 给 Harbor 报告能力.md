# U33 · Environment.capabilities 给 Harbor 报告能力

<a id="u33"></a>

[环境构造与生命周期目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 294–299](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L294-L299)

```python
return EnvironmentCapabilities(
    disable_internet=True,
    network_allowlist=True,
    network_allowlist_ipv4_addresses=True,
    mounted=True,
)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage environment.py 293–300](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L293-L300) | 读同一环境实例公布的 `mounted`、`disable_internet` 和 allowlist 能力。 |
| ② 结果　[Harbor base.py 296–315](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L296-L315) · [Harbor base.py 895–904](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L895-L904) | 看 Harbor 在构造和查询具体目录时采用哪项能力。对日志路径另核对实际绑定与查询结果。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L687-L708) | 读取环境实例的 capabilities 属性，无显式参数 | 源码可接收 | `EnvironmentCapabilities` 中 mounted、disable_internet、network_allowlist、network_allowlist_ipv4_addresses 均为 True | 基线 Trial 的 mounted 分支有源码依据 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L903-L924) | 读取环境实例的 capabilities 属性，无显式参数 | 源码可接收 | `EnvironmentCapabilities` 中 mounted、disable_internet、network_allowlist、network_allowlist_ipv4_addresses 均为 True | 能力对象可构造，逐路径挂载查询出现不符 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L968-L989) | 读取环境实例的 capabilities 属性，无显式参数 | 源码可接收 | `EnvironmentCapabilities` 中 mounted、disable_internet、network_allowlist、network_allowlist_ipv4_addresses 均为 True | 能力对象可构造，逐路径挂载查询出现不符 |

**接续**　核查某个输出目录时看 U44 的路径查询结果，能力声明本身不能证明那个目录已登记。 [environment.py 293-300](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L293-L300) · [0.25/0.26 非空日志输出](../../investigations/02-output-mounts/log-recovery-output.txt) · [基线套件的通过、失败和排除项](../../investigations/00-version-target/pytest-replay.txt) · [问题 02](../../investigations/02-output-mounts/README.md) · [问题 14](../../investigations/14-phase-network-policy/README.md)
