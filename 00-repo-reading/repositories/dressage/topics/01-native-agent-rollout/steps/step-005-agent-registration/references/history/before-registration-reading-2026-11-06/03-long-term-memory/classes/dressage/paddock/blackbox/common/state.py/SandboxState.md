# SandboxState

> 阅读位置：[init 构造并返回状态](../../../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#return-state) → **SandboxState** → 回到 generate，将 state 交给 register_agent。

- 源码定位：[dressage/paddock/blackbox/common/state.py:10–14](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/common/state.py#L10)，数据类，由助手核对。
- 首次接触：Step 001 中通过 init 返回类型定位，2026-11-05 开始独立阅读。
- 最近认识更新：2026-11-05，用户在概括环境取得后再次要求看清 SandboxState；当前补看最终交付对象，尚无对其四个字段与 lease 区别的独立复述。

- 继承入 Step 002：来自 [Step 004（原 001） 的完整记录](../../../../../../../../../../../step-004-paddock-environment-preparation/02-short-term-memory/classes/dressage/paddock/blackbox/common/state.py/SandboxState.md)，合并前序 03 + 02；原话、认识时间与未知保留，以下“本轮”沿用原记录语境。

## 1. 对象职责

SandboxState 是这一步最终交给上层的环境访问资料。init 从 lease 和 endpoint 取出必要信息构造它，generate 接住后，再将它传给 register_agent 和 call_agent。当前看清四个字段与返回关系即可。

> lease 是 provider 的环境记录；state 是 Paddock 对外交付的访问状态。两者关联同一次环境使用，不表示创建了两个环境。

这里的 State 是一份环境访问上下文。它没有 Ready/Running 之类的状态字段；是否执行过健康检查由 init 的控制流程决定。构造它只是整理已有资料，不会再次创建沙箱。

## 2. 字段总览

| 字段 | 保存什么 | 来自哪里 | 默认值 |
| --- | --- | --- | --- |
| trajectory_id | 本次执行的关联标识，后续按它查找 Paddock 中的记录 | 传入的 traj_id | 必填 |
| sandbox_url | BlackboxServer 的访问地址 | endpoint.url | 必填 |
| sandbox_id | 后端提供的环境或租用标识 | lease.sandbox_id | None |
| raw_register_response | provider、环境标识、metadata、端点 URL 等摘要 | init 整理得到 | 新空字典 |

最后一个字段虽然叫 raw_register_response，此时还没有执行 Agent 注册，不能按名字理解为注册已经成功。

完整类定义：

```python
@dataclass
class SandboxState:
    trajectory_id: str
    sandbox_url: str
    sandbox_id: str | None = None
    raw_register_response: dict[str, Any] = field(default_factory=dict)
```

## 3. 与 lease、调用方的交接

1. **lease**：provider 返回的环境记录，保留后端管理资源所需的资料。字段见 [SandboxLease](../../../../sandbox/types.py/SandboxLease.md)。
2. **state**：Paddock 从 lease 和 endpoint 整理后，交给 generate 的访问资料。完整构造参数见 [init 第 3 段](../../../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#return-state)。
3. **Paddock 同时保存两者**，随后返回同一个 state：

```python
# 位于 BlackboxAgentPaddock.init；self 是 Paddock 实例，不是 SandboxState
self._leases[traj_id] = lease
self._states[traj_id] = state
return state
```

字典为何能保存多个 traj_id，以及对象复用方式，见 [init 中的记录归属说明](../../../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#trajectory-indexes)。

4. generate 接住 state，随后传给 paddock.register_agent(...)。Paddock 可以通过 state.trajectory_id 找回对应的 lease，再取得完整的服务入口及 headers。
5. state 不是 lease 的完整拷贝；返回 state 不意味着 lease 被丢弃或沙箱已释放。两者描述同一次环境使用，不会因此创建第二个沙箱。

> 取得环境及其访问入口，保存管理记录，再把 state 交给上层继续使用。

**读完返回**：[init 的返回位置](../../../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#return-state)，接着回到 generate 的注册调用。此处只定位下一交接，不自动展开注册内部。

## 4. 我的直接表述（原话）

本轮问题：

> 以及最后的这个sandboxstate我觉得应该也许看清楚对吗?

这是明确的阅读需求，尚无字段理解的复述。完整语境见[本轮过程](../../../../../../../../../../../step-004-paddock-environment-preparation/04-flow.md#lease-state-and-shield)。

在本步整体收束后，用户继续问：

> 或者我们这里需要看清楚这里的sanboxstate是什么吗?

本次补看仍属于 Step 001 的最终交付，不扩展到新的步骤或 Agent 注册内部。过程见[交付对象回顾](../../../../../../../../../../../step-004-paddock-environment-preparation/04-flow.md#state-handoff-revisit)。

## 5. 尚不清楚

1. 用户对 state 与 lease 的区别，待后续理解反馈。
2. register_agent 和 call_agent 如何使用这些记录，后续按需进入；当前只核对调用接缝。

<details>
<summary>来源与验证边界</summary>

- 固定提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c；构造和保存：[paddock.py:117–151](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L117)。
- 后续取回 lease：[register_agent:165–167](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L165)；[endpoint 选择:311–318](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L311)。这些只用于验证 state 的去向，不扩展为本轮完整阅读任务。
- 2026-11-05，按用户要求将回贴的助手说明合并到本卡：字段含义与来源、lease/state 分工、保存与返回代码。回贴作为收录请求，不算用户独立复述；见[整理记录](../../../../../../../../../../../step-004-paddock-environment-preparation/04-flow.md#state-explanation-collected)。
- 静态核对，没有运行真实环境；没有取得实际 ID、URL 或 provider 记录。

</details>
