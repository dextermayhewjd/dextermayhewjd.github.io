# SandboxProvider.create

> 阅读位置：[Step 004（原 001） 的 2.1](../../../../../../../../../step-004-paddock-environment-preparation/01-scope.md#reading-navigation) → [SandboxProvider 接口总览](../../../../classes/dressage/sandbox/provider.py/SandboxProvider.md) → **create 的约定** → 回到 [Paddock.init 的环境取得段](../../paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#acquire-environment)。

- 源码定位：[dressage/sandbox/provider.py:20–21](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/provider.py#L20)。这是 Protocol 中的方法声明，具体后端实现保留在参考材料中。
- 首次接触：2026-11-05，Step 001 中由 init 的 provider.create 调用进入；本轮建立独立方法卡。
- 最近认识更新：2026-11-05，用户已将 SandboxProvider 理解为协议并列出六项能力，提供 Paddock.init 的调用代码作为主例；精确的属性/方法约定及取消、就绪边界继续按反馈核对。

- 继承入 Step 002：来自 [Step 004（原 001） 的完整记录](../../../../../../../../../step-004-paddock-environment-preparation/02-short-term-memory/functions/dressage/sandbox/provider.py/SandboxProvider.create.md)，合并前序 03 + 02；原话、认识时间与未知保留，以下“本轮”沿用原记录语境。

## LLM 整理：使用场合、具体内容与心智模型

以下是助手根据声明、调用方和已有实现整理的说明，不作为用户已掌握的结论。

1. **使用场合**：Paddock.init 已经整理好环境需求 spec，需要让所选环境后端取得本次沙箱。

2. **具体内容**：共同接口接收 SandboxSpec，约定返回 SandboxLease。实际后端完成资源创建或领取，并把资源身份、服务入口等资料整理为 lease；不同后端的具体流程和字段支持范围需要核对。

3. **建议构建的心智模型**：

   > create 是环境请求的交付接口：上层交出需求，后端交回可以继续管理和访问环境的记录。
   >
   > 它的返回值不是训练结果，也不是 Paddock 最终返回的 SandboxState。init 还会继续使用 lease。

4. **调用代码**：采用用户指出的 Paddock.init 调用侧例子。教学裁剪自 72–106 行：SandboxSpec 的实参省略，try/except 与取消清理未展示；以下不是独立可运行程序。注释编号沿用 scope 的第 2 段和 2.1 入口。

   ```python
   spec = SandboxSpec(...)

   create_task = asyncio.create_task(                # [2] acquire environment
       self._provider.create(spec),                 # [2.1] provider contract
       name=f"sandbox-create:{traj_id}",
   )
   lease = await asyncio.shield(create_task)
   endpoint = lease.endpoints.get("blackbox")
   ```

   这里的 self 是 Paddock，self._provider 是具体后端对象。上层按共同接口调用它，实际执行由该对象的方法完成。

   1. 构造 spec，描述本次环境需求。
   2. 创建 Task，执行具体 provider 的 create(spec)。
   3. 等待 Task，接住返回的 lease；shield 不改变返回类型。
   4. 从 lease 读取 blackbox 服务入口，结果可能是 None，后续分支才决定是否补查。

## 本场景的输入与输出

当前沿用 init 的黑盒环境请求场景：spec 已填入本次身份、环境参数和 blackbox 服务需求；本页以调用侧代码作为主例，保持后端中立；local_bwrap 的字段映射留在参考中，不选择或实现 Kubernetes 后端。

### 1. 完整接口声明

```python
async def create(self, spec: SandboxSpec) -> SandboxLease:
    """Create or acquire a sandbox lease for one trajectory."""
```

声明只给出了方法形状和用途，没有一个所有后端共用的创建函数体。下面说明的是怎样使用及核对这个约定，不是虚构的内部调用顺序。

### 2. 输入：需要什么环境

| 输入 | 本次来自哪里 | 当前理解到哪里 |
| --- | --- | --- |
| self | 已选定的具体 provider 实例 | 使用自己的配置和客户端管理环境 |
| spec.trajectory_id | init 的 traj_id，来自本次 session_id | 给环境请求和返回记录提供关联身份 |
| spec.env_type、spec.env_args | 当前任务的环境需求 | 由具体后端解释；不能假定每个后端支持全部参数 |
| spec.services | 本次包含 blackbox 的服务描述 | 告诉后端上层希望访问哪些服务 |
| spec.timeout_sec、spec.metadata、spec.env | 超时、附加说明和环境变量配置 | 字段含义见 [SandboxSpec](../../../../classes/dressage/sandbox/types.py/SandboxSpec.md)；具体支持与落实由后端确定 |

### 3. 输出：取得了什么环境

| 返回记录 | 上层用它做什么 |
| --- | --- |
| lease.trajectory_id、provider、sandbox_id | 关联本次执行、后端和资源标识；sandbox_id 的具体含义由后端定义 |
| lease.endpoints | 按服务名获取访问入口，当前关注 blackbox |
| lease.capabilities | 识别后端报告的命令、文件和地址能力 |
| lease.metadata、lease.raw | 保留后续管理所需的后端资料 |

这些是 [SandboxLease 的数据结构](../../../../classes/dressage/sandbox/types.py/SandboxLease.md)，不意味着每个可选字段都必然有值。init 已经为缺少现成服务入口保留 get_public_url 分支。

create 还会在环境后端产生创建或领取资源的副作用；返回 lease 后，这些资源仍需要被使用和最终释放。

### 4. 正常返回后，init 还要做什么

1. 接住 lease，尝试读取 lease.endpoints 中的 blackbox 入口。
2. 没有入口时，通过 [provider.get_public_url](SandboxProvider.get_public_url.md) 补齐。
3. 按配置执行服务健康检查。
4. 从环境身份和服务地址构造 SandboxState，返回给 generate。

因此 create 正常返回不单独证明题目初始化完成、业务请求可用，或某个 Kubernetes Pod 已 Ready。当前代码把部分检查放在后续 init 中；其他就绪要求必须结合具体后端及使用场景核对。

### 5. 失败和取消时的责任

1. 没有收到 lease，不等于后端一定没有分配资源。例如本地等待取消时，远端请求可能仍在执行。
2. 调用方使用 shield 并安排后台接手，是为了有机会取得晚到结果再清理；具体实现见 [init 的取消说明](../../paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#shield-create-cancellation)。
3. 后端自身如何处理部分创建失败、重复请求和释放，需要读实现验证。Protocol 的返回注解不提供这些保证。

后端内部怎样整理字段，仅在需要时回查 [local_bwrap 的完整参考](../../../../../../../../../step-004-paddock-environment-preparation/references/local-bwrap-create.md#build-lease)。当前主例使用上方的 Paddock 调用代码，不把具体后端实现作为接口的使用方式。

**本轮停止位置**：能说明 spec 是请求、lease 是资源记录、后续 init 还要处理入口与就绪，并知道失败后资源仍需明确归属。然后回到 [init 第 2 段](../../paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#acquire-environment)，继续看入口读取；不进入完整 local_bwrap 调度。

## 我的直接表述（原话）

用户先明确这个窗口的主题：

> 部队部队打错了 应该是继续看一下 SandboxProvider 接口卡
> 这个窗口是用来理解 dressage的

随后要求：

> 那么请生成一下对应的函数卡片吧
> 然后继续推进

这是继续学习共同接口并生成 create 方法卡的请求；没有据此填写对实现行为的掌握结论。

用户随后纠正主例的选择：

> 然后这里的例子应该是这里才对

并提供了从 spec 构造、创建 Task、等待 lease 到读取 endpoint 的调用代码。本页已据此采用调用侧主例；完整原话与代码见[本轮过程](../../../../../../../../../step-004-paddock-environment-preparation/04-flow.md#provider-usage-example)。

## 尚不清楚

1. 用户对 create 返回值、服务就绪和资源所有权之间区别的理解，待后续反馈。
2. 不同后端的字段支持、失败恢复、重复调用语义，尚未全面验证。
3. Kubernetes 后端需要另行实现；本页没有把示例中的字段映射当作现成的 Kubernetes 方案。

<details>
<summary>来源、验证与记录分工</summary>

- 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。声明在 sandbox/provider.py:20–21，使用处在 paddock/blackbox/paddock.py:86–151。
- [接口类卡](../../../../classes/dressage/sandbox/provider.py/SandboxProvider.md)保留六项操作的总览；本页解释 create 的具体使用约定；数据字段引用各类卡。
- 主例来自 Paddock.init:72–106；具体后端字段映射继续保留在 references，不恢复到当前主线。
- [Step 004（原 001） 本次记录](../../../../../../../../../step-004-paddock-environment-preparation/04-flow.md#create-contract-card)。这里只核对接口和静态交接，未启动实际后端、Kubernetes 或训练。

</details>
