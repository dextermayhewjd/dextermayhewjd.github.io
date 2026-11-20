# U34 · EnvironmentFactory 调用 DressageEnvironment.preflight

<a id="u34"></a>

[环境构造与生命周期目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 302](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L302)

```python
def preflight(cls) -> None:
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor factory.py 323](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/factory.py#L323) | 在工厂给 `env_class.preflight` 传参的这一行，查看所选类和实际关键字名。旧版调用行见版本表。 |
| ② 结果　[Dressage environment.py 303](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L303) | 在后端第一条可执行语句停。若一次也没有命中，就在工厂记录异常类型和关键字名。到达时才算进入 bwrap 检查。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/factory.py#L205) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L863-L871) | `env_class.preflight()` | 实测接受 | 已进入原 bwrap 预检 | 入口已测，探测在二进制检查前主动停止 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/factory.py#L273) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1079-L1087) | `env_class.preflight()` | 实测接受 | 已进入原 bwrap 预检 | 入口已测，探测在二进制检查前主动停止 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/factory.py#L323) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1144-L1155) | `env_class.preflight(kwargs=kwargs)`，关键字即使值为 None 也会传入 | 实测不匹配，TypeError | 未进入后端预检 | 未到达。工厂调用在传参处抛出异常 |

**接续**　修后先跑真实工厂回归。0.26 的默认输入、显式 `None` 和 `{}` 都应先经过基类选项解析，再到达 bwrap 检查。完整后端预检沿用原套件。[三种输入的 pytest](../../investigations/01-environment-preflight/test_factory_preflight.py) · [三版修前结果](../../investigations/01-environment-preflight/factory-contract-results.txt) · [问题 01](../../investigations/01-environment-preflight/README.md)
