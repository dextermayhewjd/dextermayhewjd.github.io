# 20 · Trial 指定 `delete=False` 后，bwrap 工作目录能否保留？

**当前判断**　Dressage 的 bwrap 后端在 Harbor 0.18.0、0.25.0 和 0.26.0 上都会删除本次会话目录。显式请求保留时，会话工作文件也随之消失。这项限制在升级前已经存在。本页保留独立的工作区清理结论。目标版新增的生产修复与证据见[第二轮复查](../upgrade-audit-026.md)。

**对应的三版用法表**　[U38 环境停止与工作目录](../../usage/环境构造与生命周期/U38-Environment.stop%20结束本次会话并释放资源.md#u38) · [原套件在本问题测到了哪里](../original-test-audit.md#i20)

<a id="sources"></a>

## 两边的源码原文

**Harbor 0.26.0** 的后端接口约定停止环境时可以选择是否删除环境。[base.py 第 1180–1181 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1180-L1181)

```python
async def stop(self, delete: bool):
    """Stops the environment and optionally deletes it."""
```

**Harbor 0.26.0** 把该 Trial 配置的 `delete` 传给当前环境实例。[trial.py 第 2070–2073 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L2070-L2073)

```python
await asyncio.shield(
    self.agent_environment.stop(delete=self.config.environment.delete)
)
self._is_agent_environment_stopped = True
```

**Dressage 3e3142f** 接收参数后立即丢弃它。[environment.py 第 424–425 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L424-L425)

```python
async def stop(self, delete: bool) -> None:
    del delete
```

同一个方法随即清理会话目录并更新启动状态。[environment.py 第 432–435 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L432-L435)

```python
self._processes.clear()
if self._session_root.exists():
    await asyncio.to_thread(shutil.rmtree, self._session_root)
self._started = False
```

0.18.0 的接口也允许选择是否删除，旧版 Trial 同样转交配置值。[0.18 接口](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L896-L897) · [0.18 调用](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L1145-L1148)

<a id="evidence"></a>

## 证据与验证范围

在三个版本各创建两个真实 Harbor Trial，使用 Dressage 的 bwrap 后端。在临时会话内的 `/app/stop-probe.txt` 写入相同内容，确认文件存在，然后从 `Trial._stop_agent_environment()` 进入清理。直接观察宿主上的会话目录和其中的文件。[六次调用的输出](stop-output.txt) · [测试输入与断言](test_stop_retention.py)

| Trial 配置 | 三个版本的实际结果 | 与请求是否一致 |
| --- | --- | --- |
| `delete=True` | Trial 已停止，会话目录和工作文件都已删除 | 一致 |
| `delete=False` | Trial 已停止，会话目录和工作文件也都已删除 | 请求保留工作目录的断言失败 |

这六次调用均使用临时本地文件，没有活动中的命令进程。已有宿主挂载日志的交付另由问题 02 验证。[日志挂载的两组输入](../02-output-mounts/README.md#mount-matrix)

## 处理与验收

本次升级记录其适用边界。若项目要支持停止后检查 bwrap 工作区，用本页两个配置分别验收。保留时应仍能读到原文件字节，删除时会话目录应消失，两条路径均应结束运行状态。若只支持随 Trial 清理，需对显式要求保留的调用说明后端能力。

<a id="history"></a>

## 判断记录

- 2026-11-18　U38 原先记录了 `delete=False` 的源码行为，关联的 02 和 03 各自处理日志挂载和 verifier 夹具。三版实测后独立登记本问题。原版套件只走 `stop(True)` 清理。[原套件的清理调用](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L109-L111) · [复现步骤](../../tools/reproduce.md#stop-retention) · [本次 PR 的范围](../../prs/001-harbor-026-compatibility/README.md#mounts)
