# U19 · JobPlugin.on_job_start 接收 Job 并登记路由与回调

<a id="u19"></a>

[Job 与 Agent 路由目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[plugin.py 269](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L269)

```python
self._job_id = str(getattr(job, "id"))
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor job_plugins.py 73–76](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/cli/job_plugins.py#L73-L76) · [Dressage rollout.py 759–761](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L759-L761) | CLI 挂接与训练分区都将现有 Job 传给插件，选择正在回放的入口并记下 Job ID。 |
| ② 结果　[Dressage plugin.py 405–418](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L405-L418) | 看本 Job 的 slot、六个回调与 `_started`。此处只能观察到注册完成，触发时序在事件条目里检查。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/job/plugin.py#L13) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/cli/job_plugins.py#L24-L42) | 新建 Job 的 id、is_resuming 和未运行的 TrialConfigs。训练入口由 Dressage 主动调用 | 三版真实 Job 加测试 Gateway 已接受 | `None`。插件保留本 Job 的 slots、六组钩子和每个 Trial 的 Gateway 配置 | 注册和配置实测。真实 Gateway 和完整生命周期待测 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/job/plugin.py#L13) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/cli/job_plugins.py#L58-L76) | 新建 Job 的 id、is_resuming 和未运行的 TrialConfigs。训练入口由 Dressage 主动调用 | 三版真实 Job 加测试 Gateway 已接受 | `None`。插件保留本 Job 的 slots、六组钩子和每个 Trial 的 Gateway 配置 | 注册和配置实测。真实 Gateway 和完整生命周期待测 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/job/plugin.py#L13) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/cli/job_plugins.py#L58-L76) | 新建 Job 的 id、is_resuming 和未运行的 TrialConfigs。训练入口由 Dressage 主动调用 | 三版真实 Job 加测试 Gateway 已接受 | `None`。插件保留本 Job 的 slots、六组钩子和每个 Trial 的 Gateway 配置 | 注册和配置实测。真实 Gateway 和完整生命周期待测 |

**接续**　实际启动新 Job 后看第一条请求是否落在该物理 Trial 的 route。 [plugin.py 261-274](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L261-L274) · [rollout.py 760](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L760) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [Job 探测的断言与替身](../../investigations/09-trial-plan/probe.py) · [问题 07](../../investigations/07-agent-routing/README.md) · [问题 09](../../investigations/09-trial-plan/README.md) · [问题 11](../../investigations/11-trial-events/README.md)
