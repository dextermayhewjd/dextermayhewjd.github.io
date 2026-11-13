> Step 011 继承：来自 [Step 010 完整记录](../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/classes/dressage/sandbox/provider.py/SandboxProvider.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/classes/dressage/sandbox/provider.py/SandboxProvider.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/classes/dressage/sandbox/provider.py/SandboxProvider.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/03-long-term-memory/classes/dressage/sandbox/provider.py/SandboxProvider.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# SandboxProvider

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/03-long-term-memory/classes/dressage/sandbox/provider.py/SandboxProvider.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../../../01-native-agent-rollout/steps/step-005-agent-registration/03-long-term-memory/classes/dressage/sandbox/provider.py/SandboxProvider.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

> 阅读位置：[Step 004（原 001） 的 2.1](../../../../../../../../01-native-agent-rollout/steps/step-004-paddock-environment-preparation/01-scope.md#reading-navigation) → [init 中的环境取得](../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#acquire-environment) → **SandboxProvider 共同约定** → 返回 init，继续 endpoint 与 state。

- 源码定位：[dressage/sandbox/provider.py:15](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/provider.py#L15)，记录对象是 Protocol 接口，不是创建环境的具体实现。
- 首次接触：2026-11-05，Step 001 中通过 provider.create 读取接口；本轮将已有共同说明整理为独立卡。
- 最近认识更新：2026-11-05，用户已概括 Protocol 的结构化接口含义并列出六项方法，要求以调用侧代码作为主例；行为保证、字段支持和异常处理未据此标为掌握。

## 1. 接口职责

SandboxProvider 规定环境后端需要提供的生命周期及基础操作。Paddock 面向这些接口调用具体 provider，得到资源记录和访问入口，再组织 Agent 交互。

> 上层说明需要什么环境；后端负责取得、访问和释放环境；双方通过 Spec、Lease、Endpoint 等数据类型交接。

Protocol 中的声明没有实现环境创建。创建或领取资源时实际运行的是传给 Paddock 的具体对象的方法。当前仓库公开提供 local_bwrap 和 e2b；Kubernetes 后端仍需另外实现与接入。

这里的“满足协议”是结构化接口匹配：具体类不必显式继承 SandboxProvider，但需要提供约定的 name 属性、方法及兼容的调用签名和返回类型。方法名齐全不等于实际行为一定正确，资源创建、就绪和清理仍须由实现兑现。Protocol 本身不会自动实现这些操作。

## 2. 接口总览

name 是后端名称属性。其余六项是操作接口，本轮重点看前三项：

| 接口 | 输入 → 返回 | 本轮关注点 |
| --- | --- | --- |
| [create](../../../../functions/dressage/sandbox/provider.py/SandboxProvider.create.md) | [SandboxSpec](../types.py/SandboxSpec.md) → [SandboxLease](../types.py/SandboxLease.md) | 接收环境需求，创建或领取资源，交付可供后续识别和操作的记录 |
| [get_public_url](../../../../functions/dressage/sandbox/provider.py/SandboxProvider.get_public_url.md) | lease、port、可选 service_name → SandboxEndpoint | 返回服务 URL 和必要 headers；入口不必等于 Pod IP 或公网地址 |
| terminate | lease 或其关联标识 → 结果字典 | 结束本次资源使用；具体后端可以销毁资源，也可以归还并重置池中环境 |
| run_command | lease、command 与执行选项 → CommandResult | 在环境中执行命令；本轮只定位用途 |
| read_file | lease、path 与编码选项 → str 或 bytes | 从环境读取文件；本轮不展开 |
| write_file | lease、path、content 与写入选项 → 结果字典 | 向环境写入文件；本轮不展开 |

源码节选，保留 name 与三个生命周期方法的完整声明，其余操作在上表定位：

```python
@runtime_checkable
class SandboxProvider(Protocol):
    """Provider-neutral sandbox capability surface."""

    name: str

    async def create(self, spec: SandboxSpec) -> SandboxLease:
        """Create or acquire a sandbox lease for one trajectory."""

    async def terminate(self, lease: SandboxLease | str) -> dict[str, Any]:
        """Terminate or release a sandbox lease."""

    async def get_public_url(
        self,
        lease: SandboxLease,
        *,
        port: int,
        service_name: str | None = None,
    ) -> SandboxEndpoint:
        """Return a public endpoint for a service/port in the sandbox."""
```

**接口签名之外，还要核对四件事：**

1. **支持哪些需求。** 每个 provider 实际消费哪些 spec 字段，需要核对实现；统一数据类型不保证所有可选配置在每个后端都生效。
2. **返回时准备到什么程度。** create 返回 lease 不自动证明服务已健康、题目已初始化。当前 Paddock 随后还会取得入口，并按配置请求 /health。
3. **怎样访问同一个环境。** lease 保存资源身份与管理资料，endpoint 提供访问方式；访问目标是沙箱服务，不是创建资源的管理 API。URL 可以经过代理或网关。
4. **失败后谁继续负责。** 没有正常收到 lease，不代表资源一定没有创建；调用方和后端需要明确取消、部分失败及释放责任。当前调用方的 shield 与后台接手见 [init 说明](../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#shield-create-cancellation)。

具体实现可能不满足全部理想条件。上述是阅读和对接时要核对的行为，不是仅凭 Protocol 就能保证的事实。

## 3. 与本轮 init 的交接

1. init 构造 spec，并用 Task 执行具体 provider.create(spec)。
2. create 正常完成，init 接住 lease，从中读取 blackbox 入口；缺少入口时调用 get_public_url。
3. init 按配置检查服务，再从 lease 和 endpoint 整理 [SandboxState](../../paddock/blackbox/common/state.py/SandboxState.md)，交回 generate。
4. 本次使用结束或取消时，生命周期清理通过 Paddock 和 provider 的释放路径收尾。create、状态交付与最终释放不是同一时刻。

Paddock 负责 Agent 注册和调用的组织；provider 提供环境基础能力。训练样本如何转换、如何计算奖励也不由这个接口规定。

create 的详细输入输出、就绪边界和 Paddock 调用侧主例见 [SandboxProvider.create 方法卡](../../../../functions/dressage/sandbox/provider.py/SandboxProvider.create.md)。完整 local_bwrap 实现继续保留在 references。

**读完返回**：[init 的环境取得段](../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#acquire-environment)，带着对 lease 和 endpoint 的理解，继续 [state 的构造与返回](../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#return-state)。

## 4. 我的直接表述（原话）

用户明确阅读重点：

> 我也觉得
> 这里应该看的内容是这个provider啊
> 不应该看过于具体的local bwrap或者只是取一下精髓我觉得会好很多对吧

随后询问取舍，并确认实施：

> 好的那么按照这样子实践吧

这是对学习范围和记录方式的确认。输入输出、就绪与失败责任是否已经理解，仍按之后的实际反馈记录。原始过程见[本轮整理](../../../../../../../../01-native-agent-rollout/steps/step-004-paddock-environment-preparation/04-flow.md#provider-implementation-to-reference)。

用户后续表述（节选）：

> 好的 我简单理解一下
> 这里是一个protocol
> 满足的都可以
> 其次这里需要有这几个2接口create terminate
> 还有get public rul 还有run command read file 还有write file等能力

助手补充 name 属性、结构匹配与实际行为保证的区别；用户提供的调用代码作为 create 方法卡主例。完整记录见[本轮过程](../../../../../../../../01-native-agent-rollout/steps/step-004-paddock-environment-preparation/04-flow.md#provider-usage-example)。

## 5. 尚不清楚

1. 用户对接口行为及资源所有权的具体理解，待后续反馈。
2. Kubernetes 后端怎样映射资源、判断就绪、提供访问入口并清理部分失败，当前仓库没有现成实现供直接阅读。
3. 各后端对可选字段、重复调用和取消的具体语义，未全面核对；local_bwrap 的完整调度不作为当前必读。

<details>
<summary>来源、记录分工与验证范围</summary>

- 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。共同接口来自 sandbox/provider.py；调用方来自 paddock/blackbox/paddock.py:64–151。
- 调用侧主例来自 paddock/blackbox/paddock.py:72–106；local_bwrap 字段映射和完整实现已放入 references，原话与来源保留。
- [Custom SandboxProvider 说明](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docs/blackbox-swegym-claude-code-experiment-zh.md#L188)提供自建平台的接入指引；其中 SWE-Gym 的特定初始化要求不扩写为所有任务的固定协议。公共工厂没有直接注册 k8s/custom 名称。
- 类卡集中维护接口总览，create 方法卡解释调用侧主例；init 卡保留自身流程；数据字段继续引用各自类卡。
- @runtime_checkable 允许做运行时协议检查，但不验证完整参数签名、类型与业务语义；不能把它当作资源管理行为正确的保证。
- 仅静态核对与文档整理，没有部署 Kubernetes、运行真实 provider 或验证端到端训练。

</details>
