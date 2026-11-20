# U39 · upload_file 把一个宿主文件交给环境

<a id="u39"></a>

[环境执行、文件与挂载目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 437](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L437)

```python
async def upload_file(self, source_path: Path | str, target_path: str) -> None:
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor base.py 1127–1130](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/agents/installed/base.py#L1127-L1130) | 沿已安装 Agent 的单文件配置上传，核对宿主源文件的字节与环境目标路径。 |
| ② 结果　[Dressage environment.py 438–443](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L438-L443) | 等 `copy2` 完成，从目标路径读回相同字节。使用无敏感信息的示例配置。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L908-L915) | `source_path` 是宿主文件，`target_path` 是可写环境路径 | 实测支持单文件输入 | 正常返回 `None`，目标文件的内容等于源文件 | 三版的 agent 单文件上传用例均读回 `artifact`。独立 verifier 的交接见 U41 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1124-L1131) | `source_path` 是宿主文件，`target_path` 是可写环境路径 | 实测支持单文件输入 | 正常返回 `None`，目标文件的内容等于源文件 | 三版的 agent 单文件上传用例均读回 `artifact`。独立 verifier 的交接见 U41 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1192-L1199) | `source_path` 是宿主文件，`target_path` 是可写环境路径 | 实测支持单文件输入 | 正常返回 `None`，目标文件的内容等于源文件 | 三版的 agent 单文件上传用例均读回 `artifact`。独立 verifier 的交接见 U41 |

**接续**　调用方换目标目录或权限约束时，留存目标文件的实际字节。 [test_environment.py 137-143](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L137-L143) · [基线套件的通过、失败和排除项](../../investigations/00-version-target/pytest-replay.txt) · [对齐夹具后四项测试](../../investigations/03-verifier-fixture/fixture-pytest.txt) · [问题 03](../../investigations/03-verifier-fixture/README.md) · [问题 05](../../investigations/05-skills-upload/README.md)
