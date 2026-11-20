# U59 · 受限网络时 Harbor 配置 Agent 的 Web 工具

<a id="u59"></a>

[题目文件与可选后端目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[plugin.py 1065–1069](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1065-L1069)

```python
hostname = urlparse(advertise_url).hostname
hosts = list(getattr(agent, "extra_allowed_hosts", None) or [])
if hostname:
    if hostname not in hosts:
        hosts.append(hostname)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor trial.py 697–707](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L697-L707) | 用受限网络的同一 Trial 看 `set_web_tools_disabled` 收到的布尔值与 harness 类型。 |
| ② 结果　[Harbor claude_code.py 84–95](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/agents/installed/claude_code.py#L84-L95) | 沿 Claude Code 的实际参数构造查看最终工具名单，核对 WebSearch 和 WebFetch 是否禁用。旧版行为见版本表。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L415-L456) | Dressage 注入 Gateway 主机。此版 Trial 没有新版的阶段 Web 工具调用 | 该新增调用不适用 | 旧路径，未观察到同名调用的输出 | 旧版的实际运行选项待验 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L694) | Trial 把阶段网络策略转换为 `disabled`，传入 Agent 和该环境 | 源码有调用，目标 harness 的实参待验 | harness 结合能力和显式配置决定最终允许的工具 | 启动标志与普通模型请求待验 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L705) | Trial 把阶段网络策略转换为 `disabled`，传入 Agent 和该环境 | 源码有调用，目标 harness 的实参待验 | harness 结合能力和显式配置决定最终允许的工具 | 启动标志与普通模型请求待验 |

**接续**　在同一次受限任务分别记录生效的 Web 工具选项和 Gateway 收到的普通模型请求。 [plugin.py 1065-1074](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1065-L1074) · [问题 14](../../investigations/14-phase-network-policy/README.md) · [问题 15](../../investigations/15-web-tools/README.md)
