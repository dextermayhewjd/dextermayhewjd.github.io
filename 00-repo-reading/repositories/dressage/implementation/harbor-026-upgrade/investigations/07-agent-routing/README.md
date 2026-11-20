# 07 · Harbor 解析 Agent 配置后，请求还会到达本次 Trial 的 Gateway 吗？

**当前判断**　0.26 启动随仓 Claude Code + Qwen 组合时，命令使用 Gateway 和 Trial API key。显式 endpoint、密钥选择器或 Agent 中的 provider 环境变量能改变最终命令的地址或凭证。插件需要处理与 Trial 路由冲突的连接配置。真实网络请求及 slot 匹配仍待验。

**对应的三版用法表**　[U21 注入 AgentConfig.env 并设置 extra_allowed_hosts](../../usage/Job%20与%20Agent%20路由/U21-注入%20AgentConfig.env%20并设置%20extra_allowed_hosts.md#u21) · [原套件在本问题测到了哪里](../original-test-audit.md#i07)

待运行的 Agent 配置中已经有 Gateway 地址，最终发 HTTP 的是解析过这份配置的 harness。

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　把同一个 Trial 凭证模板和 Gateway 地址交给 Anthropic 协议的 Agent。[plugin.py 第 1046–1051 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1046-L1051)

```python
if protocol in {"anthropic", "both"}:
    env.update({
        "ANTHROPIC_API_KEY": token_template,
        "ANTHROPIC_AUTH_TOKEN": token_template,
        "ANTHROPIC_BASE_URL": advertise_url,
    })
```

**Harbor 0.26.0**　Claude Code 解析出 API key 时，将未选中的鉴权变量设为空字符串。[claude_code.py 第 290–296 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/agents/installed/claude_code.py#L290-L296)

```python
if access.api_key is not None:
    inactive_key = (
        "ANTHROPIC_API_KEY"
        if "ANTHROPIC_AUTH_TOKEN" == access.api_key_destination_name
        else "ANTHROPIC_AUTH_TOKEN"
    )
    access = replace(access, env={**access.env, inactive_key: ""})
```

**据此判断**　插件写入的配置还会经过 harness 的连接解析。要判断路由是否可用，需检查最终请求能否抵达 Gateway 并匹配本次 Trial。

<a id="evidence"></a>

## 证据与验证范围

<a id="c06-main-agent"></a>

**C06 提交后复核。** 从干净工作树 `a1087bb` 加载 Dressage 路由函数，使用 Python 3.12.3 和已安装的 Harbor 0.26.0。固定同一题、Claude Code 和随仓模型 `Qwen/Qwen3.5-4B`。三组都成功创建 Job、通过 Dressage 原有认证检查，并走到 Harbor 构造 CLI 启动环境。只改一个连接字段就能改变最终连接。[复跑脚本](agent_connection_probe.py) · [C06 输出前四行](agent-connection-c06-0.26.txt)

| 本次唯一改动 | CLI 最终使用的地址 | CLI 最终使用的 API key |
|---|---|---|
| 基线，省略连接覆盖 | Dressage Gateway | 本次 Trial 的合成凭证 |
| 显式填写另一个 `base_url` | 另一本机测试地址 | 本次 Trial 的合成凭证 |
| 显式填写 `model_api_key_name` | Dressage Gateway | 选择器指向的另一份合成凭证 |

探测调用真实的 `Job.create`、Dressage 注入函数及 Harbor Agent 工厂和 `agent.run`。记录环境截获 `exec`，未启动 Claude CLI、未调用模型服务。本轮确认了传给进程的连接参数；真实请求是否抵达目标、Gateway 是否接受凭证仍需在独立验收中观察。

**已存输出**　0.26 的八份 Trial 配置中都查到了 Gateway URL，探测使用内存 Gateway 替身。[trial-plan-output.txt 第 26 行](../09-trial-plan/trial-plan-output.txt#L26)

```text
Trial configs with a Gateway URL: 8
```

这行记录到的是 Trial 配置。第二轮用真实 `Job.create` 创建本地 Job，调用 Dressage 原有的替代认证检查和路由注入，再用 Harbor 的 `AgentFactory` 构造 Claude Code 并调用其 `run`。记录环境复用 Harbor 的 `scoped_exec_env` 和 `_merge_env`，在 `exec` 收到启动 CLI 的命令时保存最终地址与凭证类别。两个地址均为合成的 loopback 地址，`exec` 不执行命令；未向 Gateway 或模型服务发请求。此前 0.25 的配置实验使用另一 Dressage 提交，保留原证据边界。[离线探测](agent_connection_probe.py) · [0.18 输出](agent-connection-0.18.txt) · [0.26 输出](agent-connection-0.26.txt)

| 输入 | 0.18 发给 CLI 的命令环境 | 0.26 发给 CLI 的命令环境 |
| --- | --- | --- |
| 随仓 Agent 名和模型名，无连接覆盖 | Gateway，两个 Anthropic 凭证变量都带 Trial 凭证 | Gateway，API key 带 Trial 凭证，auth token 为空 |
| 显式 `AgentConfig.base_url` | Gateway，Trial 凭证 | 另一个 endpoint，仍携带 Trial API key |
| 显式 `model_api_key_name` 选择合成的另一凭证 | Gateway，Trial 凭证 | Gateway，携带选中的另一 API key |
| OpenRouter 模型，Agent 的 `env` 同时给出 provider 地址和 key | Gateway，Trial 凭证 | provider 地址和 bearer 凭证，Anthropic API key 为空 |

0.18 的 AgentConfig 忽略这两个新增顶层字段。0.26 的连接解析显式选择 `model_api_key_name`，优先使用 `base_url`，同一 Agent 环境内 provider 变量也可先于原生变量被选中。Harbor 随后把解析后的值放回 Agent 的执行环境。仅凭 `ANTHROPIC_AUTH_TOKEN` 被清空，不能判定 Trial 凭证丢失；应一起核对实际 endpoint 和生效的认证变量。[0.18 AgentConfig](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/trial/config.py#L61-L80) · [0.26 新增连接字段](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/config.py#L66-L84) · [密钥选择顺序](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/agents/agent_auth_resolution.py#L654-L691) · [地址选择顺序](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/agents/agent_auth_resolution.py#L703-L727) · [生效的执行环境](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/agents/base.py#L361-L368)

## 处理与验收

**修后复核**　C07 在分配 Gateway 前校验待运行主 Agent，并在 Claude Code 和 Codex 配置中指定 Gateway 和 Trial 凭证来源。复跑相同输入，常规 Claude 和带 OpenRouter provider 配置的 Claude 都获得 Gateway 地址和该 Trial 的凭证。两类冲突覆盖均被拒绝。缺失厂商密钥的预检依然发生在插件之前。[修后离线输出](agent-connection-c07-0.26.txt) · [C07 实现和验收](../../prs/001-harbor-026-compatibility/commits/07-main-agent-routing/README.md)

**通过条件**　Gateway 用该请求找到本次 Trial，互相冲突的非空凭证会被拒绝，结束后路由得到清理。已有请求头与替代认证用例可复用。[Gateway 合同测试](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_execution.py#L552) · [替代认证检查](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1196)

<a id="openai-harness-credentials"></a>

### 四种 harness 的启动凭证对照

在 Dressage `0b3d570` 加上本地 Claude 凭证选择修改、Harbor 0.26.0 的环境中，用 `openai/gpt-4.1` 和两份合成凭证比较三种配置。Codex 和 Qwen Code 使用 Dressage 默认协议；OpenCode 和 OpenClaw 显式配置 `agent_protocol_overrides=openai`（按 Agent 名称映射）。第三组仅在实验的 Agent 副本上将 `model_api_key_name` 改为 `OPENAI_API_KEY`。

| 检查的产物 | 省略选择器 | 选择另一有值变量 | 实验中指定 Dressage 注入的变量 |
| --- | --- | --- | --- |
| Codex 默认配置的启动环境和准备上传的 TOML | Trial 凭证 | 另一凭证 | Trial 凭证 |
| Qwen Code 启动命令引用的环境变量 | Trial 凭证 | 另一凭证 | Trial 凭证 |
| OpenCode 生成的 provider JSON 的 key 引用和对应环境值 | Trial 凭证 | 另一凭证 | Trial 凭证 |
| OpenClaw 生成的 provider JSON 的 key 引用和对应环境值 | Trial 凭证 | 另一凭证 | Trial 凭证 |

这十二组启动材料里的 endpoint 均为 Gateway。另给 Codex 配置活动 profile，指定另一 provider、地址和凭证变量。即使实验已强制从 `OPENAI_API_KEY` 取值，最终 TOML 的活动 provider 仍保留另一地址及 `env_key=PROFILE_KEY`。实验检查到启动边界，没有执行客户端命令或发送模型请求。[Codex 的配置合并](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/installed/codex.py#L1987-L2015) · [Qwen Code 的启动命令](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/installed/qwen_code.py#L742-L755) · [OpenCode 的 provider 配置](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/installed/opencode.py#L245-L264) · [OpenClaw 的 provider 配置](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/installed/openclaw.py#L737-L750)

<a id="history"></a>

## 判断记录

- 2026-11-18　之前在 0.25 的 Claude Code 配置探测中使用测试模型名与假凭证，解析后 Gateway 地址与 `ANTHROPIC_API_KEY` 仍在，`ANTHROPIC_AUTH_TOKEN` 被清空。此探测没有运行 CLI 的真实请求。

### 复查入口

- 在隔离的 Python 3.12 环境中选用对应 Harbor 版本，将 Dressage `3e3142f` 放到模块路径，从本目录运行 `python agent_connection_probe.py`。同一探测覆盖问题 06 的创建阶段和本页的启动命令。探测直接调用路由检查与注入函数，未放宽版本门禁或启动完整插件。
- 复现与对照　[注入后的配置](../09-trial-plan/trial-plan-output.txt) · [0.25 配置实验的输入与边界](../../../../references/agent-sandbox-harbor-compatibility.md#api-integration-harbor-025-check)
- 完整调用与配置　[plugin.py:1031](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1031-L1075) · [gateway.py:1107](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/gateway.py#L1107-L1126) · [claude_code.py:169](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/installed/claude_code.py#L169) · [认证变量的选择](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/installed/claude_code.py#L285-L300)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#runtime) · [返回问题索引](../../README.md#investigations)
