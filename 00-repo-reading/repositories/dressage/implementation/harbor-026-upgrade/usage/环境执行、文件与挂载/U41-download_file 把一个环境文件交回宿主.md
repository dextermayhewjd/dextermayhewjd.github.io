# U41 · download_file 把一个环境文件交回宿主

<a id="u41"></a>

[环境执行、文件与挂载目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 459](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L459)

```python
async def download_file(self, source_path: str, target_path: Path | str) -> None:
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor oracle.py 143–148](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/agents/oracle.py#L143-L148) | 以 Oracle 下载单个日志文件为例，确认查询走入下载分支，记下容器源文件与宿主目标。 |
| ② 结果　[Dressage environment.py 459–465](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L459-L465) | 等下载返回后从宿主目标读回字节。独立 verifier 的交接再从第二个环境读一次。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L928-L935) | `source_path` 是环境文件，`target_path` 是宿主路径 | 基线夹具接受 | 正常返回 `None`，宿主文件可再上传到独立 verifier | 夹具中 verifier 读到 result |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1144-L1151) | `source_path` 是环境文件，`target_path` 是宿主路径 | 签名可接收。原独立 verifier 夹具提前失败 | 正常返回 `None`，宿主文件可再上传到独立 verifier | 该跨两个环境的文件交接尚缺 0.25 修正夹具结果 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1212-L1219) | `source_path` 是环境文件，`target_path` 是宿主路径 | 对齐 verifier 夹具后实测接受 | 正常返回 `None`，宿主文件可再上传到独立 verifier | 修正夹具中 verifier 读到 result |

**接续**　复用同一内容的下载→上传断言，核对宿主目的地和下游读回值。 [test_environment.py 104-109](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L104-L109) · [基线套件的通过、失败和排除项](../../investigations/00-version-target/pytest-replay.txt) · [0.26 夹具的一行差异](../../investigations/03-verifier-fixture/auto-mounts.patch) · [对齐夹具后四项测试](../../investigations/03-verifier-fixture/fixture-pytest.txt) · [问题 03](../../investigations/03-verifier-fixture/README.md)
