# 15 · Harbor 切换 Web 工具状态会怎样影响 Agent 启动？

**当前判断**　沿用 Harbor 的 Web 工具开关。目标 harness 在受限网络下的启动和请求仍待验证。

**对应的三版用法表**　[U59 受限网络时 Harbor 配置 Agent 的 Web 工具](../../usage/题目文件与可选后端/U59-受限网络时%20Harbor%20配置%20Agent%20的%20Web%20工具.md#u59) · [原套件在本问题测到了哪里](../original-test-audit.md#i15)

同一次 Agent 运行既有 Web 工具策略，也要向本地 Gateway 发模型请求，需要分别观察两者。

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　插件把 Gateway 主机加入 Agent 的允许列表。[plugin.py 第 1065–1069 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1065-L1069)

```python
hostname = urlparse(advertise_url).hostname
hosts = list(getattr(agent, "extra_allowed_hosts", None) or [])
if hostname:
    if hostname not in hosts:
        hosts.append(hostname)
```

**Harbor 0.26.0**　Trial 根据网络策略调用 Agent 的 Web 工具开关。[trial.py 第 703–705 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L703-L705)

```python
async def _configure_web_tools(self, policy: NetworkPolicy) -> None:
    disabled = policy.network_mode != NetworkMode.PUBLIC
    await self.agent.set_web_tools_disabled(disabled, self.agent_environment)
```

**据此判断**　网络允许列表与 harness 的 Web 工具开关由两个入口处理。实际启动时还会考虑 harness 的能力和显式设置。

<a id="evidence"></a>

## 证据与验证范围

**Harbor 的条件原文 · Harbor 0.26.0**　存在显式 `disable_web_search` 配置时，基础类会调整从策略传来的 disabled。[base.py 第 200–204 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/agents/base.py#L200-L204)

```python
"""Default native web tools from rollout policy unless explicitly configured."""
disabled = (
    disabled and "disable_web_search" not in self._model_connection_kwargs
)
if not self.capabilities.native_web_tools:
```

目前能确认调用和覆盖条件。尚缺目标 harness 最终收到的启动参数，以及在这组设置下到达 Gateway 的请求记录。

## 处理与验收

**下一步**　挑选 PR 实际支持的一个 harness，在受限任务记录 Harbor 传入的标志与 harness 生效的选项，完成一次本地启动和普通模型请求。[问题 14 的策略来源](../14-phase-network-policy/README.md)

**通过条件**　开关行为与该 harness 的能力、显式配置一致，启动成功，普通模型请求走向预期 Gateway。[插件执行用例](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_execution.py#L64)

<a id="history"></a>

## 判断记录

- 2026-11-18　源码确认两版都有这个调用。目前没有观察到独立的 Dressage 工具开关故障。

### 复查入口

- 复现与对照　[0.25 调用位置](https://github.com/harbor-framework/harbor/blob/v0.25.0/src/harbor/trial/trial.py#L692-L699) · [0.26 调用位置](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/trial/trial.py#L700-L709)
- 完整调用与配置　[plugin.py:261](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L261) · [注入 Gateway 配置](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1031-L1075) · [trial.py:703](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/trial/trial.py#L703-L709) · [agents/base.py:197](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/base.py#L197)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#network) · [返回问题索引](../../README.md#investigations)
