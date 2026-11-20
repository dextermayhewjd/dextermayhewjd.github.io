# U14 · Job.create 在插件设置路由前创建 Job

<a id="u14"></a>

[Job 与 Agent 路由目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[rollout.py 107](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L107)

```python
return await Job.create(config)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage rollout.py 103–107](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L103-L107) | 在 `Job.create(config)` 前记下该分区的 Agent、题目及凭证检查配置。 |
| ② 结果　[Dressage rollout.py 703–705](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L703-L705) · [Dressage rollout.py 759–761](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L759-L761) | 看返回的 `job` 是否是交给 `plugin.on_job_start` 的那个对象。若创建失败，插件入口不会命中。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L121-L134) | `JobConfig`，本地题目与 Agent 配置 | 三组指定 Agent/模型配置实测接受 | 返回已初始化的 `Job`，供插件挂接及计划配对 | 另两组凭证边界输入也获得 Job。0.18 忽略新式密钥选择字段 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L171-L224) | `JobConfig`，普通本地路径先做 Agent 凭证预检 | 三组指定 Agent/模型配置实测接受 | 返回已初始化的 `Job`，供插件挂接及计划配对 | 这三组配置均实测获得 Job。实际模型请求另验 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L171-L225) | `JobConfig`，普通本地路径先做 Agent 凭证预检 | 三组指定 Agent/模型配置实测接受 | 返回已初始化的 `Job`，供插件挂接及计划配对 | 随仓 Qwen 配置获得 Job。未设置的显式密钥变量、缺少凭证的 OpenRouter 默认连接均在插件启动前被拒绝 |

**第二轮输出**　[0.18 本地 Job 创建和 Claude Code 启动命令](../../investigations/07-agent-routing/agent-connection-0.18.txt) · [0.26 同输入](../../investigations/07-agent-routing/agent-connection-0.26.txt)

**接续**　增加 harness 或换凭证输入时只复核此处与 U21。 [rollout.py 704](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L704) · [rollout.py 759-762](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L759-L762) · [三版 Job 和 lock 输出](../../investigations/10-job-lock/job-lock-output.txt) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [问题 06](../../investigations/06-agent-credential-preflight/README.md) · [问题 09](../../investigations/09-trial-plan/README.md)
