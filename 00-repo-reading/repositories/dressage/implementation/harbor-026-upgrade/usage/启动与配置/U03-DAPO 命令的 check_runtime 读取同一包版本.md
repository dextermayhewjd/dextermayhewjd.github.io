# U03 · DAPO 命令的 check_runtime 读取同一包版本

<a id="u03"></a>

[启动与配置目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[prepare_dataset.py 553](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py#L553)

```python
version = importlib.metadata.version("harbor")
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage prepare_dataset.py 575–580](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py#L575-L580) | 以原 DAPO 命令的 `--check-runtime` 进入，核对当前解释器的 Harbor 版本。 |
| ② 结果　[Dressage prepare_dataset.py 599–604](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py#L599-L604) | 在命令调用方取退出码及错误提示。相同参数下，接受和拒绝各产生什么结果？ |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/pyproject.toml#L2-L3) | `--check-runtime` 读取发行包版本并与工具固定值比较 | 实测接受 | 检查通过返回 `None` | 实测进程退出码 0，无输出 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/pyproject.toml#L2-L3) | `--check-runtime` 读取发行包版本并与工具固定值比较 | 实测拒绝 | 报告版本不符 | 实测退出码 2，打印需要 0.18.0 及实装版本 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/pyproject.toml#L2-L3) | `--check-runtime` 读取发行包版本并与工具固定值比较 | 实测拒绝 | 报告版本不符 | 实测退出码 2，打印需要 0.18.0 及实装版本 |

**接续**　三版检查均已真实运行。修改版本目标后，再用同一命令复核退出码。 [三版退出码和输出](../../investigations/04-version-checks/dapo-runtime-output.txt) [prepare_dataset.py 547-560](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py#L547-L560) · [问题 04](../../investigations/04-version-checks/README.md)
