> Step 011 继承：来自 [Step 010 完整记录](../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/sandbox/provider.py/SandboxProvider.get_public_url.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/dressage/sandbox/provider.py/SandboxProvider.get_public_url.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/dressage/sandbox/provider.py/SandboxProvider.get_public_url.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/sandbox/provider.py/SandboxProvider.get_public_url.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/dressage/sandbox/provider.py/SandboxProvider.get_public_url.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/dressage/sandbox/provider.py/SandboxProvider.get_public_url.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/dressage/sandbox/provider.py/SandboxProvider.get_public_url.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# SandboxProvider.get_public_url

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/03-long-term-memory/functions/dressage/sandbox/provider.py/SandboxProvider.get_public_url.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../../../01-native-agent-rollout/steps/step-005-agent-registration/03-long-term-memory/functions/dressage/sandbox/provider.py/SandboxProvider.get_public_url.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

> 阅读位置：[Step 004（原 001） 的 2.2](../../../../../../../../01-native-agent-rollout/steps/step-004-paddock-environment-preparation/01-scope.md#reading-navigation) → [init 的服务入口读取](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#acquire-environment) → **get_public_url**（仅入口缺失时） → 返回 init，回填入口并按配置检查健康。

- 源码定位：[dressage/sandbox/provider.py:26–33](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/provider.py#L26)，记录的是共同接口声明，实际操作由具体 provider 实现。
- 首次接触：Step 001 的 init 分支与接口总览；2026-11-05 开始独立方法记录。
- 最近认识更新：2026-11-05，用户指出 SandboxLease 已包含 endpoint，并将 get_public_url 的用途概括为“拿到一个 endpoint”；更细的条件分支、参数与失败语义不据此推定全部掌握。

## LLM 整理：使用场合、具体内容与心智模型

以下由助手按接口和真实调用处整理。

1. **使用场合**：create 已返回 lease，但 init 没有从 lease.endpoints 中取得 blackbox 入口，需要向同一个 provider 补取服务地址。

2. **具体内容**：输入已有 lease、服务端口和可选服务名，约定返回 SandboxEndpoint。后端如何查询、暴露或转发该入口属于具体实现，本页只读共同交接。

3. **建议构建的心智模型**：

   > create 取得环境记录；get_public_url 回答“怎样访问这个环境中的指定服务”。
   >
   > 返回的是含 url 和 headers 的 Endpoint 对象，不只是一个字符串；取得入口也不等同于健康检查通过。

4. **调用代码**：以下是 Paddock.init:106–116 的连续原文，仅减少外层缩进。前一步已经得到 lease。

   ```python
   endpoint = lease.endpoints.get("blackbox")
   if endpoint is None:
       endpoint = await self._provider.get_public_url(
           lease,
           port=spec.services[0].port,
           service_name="blackbox",
       )
       lease.endpoints["blackbox"] = endpoint
   endpoint = endpoint.normalized()
   if self._wait_health:
       await self._client.health(endpoint)
   ```

   1. 先尝试复用 lease 中现成的 blackbox 入口。
   2. 仅当结果是 None 时调用 get_public_url，并把返回对象存回 lease.endpoints。
   3. 两条路径汇合后才整理 endpoint，并根据开关请求健康检查。

## 本场景的输入与输出

本场景选择“create 成功返回 lease，但 blackbox 入口缺失”的分支。用户已看过 Endpoint，本页只提醒它与 Lease 的包含关系；没有实际运行 provider 或取得真实 URL。

### 1. 完整接口声明

```python
async def get_public_url(
    self,
    lease: SandboxLease,
    *,
    port: int,
    service_name: str | None = None,
) -> SandboxEndpoint:
    """Return a public endpoint for a service/port in the sandbox."""
```

这是 Protocol 方法声明，不能从这个方法体读到 Kubernetes、E2B 或本地网络的实现。

### 2. 输入：已有环境与目标服务

| 参数 | 本次实参 | 用途 |
| --- | --- | --- |
| self | Paddock 持有的具体 provider 实例 | 找到提供这个环境的后端 |
| lease | 上一次 create 返回的 SandboxLease | 指向已有环境，保留资源标识和后端操作资料 |
| port | spec.services[0].port | 此次黑盒服务需求指定的端口 |
| service_name | "blackbox" | 指明要取得哪项服务的入口；协议允许省略为 None，但当前调用显式传入 |

[SandboxLease](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/classes/dressage/sandbox/types.py/SandboxLease.md) 是一份环境记录，包含身份、能力、后端资料以及可能已经存在的 endpoints；[SandboxEndpoint](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/classes/dressage/sandbox/types.py/SandboxLease.md#endpoint) 则只描述其中一项服务的访问方式。

### 3. 输出：该服务的访问入口

| 返回对象的字段 | 本次用途 |
| --- | --- |
| endpoint.url | 供调用方访问本次沙箱的 blackbox 服务；不是创建沙箱的管理 API |
| endpoint.headers | 访问入口时可能需要的认证或转发请求头，可为空字典 |

方法名称中的 public 不要求地址一定能从互联网匿名访问，也不要求它直接等于 Pod IP。连接方式和可达范围由后端实现及部署网络决定。

### 4. 返回之后由谁继续处理

1. **调用方回填入口**：lease.endpoints["blackbox"] = endpoint 是 init 中的语句，不能仅凭接口声明推定所有实现会自行回填。
2. **调用方整理对象**：endpoint.normalized() 整理 URL 尾部斜杠并复制 headers，没有发起健康请求。
3. **调用方检查服务**：启用 _wait_health 时，再由 BlackboxServerClient 请求 /health。取得 URL 和服务健康是两件事。
4. **调用方构造 state**：随后使用 endpoint.url 与 lease 的标识构造 SandboxState，交回 generate。

如果 lease 一开始已经带着 blackbox 入口，就跳过 get_public_url，但仍会走后面的整理与可选健康检查。本方法使用已有 lease，不负责重新申请一个不同的沙箱；入口如何形成可能涉及查询或网络配置，不能假定所有实现都是纯读操作。

<details>
<summary>失败边界与具体实现的深度</summary>

- 若取得入口时抛出异常，当前 init 已经持有 lease，外层异常处理会安排相应环境清理；具体代码回查 init，不在这里增加后端实现任务。
- 共同协议不保证每个后端都具备同样的公网暴露能力，也不定义 URL 的具体格式。
- 本轮不展开 Ray 池、E2B SDK 或 Kubernetes Service/Ingress 的实现；完整 local_bwrap 例子继续在 references。

</details>

**读完返回**：[init 第 2 段](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#acquire-environment)，先看入口回填、normalized 和条件健康检查，再到 [state 构造段](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#return-state)。

## 我的直接表述（原话）

用户说：

> 好的那么这里我需要在看一下这个sandboxLease是什么?
> 好的我看过了的这里的sandboxendpoint了
> 那么我们继续吧
> 下一步是否是这里的get public url了呢?
> 用来看清楚这里的provider

记录为已看过 Endpoint，并开始阅读这个接口。Lease 如需回顾可从本页链接返回；尚不将“看过”标记为掌握所有字段和网络行为。

用户随后补充：

> 但是我记得sandboxlease里面有sandboxendpoint的部分?
> 好的我理解了
> 这里只是需要拿到一个endpoint
> 好的那么我们继续吧

已记录用户对用途的概括；助手继续强调先复用已有入口、缺失时才补取，然后返回 init 整理入口与检查健康。详见[本轮返回记录](../../../../../../../../01-native-agent-rollout/steps/step-004-paddock-environment-preparation/04-flow.md#endpoint-return-and-health)。

## 尚不清楚

1. 用户已概括取得 endpoint 的用途；条件分支和调用方回填等精确关系继续按后续表述确认。
2. 具体后端怎样取得可达 URL、维护访问权限及处理失效入口，暂不展开。
3. get_public_url 返回后健康检查和 state 的具体交接，沿 init 继续确认。

<details>
<summary>来源与验证范围</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。共同声明见上述源码；调用来自 paddock/blackbox/paddock.py:106–116。
- Endpoint 字段与 normalized 位于 sandbox/types.py:40–51；异常后的清理位于 paddock/blackbox/paddock.py:131–147。
- [Step 004（原 001） 本次记录](../../../../../../../../01-native-agent-rollout/steps/step-004-paddock-environment-preparation/04-flow.md#get-public-url-contract)。仍在环境准备步骤中，不创建新 Step，不把具体后端实现恢复为当前必读。
- 静态核对，没有运行网络、创建环境或发起健康检查。

</details>
