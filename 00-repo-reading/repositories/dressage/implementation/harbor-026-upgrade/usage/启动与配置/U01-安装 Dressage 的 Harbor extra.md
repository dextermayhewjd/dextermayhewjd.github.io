# U01 · 安装 Dressage 的 Harbor extra

<a id="u01"></a>

[启动与配置目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[pyproject.toml 22](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/pyproject.toml#L22)

```toml
"harbor==0.18.0",
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage pyproject.toml 20–23](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/pyproject.toml#L20-L23) | 安装时选择 Dressage 的 `harbor` extra，查看解析器读到的版本约束。这里是包元数据。 |
| ② 结果　[Dressage compat.py 50–59](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L50-L59) | 在同一解释器读取实际安装的 `harbor` 版本，对照约束和目标版本。已经预装目标包的实验要单独记。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/pyproject.toml#L2-L3) | Python ≥3.12，按 Dressage 的 `.[harbor]` 解析依赖 | 声明匹配基线 | 解析出的 Harbor 发行包版本 | 声明为 0.18.0，干净安装待验 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/pyproject.toml#L2-L3) | Python ≥3.12，按 Dressage 的 `.[harbor]` 解析依赖 | 声明仍锁到 0.18.0 | 解析出的 Harbor 发行包版本 | 声明不能选出 0.25.0 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/pyproject.toml#L2-L3) | Python ≥3.12，按 Dressage 的 `.[harbor]` 解析依赖 | 声明仍锁到 0.18.0 | 解析出的 Harbor 发行包版本 | 声明不能选出 0.26.0 |

**接续**　版本声明调整后，从干净环境安装并读取包元数据。之前的 Job 探测使用已安装的版本。 [pyproject.toml 21-25](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/pyproject.toml#L21-L25) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [问题 00](../../investigations/00-version-target/README.md) · [问题 04](../../investigations/04-version-checks/README.md)
