> Step 011 继承：来自 [Step 010 完整记录](../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/classes/dressage/proxy/session_manager.py/Session.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/classes/dressage/proxy/session_manager.py/Session.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../step-012-task-agent-verifier/03-long-term-memory/classes/dressage/proxy/session_manager.py/Session.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/classes/dressage/proxy/session_manager.py/Session.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/classes/dressage/proxy/session_manager.py/Session.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/classes/dressage/proxy/session_manager.py/Session.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/02-short-term-memory/classes/dressage/proxy/session_manager.py/Session.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# Session（Dressage Proxy）

[StepRecord 类卡](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/classes/dressage/proxy/session_manager.py/StepRecord.md) · [本步阅读导航](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/01-scope.md#current-reading)

- 源码：[session_manager.py:157](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/session_manager.py#L157)。
- 首次单独展开：Step 007，2026-11-08。
- 最近说明更新：2026-11-08；只看分段所需的数据关系，尚未深入全部方法。

## 1. 一句话理解

> Session 是 Proxy 为一次执行会话保存的总记录：包含身份标识、多次模型交互的 StepRecord，以及这些交互所属的历史路径信息。

这是 Dressage Proxy 的 Session，不是沙箱访问资料 SandboxState，也不是 BlackboxServer 的会话类型。`session_id` 只是编号；`session` 是按编号找到的整个对象。

<a id="get-session"></a>

### 先接回调用处：get_session 到底返回什么

在 finalize 中，先按会话编号取回对象：

```python
session = session_manager.get_session(session_id)
```

`SessionManager.get_session` 的完整实现很短（session_manager.py:583），这里只作为理解 Session 来源的辅助方法展开，不另建函数卡：

```python
def get_session(self, session_id: str) -> Session | None:
    with self._lock:  # 保护查表这一步；退出后不会继续持有这把锁。
        return self._sessions.get(session_id)
```

`self` 是 SessionManager 对象，其 `_sessions` 字段类型为 `dict[str, Session]`。键是 session_id，值是已存在的 Session 对象。这个方法不创建、不重新收集，也不复制会话；找到就返回原对象，找不到返回 None。finalize 在找不到时返回 404，找到后另用 session.request_lock 管理后续操作。

因此这里连续理解为：**session_id → 管理器查表 → Session 对象 → 查看下方字段 → 交给分段函数。**

## 2. 当前先看四个字段

原类字段节选，省略了不影响当前分段问题的状态、索引、锁和计数器。

```python
@dataclass
class Session:
    session_id: str       # 这是哪次执行会话。
    instance_id: str      # 属于哪道题/哪个任务实例。
    steps: list[StepRecord] = field(default_factory=list)
    # 上面保存这次会话中积累的每次模型生成记录。
    lineages: dict[str, Lineage] = field(default_factory=dict)
    # 上面保存各条历史路径的说明，键为 lineage_id。
```

`steps` 存实际交互记录，`lineages` 存路径信息。它们通过 **step.lineage_id == lineage.id** 对应，不是把 StepRecord 列表存进 Lineage。

当前涉及的 Lineage 很短，先就地理解，不单独展开新类卡：

```python
@dataclass
class Lineage:
    id: str                         # 路径编号。
    index: int                      # 路径顺序，分段函数按它排序。
    latest_step_id: str | None       # 这条路径最新的模型记录编号。
    branch_from_step_id: str | None = None  # 如有分支，从哪个旧 step 分出。
```

路径信息由前面的请求处理建立。当前分段函数使用已有归属，不重新推断每条交互属于哪条路径。

## 3. 用同一份对象说明 steps 与 lineages

下面是对象关系示意，不是完整构造代码，A/B 仅为便于阅读的代号：

```text
session
  session_id = run-1
  instance_id = task-1
  steps = [step-1(A), step-2(A), step-3(B)]
  lineages = {A: Lineage-A, B: Lineage-B}
```

如果 B 从 step-1 分支，Lineage-B 的 branch_from_step_id 会保存 step-1 的编号；原 step-1 仍保留自己的 A 归属。分段函数不会在筛选时自动把 A 的祖先记录复制到 B；分支如何准备上下文属于后续拼接材料的问题。

先取 Lineage-A，用它的 id 筛选 steps，就得到 step-1、step-2；再取 Lineage-B，得到 step-3。之后才在每组内部根据 lineage_segment_boundary_before 切段。

## 4. Session 从哪里来，分段函数怎么用

模型请求到达 Proxy 时，按 session_id 取得或创建 Session；每次记录时将新 StepRecord 追加到 session.steps。到 finalize，先取得这份已有 Session，再交给分段函数：

```python
# finalize_session 的数据交接节选。
session = session_manager.get_session(session_id)
# ... 会话检查与加锁。
lineage_segments = _split_session_into_lineage_segments(session)
```

这一次输入的确是整个 Session。分段函数开头实际使用它的两份数据：

```python
sorted_lineages = sorted(session.lineages.values(), key=lambda item: item.index)
for lineage in sorted_lineages:
    lineage_steps = [
        step for step in session.steps if step.lineage_id == lineage.id
    ]
```

当前先看懂：**按路径逐组取出该路径的模型记录**。函数后面如何切段与返回 segments，留在分段函数本身阅读；此处不展开循环和 flush_segment 的完整实现。

读完返回 `_split_session_into_lineage_segments` 的开头（server.py:670）。这是本轮下一处函数入口，不重新读 API 采集或 Session 的全部管理方法。

## 5. 我的直接表述（原话）

> 我们当前在看的是这个split session into lineage segments对吧?
> 那么是否考虑一下简单拆解一下这里的session呢?
> 否则感觉我也看不是特别明白?

位置校准：上一轮在 StepRecord 类卡；当前补齐分段函数输入 Session 的关系，尚未正式逐段展开整个分段函数。不以类卡生成视为个人已经理解。

本轮前置关系提问：

> 那么前置条件的函数我们都读了吗?
> 例如这里的sesion manager 的get session?
> 这里可以放入session到底的格式是什么?

说明：没有把所有前置函数逐个深入；本轮补齐 get_session 的完整查表实现和返回类型，其余前置按是否影响当前分段理解来决定深度。

## 6. 尚不清楚

- 分段循环怎样根据边界保存一段、开始下一段。
- 历史路径的选择算法、全部 Session 状态与管理方法，本轮不展开。

<details>
<summary>来源与验证</summary>

固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。静态核对 session_manager.py:38–44、156–200；server.py:670–706、1960 附近及 finalize_session。无真实请求或运行验证。

[本轮形成过程](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/04-flow.md#session-for-lineage-split)。

</details>
