# 新增 SandboxProvider：需要提供什么，覆盖哪些场景

这是一份后续实现 provider 时使用的清单，独立于 steps。它回答的是：**我要让一种新的执行环境接入 Dressage，必须交付哪些接口、数据和行为？** 当前只记录要求，不实施新后端。

要求需要从两侧核对：SandboxProvider 定义共同接口；Paddock、工具适配层和预热生命周期代码决定接口实际怎样被使用。只读 Protocol 不足以确认接入完整。

> 2026-11-07 范围澄清：搭建单集群内部容器平台，可以先复用现有 Kubernetes controller，验证创建、状态、访问执行、回收与基本资源/权限约束，再把平台接成此处的 Provider。Dressage 的 TITO、奖励、训练数据与完整异步 worker 阅读不是搭平台的前置。此页仍是接口要求，不能代替真实集群验证，也不表示已开始实现 Kubernetes 后端。

## 1. 接口层：提供 name 和六个异步方法

要实现当前 SandboxProvider 协议，应对齐下面的方法签名与返回类型；可选参数也应按源码接收。不同模式实际使用的能力有所区别，不支持的能力应明确失败，不能伪造成功结果。

| 需要提供 | 需要完成什么 | 交回什么 |
| --- | --- | --- |
| name | 标识这个后端；用于 lease 归属、配置和诊断 | 稳定的后端名称 |
| create(spec) | 将 SandboxSpec 落实为新建或取得的环境 | SandboxLease |
| terminate(lease 或标识) | 释放已取得的环境或归还池中资源 | 操作结果字典 |
| get_public_url(lease, port, service_name) | 提供指定服务可访问的入口 | SandboxEndpoint，含 URL 和所需请求头 |
| run_command(lease, command, ...) | 在指定环境执行命令，处理 cwd/env/timeout/stdin 等参数 | CommandResult，含输出、退出码和超时状态 |
| read_file(lease, path, ...) | 按路径、编码与读取上限读取文件 | str 或 bytes |
| write_file(lease, path, content, ...) | 写入或追加文件，处理编码 | 操作结果字典 |

完整参数以 [SandboxProvider 协议源码](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/provider.py)为准。它是结构化协议，不强制具体类必须继承它。

## 2. 数据层：正确接收 spec，交回 lease 与入口

**Spec 由 Paddock 构造；provider 消费 spec，不负责为调用者构造它。**

### 输入需要处理哪些含义

1. **trajectory_id**：将这次申请与实际资源关联，供后续查找和回收。
2. **env_type、env_args**：把环境类型与参数映射到后端资源。镜像、模板或已有资源池怎样选择，需要由新后端明确支持范围。
3. **services**：理解服务名称和端口需求；黑盒路径要求可访问的 BlackboxServer。health_path 不是调用方替你部署服务的指令。
4. **timeout_sec、env**：明确支持哪些生命周期限制和进程环境变量，怎样落实；不要把环境寿命、单条命令超时混为一谈。
5. **metadata**：保存/传递需要的资源标签等信息。它与整份 sample.metadata 不同；现有 Paddock 会写入 paddock_mode。

不是所有 env_args 键都由共同协议统一解释。实现时应写明接受哪些键、默认值是什么、哪些需求不支持；具体后端之间也可能不同。

### 返回资料必须能被后续操作使用

| 数据 | 新 provider 应明确的内容 |
| --- | --- |
| SandboxLease.trajectory_id / provider | 对应哪次申请、哪个后端 |
| sandbox_id | 后端的资源标识；类型允许 None，但仍必须有可靠的资源查找/回收办法 |
| endpoints | 服务名到 SandboxEndpoint 的映射；若 create 未填，get_public_url 必须能在相应场景补出 |
| capabilities | 如实标明 command、file、public_url 能力；不能只靠标记代替实际实现 |
| metadata / raw | 后端需要保留的管理资料或 SDK 对象；不要要求上层依赖某个特定 SDK 才能使用共同接口 |
| CommandResult | 区分命令正常非零退出、超时和基础设施异常，不把 stdout 当作唯一成功标志 |

例如 terminate 可能收到完整 lease，也可能收到轨迹标识字符串。当前黑盒 Paddock 在缺失 lease 的回退路径中传入 state.trajectory_id，因此不能默认所有字符串都是 sandbox_id。

## 3. 场景层：接入哪种用法，就验证对应流程

下面不是新增必读课程，而是实现后端时要逐项核对的使用场景。

