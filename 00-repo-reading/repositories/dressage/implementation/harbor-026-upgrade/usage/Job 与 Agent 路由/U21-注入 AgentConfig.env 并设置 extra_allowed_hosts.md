# U21 · 注入 AgentConfig.env 并设置 extra_allowed_hosts

<a id="u21"></a>

[Job 与 Agent 路由目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[plugin.py 1064](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1064)

```python
agent.env = env
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage plugin.py 382–386](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L382-L386) | 看注入的 Gateway 地址、占位变量名及允许的 host，只记录键名和路由身份。 |
| ② 结果　[Harbor trial.py 728–737](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L728-L737) · [Dressage gateway.py 875–893](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/gateway.py#L875-L893) | 看 harness 的有效地址，再在 Gateway 检查第一条真实请求是否找到同一 slot。只需记录路由匹配结果。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/trial/config.py#L124) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/trial/config.py#L100-L106) | 按 Agent 名或导入路径选择协议，向复制的 AgentConfig 写 Gateway 地址、凭证引用、允许主机 | 试验已接收配置并在 Trial 中读到 Gateway URL | 配置交给 harness，首条模型请求应关联正确的 Trial 和 Gateway | 六组输入的 Claude Code 启动命令均携带 Gateway 与 Trial 凭证。首个 HTTP 请求待验 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/config.py#L166) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/config.py#L142-L148) | 按 Agent 名或导入路径选择协议，向复制的 AgentConfig 写 Gateway 地址、凭证引用、允许主机 | 试验已接收配置并在 Trial 中读到 Gateway URL | 配置交给 harness，首条模型请求应关联正确的 Trial 和 Gateway | URL 写入实测。首个真实请求及最终 auth 解析待验 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/config.py#L167) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/config.py#L143-L149) | 按 Agent 名或导入路径选择协议，向复制的 AgentConfig 写 Gateway 地址、凭证引用、允许主机 | 试验已接收配置并在 Trial 中读到 Gateway URL | 配置交给 harness，首条模型请求应关联正确的 Trial 和 Gateway | 随仓配置的启动命令携带 Gateway 和 Trial API key。指定其他 endpoint、key 名或 provider 环境变量可改写生效地址或凭证。首个 HTTP 请求待验 |

**第二轮输出**　[0.18 本地 Job 创建和 Claude Code 启动命令](../../investigations/07-agent-routing/agent-connection-0.18.txt) · [0.26 同输入](../../investigations/07-agent-routing/agent-connection-0.26.txt)

**接续**　实测时记录请求落到哪个 Trial。仅比较配置字符串无法观察实际终点。 [plugin.py 1066-1074](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1066-L1074) · [plugin.py 1153-1158](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1153-L1158) · [plugin.py 385](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L385) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [Job 探测的断言与替身](../../investigations/09-trial-plan/probe.py) · [问题 07](../../investigations/07-agent-routing/README.md) · [问题 14](../../investigations/14-phase-network-policy/README.md)
