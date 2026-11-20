# U07 · TaskConfig.get_local_path 定位题目目录

<a id="u07"></a>

[启动与配置目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[plugin.py 1085–1089](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1085-L1089)

```python
try:
    path = Path(getter()).expanduser().resolve()
except (OSError, TypeError, ValueError):
    return None
return path if (path / "task.toml").is_file() else None
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage plugin.py 1085–1089](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1085-L1089) | 看 `get_local_path()` 的结果、解析后的目录以及其中是否有 `task.toml`。 |
| ② 结果　[Dressage plugin.py 293–301](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L293-L301) | 看插件拿到的 `task_dir`。有文件时进入网络审核。定位失败时记录是哪个 Trial 停在了路由分配之前。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/trial/config.py#L376-L377) | Trial 的任务引用提供 `get_local_path()`，本地目录里有 `task.toml` | 源码可接收 | 取到本地路径。Dressage 对不存在或无题目文件的路径按未取得目录处理 | 本地 Job 有间接证据。远程下载后的路径待验 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/config.py#L454-L455) | Trial 的任务引用提供 `get_local_path()`，本地目录里有 `task.toml` | 源码可接收 | 取到本地路径。Dressage 对不存在或无题目文件的路径按未取得目录处理 | 本地 Job 有间接证据。远程下载后的路径待验 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/config.py#L463-L464) | Trial 的任务引用提供 `get_local_path()`，本地目录里有 `task.toml` | 源码可接收 | 取到本地路径。Dressage 对不存在或无题目文件的路径按未取得目录处理 | 本地 Job 有间接证据。远程下载后的路径待验 |

**接续**　复查远程来源时看下载完成后的实际目录。题目定义模型由 U08 接收。 [plugin.py 1085-1090](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1085-L1090) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [Job 探测的断言与替身](../../investigations/09-trial-plan/probe.py) · [问题 09](../../investigations/09-trial-plan/README.md) · [问题 14](../../investigations/14-phase-network-policy/README.md)
