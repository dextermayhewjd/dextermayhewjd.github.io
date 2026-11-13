# SandboxState

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../../../step-005-agent-registration/03-long-term-memory/classes/dressage/paddock/blackbox/common/state.py/SandboxState.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

[来自 init 的返回阶段](../../../../../../functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#return-state) · [SandboxLease](../../../../sandbox/types.py/SandboxLease.md)

- 源码：[common/state.py:10–14](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/common/state.py#L10)。
- 首次接触：2026-11-05，原 Step 001（现 Step 004）。
- 最近认识更新：2026-11-06，用户已概括 state 整理 lease 的字段且由 Paddock 管理；助手校准并非全部重要信息的转移。

## 1. 一句话理解

**SandboxState 是 Paddock 从 lease 中摘取、重新组织的资料，加上本次执行 ID，返回给 generate 继续使用。** 它没有创建新环境，也不记录 Ready/Running 状态。

## 2. 与 SandboxLease 的字段对照

```python
@dataclass
class SandboxState:
    trajectory_id: str
    sandbox_url: str
    sandbox_id: str | None = None
    raw_register_response: dict[str, Any] = field(default_factory=dict)
```

<a id="lease-state-fields"></a>

| lease 中的信息 | state 中的位置 | 怎样处理 |
| --- | --- | --- |
| trajectory_id | trajectory_id | 实际取 init 的参数 traj_id；正常路径中标识同一次执行 |
| sandbox_id | sandbox_id；摘要中的 sandbox_id | 同一环境 ID，保存两处 |
| provider | raw_register_response["provider"] | 放入摘要 |
| endpoints["blackbox"].url | sandbox_url | 取黑盒入口，去掉 URL 尾部斜杠 |
| 所有 endpoints | raw_register_response["endpoints"] | 重新组成“服务名 → URL 字符串”，不保留完整 Endpoint 对象 |
| metadata | raw_register_response["metadata"] | 直接引用原字典，没有深拷贝 |
| endpoint.headers | 无 | 不带入 state |
| capabilities | 无 | 不带入 state |
| raw（后端原始对象） | 无 | 不带入 state |

缺少 blackbox 入口时，init 会先向 provider 取得并写入 lease，再进行上面的整理。**因此 state 是取字段、提取 URL、调整布局后的结果，不是 lease 的完整复制。**

raw_register_response 是这里组装的来源摘要，不是 Agent 注册响应；此时还没有执行注册。

<a id="lease-state-relation"></a>

## 3. lease 留在 Paddock，state 返回上层

```python
# BlackboxAgentPaddock.init 的最后三行
self._leases[traj_id] = lease
self._states[traj_id] = state
return state
```

generate 后续把 state 传给 register_agent/call_agent；Paddock 可以用 state.trajectory_id 找回完整 lease。因此两者有重复字段，但没有完整互相复制。

## 4. 我的直接表述（原话）

最近一次字段观察（节选）：

> 我想要知道这里到底有什么不一样的地方?
> 因为我看达到的是
> 这里的state的内容似乎全部内容都是sandbox lease创造出来的

更早的疑问、操作示例与完整原话保留在[精简前记录](../../../../../../../../step-004-paddock-environment-preparation/references/history/sandboxstate-before-trim-2026-11-06.md)。

本轮后续表述：

> 好的我的理解是sandboxstate把lease中重要的部分全部都转移到了这里state中
> 但是还是由paddock来统一管理
> 好的
> 那么我们继续吧
> 这里应该是init所有的内容了吧
> 我们是否需要进入下一个部分呢?

助手校准：state 摘取并重新组织部分字段，完整 lease 仍由 Paddock 保留，并非搬走或转移全部重要信息；例如 headers 仍在 lease 中供后续使用。

## 5. 尚不清楚

- 用户已表达字段整理及 Paddock 管理的关系；“部分摘取，不搬走全部资料”的校准尚待进一步确认。
- 注册与调用方法怎样使用 state，留到对应方法继续阅读。

<details>
<summary>源码与历史依据</summary>

- 固定版本：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 构造与保存：[paddock.py:117](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L117)；后续按轨迹找回 lease：[paddock.py:165](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L165)。
- [原始讨论](../../../../../../../../step-004-paddock-environment-preparation/04-flow.md)；[精简前完整记录](../../../../../../../../step-004-paddock-environment-preparation/references/history/sandboxstate-before-trim-2026-11-06.md)保留历次问题与说明。
- 仅静态源码核对，没有执行真实环境；源码实现未修改。

</details>
