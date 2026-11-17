# Dressage 与 Agent Sandbox：谁决定预热，谁领取环境

[当前阅读入口](../README.md#current-reading) · [Agent Sandbox 的领取路径](../topics/fleet-environment-orchestration/steps/step-001-start-warmpools/references/task-to-warm-pool.md) · [全异镜像时的设计边界](rl-batch-flow-and-entry.md#unique-images-and-provisioning-boundary) · [Dressage 阅读记录](../../dressage/README.md)

## 1. 本次结论与比较范围

针对“每个任务需要独有环境，提前为后续 RL 任务准备，再准确交给同一个任务”的目标，Dressage 的异步 rollout 预热设计比此前阅读的 Agent Sandbox naive/start_warmpools 路径更贴近需求。它按 sample/session 预热，不要求同镜像有持续的备用库存需求。

但 Dressage 当前也没有根据环境 Ready 顺序反向选择任务。它先按 FIFO 取预取组，进入 dispatch 后再按 session_id 领取；该 session 的初始化没结束时会等待。不能将它描述成“只运行已经预热完成的任务”的调度器，也没有本次性能测试证明它普遍更快。

这比较的是应用侧任务调度方式。Agent Sandbox 还有 sliding、pipelined、LookaheadWarmer 等其他入口，不能把 naive 的限制扩展成整个项目没有相应能力；Dressage 的预热层也不替代 Kubernetes 资源协调与隔离机制。

## 2. Dressage 的实际链路

1. [异步 worker](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/fully_async_rollout.py#L330)维护正在执行的组和结果队列。循环中先处理完成组，再调用预取调度器，为后续组准备环境；任务执行和后续初始化可以重叠。
2. [PrewarmScheduler.do_prefetch](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/scheduler.py#L50)从 data_buffer 取具体 sample 组，填充预取队列；ahead 以组为单位，默认 8。
3. [_prefetch_and_prewarm](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/scheduler.py#L90)逐 sample 提取 env_args，其中可以包含各自的 sandbox_image，再调用 start_prewarm。
4. [PrewarmStore.start](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/store.py#L78)为 sample 固定 session_id，深复制环境参数，用 asyncio.create_task 提前执行 paddock.init，并把初始化任务保存在 _records[session_id]。
5. [blackbox_dispatch.generate](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L183)使用同一个 session_id 调用 claim_prewarm。命中后取得同一份 paddock、state 和 env_args，直接继续注册并执行 Agent，不再创建第二份环境。
6. [PrewarmStore.claim](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/store.py#L115)先移走记录，再等待这份 record.task；取得后转移所有权。没有记录或初始化失败时返回 None，dispatch 用新的 session_id 内联初始化。
7. [组清理](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/store.py#L143)处理从未被 dispatch 领取的预热；已领取环境由 dispatch 的退出路径负责回收。取消期间的晚到创建结果也有对应生命周期处理，但这些路径不等于远端故障下绝对不会泄漏。

```text
future sample + its environment arguments
  -> stable session_id
  -> async paddock.init(session_id, ...)
  -> PrewarmStore._records[session_id]
  -> dispatch the same sample
  -> claim_prewarm(session_id)
  -> await that initialization task
  -> same environment handle
  -> register and execute Agent
```

## 3. 和刚才读的 Agent Sandbox 路径比较

| 问题 | Agent Sandbox：当前 naive 路径 | Dressage：异步 worker + prewarm |
| --- | --- | --- |
| 预热对象 | 按镜像计划维护对应池的备用副本 | 对已知的具体 sample/session 提前初始化一份环境 |
| 每题不同镜像 | 各镜像形成各自池；naive 先准备整批 | 每个 sample 携带自己的 env_args，独有环境也能提前创建 |
| 领取依据 | task.image → 计划中的集群/池 → Claim | sample.session_id → 对应初始化任务与环境句柄 |
| 是否等待整批预热 | naive 在 executor 前等待 setup 返回 | 初始化可与当前 rollout 重叠；选中 sample 后仍会等待自身初始化 |
| 是否优先运行 Ready 任务 | 默认执行器未按池就绪状态挑任务 | 没有；pop_next_group 使用预取队列的 pop(0) |
| 预热资源怎样退出 | 池备用目标在缩减或 teardown 前继续存在 | 不再消费的预取组清理未领取环境；领取后由任务生命周期负责 |
| 核心价值 | Kubernetes 环境供给、备用池和领取机制 | RL 任务组预取、按 session 精确交接、取消与回收协调 |

## 4. 对用户场景的实际意义与限制

1. **更贴近需求的部分**：下一批的某个任务已确定需要独有镜像，可以为它提前创建，并保证该任务按 session_id 找到自己的环境；不依赖“后续还有相同镜像任务”才能使用这种提前准备。
2. **尚未解决的部分**：先排队的组仍可能等待慢环境，即使后面某组已就绪。异步调度可以同时处理其他活动组，但它没有以 Ready 作为挑选下一组的依据；不是自动的就绪优先调度。
3. **范围限制**：[prewarm_enabled](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/config.py#L11)仅对 provider=e2b 启用，local_bwrap 即使设置预热开关也跳过；后者有自己的预创建槽位池。不能把本次 E2B 行为直接当作任意本地镜像或 Kubernetes 集群的实现。
4. **镜像要求**：E2B 的 [sandbox_image 选择](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/remote/e2b/provider.py#L388)指向预先构建的 E2B 模板；黑盒模式要求模板预置对应服务。它不是直接把任意 Docker 镜像字符串交给本地 Docker 运行。
5. **资源预算**：ahead 控制预取组数，额外环境数量约随 ahead × n_samples_per_prompt 增长；还有正在执行的组。未领取资源清理积压时，调度器暂停新增预取，但不能把 ahead 理解成整个系统绝对的环境数上限。
6. **命中语义**：claim 等到指定初始化完成也会算预热命中，所以 hit 并不保证零等待；dispatch 同时记录 prewarm_wait_seconds。

## 5. 验证与证据边界

2026-11-04 核对本地 checkout：Dressage 为 /home/fredkeira/projects/Dressage，提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，工作区干净；Agent Sandbox 为 /home/fredkeira/projects/agent-sandbox，提交 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。旧笔记的 /Users/dextermayhew/projects/Dressage 是历史路径，未批量重写原步骤引用。

读过仓库中的 prewarm_store、prewarm_scheduler、prewarm_provider_integration 及相关 dispatch 测试。当前执行环境缺少 pytest_asyncio、pydantic 等依赖，未运行这些 pytest 测试，也没有安装依赖或调用云服务。

另用标准库隔离实验加载源码中的 PrewarmStore、PrewarmScheduler 原始定义，注入假的 provider 与输入缓冲区：A 的初始化被 Event 暂停，B 先完成。观察结果为：

1. pop_next_group 仍先选择 A，未因 B 就绪而重排。
2. claim(A) 保持等待，claim(B) 能得到 B 自己的 image-b 环境。
3. 放行 A 后，只取得 A 自己的 image-a 环境。
4. 再领取 B 返回 None，说明同一条记录只交接一次。
5. 两次成功领取后，store 无未领取记录。

实验脚本位于本次会话的 /tmp/dressage_prewarm_probe.py。它验证局部匹配、等待和取出顺序；不验证真实 E2B、Kubernetes、吞吐、成本或故障恢复效果。

## 6. 如果接着阅读

更适合用户当前问题的首个入口是 PrewarmScheduler.do_prefetch，接着追踪 PrewarmStore.start → claim → blackbox_dispatch.generate。先回答“具体未来任务怎样提前初始化、执行时怎样领回同一个环境”，再考虑是否需要改为就绪优先调度。本次仅比较，没有创建 Dressage 新步骤或替换 Agent Sandbox 的既定学习范围。


<a id="reading-investment"></a>

## 7. 后续阅读投入：RL 调度看 Dressage，Kubernetes 协调看 Agent Sandbox

用户进一步询问是否应将 Agent Sandbox 的学习重点放到 Kubernetes 侧，并提出其 WarmPool 机制是否不如 Dressage。

建议把任务侧预热调度与资源侧预热池分开评价：Dressage 的 sample/session 前瞻更贴近“独有环境、后续具体任务提前准备”的问题；此前选读的 Agent Sandbox naive 示例是有限任务集合的基线。这个比较不足以判定 Kubernetes WarmPool controller 较差，也不涉及真实吞吐优劣。

对当前学习目标，Agent Sandbox 更值得继续精读的是：

1. 单个 Sandbox 资源如何经控制器产生 Pod、Service 和需要的 PVC，并把观察到的状态写回。
2. WarmPool 如何按期望数量维持备用环境，在缓存滞后、创建失败、资源不足或领取突发时避免错误补池和持续重试。
3. Claim 如何定向领取、避免并发重复分配、转移控制归属，并处理未命中与清理。

这些是通过 Kubernetes API 管理沙箱工作负载的实现；不是重新实现 kube-scheduler、kubelet，也不是代替整个集群控制面。

下一入口建议先选 controllers/sandbox_controller.go 的 SandboxReconciler.Reconcile，再聚焦 reconcileChildResources（507 行）和它管理 Pod 的调用。先回答“一份 Sandbox 对象如何变成可用的环境”，然后再接批量池与 Claim。当前 Python Fleet、wave 和有限任务策略已有基础定位，无需以逐一读完它们作为进入控制器的前置。

以上是阅读重心建议，原四项学习目标和历史卡片保留；尚未创建控制器步骤、改写 Step 001 scope 或宣称原步骤全部机制已经完成。


<a id="dressage-kubernetes-provider-boundary"></a>

## 8. 2026-11-05：Dressage 是否直接提供单个 Pod 的启动配置

本次核对本地 /home/fredkeira/projects/Dressage，HEAD 仍为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，工作区干净。结论限定在该 checkout 的 Dressage 自有代码与已跟踪文件：未找到内置 Kubernetes sandbox provider、创建 Pod 的 Kubernetes API 调用，或面向单任务沙箱的 Pod/Job/Deployment YAML。

1. [provider 工厂](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/factory.py#L10)只注册 e2b 和 local_bwrap；传 k8s 或 custom 不会自动得到新 provider。
2. e2b 委托远端 E2B API 创建沙箱；该仓库不展示这项服务内部如何调度底层基础设施。
3. [local_bwrap](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/local/bwrap/provider.py#L17)使用 Ray 管理的槽位池；[LocalSandboxRunner.start](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/local/bwrap/runner.py#L331)通过 create_subprocess_exec 启动本地隔离进程，不创建 Kubernetes Pod。
4. [docker/Dockerfile](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docker/Dockerfile)与 README 的 docker run 用于构建/运行 Dressage 容器环境；这不同于一条 rollout 请求触发一个新 Pod 的生命周期实现。
5. [SandboxProvider 协议](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/provider.py#L15)保留 create、terminate、get_public_url 及命令/文件接口。因此可以接入 Kubernetes，但需要实现对应 provider。

仓库的 [Custom SandboxProvider 文档](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docs/blackbox-swegym-claude-code-experiment-zh.md#L188)明确说明：已有能够按样本启动镜像的 Kubernetes 平台时，可以自行实现该协议。它还要求 create 处理 sample 的 sandbox_image、sandbox_cmd、服务健康与端口，并返回 SandboxLease；通过 DRESSAGE_PADDOCK_CLASS 注入自定义 paddock。这里提供的是接入合同，不是已完成的 Kubernetes backend。

要区分两个目标：把 Dressage 程序部署到一个 Pod 中，可以额外编写部署清单；让 Dressage 每次为任务创建、等待和回收一个 Pod，则需要底层 provider 或外部平台支持。当前仓库没有现成配置把这两件事自动接起来。

核对方式：搜索自有代码中的 Kubernetes/k8s/kubectl/Pod API 等关键字，盘点 git 跟踪的 YAML 和 Dockerfile，并核对 provider 工厂与生命周期入口。Git 子模块 slime 当前未初始化（git submodule status 的前缀为 -），不把本次结论扩展到未展开的上游子模块或外部 E2B/Harbor 服务。未安装、部署或启动任何运行环境。


<a id="revisit-for-harbor-integration-20261117"></a>

## 2026-11-17：复用原生预热认识，收敛 Harbor/K8s 接入路径

用户的问题分为四项：记忆核实（blackbox dispatch 是否已有预热）；机制核实（它怎样准备与交接）；方案判断（当前是否应考虑复用）；目标约束（K8s 主要服务接入与岗位实践，不无限扩大阅读）。

本机 `/home/hongshi/projects/Dressage` HEAD 仍为 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`，工作区干净。重新读取 scheduler.py、store.py、config.py、blackbox_dispatch.py 和 fully_async_rollout.py，并查阅 Dressage 原生 Step 002 的 start/claim 卡。原生预热已实际讨论过，不能当作完全没读过的新模块。

真实交接仍是 do_prefetch 取后续组 → 按 sample 创建固定 session 的初始化 Task → store 保存 → dispatch 按 session claim → await 同一 Task → 使用返回 state。没有预热记录或初始化失败则按新 session 内联初始化。claim 命中也可能等待，组选择仍是 FIFO。store 保存的是初始化记录/任务，不是 Kubernetes WarmPool 资源。

限制同样仍在：prewarm_enabled 仅对 provider=e2b 开启；provider 工厂公开 e2b/local_bwrap。对当前 harbor integration 源码搜索未见 PrewarmScheduler、start_prewarm 或 claim_prewarm 调用，所以不能说 Harbor Environment.start 已复用这套预热。任务特定的提前初始化与集群侧按模板维持库存可以组合，但需要显式设计环境身份、所有权与清理，不能直接叠加后假定可用。

针对用户当前目标的建议：先用已有 start/claim 卡短回顾，保留“已知下一题就提前初始化、以后领回同一份环境”的模式；继续沿 Harbor Environment 接入 Agent Sandbox，不另外启动将原生 PrewarmStore 移植到 Harbor 的工程。先完成一份环境的真实命令/文件/释放，再加入一个小预热池，验证两份 Trial 独立领取与回收，最后记录一次失败定位及冷/热时间。只有实测表明需要按未来题目精确前瞻时，再将原生预热策略作为改进候选。

此为阅读和实践建议，不代表新步骤已获确认、代码已移植或集群验证已完成。此次未运行测试或云服务。
