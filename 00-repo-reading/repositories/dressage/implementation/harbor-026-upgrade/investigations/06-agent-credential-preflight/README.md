# 06 · 插件写入路由凭证之前，Harbor 会不会拒绝创建 Job？

**当前判断**　随仓 Claude Code + Qwen 配置在 0.26 能创建 Job。若指定缺失的密钥变量，或给 Claude Code 指定 OpenRouter 模型却未提供该连接的凭证、地址，0.26 会在插件启动前拒绝创建 Job。相同输入在 0.18 能进入插件注入阶段。

**对应的三版用法表**　[U14 Job.create 在插件设置路由前创建 Job](../../usage/Job%20与%20Agent%20路由/U14-Job.create%20在插件设置路由前创建%20Job.md#u14) · [原套件在本问题测到了哪里](../original-test-audit.md#i06)

Dressage 在 Job 创建后才写 Trial 路由凭证，需要确定创建阶段会不会提前拦下目标配置。

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　`_run_partition` 先创建 Job。[rollout.py 第 704 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L704)

```python
job = await _CREATE_JOB(job_config)
```

**Dressage 3e3142f**　同一函数稍后启动插件并执行 Job。[rollout.py 第 759–762 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L759-L762)

```python
try:
    await plugin.on_job_start(job)
    result = await job.run()
    await plugin.on_job_end(result)
```

**Harbor 0.26.0**　普通本地 Job.create 在解析任务前检查 Agent。[job.py 第 181–183 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L181-L183)

```python
if not config.source_jobs:
    cls._preflight_agents(config, config.agents)
task_configs = await cls._resolve_task_configs(config)
```

**据此判断**　凭证预检在插件注入路由之前发生。检测顺序成立，但某一组配置会不会被拒绝，还取决于具体的 Agent 和模型设置。

<a id="evidence"></a>

## 证据与验证范围

**已存输出**　子进程没有模型厂商凭证变量，输入三种本地 Agent／模型组合。[job-lock-output.txt 第 11–14 行](../10-job-lock/job-lock-output.txt#L11-L14)

```text
Harbor 0.26.0
claude-code | MiniMax-M3 | Job.create succeeded | lock schema 3
claude-code | Qwen/Qwen3.5-4B | Job.create succeeded | lock schema 3
codex | openai/gpt-4o | Job.create succeeded | lock schema 3
```

三种输入都创建了 Job。CLI 帮助中的 credential-mode 适用于 Hub launch 路径。

第二轮在隔离的进程环境中创建本地 Job，仅提供实验用的合成变量。Claude Code + `anthropic/claude-sonnet-4-5` 显式选择不存在的 `PROBE_MISSING_KEY` 时，0.26 在连接解析阶段抛出 `MissingModelCredentialError`。Claude Code + `openrouter/anthropic/claude-sonnet-4.5` 使用默认 endpoint、未提供该连接的凭证时，0.26 在 Agent 凭证检查阶段抛出同类异常。两个 Job 均未返回，插件没有机会注入 Trial 凭证。0.18 对两份配置都返回 Job；当时的 AgentConfig 没有 `model_api_key_name` 字段。[0.18 输出](../07-agent-routing/agent-connection-0.18.txt#L5-L7) · [0.26 输出](../07-agent-routing/agent-connection-0.26.txt#L5-L7) · [0.26 AgentFactory 预检](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/agents/factory.py#L183-L199) · [Claude Code 对外部模型的检查](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/agents/installed/claude_code.py#L135-L143)

随仓 CLI 的 `--yes` 仅自动确认提示。0.26 在 `Job.create` 返回后、插件挂接前，还会扫描题目中生效的 HTTP MCP server 请求头模板；若需要的宿主环境变量缺失且无默认值，会先退出。这个条件按源码核对，随仓 YAML 本身没有声明这些请求头，远程题目是否触发仍待验证。[题目模板来源](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/cli/jobs.py#L204-L222) · [缺失变量与确认的先后](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/cli/jobs.py#L253-L287) · [CLI 挂接顺序](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/cli/jobs.py#L2367-L2377)

## 处理与验收

**下一步**　为承诺支持的模型和 Agent 列出允许的连接参数，保存上述两个预检失败用例。若要求支持只能由插件提供凭证的外部模型，需要在 Job 创建前解决该配置的凭证检查。

**通过条件**　支持的组合能进入插件。对于声明必须提供凭证的配置，缺失凭证时观察到预期拒绝。实际 harness 请求独立验证。[问题 07](../07-agent-routing/README.md)

<a id="history"></a>

## 判断记录

- 2026-11-18　在清空宿主凭证的临时环境中，Claude Code + MiniMax-M3、Claude Code + Qwen/Qwen3.5-4B、Codex + openai/gpt-4o 均能在 0.25 和 0.26 创建本地 Job。Qwen 组合有模型识别警告。模型名只是该轮验证的输入，结论止于 Job 创建。

### 复查入口

- 复现与对照　[本地 Job 探测](../10-job-lock/probe.py) · [三版输出](../10-job-lock/job-lock-output.txt) · [CLI 帮助摘录](cli-help-excerpts.txt)
- 完整调用与配置　[rollout.py:505](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L505-L579) · [plugin.py:261](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L261) · [job.py:148](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/job.py#L148-L185) · [cli/jobs.py:113](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/cli/jobs.py#L113)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#job) · [返回问题索引](../../README.md#investigations)
