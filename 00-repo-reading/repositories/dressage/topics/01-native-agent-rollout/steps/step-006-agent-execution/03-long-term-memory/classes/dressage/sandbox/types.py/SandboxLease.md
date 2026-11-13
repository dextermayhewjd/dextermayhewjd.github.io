# SandboxLease

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../step-005-agent-registration/03-long-term-memory/classes/dressage/sandbox/types.py/SandboxLease.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

> 阅读位置：[init 的创建与等待](../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#acquire-environment) → **SandboxLease** → [其中的服务入口](#endpoint) → 返回 init，准备 [SandboxState](../../paddock/blackbox/common/state.py/SandboxState.md)。

- 源码定位：[dressage/sandbox/types.py:55–76](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/types.py#L55)，数据类，由助手核对。
- 首次接触：Step 001，先通过 provider.create 的返回类型定位，2026-11-05 开始独立阅读。
- 最近认识更新：2026-11-05，用户明确已看过 SandboxEndpoint，并提出继续 get_public_url；Lease 的整体关系仍允许按需回顾，不把看过记录为全部掌握。

## 1. 对象职责

SandboxLease 是 provider 交回的沙箱环境记录。它让调用方知道本次取得了哪个环境、有哪些服务入口和能力，并保留后续操作或释放资源需要的 provider 资料。

> 先把 SandboxLease 理解为“本次沙箱的领用记录”。spec 说明想要哪种环境，lease 说明这次具体分到了哪一个环境，以及怎样访问、管理和释放它。
>
> 例如相同镜像可以生成 sandbox-A 与 sandbox-B 两个环境，它们的镜像相同，但各有对应的 lease。lease 是 Python 数据对象，实际沙箱在它记录的后端资源中，不在这个对象里面。

变量 create_task 保存执行 provider.create(spec) 的 Task；正常等待结束后，lease 接住该调用返回的 SandboxLease。shield 只影响取消传播，不改变返回值类型。

### 先用一次实际环境分配来理解

假设 spec 表达“需要一种指定镜像/模板的环境”。provider 接收请求后，实际创建或分配了一个环境，编号为 sandbox-42。它返回的 lease 描述的是这次分配的结果，而不仅是重复返回镜像配置。

教学示意（不是实际运行输出）：

```python
lease.sandbox_id  # "sandbox-42"
lease.endpoints["blackbox"].url  # "https://sandbox-42.example"
```

1. **访问这个环境**：init 从 lease 取服务入口，继续健康检查与 state 整理。create 返回不代表所有后续健康/任务准备已完成。
2. **记住这次分配**：Paddock 将完整 lease 保存在自己的 _leases[traj_id]，后面仍能找到它。
3. **释放这个环境**：Paddock 最终把 lease 传给 provider.terminate(lease)，provider 根据其中的标识或自己保存的对应关系释放资源。

因此 spec 是“申请什么”，lease 是“实际分给了哪个环境，以及怎样管理它”。lease 自身是数据记录，不会自动执行命令或释放环境，也不是实体沙箱。

## 2. 字段总览

| 字段 | 默认值 | 本轮先理解的用途 |
| --- | --- | --- |
| trajectory_id | 必填 | 关联本次执行 |
| provider | 必填 | provider 名称字符串，例如 e2b 或 local_bwrap；不是 provider 对象或服务 URL |
| sandbox_id | None | provider 给出的环境或租用标识，便于后续操作 |
| endpoints | 新空字典 | 服务名 → SandboxEndpoint；当前 init 查找其中的 blackbox |
| capabilities | 新空集合 | provider 报告的能力，例如 command、file、public_url |
| metadata | 新空字典 | provider 补充的环境资料；不同于创建请求中固定的 paddock_mode 字段 |
| raw | None | provider 相关的原始对象或返回数据，供具体后端后续操作使用 |

字段声明原文，省略本类的 endpoint 辅助方法：

```python
@dataclass
class SandboxLease:
    """Provider-neutral sandbox lease returned from ``SandboxProvider.create``."""

    trajectory_id: str
    provider: str
    sandbox_id: str | None = None
    endpoints: dict[str, SandboxEndpoint] = field(default_factory=dict)
    capabilities: set[SandboxCapability] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)
    raw: Any | None = None
```

init 当前直接调用 lease.endpoints.get("blackbox")，没有调用 lease.endpoint(...)；因此本轮只看字段与交接。

<a id="endpoint"></a>

### 2.1 SandboxEndpoint：记录怎样访问某项服务

字段声明原文，省略 normalized 方法：

```python
@dataclass(frozen=True)
class SandboxEndpoint:
    """Public endpoint for a sandbox service.

    ``headers`` travels with the endpoint because remote providers may expose a
    URL that requires authentication or provider-specific forwarding headers.
    """

    url: str
    headers: dict[str, str] = field(default_factory=dict)
```

1. url 是沙箱所提供服务的访问入口。当前 blackbox 入口用于健康检查、Agent 注册与交互，不是 provider 的“创建沙箱”管理接口。
2. headers 保存访问该入口可能需要的认证或转发请求头；它与 url 一起使用。
3. URL 可以经过 provider 的网关或代理，不必直接等于沙箱 IP；判断的是请求最终访问哪项服务，而不是域名看起来属于谁。
4. normalized 只整理 URL 尾部斜杠并复制 headers。这里不展开网络部署。

本轮已进入返回它的 [LocalBwrapSandboxProvider.create](../../../../../../step-004-paddock-environment-preparation/references/local-bwrap-create.md)；可在那里对照 payload 与 lease 的字段映射，再回本卡查看字段。

## 3. 与 init 的交接

lease 与 state 为何同时保留、怎样互相关联，见 [SandboxState 的对照说明](../../paddock/blackbox/common/state.py/SandboxState.md#lease-state-relation)。


1. provider.create(spec) 正常完成，init 得到 lease。不同后端的构造方式不同：E2B 记录 SDK 环境对象；local_bwrap 记录管理器的领取结果。本轮只核对返回字段，没有展开完整实现。
2. init 读取 lease.endpoints["blackbox"] 对应的入口；没有现成入口时调用 provider.get_public_url 补齐。
3. init 用 lease.sandbox_id 和 endpoint.url 等信息构造 SandboxState。
4. Paddock 同时保留 self._leases[traj_id] 与 self._states[traj_id]。返回 state 后仍保留 lease，后续可能需要完整 endpoint 的 headers 或 provider 原始资料。

**读完返回**：[init 第 2 段](../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#acquire-environment)，继续读 endpoint 取得与健康检查；然后进入 [state 构造段](../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#return-state)。

## 4. 我的直接表述（原话）

2026-11-06 回顾时的疑问：

> 等一下 我需要了解和知道的是
> 这里的lease到底是在做什么?
> 或者说
> 我知道这里的在做的内容是通过这个spec
> 拿到了这个sandbox的image等一系列的meta data
> 然后呢?
> 我需要知道什么?
> 我的意思是当前情况下的这个lease到底是什么

助手补充了“需求配置 → 实际分配环境 → 管理记录”的例子，用户尚未确认理解。下面保留原有讨论。


本轮问题节选：

> 以及为什么下面还有一个lease我没有理解
> end_point
> 这里的url应该是还是如何访问这个provider
> 不是sandbox
> 而是provider?

> 当前这一步是否需要单独看清楚这个lease到底是什么?

这是对对象身份及访问目标的疑问。助手校准见上文，理解反馈待记录；完整原话见[本轮过程](../../../../../../step-004-paddock-environment-preparation/04-flow.md#lease-state-and-shield)。

用户后续明确：

> 好的我看过了的这里的sandboxendpoint了

本轮接续见 [get_public_url 方法卡](../../../../functions/dressage/sandbox/provider.py/SandboxProvider.get_public_url.md)，保留已看过的事实。

本轮后续表述：

> 好的 我简单的理解就是这里的一个provider 返回的内容
> 也就是这样子通过这个lease 返回的和sandbox相关的内容
> 虽然我不清楚这个sandboxlease应该要怎么去理解

助手补充“本次沙箱的领用记录”的理解方式：区分环境种类与实际分配实例；尚待用户反馈。

## 5. 尚不清楚

1. 具体 provider 怎样创建或领取环境、生成 URL，尚未展开完整过程。
2. raw、metadata 和 capabilities 在各后端后续操作中的细节，按实际问题再读。
3. 用户对 lease 与 endpoint 的校准理解，待后续反馈。

<details>
<summary>来源与验证边界</summary>

- 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；消费处 paddock/blackbox/paddock.py:86–151。
- 返回记录的字段核对：[local_bwrap provider](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/local/bwrap/provider.py#L69)、[E2B provider](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/remote/e2b/provider.py#L129)。仅作返回类型证据，不表示已阅读完整创建实现。
- 服务目标核对：[BlackboxServerClient.health](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L49)；完整入口优先从 lease 取的依据：[Paddock._endpoint_for_state](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L311)。
- 静态核对，没有实际创建沙箱或访问 URL；当前 provider 和实际地址未取得。

</details>
