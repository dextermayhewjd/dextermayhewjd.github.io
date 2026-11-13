# SandboxFleet.start_warmpools

[Step 001 scope](../../../../../../01-scope.md#reading-navigation) → [setup](SandboxFleet.setup.md) → **start_warmpools（当前）** → [_warm_entries 源码](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1111)

- 源码定位：[fleet.py:1144–1192](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1144)。
- 首次接触：Step 001，先在 scope 中定位；2026-11-04 从 setup 的第 [6] 项正式进入本函数。
- 最近认识更新：2026-11-04，用户明确表示 warm、warm pool、wave 及其与 Agentic RL 任务进度的关系尚不清楚；本轮先补概念与调用时机，不据已展示代码认定理解。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：setup 已检查运行条件并生成资源计划，接着请求准备这些计划中的镜像池。
2. **具体内容**：读取已经决定好的计划条目和创建预算，组织直接提交或分波提交；不负责依据训练进度判断未来还需要哪些镜像。
3. **建议构建的心智模型**：

   > plan 已决定每个镜像在哪个集群、准备多少副本；start_warmpools 决定这些计划怎样分批交给预热。具体怎样创建一个池、怎样检查就绪，是它委派给下层的工作。

4. **调用代码**：来自 setup:1422–1423，保留真实参数与返回位置。

   ```python
   self.start_warmpools(wait=True, create_budget=create_budget)
   return self
   ```

本函数解决“已知资源目标怎样分批准备”，不解决“训练下一步应该需要什么环境”。每题独有镜像且只用一次时，池化收益可能有限；naive 会先准备整批，不能把它理解为按剩余任务自动优化预热。完整场景与界限见 [全异镜像时的架构作用](../../../../../../../../../../references/rl-batch-flow-and-entry.md#unique-images-and-provisioning-boundary)。

## 本场景的输入与输出

<a id="warm-pool-wave"></a>

### 先只看预热池：提前启动、等待被任务领取的环境

预热池维护的是备用沙箱环境。指定模板和目标数量后，控制器提前创建相应 Sandbox 及 Pod，使基础环境达到可领取的就绪状态；它们此时还没有被这批具体任务领取，也没有开始解题。

以某种镜像的备用目标为 3 举例，这是教学数量：

1. 先准备 3 个对应环境，留在池里等任务使用。
2. 一条任务需要这种环境时，领取其中 1 个，并在领取后进行题目初始化和执行。
3. 被领取的环境离开备用池，此时备用数变为 2，另有 1 个正在被使用。
4. 控制器观察到备用数量不足后补充环境，目标是恢复 3 个备用；因此备用目标不等于总运行数量上限。

目的在于把基础环境创建和启动的等待提前，减少任务真正开始时的冷启动延迟。严格说 SandboxWarmPool 资源描述模板与备用目标，控制器负责落实；它本身不是额外启动的一台容器，也不是任务队列。后面的 wave 只是批量准备这些池时的分组，先不展开。

### 不同任务需要不同环境，怎样提前准备

当前顺序是先加载 Task，再规划和预热；因此 Fleet 在启动任务前已经能看到每条 Task.image。它按镜像分别准备对应池，不是把所有环境混在一个通用池中。

下面是环境分组的教学例子，不是实际数据集记录：

| 任务 | Task.image | 对应环境池 |
| --- | --- | --- |
| T1 | python-env:v1 | Python 镜像对应的池 |
| T2 | browser-env:v1 | 浏览器镜像对应的池 |
| T3 | python-env:v1 | 同一个 Python 镜像池，但领取独立沙箱 |

1. 基础依赖不同，可以由不同的 image 描述；plan 为每种镜像形成对应集群、模板、池与副本目标。
2. 基础镜像相同但题目不同，可以从同一个池分别领取独立环境，再由任务回调完成题目初始化。当前非 recycle 路径不让两个任务共同使用同一个可变沙箱。
3. 如果每道题都使用独有镜像，也可以在 Task 加载后按这些已知镜像预热，只是环境种类多、同时驻留的成本更高。
4. 当前 Fleet 的分组依据主要是 Task.image；它不会自动将 metadata 中任意差异解释成不同环境规格。池的副本目标还受并发与配置预算影响，不直接等于该镜像的任务数量。

静态源码依据：image_counts 按 t.image 计数（fleet.py:577）；_plan 按镜像形成 PlanEntry（815 起）；领取时按 task.image 查找计划项（_acquire_reserved）。

### 先分清：准备动作、备用池、提交批次

| 名称 | 在这里指什么 | 不要混淆的对象 |
| --- | --- | --- |
| warm | 让相应环境提前准备好，达到可领取的就绪条件；新建路径由模板、预热池、控制器和 Pod 启动共同完成 | 不只是保存镜像名，也不是执行题目 |
| warm pool | 按模板维护的备用沙箱；SandboxWarmPool 对象声明备用目标，控制器负责维持。本 Fleet 按镜像计划准备对应池 | 不是保存镜像文件的仓库，也不是训练任务列表 |
| wave | 当前函数中临时收集的一组 PlanEntry，用来分批提交池的预热 | 不是 Kubernetes 资源，也不是训练器的 rollout batch |

例如已有计划要求镜像 A、B 各准备 2 个备用环境，创建预算为 2（教学假设）：先提交 A 池并等到就绪，再提交 B 池并等待。两个池仍分别管理自己的备用环境；第二波不会自动删除第一波。这里的 wave 控制资源准备的批次，不控制题目的分批采样。

### 与已加载任务、正在执行的任务怎样连接

1. 当前 naive 路径先由 load_tasks 保存本批 Task；plan 统计这些任务使用的镜像，并结合配置计算每个池的目标副本数。
2. setup 内调用 start_warmpools，把这些既定计划分批交给下层准备。
3. 这些波次完成、setup 正常返回之后，run_naive 才调用 executor。因此本次启动阶段不是先观察“哪些题已完成”再决定预热哪些池。
4. 任务执行期间，Claim 从池中领取环境，池的补充由 Kubernetes 控制器协调；这是备用库存的补充机制。
5. 持续训练中“哪批还需要多少环境、下一批要预热什么”是训练侧需求管理。仓库的 LookaheadWarmer 可接收训练器报告的批次镜像需求及完成事件，但它不会自行预测任务。它是另一层用法，不是当前 start_warmpools 中的 wave，也不作为本轮新的必读函数。

这里区分两个问题：训练侧决定还需要哪些环境；资源准备侧决定怎样把环境准备出来。预热池服务于领取需求，wave 则用于限制一次集中提交的准备规模。

### 1. 进入时已有的数据

当前从 setup 的默认新建路径进入：adopt_existing=False、wait=True；setup 未显式收到 create_budget，因此此处收到 None。

| 输入或已有状态 | 本次怎样使用 |
| --- | --- |
| self.plan_ | setup 已生成的 FleetPlan；其中 entries 是各个镜像池的规划条目 |
| create_budget | None 时采用 self.config.warm_create_budget；当前配置默认值为 1000 |
| wait | setup 显式传 True；末波也需要等待就绪 |
| config.adopt_existing | 当前 False；采用已有池的另一条路径保留在源码中 |

每个条目 e 是 PlanEntry。本函数分组时使用 e.replicas；它还包含 image、cluster、template、pool、tasks 等信息，供下层执行计划。

1. e.replicas 是这个池计划保有的目标副本数。
2. budget 是本次分组时累计目标副本数的预算，不是任务数或线程数，也不是精确计算出来的新增 Pod 差额。
3. 一波内同时处理多少条目，由下一层读取 config.max_concurrent 决定；这是另一个控制量。

### 2. 正常返回后的结果

1. 本函数返回 None，不返回 Task 列表或 Fleet 对象。
2. 当前 wait=True：所有提交的波次都正常完成相应预热与就绪等待后，本函数才正常返回。
3. setup 随后执行 return self；再回到 run_naive，才进入任务执行器。
4. 本函数按计划分批提交，不在这里领取环境或执行题目，也不会在波次之间删除上一波已经准备好的池。

<a id="start-warmpools-numbered-flow"></a>

### 3. 完整源码：七段定位，一套编号

下面保留函数签名和全部执行语句，只移去原 docstring、替换注释并增加空行。先沿当前新建、正预算的路径阅读；[3]、[4] 是源码中必须保留的其他分支。

```python
def start_warmpools(self, wait: bool = True,
                    create_budget: int | None = None) -> None:
    # [1] choose the budget
    budget = self.config.warm_create_budget if create_budget is None else create_budget

    # [2] obtain plan entries
    entries = (self.plan_ or self.plan()).entries

    # [3] adopting existing pools: submit directly
    if self.config.adopt_existing:
        self._warm_entries(entries, wait)
        return

    # [4] no staging budget: submit directly
    if not budget or budget <= 0:
        self._warm_entries(entries, wait)
        return

    # [5] initialize the current wave
    wave: list = []
    wave_creates = 0
    n_waves = 0

    # [6] collect entries; submit the previous wave before overflowing
    for e in entries:
        if wave and wave_creates + e.replicas > budget:
            n_waves += 1
            logger.info("staged warm: wave %d — %d pools / %d creates (budget %d)",
                        n_waves, len(wave), wave_creates, budget)
            self._warm_entries(wave, wait=True)
            wave, wave_creates = [], 0
        wave.append(e)
        wave_creates += e.replicas

    # [7] submit the remaining final wave
    if wave:
        n_waves += 1
        logger.info("staged warm: wave %d — %d pools / %d creates (budget %d)",
                    n_waves, len(wave), wave_creates, budget)
        self._warm_entries(wave, wait=wait)
```

1. **[1] 取预算（1164）**：只有 create_budget 是 None 才使用配置值；显式传 0 会保留 0，随后进入不分波的路径。
2. **[2] 取计划（1165）**：当前使用已有 self.plan_.entries；若没有可用计划，则调用 self.plan() 后取 entries。
3. **[3] 使用已有池（1166–1171）**：直接交给 _warm_entries，再返回。下层将使用已有池的路径处理，不按新建目标分波。
4. **[4] 关闭分波（1172–1174）**：预算未启用或不大于 0 时，直接提交全部 entries；这不代表关闭预热，也不代表下层可以无限并发。
5. **[5] 建立当前波次（1175–1177）**：wave 收集条目，wave_creates 累计目标副本数，n_waves 只用于记录波次数量。
6. **[6] 检查、提交、再加入当前条目（1178–1187）**：如果已有 wave 加上当前 e 会超过预算，先把旧 wave 交给 _warm_entries，并等待；返回后清空局部列表和累计值，再把当前 e 加进新的一波。未超过预算时，直接加入当前波次。
7. **[7] 提交末波（1188–1192）**：循环结束后，仍有条目就再提交一次。这里传入 wait，而不是写死 True；当前 setup 传的是 True。

<a id="wave-example"></a>

### 4. 用三个计划条目跟一遍循环

以下仅是解释分组的教学输入：预算取 5，按顺序有 A、B、C 三个池，目标副本数分别为 3、3、2。它不是当前默认预算 1000 的实际运行结果，也不需要创建这些环境。

| 读到的条目 | 加入前检查 | 调用及之后的局部状态 |
| --- | --- | --- |
| A：3 | wave 为空 | 不提交；加入 A，累计为 3 |
| B：3 | 3 + 3 > 5 | 先提交并等待 [A]；再加入 B，新一波累计为 3 |
| C：2 | 3 + 2 = 5，没有超过 | 加入 C，当前为 [B, C]，累计为 5 |
| 循环结束 | wave 仍非空 | 提交末波 [B, C]，使用传入的 wait |

1. 分组预算控制这一波交给下层的计划规模；上一波准备好的环境仍可保留，所以它不是整个集群的存活副本上限。
2. 单个池不会被拆分。若某个 e.replicas 自己就超过预算，它仍会单独进入一波；预算不是无例外的硬上限。
3. 只有末波使用传入的 wait。即使调用方传 False，中间波仍然会等待；但当前 setup 的调用全程使用 True。

### 5. 下钻与返回位置

下一处是 [_warm_entries](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1111)。现在先按“接收这一组 PlanEntry，组织它们的预热，并按 wait 等待”理解，不展开内部线程和单池创建。

1. 从第 [6] 项进入它，返回后继续处理当前 e，再检查后续条目。
2. 从第 [7] 项进入它，返回后 start_warmpools 正常结束，控制回到 setup:1423。
3. 下层异常会向上传播，本函数没有捕获后继续的兜底；不能把一次提交直接当作环境已就绪。

## 我的直接表述（原话）

用户在认可 setup 当前逻辑后要求继续：

> 好的 我觉得这里的逻辑没有问题
> 那么我们是否考虑做下一个部分的内容呢?

据此进入 setup 的第 [6] 项。本函数尚无用户关于分波、预算或等待时机的独立复述；上述教学输入与解释均为助手整理。

用户随后明确提出概念与训练场景的疑问：

> 主要这里其实我都不是特别清楚
> 这里的warm到底在组队偶尔是什么呢?
> 以及这里的wave又是什么呢?
> 我其实不是特别理解
> 因为如果是agentic rl的话
> 那么这里的start warmpools
> 不是应该是根据一共load了哪些tasks
> 看到底执行了哪些还需要预热哪些这样子来决定的吗?
> 为什么这里还有这个warmpools呢?
> 其实我没有特别理解

以上概念说明与例子为助手核对后补充，尚未得到用户理解确认。

用户随后把疑问进一步收敛到预热池本身：

> 那么这里的这个预热池在做的是什么呢?
> 我其实没有特别理解这件事情

当前先用备用 3 个、领取 1 个后补充的例子解释池的作用，暂不推进波次算法。尚无用户对该解释的确认。

用户进一步追问不同任务的环境差异：

> 但是每一个任务可能需要的环境不一样?
> 这样子怎么预热呢?
> 我不是特别理解

本次解释任务先加载、按 image 分池，以及领取后题目初始化的区别；尚未收到用户对这些关系的确认。

用户进一步强调需要理解设计所解决的问题，而不仅是按镜像分组的方法：

> 对啊 我的理解就是 如果每一个人物需要的是不同的镜像 那么这里的预热池子的逻辑是什么 这里的fleet没有完全解释这个问题
> 或者说这里的这个fleet的start warmpool没有解决这个问题
> 我希望你告诉我的是当前的这个结构到底解决的是怎样的一个问题
> 我需要知道的是这个

本轮据源码区分“已知环境供给”与“训练需求调度”，未把设计适用性疑问视作用户不理解术语；判断与限制保存在上述 reference。

用户进一步追问任务与已预热环境怎样匹配：

> 或者 我更加想要知道的是 这里到底是如何做到让 任务端口是根据已经热好的内容来获得任务的 否则就会碰到到底是预热池子等命中 还是这里直接通过已经热好的池子来领取任务 这里是怎么做的呢 能看一下吗?

已另行静态核对 [任务定向领取环境的路径](../../../../../../references/task-to-warm-pool.md)：先有 task，再按 task.image 指定池；是否热命中由该池候选与控制器处理决定，不是按已热池反向选任务。当前函数仍只负责准备，领取由 executor / acquire 路径完成。

## 尚不清楚

1. 用户明确未理解 warm、warm pool、wave 及其与 Task、训练批次的关系；本轮先补清这一层。
2. 两处 _warm_entries 调用的等待与返回位置、超大单池例外，尚待确认。
3. _warm_entries 怎样分发条目、_warm_entry 怎样创建或确认池，本轮先停在接口。
4. 训练侧需求更新、当前启动准备和运行中补池的职责边界仍待确认。

<details>
<summary>源码、来源与验证范围</summary>

- 固定提交：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1，当前源码工作区干净。
- 入口：fleet.py:1144–1192；调用方 setup:1422–1423；下一层 _warm_entries:1111–1142。
- PlanEntry：fleet.py:85–102；创建预算默认值：config.py:251；plan 统计镜像并生成条目：fleet.py:815–866；naive 调用次序：strategies.py:92–97。
- 动态批次需求的边界核对：lookahead.py 模块说明及 add/finish 接口；这里只用于对照职责，没有在本轮展开实现。
- [本轮进入与记录](../../../../../../04-flow.md#start-warmpools-entry)。
- 保留前一张 setup 卡认可的“完整函数体与同号解释”呈现；本次只静态核对，没有运行分组实验、创建资源或执行任务。

</details>
