# U32 · Environment.type 返回后端标识

<a id="u32"></a>

[环境构造与生命周期目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 290](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L290)

```python
return "dressage-bwrap"
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor base.py 596–603](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L596-L603) | 从基类的资源检查进入 `self.type()`，确认运行中的实例类型。 |
| ② 结果　[Dressage environment.py 288–290](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L288-L290) · [Harbor base.py 598–605](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L598-L605) | 把返回的 `dressage-bwrap` 和基类继续使用的 `environment_label` 对上。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L645-L650) | 静态调用 `type()`，无参数 | 源码可接收 | 字符串 `dressage-bwrap` | 返回值有源码依据。导入路径装载另见 U13 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L861-L866) | 静态调用 `type()`，无参数 | 源码可接收 | 字符串 `dressage-bwrap` | 返回值有源码依据。导入路径装载另见 U13 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L926-L931) | 静态调用 `type()`，无参数 | 源码可接收 | 字符串 `dressage-bwrap` | 返回值有源码依据。导入路径装载另见 U13 |

**接续**　后端标识或工厂选择逻辑发生变化时复核。 [问题 01](../../investigations/01-environment-preflight/README.md)
