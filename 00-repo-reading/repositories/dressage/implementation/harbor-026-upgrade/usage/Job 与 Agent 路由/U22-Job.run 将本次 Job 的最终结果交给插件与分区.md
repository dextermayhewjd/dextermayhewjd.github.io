# U22 · Job.run 将本次 Job 的最终结果交给插件与分区

<a id="u22"></a>

[Job 与 Agent 路由目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[rollout.py 761](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L761)

```python
result = await job.run()
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage rollout.py 759–762](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L759-L762) | 在 `await job.run()` 前记下 Job ID 和计划中的 Trial 名。 |
| ② 结果　[Dressage rollout.py 762–765](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L762-L765) | 在插件与分区读 `result.trial_results`，核对最终的物理 Trial ID。重试用例要同时保留被取代的那次 ID。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L850) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L857) | 已挂接插件的 Job，`await job.run()` 无额外实参 | 源码可接收 | 返回 `JobResult`，包含合并后的 `trial_results`。Dressage 读取最终 Trial 名和物理 ID | 源码及替身用例有据。真实 Job 发生重试的完整交接待验 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1207) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1216) | 已挂接插件的 Job，`await job.run()` 无额外实参 | 源码可接收 | 返回 `JobResult`，包含合并后的 `trial_results`。Dressage 读取最终 Trial 名和物理 ID | 源码及替身用例有据。真实 Job 发生重试的完整交接待验 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L1219) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L1228) | 已挂接插件的 Job，`await job.run()` 无额外实参 | 源码可接收 | 返回 `JobResult`，包含合并后的 `trial_results`。Dressage 读取最终 Trial 名和物理 ID | 源码及替身用例有据。真实 Job 发生重试的完整交接待验 |

**宿主遥测**　0.26 中，Job 正常完成或命中特定异常分支时会调度 `harbor.job_finished`；宿主开关 `HARBOR_TELEMETRY=0` 可关闭。这一 Job 路径按源码核对，已录制的运行证据覆盖 CLI 命令结束事件。[问题 24](../../investigations/24-host-telemetry/README.md)

**接续**　对照 JobResult 中最终 id 与 bundle、Sample、manifest 的 id。 [rollout.py 762-765](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L762-L765) · [问题 11](../../investigations/11-trial-events/README.md) · [问题 13](../../investigations/13-final-attempt/README.md)
