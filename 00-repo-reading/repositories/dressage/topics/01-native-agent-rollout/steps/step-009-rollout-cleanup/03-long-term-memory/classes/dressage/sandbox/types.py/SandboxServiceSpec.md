> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../step-008-segments-to-samples/03-long-term-memory/classes/dressage/sandbox/types.py/SandboxServiceSpec.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../step-007-proxy-finalization-and-trajectory/03-long-term-memory/classes/dressage/sandbox/types.py/SandboxServiceSpec.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# SandboxServiceSpec

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../step-006-agent-execution/03-long-term-memory/classes/dressage/sandbox/types.py/SandboxServiceSpec.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../step-005-agent-registration/03-long-term-memory/classes/dressage/sandbox/types.py/SandboxServiceSpec.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

> 阅读位置：[Step 004（原 001） scope](../../../../../../step-004-paddock-environment-preparation/01-scope.md#reading-navigation) → [init 构造 spec](../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#build-spec) → [SandboxSpec](SandboxSpec.md) 的 services → **SandboxServiceSpec**。读完回到外层 spec。

- 源码定位：[dressage/sandbox/types.py:18–23](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/types.py#L18)，记录对象是 dataclass，由助手核对。
- 首次接触：2026-11-05，Step 001 中从 init 的 services 参数回查；本轮建立独立类卡。
- 最近认识更新：2026-11-05，用户已联系到服务访问需求，但仍混合了后端选择、服务访问方向和实际地址；助手已补充这些区别，尚待后续反馈。

## 1. 对象职责

SandboxServiceSpec 描述沙箱中预期可访问的一项服务。当前 init 用它描述 blackbox 服务，再将实例放进外层 SandboxSpec.services 元组。

> 它记录“服务叫什么、用哪个端口、健康检查路径是什么”。构造这个对象不会直接启动服务或发起健康检查。

1. 它描述“沙箱中哪一项服务需要可访问”，当前为 blackbox 服务；不是在这里选择 E2B 或 local_bwrap，provider 已由 Paddock 的配置确定。
2. 这里保存 name、port、health_path，尚没有实际 URL。创建后 provider 返回的 endpoint 才携带 URL 和可能需要的请求头。
3. 当前使用方向是 Paddock 的客户端访问沙箱中的 BlackboxServer；不将它解释为一份“沙箱内部访问其他服务”的网络配置。

## 2. 字段总览

| 字段 | 默认值 | 当前 init 场景 |
| --- | --- | --- |
| name | 必填 | "blackbox"，这项服务的名字；后续 init 按同名键查找 lease.endpoints 中的入口 |
| port | 必填 | int(env_args.get("blackbox_port") or self._blackbox_port)，优先使用本次参数中的有效端口，否则使用 Paddock 的默认端口 |
| health_path | "/health" | 本次显式填 "/health"，作为服务健康检查路径的需求信息 |

完整类定义：

```python
@dataclass(frozen=True)
class SandboxServiceSpec:
    """A service expected to be reachable inside a sandbox."""

    name: str
    port: int
    health_path: str = "/health"
```

## 3. 与外层 spec 的交接

init 中的实际构造代码：

```python
SandboxServiceSpec(
    name="blackbox",
    port=int(env_args.get("blackbox_port") or self._blackbox_port),
    health_path="/health",
)
```

1. 上述表达式得到一个服务描述对象。原源码没有给它另取局部变量名，而是直接将它放入 SandboxSpec 的 services 参数。
2. 外层 spec 将这项服务需求一起交给 provider.create；如何提供访问入口由 provider 实现。
3. provider 返回之后，init 才尝试读取 lease.endpoints["blackbox"]。健康检查是后续 self._client.health(endpoint) 的动作，不是这个数据类自动执行的行为。

**读完返回**：[SandboxSpec 的 services 字段](SandboxSpec.md) → [init 第 1 段](../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#build-spec)。服务描述与其他环境参数共同组成一次请求，再继续 provider.create。

## 4. 我的直接表述（原话）

用户在 init 中询问：

> 但是这里是否需要单独看一下sandboxspec和这里的sandboxservicespec是什么呢?

随后请求：

> 好的 那么是否考虑一下构建一下这里的class相关的short term memory呢?
> 会不会更加好一点?

这是此前的阅读与建卡请求。完整讨论见[前一次阅读问题](../../../../../../step-004-paddock-environment-preparation/04-flow.md#spec-and-provider-reading-depth)与[本次记录](../../../../../../step-004-paddock-environment-preparation/04-flow.md#spec-class-cards)。

2026-11-05 的进一步复述（节选）：

> 还有sandboxservicespec是提供的 具体运行什么后端的sandbox对吗?

> 然后这里的service spec反而是具体应该如何访问这个sandbox 如何在sandbox环境中访问这个服务是我的理解

这是对对象职责的实际表达，含有仍需校准的后端选择与访问含义；上面的三项说明由助手核对。完整记录见[本轮讨论](../../../../../../step-004-paddock-environment-preparation/04-flow.md#spec-understanding-and-return)。

## 5. 尚不清楚

1. provider 怎样根据服务描述启动或暴露服务，尚未展开。
2. 服务名称、端口与返回 endpoint 的具体对应过程，只按 init 的输入输出定位，未读某个后端实现。
3. “服务描述不选择 provider”“需求里尚无实际地址”的区别，已补充说明，用户理解反馈待记录。dataclass 语法继续不作为本轮主读内容。

<details>
<summary>来源与验证范围</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c；构造位于 [paddock.py:76–82](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L76)，入口读取和健康请求位于 106–116 行。
- 本类是 frozen dataclass，只有三个字段，没有手写的创建环境方法。其使用方式与 provider 的具体服务准备流程分开判断。
- 沿用已有 Session 类卡栏目；静态核对类定义和构造表达式，没有运行服务或发起健康请求。

</details>
