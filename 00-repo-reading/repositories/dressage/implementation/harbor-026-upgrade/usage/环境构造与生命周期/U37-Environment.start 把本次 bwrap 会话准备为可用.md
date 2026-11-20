# U37 · Environment.start 把本次 bwrap 会话准备为可用

<a id="u37"></a>

[环境构造与生命周期目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 419–422](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L419-L422)

```python
relay_path = self._session_root / "relay.py"
relay_path.write_text(_RELAY_SOURCE, encoding="utf-8")
relay_path.chmod(0o500)
self._started = True
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor trial.py 1880–1886](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L1880-L1886) | 看本 Trial 等待哪个实例的 `start`，以及 `force_build`、超时时限。 |
| ② 结果　[Dressage environment.py 419–422](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L419-L422) | 单步越过返回，确认 `_started`、会话 rootfs 和 relay 文件，再用同一实例读一个测试文件。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L892-L893) | `await start(force_build=False)`。bwrap 拒绝 `force_build=True` | 基线环境用例接受 False | 正常返回 `None`，创建会话 rootfs、挂载目标和 relay，独立 verifier 会话还准备测试目录 | 环境可用于后续文件操作有证据。显式强制构建另按拒绝路径判断 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1108-L1109) | `await start(force_build=False)`。bwrap 拒绝 `force_build=True` | 目录存在时接受 False | 创建会话 rootfs、挂载目标和 relay；独立 verifier 对缺失目录的失败见下文 | 环境可用于后续文件操作有证据。显式强制构建另按拒绝路径判断 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1176-L1177) | `await start(force_build=False)`。bwrap 拒绝 `force_build=True` | 目录存在时接受 False | 创建会话 rootfs、挂载目标和 relay；独立 verifier 对缺失目录的失败见下文 | 环境可用于后续文件操作有证据。显式强制构建另按拒绝路径判断 |

**独立 verifier 实测**　独立 verifier 若省略空 `environment/`，0.18 仍返回 reward 1，0.25、0.26 在 `start(False)` 抛 `NotADirectoryError`。保留该目录并放入普通 Agent 输入时，新版的启动路径把它复制进 `/tests`。[问题 21 的输入对照](../../investigations/21-separate-verifier-input/README.md#evidence)

**升级分支后来补到的观察。** `start()` 返回后，Agent 第一次打开 `/logs/agent/oracle.txt` 时也依赖已经建好的父目录。用同一道题比较沙箱自有目录和空宿主父挂载，让 Oracle 自己写第一行。两种输入的修前与修后结果见 [C05 的共同分析与两笔修复](../../prs/001-harbor-026-compatibility/commits/05-log-directories/README.md#shared-analysis)。

**接续**　接入运行中验收可执行命令或可读文件，单凭 None 无法判断环境可用。 [environment.py 394-417](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L394-L417) · [基线套件的通过、失败和排除项](../../investigations/00-version-target/pytest-replay.txt) · [两个新版本的技能文件读回](../../investigations/05-skills-upload/skills-upload-output.txt) · [对齐夹具后四项测试](../../investigations/03-verifier-fixture/fixture-pytest.txt) · [问题 03](../../investigations/03-verifier-fixture/README.md) · [问题 05](../../investigations/05-skills-upload/README.md)
