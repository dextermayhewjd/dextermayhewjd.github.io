# U02 · require_harbor_runtime 读取并检查发行包版本

<a id="u02"></a>

[启动与配置目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[compat.py 52](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L52)

```python
harbor_version = importlib.metadata.version("harbor")
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage compat.py 50–59](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L50-L59) | 从正常入口读已装版本，记下实际值和 `SUPPORTED_HARBOR_VERSION`。 |
| ② 结果　[Dressage rollout.py 103–107](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L103-L107) | 单步越过版本检查。能继续时才进入 `Job.create`。拒绝时记录异常和 Job 尚未创建。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/pyproject.toml#L2-L3) | `importlib.metadata.version("harbor")` 返回已装版本 | 实测接受 0.18.0 | 返回 `HarborRuntimeInfo` | 版本门槛放行 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/pyproject.toml#L2-L3) | `importlib.metadata.version("harbor")` 返回已装版本 | 实测拒绝 0.25.0 | 抛 `HarborCompatibilityError` | 正常入口未到达 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/pyproject.toml#L2-L3) | `importlib.metadata.version("harbor")` 返回已装版本 | 实测拒绝 0.26.0 | 抛 `HarborCompatibilityError` | 正常入口未到达 |

**接续**　版本变更后复跑这一处原始检查。后续 Job 探测在进程内临时替换了受支持版本。 [compat.py 55-65](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L55-L65) · [gateway.py 481](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/gateway.py#L481) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [Job 探测的断言与替身](../../investigations/09-trial-plan/probe.py) · [问题 04](../../investigations/04-version-checks/README.md)
