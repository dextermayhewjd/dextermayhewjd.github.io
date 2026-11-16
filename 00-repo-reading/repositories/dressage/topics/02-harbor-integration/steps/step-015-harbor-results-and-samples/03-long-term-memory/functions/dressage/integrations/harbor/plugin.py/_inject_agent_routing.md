# _inject_agent_routing

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../../step-014-model-routing-and-api-contract/02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/_inject_agent_routing.md) 完整继承；不改变原认识时间或掌握状态。

- 源码：[dressage/integrations/harbor/plugin.py:1031–1074](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1031)，Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次单独展开：Step 014，2026-11-13。
- 最近认识更新：2026-11-13，用户表示大致理解地址改写；本轮进一步区分具体 URL 值、token 变量引用与回调函数对象。

[回查 _run_partition 的运行前准备](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#run-job) → [plugin.on_job_start](DressageHarborPlugin.on_job_start.md#job-start-routing) → **当前 _inject_agent_routing** → 写回 TrialConfig；以后创建 Agent 并运行 [ClaudeCode.run](../../../../harbor/agents/installed/claude_code.py/ClaudeCode.run.md#claude-run-mainline)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Job 执行前，Dressage 插件给 Harbor 各次尝试配置模型请求的目的地与路由身份。
2. **具体内容**：按协议修改 AgentConfig.env，按需覆盖模型名，并更新允许访问的主机名单。
3. **建议构建的心智模型**：

   > 先在 Agent 配置中写好“请求发给谁、属于哪次尝试”，之后由 Harbor 创建 Agent 并传到 CLI。

4. **调用代码**（[on_job_start 的配置注入段](DressageHarborPlugin.on_job_start.md#job-start-routing)，382–385，节选）：

   ```python
   # agent 是待写回的 AgentConfig 副本，token 先前由注册表产生。
   token = registry.current(slot_id)
   os.environ[env_name] = token  # 将真实令牌保存到命名的环境变量。
   _inject_agent_routing(agent, self.config, env_name, gateway_url)
   trial_config.agent = agent  # 把修改后的配置交回 Harbor。
   ```

## 本场景的输入与输出

当前沿用 Claude Code 的 Anthropic 路径。`agent` 是配置对象，`config` 是 Dressage 集成配置；`env_name` 是上方保存 token 的变量名，`advertise_url` 是要提供给 Agent 的 Gateway 地址。函数正常返回 None，就地更新配置。

<a id="inject-routing-mainline"></a>

下面保留地址与令牌注入主干；省略 OpenAI 分支、模型覆盖和主机名单处理，完整函数在下方。

```python
env = dict(getattr(agent, "env", {}) or {})
advertise_url = advertise_url.rstrip("/")
token_template = "${" + env_name + "}"  # 保存变量引用，稍后由 Harbor 解析出真实 token。
protocol = _agent_protocol(agent, config)

if protocol in {"anthropic", "both"}:
    env.update({
        "ANTHROPIC_API_KEY": token_template,    # Gateway 识别本次尝试的路由身份。
        "ANTHROPIC_AUTH_TOKEN": token_template,
        "ANTHROPIC_BASE_URL": advertise_url,   # CLI 的模型请求发到这个 Gateway 地址。
    })
agent.env = env  # 此处尚未启动 CLI，也未创建网络连接。
```

### Harbor 如何接住这份配置

```python
# Harbor AgentFactory.create_agent_from_config 中的真实语句：
extra_env = resolve_env_vars(config.env)  # 把 ${变量名} 解析成之前保存的令牌。
# 随后通过 extra_env=extra_env 创建具体 Agent。
```

后续进入已读的[执行阶段](../../../../harbor/trial/trial.py/Trial._run_agent_phase.md#run-agent-phase-mainline)与 [ClaudeCode.run](../../../../harbor/agents/installed/claude_code.py/ClaudeCode.run.md#claude-run-mainline)，这些配置被用于 CLI 的命令环境与模型连接。这里回查的是运行前配置，读完再接回 CLI 发请求的位置。

**收集边界**：CLI 必须实际使用这个地址，且所在环境能访问 Gateway。Proxy 能处理和记录经过它的模型请求/响应，其中可以包含提交给模型的消息和工具结果；未发送的内部状态、本地文件或绕过代理的请求不会因此被自动收集。

<details>
<summary>完整函数：其他协议、模型覆盖与允许主机</summary>

```python
def _inject_agent_routing(
    agent: Any,
    config: Any,
    env_name: str,
    advertise_url: str,
) -> None:
    env = dict(getattr(agent, "env", {}) or {})
    advertise_url = advertise_url.rstrip("/")
    token_template = "${" + env_name + "}"
    protocol = _agent_protocol(agent, config)
    if protocol in {"openai", "both"}:
        env.update({
            "OPENAI_API_KEY": token_template,
            "OPENAI_BASE_URL": f"{advertise_url}/v1",
        })
    if protocol in {"anthropic", "both"}:
        env.update({
            "ANTHROPIC_API_KEY": token_template,
            "ANTHROPIC_AUTH_TOKEN": token_template,
            "ANTHROPIC_BASE_URL": advertise_url,
        })
        model_override = _config_get(config, "training.model_override", None)
        if model_override:
            model = str(model_override)
            env.update(
                {
                    "ANTHROPIC_MODEL": model,
                    "ANTHROPIC_DEFAULT_SONNET_MODEL": model,
                    "ANTHROPIC_DEFAULT_OPUS_MODEL": model,
                    "ANTHROPIC_DEFAULT_HAIKU_MODEL": model,
                    "CLAUDE_CODE_SUBAGENT_MODEL": model,
                }
            )
    agent.env = env
    hostname = urlparse(advertise_url).hostname
    hosts = list(getattr(agent, "extra_allowed_hosts", None) or [])
    if hostname:
        if hostname not in hosts:
            hosts.append(hostname)
    for host in _config_get(config, "security.additional_agent_egress_hosts", ()) or ():
        normalized = str(host).strip()
        if normalized and normalized not in hosts:
            hosts.append(normalized)
    agent.extra_allowed_hosts = hosts
```

主机名单属于配置声明，不能单凭写入地址或名单就认定实际网络已连通。路由登记、激活与 Gateway 接收分派是后续各自的步骤。

</details>

## 我的直接表述（原话）

> 好的那么这里这个cli部分的base url是定好的
> 那么proxy是一开始dressage这里定好的 是我的理解
> 所以其实没有什么太大的问题?
> 无论agent在哪里
> 这里的agent的上下文都可以通过proxy那一层拦截
> 那么现在还是看一下这里是怎么在harbor这里做到的吧

助手校准：地址与路由确实由 Dressage 提前配置，但收集范围限于经过代理的模型交互；部署位置仍需满足地址可达。没有将“所有上下文都可自动拦截”记录为已核实结论。

本轮理解与追问（节选）：

> 不过这里的这个inject agent routing 写入的是引用
> 我的理解是改写base url啊 之类的

助手校准：BASE_URL 写入具体地址；API_KEY/AUTH_TOKEN 写入 `${环境变量名}` 引用。另一个层次的回调登记保存函数对象，不能把这三种值都理解成同一种“引用”。

## 尚不清楚

- token 对应的路由如何登记、激活，以及 Gateway 如何把请求交给 Proxy，后续再读。
- Harbor 模型连接配置与不同版本的完整兼容性、实际网络连通尚未验证。

<details>
<summary>来源与验证</summary>

- Dressage plugin.py:338–349 取得并复制 AgentConfig；382–385 保存 token、调用注入并写回 trial_config.agent；_gateway_public_url:1298 从配置或 Gateway 租约取得对外地址。
- Harbor v0.25.0 的 agents/factory.py:272 起，create_agent_from_config 先执行 resolve_env_vars(config.env)，再把 extra_env 交给构造函数；agents/base.py:172 保存为 _extra_env。本轮仅核对消费位置，不扩展工厂或凭证解析的完整阅读。
- 后续命令环境见已读 Trial._run_agent_phase 和 ClaudeCode.run；当前使用不同固定版本做静态接口对照，不代表 Dressage 对 Harbor 0.25 的运行适配已完成。
- 未读取或打印真实 token，未改变环境变量或执行网络请求；上述 os.environ 赋值仅为源码摘录。
- [本轮记录](../../../../../../../step-014-model-routing-and-api-contract/04-flow.md#inject-agent-routing-entry)。

</details>
