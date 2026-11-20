# U44 · Trial 回收前查询挂载是否与宿主目录对应

<a id="u44"></a>

[环境执行、文件与挂载目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 545–548](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L545-L548)

```python
mounts[target] = (
    Path(mount["source"]).expanduser().resolve(),
    bool(mount.get("read_only", False)),
)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor trial.py 823](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L823) | 在 `is_path_mounted(source_dir, target_dir)` 记录两条路径和布尔结果。旧版在同一回收入口读 `capabilities.mounted`。 |
| ② 结果　[Harbor trial.py 814](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L814) · [Harbor trial.py 835–843](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L835-L843) | 回到 `_download_agent_logs`，同时看实际选中的方法、Trial 日志和宿主文件内容。查看 `_are_agent_logs_downloaded` 是否仍为 True。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L462) | 回收日志时读取 `capabilities.mounted`，没有逐路径查询 | 基线按 mounted=True 选分支 | True 时跳过日志复制 | 原 Trial 实测走 `prepare_logs_for_host` 一次，`download_dir` 零次。 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L830-L850) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L812) | `is_path_mounted(environment_path, host_path)` 按一对路径查询 | 实测试验提供同一物理目录 | 返回 `False`，Trial 进入下载分支 | 查询实测为 `False`。原 Trial 走下载一次、记录复制错误，宿主原文件仍在。 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L895-L915) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L823) | 同 0.25，默认 auto_mounting=False 影响宿主挂载登记 | 实测试验提供同一物理目录 | 返回 `False`，Trial 进入下载分支 | 查询实测为 `False`。原 Trial 走下载一次、记录复制错误，宿主原文件仍在。 |

**显式改绑时走哪条路？** 三版都标记回收完成。0.18 只看后端的 `mounted`，跳过下载，Trial 目录缺文件。0.25 和 0.26 走下载分支并把文件交给 Trial。[问题 02 的挂载对照](../../investigations/02-output-mounts/README.md#mount-matrix) · [六次回放](../../investigations/02-output-mounts/trial-log-mount-matrix.txt)

**接续**　修后默认直挂应跳过，异目录仍应下载一次。独立 verifier 的四项夹具测试另行查看。[回放代码](../../investigations/02-output-mounts/trial_log_recovery.py) · [问题 03 的夹具](../../investigations/03-verifier-fixture/README.md)
