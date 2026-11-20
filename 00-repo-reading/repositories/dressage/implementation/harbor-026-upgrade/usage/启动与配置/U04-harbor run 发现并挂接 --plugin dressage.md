# U04 · harbor run 发现并挂接 --plugin dressage

<a id="u04"></a>

[启动与配置目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[pyproject.toml 27](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/pyproject.toml#L27)

```toml
dressage = "dressage.integrations.harbor.plugin:DressageHarborPlugin"
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor job_plugins.py 64–67](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/cli/job_plugins.py#L64-L67) | 从 `harbor run --plugin dressage` 看注册名解出的 import path 和构造的插件类型。 |
| ② 结果　[Harbor job_plugins.py 73–76](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/cli/job_plugins.py#L73-L76) | 观察这个实例收到哪个 Job、`await on_job_start` 是否正常完成，CLI 最后拿回哪一个实例。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/cli/job_plugins.py#L24-L42) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/cli/plugin_registry.py#L13-L25) | `--config`、`--plugin dressage`、插件 kwargs 和已安装的 `harbor.plugins` entry point | 源码可接收 | 找到插件类、构造实例、调用 `on_job_start(job)`。安装元数据决定名字能否解析 | 已从基线 wheel 的短名解析并加载插件类；完整 CLI 挂接和 Job 执行待验 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/cli/job_plugins.py#L58-L76) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/cli/plugin_registry.py#L13-L25) | `--config`、`--plugin dressage`、插件 kwargs 和已安装的 `harbor.plugins` entry point | 源码可接收 | 找到插件类、构造实例、调用 `on_job_start(job)`。安装元数据决定名字能否解析 | 源码吻合，运行待验 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/cli/job_plugins.py#L58-L76) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/cli/plugin_registry.py#L13-L25) | `--config`、`--plugin dressage`、插件 kwargs 和已安装的 `harbor.plugins` entry point | 源码可接收 | 找到插件类、构造实例、调用 `on_job_start(job)`。安装元数据决定名字能否解析 | 已从基线 wheel 的短名解析并加载插件类；完整 CLI 挂接和 Job 执行待验 |

**宿主遥测**　0.25、0.26 的本地 CLI 在关闭命令时默认准备发往 PostHog 的事件。加 `--print-config` 已在发送进程启动前观察事件，设置宿主 `HARBOR_TELEMETRY=0` 后没有进入发送入口。[问题 24](../../investigations/24-host-telemetry/README.md)

**接续**　从目标版新安装环境通过短名装载一次。直接构造插件的 U19 验不到这个入口。 [run_harbor_rollout_qwen3.5_4b.sh 109-112](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_rollout_qwen3.5_4b.sh#L109-L112) · [之前归档的 CLI 帮助](../../investigations/06-agent-credential-preflight/cli-help-excerpts.txt) · [问题 04](../../investigations/04-version-checks/README.md) · [问题 07](../../investigations/07-agent-routing/README.md) [wheel 与短名解析的实测](../../investigations/04-version-checks/wheel-output.txt)
