# U52 · JobPlugin.on_job_end 从 JobResult 提取最终尝试

<a id="u52"></a>

[结果、样本与最终选择目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[plugin.py 423–426](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L423-L426)

```python
final_keys = {
    (str(getattr(result, "trial_name")), str(getattr(result, "id")))
    for result in (getattr(job_result, "trial_results", None) or [])
}
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage rollout.py 760–765](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L760-L765) · [Dressage plugin.py 423–426](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L423-L426) | 从 `job.run` 的实际 JobResult 读最终物理键。有重试时同一 trial 名会有多个历史 ID。 |
| ② 结果　[Dressage plugin.py 428–440](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L428-L440) | 看 `final_keys` 是否送入 manifest 或按配置推迟，再看 `aclose`。只采用 JobResult 对应的物理尝试。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/cli/job_plugins.py#L60-L69) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/job/result.py#L243) | Harbor JobResult 给出 id 和 trial_results。每个结果有 trial_name、id | 真实 Job 与插件的默认结束入口已实测 | 返回 None，非延后选择模式将最终键交给 manifest。finally 关闭插件。训练路径可推迟整组最终选择 | 插件默认结束入口从真实 JobResult 取最终物理 ID，磁盘 manifest 与之相符 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/cli/job_plugins.py#L94-L103) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/job/result.py#L243) | Harbor JobResult 给出 id 和 trial_results。每个结果有 trial_name、id | 真实 Job 与插件的默认结束入口已实测 | 返回 None，非延后选择模式将最终键交给 manifest。finally 关闭插件。训练路径可推迟整组最终选择 | 插件默认结束入口从真实 JobResult 取最终物理 ID，磁盘 manifest 与之相符 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/cli/job_plugins.py#L94-L103) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/job/result.py#L259) | Harbor JobResult 给出 id 和 trial_results。每个结果有 trial_name、id | 真实 Job 与插件的默认结束入口已实测 | 返回 None，非延后选择模式将最终键交给 manifest。finally 关闭插件。训练路径可推迟整组最终选择 | 插件默认结束入口从真实 JobResult 取最终物理 ID，磁盘 manifest 与之相符 |

**CLI 验收还要读 manifest。** 给真实插件的 store 注入一次合成写入异常，两版 Harbor 的 CLI 收尾函数都记录 warning 后返回。测试检查实际产物是否已提交；训练分区直接等待插件并负责最终选择。[两版的运行结果](../../investigations/04-version-checks/wheel-output.txt) · [训练分区](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L759-L766)

**接续**　训练分区启用推迟选择后，另验整组失败分支。 [plugin.py 420-440](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L420-L440) · [rollout.py 762](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L762) · [问题 11](../../investigations/11-trial-events/README.md) · [问题 13](../../investigations/13-final-attempt/README.md)

[三版默认结束入口实测](../../investigations/22-retry-policy/job-trial-output.txt)
