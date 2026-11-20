# U42 · download_dir 回收环境里的非空日志目录

<a id="u42"></a>

[环境执行、文件与挂载目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 467](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L467)

```python
async def download_dir(self, source_dir: str, target_dir: Path | str) -> None:
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor trial.py 827–838](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L827-L838) | 用一个非空日志目录跟随 Trial 的下载分支，核对它交给 `download_dir` 的源和目标。 |
| ② 结果　[Dressage environment.py 472–479](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L472-L479) · [Harbor trial.py 839–843](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L839-L843) | 比较两个真实目录。返回 Trial 后看文件内容、错误日志与下载标记。三者各自记录。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L938-L946) | `source_dir` 在环境中，`target_dir` 在宿主。有风险的特例是两者映射到同一目录 | 签名匹配，基线挂载路径会跳过复制 | 预期 `None`，宿主留有全部文件。同目录时上层应识别挂载 | 原 Trial 实测跳过下载，文件字节一致，错误日志为空。 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1154-L1162) | `source_dir` 在环境中，`target_dir` 在宿主。有风险的特例是两者映射到同一目录 | 签名匹配，但会被要求将非空目录复制到自身 | 后端尝试复制同一非空目录，抛出 `shutil.Error` | 真实后端复制抛 `shutil.Error`。Trial 记录错误并返回 `None`，标记已下载。直挂的原文件仍可读。 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1222-L1230) | `source_dir` 在环境中，`target_dir` 在宿主。有风险的特例是两者映射到同一目录 | 同 0.25，输入被错误地送入复制分支 | 后端尝试复制同一非空目录，抛出 `shutil.Error` | 真实后端复制抛 `shutil.Error`。Trial 记录错误并返回 `None`，标记已下载。直挂的原文件仍可读。 |

**换一个输入后的实测**　把 `/logs/agent` 显式绑到另一个宿主目录，回收前 Trial 目录没有这份日志。0.18 跳过下载，目标仍缺文件。0.25 和 0.26 均调用一次 `download_dir`，目标收到字节相同的文件。[问题 02 的三版对照](../../investigations/02-output-mounts/README.md#mount-matrix) · [原始输出](../../investigations/02-output-mounts/trial-log-mount-matrix.txt)

**接续**　修后同时重跑默认直挂和显式改绑，核对复制次数和 Trial 实际收到的文件。[回放代码](../../investigations/02-output-mounts/trial_log_recovery.py)
