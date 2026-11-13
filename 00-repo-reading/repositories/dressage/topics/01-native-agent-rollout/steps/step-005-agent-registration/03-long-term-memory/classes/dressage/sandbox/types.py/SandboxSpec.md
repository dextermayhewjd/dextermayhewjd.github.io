# SandboxSpec

> 阅读位置：[Step 004（原 001） scope](../../../../../../step-004-paddock-environment-preparation/01-scope.md#reading-navigation) → [init 构造 spec](../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#build-spec) → **SandboxSpec** → [SandboxServiceSpec](SandboxServiceSpec.md)。读完返回 init，将 spec 交给 provider。

- 源码定位：[dressage/sandbox/types.py:27–36](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/types.py#L27)，记录对象是 dataclass，由助手核对。
- 首次接触：2026-11-05，Step 001 中为理解 init 构造环境需求而回查；本轮建立独立类卡。
- 最近认识更新：2026-11-05，用户已将 SandboxSpec 概括为“用来做什么、怎样的一个 sandbox”，并列出执行归属、环境类型、参数和超时；trajectory_id、metadata 与服务描述的精确含义由助手补充，尚待反馈。

## 1. 对象职责

SandboxSpec 保存一次创建或取得沙箱的请求，包括执行归属、环境配置和需要访问的服务。init 构造实例并赋给 spec，再把它交给 provider.create。

> spec 表达“本次需要什么环境”；它自身不创建环境。provider 消费这份请求并返回环境记录 lease。

## 2. 字段总览

下表沿用当前 init 调用场景；具体运行时值没有取得。

| 字段 | 默认值 | 本次 init 怎样填写、表示什么 |
| --- | --- | --- |
| trajectory_id | 必填 | traj_id，来自 generate 传入的 session_id，是本次执行/轨迹的关联标识；不是轨迹内容本身，也不只是收集信息时才使用 |
| env_type | None | 传入的 env_type，作为环境类型提示交给 provider |
| env_args | 新空字典 | 本次传入 init 合并后的环境参数；具体配置由 provider 解释 |
| services | 空元组 | 本次填入一个 SandboxServiceSpec，描述 blackbox 服务的端口和健康检查路径 |
| timeout_sec | None | env_args.get("sandbox_timeout_sec")，提供沙箱超时配置 |
| metadata | 新空字典 | 本次填写 {"paddock_mode": "blackbox"}，标记 Paddock 的工作模式；用途由使用方约定，不是把整个任务 metadata 或轨迹复制进来 |
| env | 新空字典 | 环境变量配置；本次 init 未传此项，保留默认空字典 |

完整类定义：

```python
@dataclass(frozen=True)
class SandboxSpec:
    """Sandbox creation request shared by local and remote providers."""

    trajectory_id: str
    env_type: str | None = None
    env_args: dict[str, Any] = field(default_factory=dict)
    services: tuple[SandboxServiceSpec, ...] = ()
    timeout_sec: float | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)
```

1. 默认值说明的是“未传该参数时”；本次显式传入的 env_args、services 和 metadata 使用调用方提供的值。
2. services 中每个元素是[服务需求描述](SandboxServiceSpec.md)，不是已运行的服务对象。本次元组只有一个元素，也仍然只描述一次沙箱请求。

## 3. 与 init 和 provider 的交接

1. [init 的第 1 段](../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#build-spec)先整理 env_args，构造内层 SandboxServiceSpec，再构造外层 SandboxSpec；完整调用参数保留在 init 卡。
2. 构造结束得到 spec。此时只是 Python 进程中的请求数据，尚未获得 sandbox_id 或服务 URL。
3. [init 的第 2 段](../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#acquire-environment)执行 provider.create(spec)，等待返回 SandboxLease。实际创建取决于配置的 provider，不由这个数据类实现。

**读完返回**：回到 [init 构造 spec 的位置](../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#build-spec)，确认字段来源后继续看 create 如何接收 spec。

## 4. 我的直接表述（原话）

用户对当前构造动作的理解：

> 我的理解是这个首先根据环境信息给出这里的应该怎么造这里的sandboxspec

随后请求类级记录：

> 好的 那么是否考虑一下构建一下这里的class相关的short term memory呢?
> 会不会更加好一点?

前一条概括构造用途，后一条是记录方式的请求；不能据此推定已经理解全部字段。完整语境见[前一次讨论](../../../../../../step-004-paddock-environment-preparation/04-flow.md#spec-and-provider-reading-depth)与[本次建卡记录](../../../../../../step-004-paddock-environment-preparation/04-flow.md#spec-class-cards)。

2026-11-05 的进一步复述（节选）：

> 主要提取的抽象应该是
> 这个sandbox 是用来做什么的sandbox和怎样的一个sandbox

用户同时询问：

> 1.这个trajectory具体是什么(用于日后收集信息吧)

> 还有这里的metadata到底记录什么是什么

完整复述和返回位置见[本轮记录](../../../../../../step-004-paddock-environment-preparation/04-flow.md#spec-understanding-and-return)。字段表中的精确说明属于助手源码核对，未据此认定用户已接受全部校准。

## 5. 尚不清楚

1. env_type、env_args 在具体 provider 中怎样解释，尚未展开。
2. 不同 provider 怎样落实 services、超时及环境变量，尚未展开。
3. 用户已概括环境请求的整体作用；trajectory_id 是关联标识、metadata 当前只标记工作模式等精确区别，校准后的理解待反馈。

<details>
<summary>来源、默认值语义与验证范围</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，类定义见上述源码；使用处 [paddock.py:71–89](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L71)。
- field(default_factory=dict) 在省略对应参数时为实例创建新字典；显式传入字典时，dataclass 不自动深拷贝它。
- frozen=True 限制实例字段重新赋值，不表示 env_args 等字典内容也被深层冻结。
- 版式参考[已有 Session 类卡](../../../../../../../../../../slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/02-short-term-memory/classes/slime/agent/adapters/common.py/Session.md)：对象职责、字段、与使用方交接、原话、未知及折叠来源。这里只借鉴记录形式。
- 本次只静态核对定义及调用，未创建沙箱、运行 provider 或修改训练状态；不另建 dataclass 自动生成的 __init__ 方法卡。

</details>
