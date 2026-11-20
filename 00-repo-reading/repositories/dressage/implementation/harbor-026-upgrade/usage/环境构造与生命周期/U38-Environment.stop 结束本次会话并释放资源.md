# U38 · Environment.stop 结束本次会话并释放资源

<a id="u38"></a>

[环境构造与生命周期目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 432–435](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L432-L435)

```python
self._processes.clear()
if self._session_root.exists():
    await asyncio.to_thread(shutil.rmtree, self._session_root)
self._started = False
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor trial.py 2067–2074](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L2067-L2074) | 从 Trial 收尾进入 `stop`，看本次 session、`delete` 与仍活跃的子进程。 |
| ② 结果　[Dressage environment.py 426–435](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L426-L435) | 等返回后核对 Trial 与环境的停止标志，再检查会话目录及其中的工作文件。请求保留时，文件应仍然可读。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L896-L897) | Trial 分别配置 `delete=True` 和 `False`，会话目录内已有一个工作文件 | 两次均进入真实停止流程，Trial 最终标为已停止 | 两次的会话目录和工作文件都消失，后端 `_started` 为 False | 请求删除时符合预期，请求保留时文件仍被删除 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1112-L1113) | Trial 分别配置 `delete=True` 和 `False`，会话目录内已有一个工作文件 | 两次均进入真实停止流程，Trial 最终标为已停止 | 两次的会话目录和工作文件都消失，后端 `_started` 为 False | 请求删除时符合预期，请求保留时文件仍被删除 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1180-L1181) | Trial 分别配置 `delete=True` 和 `False`，会话目录内已有一个工作文件 | 两次均进入真实停止流程，Trial 最终标为已停止 | 两次的会话目录和工作文件都消失，后端 `_started` 为 False | 请求删除时符合预期，请求保留时文件仍被删除 |

**接续**　三版分别请求删除和保留的六次结果已归档。工作文件位于 bwrap 会话内，探测时没有活动子进程。仍需进程退出证据时，单独在有运行中命令的场景观察。[问题 20 与处理边界](../../investigations/20-bwrap-stop-delete/README.md) · [六次停止的原始结果](../../investigations/20-bwrap-stop-delete/stop-output.txt) · [问题 02 的宿主挂载日志](../../investigations/02-output-mounts/README.md) · [问题 03 的 verifier 夹具](../../investigations/03-verifier-fixture/README.md)
