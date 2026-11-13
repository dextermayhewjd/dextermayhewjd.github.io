> Step 011 继承：来自 [Step 010 完整记录](../../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/classes/dressage/rollout/prewarm/store.py/PrewarmHandle.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

本步继承：[Step 011 来源记录](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/classes/dressage/rollout/prewarm/store.py/PrewarmHandle.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/classes/dressage/rollout/prewarm/store.py/PrewarmHandle.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/classes/dressage/rollout/prewarm/store.py/PrewarmHandle.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/03-long-term-memory/classes/dressage/rollout/prewarm/store.py/PrewarmHandle.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# PrewarmHandle

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/03-long-term-memory/classes/dressage/rollout/prewarm/store.py/PrewarmHandle.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../../../../01-native-agent-rollout/steps/step-005-agent-registration/03-long-term-memory/classes/dressage/rollout/prewarm/store.py/PrewarmHandle.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

- 源码定位：[store.py:46](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/store.py#L46)。
- 首次单独展开：Step 002，2026-11-06。
- 最近认识更新：Step 002，2026-11-06；用户概括取得 handle 后回填先前变量，助手区分复用资料与重新配置环境。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：领取端等待预热初始化成功后，把已有环境的使用资料交给 generate。
2. **具体内容**：保存会话与组编号、Paddock 操作对象、初始化返回的 state 和环境参数。
3. **建议构建的心智模型**：

   > 这是预热环境的交接记录。generate 拿到它后，可以接着注册和调用 Agent，不需要再次初始化同一个环境。它本身不是沙箱，也不是 Proxy 客户端或 provider 的 lease。

4. **调用代码**：

   ```python
   handle = await claim_prewarm(session_id)
   if handle is not None:
       paddock = handle.paddock
       state = handle.state
       env_args = handle.env_args
       initialized = True
   ```

## 本场景的输入与输出

完整定义：

```python
@dataclass(frozen=True, slots=True)
class PrewarmHandle:
    """A ready sandbox whose ownership has transferred to rollout dispatch."""

    session_id: str
    group_id: int
    paddock: Any
    state: Any
    env_args: dict[str, Any]
```

| 字段 | 从哪里来、供什么用 |
| --- | --- |
| session_id | 原预热记录的执行会话编号，也是本次查找的键 |
| group_id | 原预热记录的分组编号，用于组归属/清理与日志；不是沙箱 ID |
| paddock | 启动预热时使用的操作对象，后续用来注册、调用 Agent 与终止环境 |
| state | 等待预热 Task 得到的初始化结果；当前黑盒路径是 SandboxState，包含访问地址、沙箱 ID 等 |
| env_args | 原预热参数的深拷贝；generate 命中后使用这一份参数 |

例如为 session_id="bbs-demo" 预热时，store 保存初始化 Task 及其 Paddock。领取同一编号，等待成功得到 state 后，返回携带上述五项的对象；这只是教学情境，未创建实际环境。

1. 领取按 session_id 精确匹配预热记录，不是按镜像随便取一个空闲环境。
2. 此时 state 表示预热初始化已正常返回，不代表 Agent 已注册或题目已执行。
3. 命中后 generate 将 initialized 设为 True，后续继续注册；finally 依据这个标记安排环境回收。
4. provider.create 返回的 SandboxLease 位于更底层，由 Paddock 管理；PrewarmHandle 是预热存储层交给 rollout 的记录，二者不能混用。

**读完返回**：[PrewarmStore.claim](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.claim.md) 查看这份记录何时构造，再回 generate 使用返回字段。

## 我的直接表述（原话）

> 好的那么我们开始看一下这里的这个proxy client吧
> 看一下这个proxy是在做什么这件事情
> 然后重点看一下这里的这个handle吧

上述为最初阅读请求。后续表述：

> 那么这里的内容做的差不多了吗?
> 总结就是如果拿到了这个prewarm的handle了之后
> 就是通过这个handle来设置之前的一系列的内容是我的理解
> 那么之后呢?
> 我还需要做什么呢?

助手校准：命中后把 handle 中已有的 paddock、state、env_args 赋给 generate 的局部变量，并设置 initialized=True；不是重新创建或配置沙箱。正常命中分支随后直接进入 Agent 注册。

## 尚不清楚

- 上游调度器的启动位置已回查；完整预取容量与并发策略尚未展开。
- 取消时的完整资源释放链尚未展开；这里保留领取端的责任边界。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- store.py 的 PrewarmHandle、PrewarmStore.start/claim/_take、claim_prewarm；generate:182–242。
- 静态源码核对，没有创建或领取真实环境，没有执行任务。
- [原始讨论](../../../../../../../../../01-native-agent-rollout/steps/step-002-proxy-client-and-prewarm-claim/04-flow.md)。

</details>
