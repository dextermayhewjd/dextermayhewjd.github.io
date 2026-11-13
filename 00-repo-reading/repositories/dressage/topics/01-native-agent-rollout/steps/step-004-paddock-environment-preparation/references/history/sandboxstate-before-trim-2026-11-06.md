# SandboxState：精简前完整记录

2026-11-06 历史快照，保留原话、例子与来源；不作为当前正文继续维护。[返回精简卡片](../../02-short-term-memory/classes/dressage/paddock/blackbox/common/state.py/SandboxState.md)。

> 阅读位置：[init 构造并返回状态](../../02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#return-state) → **SandboxState** → 回到 generate，将 state 交给 register_agent。

- 源码定位：[dressage/paddock/blackbox/common/state.py:10–14](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/common/state.py#L10)，数据类，由助手核对。
- 首次接触：Step 001 中通过 init 返回类型定位，2026-11-05 开始独立阅读。
- 最近认识更新：2026-11-06，用户观察 state 的内容主要来自 lease，要求直接核对字段；逐项来源、引用和省略项由助手补充。

## 1. 先看结论：主要是从 lease 摘取并重新组织字段

用户观察到 state 的内容基本来自 lease，这个方向正确。Paddock 构造 state 时没有再申请一个环境，也没有产生另一份独立运行状态；主要是从 lease 取部分信息、提取 blackbox URL，换一种布局返回。

严格区分两点：trajectory_id 直接使用 init 的参数 traj_id，而不是读取 lease.trajectory_id；endpoint 若原先缺失，会先由 provider 补入 lease，再用于构造 state。正常实现中两份记录关联同一轨迹和同一环境。

## 2. 字段逐项对应

| SandboxLease 中的信息 | 构造 SandboxState 时怎样处理 |
| --- | --- |
| trajectory_id | state.trajectory_id 直接取 init 参数 traj_id；正常路径中与 lease 的轨迹标识对应 |
| provider | 放入 state.raw_register_response["provider"] |
| sandbox_id | 既赋给 state.sandbox_id，也放入 raw_register_response["sandbox_id"] |
| endpoints["blackbox"].url | 整理尾部斜杠后赋给 state.sandbox_url；如原先无入口，先向 provider 取得 |
| 所有 endpoints 的 URL | 构造成新的“服务名 → URL 字符串”字典，放入 raw_register_response["endpoints"]；这里不带 headers，且使用 lease 中各 endpoint 的原 URL |
| endpoints 中的 headers | 没有放入 state |
| capabilities | 没有放入 state |
| metadata | 直接放入 raw_register_response["metadata"]；这里没有深拷贝，仍引用同一个字典 |
| raw（如 SDK 环境对象） | 没有放入 state |

raw_register_response 是 init 新组装的字典，名字虽有 register，却不是 Agent 注册响应。state 没有健康检查结果字段；检查是否执行并成功，属于 init 的控制流程。

完整类定义：

```python
@dataclass
class SandboxState:
    trajectory_id: str
    sandbox_url: str
    sandbox_id: str | None = None
    raw_register_response: dict[str, Any] = field(default_factory=dict)
```

<a id="lease-state-relation"></a>

## 3. 与 lease、调用方的交接

**两者描述同一个实际沙箱，面向不同的操作接口。** SandboxLease 属于通用 provider 的环境管理记录；SandboxState 属于黑盒 Paddock 交给 generate 的访问资料。state 不是另一个沙箱，也不是 lease 的子类。

| 对比 | SandboxLease | SandboxState |
| --- | --- | --- |
| 谁创建 | provider.create | Paddock.init 根据 lease 和 endpoint 整理 |
| 保存哪些信息 | 环境 ID、provider、多个服务端点及 headers、能力、后端 metadata/raw 等 | 本次 trajectory_id、blackbox 服务 URL、环境 ID、来源摘要 |
| 谁使用 | Paddock 保留，provider 的后续操作/释放可接收它 | generate 接住，再传给 Paddock 的注册与调用方法 |

例如 provider 实际分配 sandbox-42，lease.sandbox_id 就记录它。Paddock 构造 state 时使用同一个 lease.sandbox_id 和选出的 blackbox endpoint.url；此时没有重新分配资源。raw_register_response 还会保存来源摘要，但不是把整个 lease 对象放入 state。

**为什么没有把 lease 扔掉？** 后续仍需要完整端点的 headers、后端资料或释放环境的记录。Paddock 保留它们，同时让上层通过更聚焦于黑盒交互的 state 来调用。

实际交接分两处：

```python
# Paddock.init：保存两份记录，向 generate 返回 state。
self._leases[traj_id] = lease
self._states[traj_id] = state
return state
```

```python
# Paddock.register_agent：根据传回来的 state 找到原来的 lease。
state = self._resolve_state(state)
lease = self._leases.get(state.trajectory_id)
endpoint = self._endpoint_for_state(state, lease)
```

因此 state.trajectory_id 是找回 lease 的关联键。state 不直接持有 lease；Paddock 的实例字典保存了这种对应关系。返回 state 也不意味着环境已释放。

**读完返回**：[init 构造与返回段](../../02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#return-state)。完整 lease 字段见 [SandboxLease](../../02-short-term-memory/classes/dressage/sandbox/types.py/SandboxLease.md)，多轨迹记录归属见 [init 的实例字典说明](../../02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#trajectory-indexes)。

<details>
<summary>按需回看：state 作为后续操作参数的例子</summary>

**Paddock 返回 state，相当于告诉调用方：“以后操作这次环境，把这份 state 传回来。”** state 自己不执行动作；它是注册、调用 Agent 等方法用于定位目标环境的参数。

假设同一个 Paddock 已分别取得两个环境。下面是调用形式示意，env_args 表示已准备好的环境配置，没有实际运行：

```python
state_a = await paddock.init("run-a", env_args=env_args)
state_b = await paddock.init("run-b", env_args=env_args)

await paddock.register_agent(
    state_a,
    instance_id="question-1",
    session_id="run-a",
    blackbox_type="claude_code",
)
```

1. 前两行得到分别对应环境 A、B 的访问资料，不是两个运行状态枚举。
2. 注册调用传入 state_a，表示要操作 A；并非让 Paddock 自己猜测最近创建了哪个环境。其他会话参数也需与该环境的执行身份一致。
3. Paddock 内部可以用 state_a.trajectory_id 找回 A 的完整 lease，再取得 URL 和 headers 访问其 BlackboxServer。

**为什么还有 lease？** provider 已把资源记录 lease 交给 Paddock 并由它保留；Paddock 的黑盒 API 选择把 state 交给上层作为后续操作参数。两者信息重叠是正常的。这是 Dressage 的接口设计，不是所有沙箱系统都必须有两个对象；另一套 API 也可以直接传 lease 或 ID。

这里的 state 不是 Ready/Running 状态，也不是新环境。它不代表已注册 Agent；字段 raw_register_response 的命名不改变这一点。真正的健康判断发生在 init 的控制流程中。


</details>

## 4. 我的直接表述（原话）

本轮问题：

> 以及最后的这个sandboxstate我觉得应该也许看清楚对吗?

这是明确的阅读需求，尚无字段理解的复述。完整语境见[本轮过程](../../04-flow.md#lease-state-and-shield)。

在本步整体收束后，用户继续问：

> 或者我们这里需要看清楚这里的sanboxstate是什么吗?

本次补看仍属于 Step 001 的最终交付，不扩展到新的步骤或 Agent 注册内部。过程见[交付对象回顾](../../04-flow.md#state-handoff-revisit)。

2026-11-06 的进一步追问：

> 那么我有点困惑的是
> 这里的这个sandboxstate和sandboxlease之间的关系什么?
> 这个比较重要

本轮按同一环境的两种资料接口、共同环境 ID 和轨迹关联键补充说明；尚未得到用户理解确认。

本轮对讲解方式的反馈：

> 我很难理解
> 主要是这个抽象我觉得我很难理解
> 我可以理解的sandbox通过provider 创建了之后
> 这里记录的是这个sandbox
> 但是这个sandboxstate是用来干什么的我不能理解
> 要么是不同层次的抽象
> 从认知学的角度和资深大厂程序员的角度
> 你会考虑怎么和我解释呢?

本次改从 state 的后续使用说明：返回后作为注册/调用的目标环境参数，并可据 trajectory_id 找回 lease；不再只用“不同层资料”定义。用户尚未确认理解。

本轮要求字段对照：

> 算了
> 我看到的内容是
> 这个lease是请仔细对比这里字段
> 我想要知道这里到底有什么不一样的地方?
> 因为我看达到的是
> 这里的state的内容似乎全部内容都是sandbox lease创造出来的

助手确认 state 的主要信息来自 lease，并逐项区分直取字段、重组 URL 字典、未保留信息以及 traj_id 参数的来源；先前操作示例改为折叠回查。

## 5. 尚不清楚

1. 用户对 state 与 lease 的区别，待后续理解反馈。
2. register_agent 和 call_agent 如何使用这些记录，后续按需进入；当前只核对调用接缝。

<details>
<summary>来源与验证边界</summary>

- 固定提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c；构造和保存：[paddock.py:117–151](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L117)。
- 后续取回 lease：[register_agent:165–167](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L165)；[endpoint 选择:311–318](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L311)。这些只用于验证 state 的去向，不扩展为本轮完整阅读任务。
- 2026-11-05，按用户要求将回贴的助手说明合并到本卡：字段含义与来源、lease/state 分工、保存与返回代码。回贴作为收录请求，不算用户独立复述；见[整理记录](../../04-flow.md#state-explanation-collected)。
- 静态核对，没有运行真实环境；没有取得实际 ID、URL 或 provider 记录。

</details>