| 场景 | 调用方怎样使用 provider | 接入时需要确认 |
| --- | --- | --- |
| 普通环境初始化 | Paddock.init → create → lease | 申请落实到正确资源，返回资料能支持后续操作与释放 |
| 黑盒 Agent | init 要求 blackbox 服务，再用 BlackboxServerClient 注册/调用 Agent | 环境中的 BlackboxServer 及目标 Agent 所需运行依赖已部署；入口从调用方可达；环境也能访问配置的 Dressage Proxy |
| 服务入口与健康检查 | 优先用 lease.endpoints；缺失时调用 get_public_url，默认再请求 /health | URL、端口与请求头正确；不能返回无法使用的地址。Paddock 的健康检查不能替代服务部署或证明题目已初始化 |
| 白盒工具执行 | WhiteboxToolAdapter → run_command/read_file/write_file | 实际覆盖工作目录、参数、编码、文件内容和结果结构，不只是能够创建环境 |
| 批量上传文件（可选扩展） | 黑盒 Paddock.write_files 检查并调用 provider.write_files | 若要支持此入口，还需实现批量方法；单个 write_file 不会自动满足它 |
| 提前预热后领取 | store.start 提前执行 Paddock.init，claim 等待结果 | create 不依赖 Agent 已开始运行；结果可以保存一段时间后再使用。预热领取由 store 管，不由 provider 再做一套 |
| 创建途中失败或取消 | 本地等待结束时，远端可能已创建资源或仍在创建 | 已分配但尚未返回 lease 的资源谁来清理、晚到结果如何处理，需要与 Paddock 的清理路径接上 |
| 正常结束、未领取预热或重复清理 | 上层最终调用 terminate | 清理应定位到正确资源；资源不存在或重复释放时的结果要明确，不能误删其他会话 |
| 多条 rollout 并发使用 | 同一个 provider 对象可处理多个 trajectory_id | 申请与管理记录不串线；共享资源池中的可变状态要满足任务隔离要求；异步方法中避免阻塞整个事件循环 |

其中最后几项的完整保证并不由 Protocol 自动检查。它们需要实现者结合后端的创建、取消、超时及并发语义验证，不能由“方法名字齐了”推断已经满足。

### 失败与取消尤其要明确的责任边界

1. **create 尚未交回 lease**：如果已经部分分配资源，provider 应提供自己的回滚/补偿逻辑；上层可能还没有足够资料清理它。
2. **lease 已交给 Paddock**：后续入口取得或健康检查失败时，现有 Paddock 会尝试 terminate(lease)。
3. **调用方取消，但远端创建还在进行**：现有 Paddock 会保护创建任务并安排接手晚到的 lease；新后端仍要说明 SDK/API 是否可取消、是否可能创建后丢失响应。
4. **清理可能失败**：要让上层能识别结果。是否需要资源寿命上限、标签检索或后台清扫，属于新后端需评估的工程补充，不是现有协议已经保证的能力。

## 4. 接入层：写完类以后，还有哪些地方要接上

1. **让调用方能取得新 provider。** 直接构造 Paddock 时可注入 provider 对象；若沿现有环境变量路径使用，需要修改 sandbox/factory.py 的名称选择与构造逻辑，并定义连接参数。只设置一个新名称，现有工厂不会自动发现新类。
2. **对齐环境参数约定。** 文档说明新后端如何解释 env_type、镜像/模板、端口、超时和附加参数。若上层参数筛选没有转交所需字段，还需调整相应接入位置。
3. **若要使用标准预热调度，核对开关策略。** 当前 prewarm_enabled 只对 e2b 开放。新增 provider 具备 create 并不意味着标准 Scheduler 自动为它启用预热，还需评估并接入该策略。
4. **选一个完整正常场景验证，再覆盖失败路径。** 黑盒看“创建 → 入口/健康 → 注册并调用 → 释放”；白盒看“创建 → 命令/文件 → 释放”。随后验证取消、重复清理和多会话并发。这里列的是未来实现的验证目标，本次没有运行这些场景。

## 5. 新 provider 不需要包办什么

- 选择未来哪组任务、预热多少：属于 rollout worker / Scheduler。
- 按 session_id 保存和领取初始化 Task：属于 PrewarmStore。
- 选择 Claude Code、Codex 等 Agent 并处理其注册消息：属于 Paddock、BlackboxServer 与 Agent 适配器；provider 只需交付所选场景可运行的环境与依赖。
- 模型请求协议转换、轨迹记录、奖励和训练样本转换：分别由代理及训练接入层处理。
- 构造 SandboxState：属于黑盒 Paddock，provider 返回的是 SandboxLease。

如果后端是 Kubernetes，可以由 provider 或其下层管理 Pod/Service 等资源，但要对上保持同样的数据和生命周期约定。当前仓库没有内置 Kubernetes provider；也不要求所有 provider 都用 Pod。

## 6. 对照源码时只需先打开这些入口

以下均为固定提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c：

| 要核对的要求 | 源码入口 |
| --- | --- |
| 共同方法与参数 | [sandbox/provider.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/provider.py) |
| 输入输出对象 | [sandbox/types.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/types.py) |
| 黑盒对 create、入口、文件扩展及释放的使用 | [blackbox/paddock.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py) |
| 白盒命令与文件的调用参数 | [whitebox/tools.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/whitebox/tools.py) |
| 失败/取消后的释放 | [paddock/lifecycle.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/lifecycle.py) |
| 工厂接入 | [sandbox/factory.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/factory.py) |
| 预热启用策略 | [prewarm/config.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/config.py) |
| 对照一个本地实现 | [local/bwrap/provider.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/local/bwrap/provider.py) |
| 对照一个远端实现 | [remote/e2b/provider.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/remote/e2b/provider.py) |

本机源码：/home/fredkeira/projects/Dressage。本页由接口和调用方静态核对整理；工程验证项与已实现保证分开，不声称当前所有后端已经满足全部目标。本次只更新这份文档，不修改 steps 或实际 provider 代码。
