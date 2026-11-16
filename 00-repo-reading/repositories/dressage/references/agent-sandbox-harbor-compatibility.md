# 当前 Agent Sandbox 与 Harbor 的兼容性核对

最新版本核对：[2026-11-11：Dressage 的 0.18.0 锁定与 Harbor 0.25.0 升级边界](#harbor-version-upgrade-20261111)。本机现已存在 Harbor checkout；以下原有 2026-11-08 结论保留历史归属。

[环境接入 scope](../topics/02-harbor-integration/steps/step-013-harbor-kubernetes-environment/01-scope.md) · [Harbor 已有 K8s 后端](harbor-kubernetes-backends.md) · [整体接入研究](agent-sandbox-harbor-integration-research.md)

2026-11-08。**结论：当前本地 checkout 不能按现有示例直接组成可运行的 Agent Sandbox + Harbor + Dressage 链路。** 架构上有 Environment 接缝，Agent Sandbox 也有相应资源能力，但缺少示例指定的适配实现，且示例与 Dressage 的 Harbor 版本要求不一致。不能把这项判断扩大为“Agent Sandbox 原理上不能接 Harbor”。

## 1. 本次核对的实际版本

| 组件 | 本地版本或要求 |
| --- | --- |
| Agent Sandbox | 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1，已跟踪工作区干净 |
| Dressage | 3e3142fe8ea07e4504c3b20a936a4c201a3de44c |
| Dressage 使用的 Harbor | pyproject 声明 harbor==0.18.0，compat 运行时也严格检查该版本 |
| Agent Sandbox 的 Harbor 示例 | README 要求 harbor>=0.25，使用外部 Environment 类 |

这里检查的是代码、配置及版本保护条件，没有运行集群、Harbor Trial 或模型。

## 2. 两个直接阻碍

### 2.1 示例在，但指定的适配代码不在当前源码树

[sample.yaml](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/harbor-terminal-bench/configs/sample.yaml) 指定：

```yaml
environment:
  import_path: k8s_agent_sandbox_harbor:AgentSandboxEnvironment
```

[示例 README](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/harbor-terminal-bench/README.md)要求安装 clients/integrations/harbor。但本次同时核对文件系统与 Git HEAD 树：

1. 该目录不存在。
2. git ls-tree 没有列出其中任何文件。
3. 当前 clients 下没有 AgentSandboxEnvironment 实现，已有集成清单也没有这一项。
4. run-sample.sh 本身会先检查能否 import k8s_agent_sandbox_harbor，失败就退出；因此不能把有配置示例等同于已经具备实现。

本次补查官方 main 的该路径 pyproject.toml 与 PyPI 包元数据，均未取得实现（返回 404）；GitHub contents API 在工具中不可访问，未作为 HTTP 状态证据。外部代码可能位于其他分支或尚未公开，本次不据此断言它在任何地方都不存在。PyPI 未收录本身也不是决定性证据，因为仓库说明部分 integrations 不发布到 PyPI；决定当前结论的是本地与 HEAD 的实现缺失。

### 2.2 示例版本不能直接放进当前 Dressage

[Dressage pyproject](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/pyproject.toml)锁定 0.18.0；[require_harbor_runtime](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py)会拒绝其他版本，还要求 Python >=3.12。

本次从原文件提取版本检查函数及必要定义，显式传入 Python 3.12 与两个版本做局部验证，结果是：

```text
0.18.0 -> accepted by original version guard
0.25.0 -> unsupported Harbor version '0.25.0'; expected exactly '0.18.0'
```

这只验证版本保护分支，不是安装或端到端兼容测试。不能仅放宽依赖和这条检查，就假定其依赖的 Harbor 私有接口与生命周期仍然兼容。

## 3. 接口方向可以对应，但不是换一个类名就完成

| Harbor 需要的能力 | Agent Sandbox 侧可用的方向 | 必须继续核对的内容 |
| --- | --- | --- |
| start / Ready | Template、WarmPool、Claim，以及 Sandbox/Pod 状态 | 模板生成、镜像准备、冷创建与热领取的条件、等待执行入口可用 |
| stop(delete) | 删除 Claim 并按归属回收 | 保留环境与删除环境的区别；关闭本地连接不是删除资源 |
| exec(command, cwd, env, timeout, user) | SDK 的命令服务，或 Kubernetes pods/exec | 题目镜像是否运行 SDK 所需服务、工作目录/环境变量/用户、超时与输出合同 |
| 文件和目录上传下载 | SDK 文件能力，或通过 Pod exec 传 tar | 文本/字节、目录、权限、退出状态与中断后的行为 |

当前 SDK 的 commands.run 支持 command_timeout；env/cwd 仅在 sandboxd 路径支持，legacy runtime 会拒绝这些选项。示例文档则描述直接用 pods/exec 和 tar 操作题目镜像。两种数据通道不能在没有实现证据时当作等价替换。

另外，Harbor 的 ACK 后端使用 agents.kruise.io 的 SandboxClaim；目标 Agent Sandbox 的扩展资源属于 extensions.agents.x-k8s.io。现成 ACK Claim 路径不能仅因同名就直接操作这套 CRD。

## 4. 对当前方案的影响

1. **如果目标只是在 K8s 上运行任务**：先评估 Harbor 已有的 GKE/ACK/OpenShift 后端，可能不需要 Agent Sandbox 专用适配。
2. **如果明确要复用这套 Agent Sandbox 的 WarmPool/Claim**：先取得示例引用的实现或按 Environment 合同补齐桥接，再核对版本。当前不能标记为开箱即用。
3. **如果还要原样复用当前 Dressage**：以 Harbor 0.18.0 作为明确基线，或者将升级 Dressage compat 与生命周期的工作单独验证；不能让示例的 >=0.25 约束悄悄替换整个基线。
4. **取得实现之后再做最小验证**：先一题 Oracle、预制镜像、冷创建、命令/文件、Verifier 和删除；通过后再增加模型、预热和并发。这是后续验证顺序，本次未执行。

本轮没有更改任何源码仓库、安装依赖或部署资源。阅读计划的 Environment 接缝仍然成立，但其第一项工作是确认和取得兼容实现，而不是直接运行当前示例。

<a id="integration-first-reading"></a>

## 5. 如果本轮优先做接入，阅读怎样安排

2026-11-08，用户进一步询问同时兼顾 Dressage、Harbor 与 Agent Sandbox 时的必要知识和顺序。下面是针对实际接入目标的优先级建议，不重编号已有 Step，不把已准备的全部 scope 变成接入前置，也不直接改变项目当前阅读进度。

随后用户重申：“主要的目标是腾讯的强化学习框架这个岗位”。因此本节保留为接入子任务的参考，不作为当前学习顺序的自动替换。岗位主线仍需覆盖结果到训练/评测数据、组件扩展、并发失败治理和集群实践；不能把完成 Harbor–Agent Sandbox 的版本适配当作全部目标。

### 5.1 先弄清三方分别负责什么

1. Harbor Trial 组织一次任务，Agent/Verifier 使用 Environment 提供的执行和文件能力。
2. 目标桥接层实现 Harbor 的 Environment 合同，把环境生命周期映射到 Agent Sandbox；不必因此重写 Dressage 原生 Paddock、BlackboxServer 或 CLI adapter。
3. Dressage 的 Harbor 插件负责相关模型路由、尝试身份、轨迹和结果收尾。环境接通只是其中一部分，还要验证插件与模型接口。

### 5.2 最小阅读与验证顺序

| 顺序 | 对应已有材料 | 这次只需解决什么 |
| --- | --- | --- |
| 1. 固定版本和取得实现 | Dressage compat.py；本页第 2 节；Step 010/013 的前提 | 优先以当前 0.18.0 为兼容基线，确认取得的桥接实现适用版本；若升级，先验证 Dressage 依赖的私有接口，不只改版本号 |
| 2. 定位入口和生命周期 | Step 010 短定位 → Step 011；Step 012 的一题配置 | 知道 Job/Trial 谁创建环境、何时调用 Agent/Verifier、何时停止；无需完整阅读训练批次或所有 Agent |
| 3. 明确 Environment 合同 | Step 013；BaseEnvironment、EnvironmentFactory；现有 K8s adapter | 列出 start/stop、exec、文件/目录传输及资源配置的输入输出，检查实际分支能否兑现，不能仅凭已有类名认定兼容 |
| 4. 选择 Agent Sandbox 控制面与执行通道 | K8s 主题的当前状态、Claim 及 SDK 入口 | 明确每个 Trial 的资源身份、创建/领取/Ready/删除；选择 pods/exec+tar 或镜像内的 SDK 服务。确认题目镜像、cwd/env/user 和超时支持，不把两种通道当成相同实现 |
| 5. 验证一题冷创建 | Step 013 的局部验证，结果并入 Step 017 | 预制镜像 + Oracle/确定性执行，覆盖创建、文件、命令、Verifier 和删除；此时先验证环境合同，不声称 Dressage 模型采集也已经兼容 |
| 6. 接入模型与完整结果 | Step 014 → Step 015；按需回查原生 Step 007/008 | 验证 Pod 到 Gateway、Gateway 到 Proxy 的访问；核对模型请求、finalize、read_trajectory 与 trial/attempt/session 关联，再接真实 Agent |
| 7. 扩展到预热和失败 | K8s Step 004/005 → Dressage Step 016/017 | 先准备备用环境，再用少量并发检查独立领取；追一次取消或重试，验证清理和不重复提交 |

Harbor 内置后端可作为 Environment 方法实现的参考；若目标仍指定 kubernetes-sigs/agent-sandbox，最终创建/领取/删除要对应它的资源合同。控制器内部所有补池算法不应成为首次冷创建验证的前置，但正式使用预热前必须理解 Claim 归属与未命中行为。

### 5.3 不能漏掉的接口细节

1. **环境身份与所有权**：一个 Trial/attempt 对应哪个 Claim/Sandbox，超时或重试时谁删除旧资源，delete=false 留下什么。
2. **命令与文件**：cwd、env、user、stdout/stderr、退出码、命令超时、目录上传下载及二进制内容。Harbor Agent 安装和 Verifier 往往会用到这些能力。
3. **就绪标准**：Kubernetes Ready 与实际可执行命令是不同检查点；题目/Agent 初始化也不等于环境 Ready。
4. **模型网络与归属**：Gateway 广播地址必须从 Pod 可达；本机示例的 host.docker.internal 不能不加核对就用于集群。凭据和会话身份按原插件合同传递。
5. **结果与训练边界**：任务跑通、评分成功、API 日志采集、可训练 token/logprob 是不同验收项。不能靠占位值把缺失数据标成真实训练轨迹。

### 5.4 既有阅读不作废，但不全部成为前置

Step 007–009 适合继续理解原生闭环；它们不是编写 Harbor Environment 的强制依赖。需要了解 finalize/read 或清理语义时可按问题回查。Step 008 的训练字段在真正接 Slime 训练输出时再重点核对。

首个接入版本无需通读所有原生 worker、所有 CLI 适配器、完整 TITO、完整训练后端或全部 K8s 控制器。前面把完整学习路线讲成接入前必须顺序完成，会推迟关键兼容性验证；本节明确区分两种用途。是否按此优先级切换下一处实际带读，仍由后续明确的阅读指令决定。


<a id="environment-replacement-boundary"></a>

## 6. 2026-11-09：能否保留 Dressage/Harbor，只替换 K8s 环境层

用户希望通过完整走通 Harbor integration 确定实际替换位置，复用已有框架而集中完成 K8s 沙箱适配。本轮再次核对固定版本本地源码，结论是：**在沿用已有任务/Agent/模型后端及结果协议的前提下，主要新增实现可以集中在 Harbor Environment 后端；但交付范围还包括环境配置、Gateway 可达性和接口语义验证，不是只换容器启动命令。**

### 源码证据

- `dressage/integrations/harbor/config.py:29` 定义 NativeEnvironmentConfig（mode="native"），与 bwrap 模式区分。native 在此表示委托 Harbor 环境后端，不代表强制本地进程运行。
- `rollout.py:_temporary_job_config`（:566）只有在 bwrap 模式才将 Environment import_path 改为 DressageEnvironment。native 模式不覆盖来源 JobConfig 的 environment，说明目标环境可在 Harbor 配置/实现层选择。
- 示例 `harbor_job_configs/terminal-bench-2-e2b.yaml` 使用 `environment.type: e2b`；对应 `dressage_profiles/training-native-remote.yaml` 使用 `environment.mode: native`，说明 Dressage 插件已与远程沙箱方案分离。
- `_run_partition`（:760）仍走 plugin.on_job_start(job) → job.run() → plugin.on_job_end(result)。插件 `on_job_start`（plugin.py:261）注入 Agent 模型地址/凭据并注册 Trial 事件，而不在这里直接创建某个 E2B 容器。
- `_inject_agent_routing`（plugin.py:1033）把 gateway URL 写入 Agent 环境；`_gateway_public_url`（:1298）支持配置 advertise_url。换 K8s 环境后必须提供 Pod 可达地址，设置 URL 本身不创建网络连通性。
- artifacts.py 的 commit_attempt 继续通过 Proxy finalize/read 取得轨迹并结合 Trial 结果；按原接口运行时无需为每个环境后端重新实现轨迹转换。

### 主要变化与保留内容

| 层次 | 本轮目标 |
| --- | --- |
| Harbor Job/Trial、已有 Agent 与 Verifier | 保留；用同一题和同一 Agent 作为基线 |
| Dressage 的插件、Gateway/Proxy、结果/训练适配 | 原则上保留，验证其接口及身份传递 |
| Harbor Environment 实现 | 目标适配位置；对接现有 Agent Sandbox/K8s 能力 |
| 配置和部署 | Harbor 选择适配实现；Dressage 用 native；配置 Pod 可达的 Gateway 地址与匹配网络规则 |

环境适配必须兑现 start/stop、exec、文件与目录传输，并核对任务镜像准备、cwd/env/user、退出码与命令超时、delete/保留资源、能力声明及网络限制。单纯 Pod Ready 不等于这些合同都通过。

### 已知条件仍然存在

Harbor 自身已有 GKE/ACK/OpenShift 等 K8s 实现，所以不是为 Harbor 从零发明 K8s 能力。本目标是接入指定 kubernetes-sigs/agent-sandbox，不能将其他 CRD 后端当作等价实现。

Dressage 仍严格固定 Harbor 0.18.0、Python >=3.12；本地 Agent Sandbox 例子引用的 Harbor 适配目录仍未找到，且示例要求不同版本。不能只修改一个 type 字符串就声称已经接通。优先按固定版本 Environment 合同核对复用或补齐方案；升级作为独立验证事项。

若同时更换不兼容的商业模型 API 或任务格式，会额外产生模型/数据协议适配；上述“集中于环境层”的判断以其他合同维持既有支持范围为前提。

### 阅读应该覆盖哪里

完整走通一条集成主线有价值，逐行读完整包不是前提。当前优先顺序：Job 环境配置来源 → _run_partition 的 Job/插件交接 → Harbor Trial 的 Environment 调用 → BaseEnvironment 与一个现成后端 → 目标 Agent Sandbox 实现；最后验证插件的模型网络和结果回收。

停止标准：能指出实际需要实现的 Environment 方法、配置加载位置、数据/网络/回收合同，并给出一题可运行验收。批次采样细节、统计和复杂重试内部按实际适配问题回查。

验证范围：本轮读取了 Dressage 源码、已跟踪的 docs/harbor.md 和示例；未使用新增 docs/wiki 内容作为证据，未修改业务代码、安装依赖、启动模型或运行 K8s。当前未发现本地 Harbor checkout，因此不把固定版本基类及所有能力合同当作本轮运行验证。


<a id="harbor-version-upgrade-20261111"></a>

## 2026-11-11：版本锁定与升级边界

本轮为只读源码对照，没有修改依赖、checkout、源码或安装环境；未运行 Harbor Job/模型/集群。用户希望知道 0.18 来源、升级方法、旧阅读是否仍有效及当前 Harbor 情况。

### 1. 版本由谁确定

- Dressage 本地 HEAD：`3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。其 [pyproject.toml:22](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/pyproject.toml#L22) 在 harbor extra 中精确声明 `harbor==0.18.0`。
- [compat.py:13、57](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L13) 定义 SUPPORTED_HARBOR_VERSION 并要求精确相等。只安装新版会在运行时被拒绝，不是宽松的最低版本。
- tests/integrations/harbor/test_contracts.py 包含拒绝 0.18.1 的测试、0.18 版本断言和任务/Trial 顺序契约。兼容层依赖 `_remaining_trial_configs`、`_task_configs`、`Job._resolve_task_configs` 以及 Trial 排列/对象对应关系。

### 2. 当前本地与发布版必须分开

| 对象 | 本轮核对结果 |
| --- | --- |
| Harbor 本地仓库 | `/home/fredkeira/projects/harbor`，main，工作区干净 |
| 本地 HEAD | `500af91374dcc43b59fac54cf90295646617b14d`，提交日期 2026-11-10 |
| 本地 pyproject 声明 | 0.25.0，Python >=3.12 |
| 当前 PyPI 最新发布 | [0.25.0](https://pypi.org/project/harbor/0.25.0/)，官方 JSON 查询的上传日期 2026-10-25 |
| v0.25.0 标签提交 | `fdba28fc411e47e8765420a1a063b4918fce3def` |
| HEAD 与标签差别 | 本地 HEAD 在标签之后有 123 个提交，不能把本地 main 当成发布 wheel 的同一份代码 |
| 旧阅读提交 | `527d50deb63a5d279e8c20593c18a2cbc7f61f9e`，其 pyproject 为 0.18.0，本地 git 对象可查 |

版本号相同不保证 checkout 等于发布标签。升级应固定发布版本及其提交，或明确选择 main 的具体 SHA。这里只对照，没有自动切换正式阅读版本。

### 3. 已确认保留与需要验证的接口

- **核心流程仍在**：v0.25.0 的 [Job.run:1082](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1082) 仍组织队列与汇总结果；[Trial.run:601](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L601) 仍有 prepare/run/finalize 主线。旧笔记的职责模型可复用，原行号与全部细节不能直接视为新版事实。
- **任务/尝试规划有重构**：v0.25.0 中 Job 的任务解析与普通 Trial 构建委派给 [JobPlan](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job_plan.py#L139)。普通 Trial 的循环仍按 attempt → task → agent，旧兼容层用到的私有字段及解析方法仍可见；这支持有针对性的迁移，不等于已通过对象身份、命名写回和重试测试。
- **插件基本事件仍在**：v0.25.0 Job 仍有 on_trial_started/on_agent_started/on_agent_ended/on_verification_started/on_trial_cancelled/on_trial_ended，TrialHookEvent 仍暴露 config/result/trial_name/trial_id。必须验证实际事件顺序、AgentConfig 路由注入、结束/取消和重复提交语义。
- **环境合同有变化**：v0.25.0 BaseEnvironment 将显式 mounts 与 auto_mounts 区分，并默认 auto_mounting=False；资源、传输和采集逻辑也有增加。Dressage 的 bwrap 实现读取 `_mounts`，还根据 mount 形状识别 verifier，需专门验证/适配。它不是仅修改版本字符串就能证明可用的部分。
- **本地 main 还有额外变化**：相对发布标签，preflight 开始支持 kwargs 参数，内置选项校验等有进一步调整。不要把这些 HEAD 行为混写成 v0.25.0 发布版行为。
- **结果与训练合同需回归**：确认 JobResult/TrialResult 与插件轨迹能完成模板匹配、token/mask/reward 转换、版本检查、部分失败和清理。API 请求成功或非空 reward 都不能替代训练数据合同验证。

### 4. 建议的迁移顺序

1. 保留当前 0.18 基线和原阅读记录，在隔离环境/分支固定一个目标。若目标是稳定的新接口，先以 v0.25.0 标签为候选，避免跟随浮动 main。
2. 先处理 compat.py 与契约测试：真实 Job.create、任务解析、Trial 数量/顺序、名称写回、模板/身份映射。只调整确实变更的部分，不重写 Slime rollout 主流程。
3. 校验 plugin.py 的 Agent 路由注入与生命周期事件，验证结果读取/重复事件/取消/资源释放；环境侧根据选用 native 或 bwrap 分别核对。
4. 更新 pyproject 的固定依赖、SUPPORTED_HARBOR_VERSION、错误信息与版本测试，使它们与实际支持目标一致。不要只放宽版本门禁而不验证运行行为。
5. 从最小无模型任务验证调度/文件/评测/清理，再使用一个真实 Agent 经 Dressage Proxy 验证轨迹及 Sample；然后补多尝试、多分区、失败/取消用例。优先复用 tests/integrations/harbor 下的 contracts、data_path、execution、environment、gated_e2e 测试。
6. 最后接入目标 Agent Sandbox/K8s 环境，验证 start/exec/文件传输/stop、网络可达和重试回收，不把框架升级与所有集群问题一次混在一起。

### 5. 与已有 Agent Sandbox 目标的关系

本地 examples/harbor-terminal-bench/README.md 仍要求 `harbor>=0.25`，但其指定的 `clients/integrations/harbor` 实现目录本轮核对仍不存在。升级到 0.25 只能解决版本要求的一部分，不能自动补齐缺失的 Environment 适配。

旧函数卡、Step 010 收束记录和 0.18 固定源码依据继续保留。本轮发现本机已有新版 Harbor，不回写旧版本行号或将历史笔记伪装成 0.25 的阅读完成记录。


<a id="dressage-harbor-coupling-map"></a>

## 2026-11-11：哪些 Dressage 代码绑定 Harbor

固定 Dressage 提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。本轮按 import、对象字段与方法调用、配置入口三种方式核对，而不是将出现 Harbor 字符串等同于强依赖。

### 直接使用 Harbor 接口或数据合同

以下路径均相对于 `dressage/integrations/harbor/`：

| 文件 | 与 Harbor 的联系 | 升级时的主要检查点 |
| --- | --- | --- |
| `compat.py` | 精确版本门禁；Job 私有任务解析、待执行 Trial 列表和对象顺序 | 最强版本耦合；优先检查真实对象布局、顺序和名称写回 |
| `data_source.py` | 加载 Harbor JobConfig，经 compat 解析任务，构造任务/Agent 规格 | 配置模型、任务解析、Agent 配置序列化与规格身份 |
| `rollout.py` | 创建 Job，执行 Job.run，按 Trial 结果关联插件 bundle，再转为 Sample | Job.create/run、Trial 计划与名称、JobResult 字段和组映射 |
| `plugin.py` | 向 Job 注册生命周期回调、读取 Trial 事件，调整 Agent 路由配置 | 事件顺序/字段、取消与 END、Agent/Task 配置和身份 |
| `environment.py` | 继承 Harbor BaseEnvironment，使用 ExecResult、环境能力和任务配置模型 | 构造参数、挂载、exec/文件传输/stop、网络和 verifier 语义；这是 Dressage 的 bwrap 后端 |
| `artifacts.py` | 按 Harbor 结果的 verifier_result、step_results、exception_info 等字段组织轨迹 bundle | 虽无直接 Harbor import，仍有结果结构与生命周期合同，不能归为完全独立的通用存储 |

### 接入专用支持代码：有绑定，但不直接组织 Job/Trial

| 文件 | 判断 |
| --- | --- |
| `gateway.py` | 模型路由与租约是通用机制，但当前模块使用 HarborIntegrationConfig，acquire 路径默认执行 Harbor 版本检查；仍属于这条接入路径，不等于完全独立模块 |
| `config.py` | 定义 Dressage 自己的 HarborIntegrationConfig 及环境/路由/训练规则，不直接导入 Harbor；升级时按行为变化决定是否调整，无需预设全部重写 |
| `__init__.py` | 主要导出配置符号，本身没有 Job/Trial 编排逻辑 |

另外，`pyproject.toml` 的 harbor extra、harbor.plugins 入口，`examples/harbor/` 的配置与脚本，以及 `tests/integrations/harbor/` 的合同测试也属于接入范围。两个通用测试文件中出现的 Harbor 字符串是测试数据/头字段，不代表生产代码依赖 Harbor。

### 没有直接绑定 Harbor 的核心与原生路径

| 路径 | 用途 |
| --- | --- |
| `dressage/proxy/` | 模型请求代理、会话、TITO 与轨迹保存/读取；Harbor 接入通过这些已有能力采集数据 |
| `dressage/rollout/multi_segment.py`、`convert_samples.py`、`artifacts/` | 通用轨迹分段、Sample/训练数据转换及产物写出 |
| `dressage/paddock/`、`dressage/sandbox/`、`dressage/rollout/generate/`、`dressage/rollout/prewarm/` | 原生 Agent/沙箱执行与预热路径；不是 Harbor Job/Trial 实现 |
| 其他 `dressage/rollout/`、`dressage/training/` | 通用批次/训练及 Slime 对接；不需要为 Harbor 升级预先整体重写 |

本轮扫描 dressage 下 137 个 Python 文件，Harbor 字符串命中集中在集成目录的 9 个文件；AST 检查在该目录外未发现直接 Harbor import 或对 Harbor 集成目录的绝对 import。此为静态依赖核对，不代替运行测试。

依赖方向是 Harbor 集成层调用 Dressage 通用层，通用层没有反过来要求 Harbor 才能使用。因此升级的首要修改面是集成层与其配置/合同测试；通用层通常保留，但仍需用端到端测试确保升级后的数据满足既有 Sample、token、mask、reward 等合同。

与阅读步骤对应：Step 000–009 多为原生路径和共用能力；Step 010 开始正式阅读 Harbor 接入。此前 Proxy、轨迹与 Sample 的认识仍然有用，不因更换 Harbor 版本而全部作废。


<a id="extension-contracts-versus-version-adaptation"></a>

## 2026-11-11：扩展接口与 0.25 版本适配的区别

本节比较对象是 v0.25.0 发布标签 fdba28fc411e47e8765420a1a063b4918fce3def，不把本地 main 之后新增的 preflight kwargs/选项校验变化算进该发布版。

| 类别 | Harbor 提供什么 | Dressage 或接入方负责什么 | 升级判断 |
| --- | --- | --- | --- |
| 执行引擎 | 已实现的 Job.run、Trial.run、队列、内置 Agent 和 Verifier | 创建配置、调用引擎并接收结果 | 使用 0.25 引擎即可；不用自己重写调度/生命周期，但要核对行为影响 |
| 插件扩展协议 | JobPlugin 的 on_job_start/on_job_end，以及 Trial 事件注册/事件对象 | DressageHarborPlugin 的路由、身份、采集与收尾逻辑 | 两个插件入口和主要事件仍存在；可保留实现，但必须测试字段、顺序和取消语义 |
| 环境扩展协议 | BaseEnvironment、exec 返回类型及生命周期/文件接口 | 内置环境直接复用；自定义环境实现后端资源操作 | 自定义 bwrap 或 Agent Sandbox Environment 必须符合目标版本的签名与行为合同；这不等于每个方法都重写 |
| 配置和结果模型 | JobConfig、TrialConfig、JobResult、TrialResult 等 | data_source/rollout/artifacts 按模型组织输入、提取输出 | 看字段和语义是否变更，失配处调整；不是纯粹两个 hook 就能隔离所有版本变化 |
| 私有接口依赖 | _task_configs、_remaining_trial_configs、任务解析和计划顺序等内部实现 | compat.py 与基于计划的模板/身份匹配 | 最需要针对 0.25 实测；发布版仍保留部分旧入口，不能仅因私有就宣称必须全部重写 |
| Dressage 通用层 | 不属于 Harbor 的接口实现 | Proxy、TITO、通用 Sample 转换、原生 Paddock/预热等 | 保留为主，通过接入层验证数据合同 |

JobPlugin 在该发布版为 runtime_checkable Protocol，要求两个异步方法；CLI 根据结构检查并调用。插件不因升级就必须继承一个新的 Harbor 基类。BaseEnvironment 则是自定义环境的明确扩展基类，除方法名外，还包括路径、输出收集、网络/用户/超时等行为要求。

### 哪些已确定，哪些仍需测试

- **确定必须处理的版本限制**：Dressage 的 harbor==0.18.0、SUPPORTED_HARBOR_VERSION 和相应版本测试。不能只改这些就声称兼容。
- **确定存在的 0.25 行为差异**：BaseEnvironment 引入 auto_mounts/auto_mounting，_mounts 与 _host_mounts 分工变化。旧 bwrap 读取 _mounts 并依赖挂载形状判断 verifier，必须核对并选择适配或明确保留旧行为的策略；没有实际环境测试，不能断言每条路径都会报错。
- **尚不能断言要重写的部分**：插件生命周期方法、Job.create/run、主要结果字段和普通 Trial 的排列关系。已观察到相同入口仍存在，下一步应该用合同测试定位差异，而不是预先重写全部集成层。
- **与版本升级不同的新增工作**：当前本地缺少 Agent Sandbox 示例指定的 Environment 实现。补齐这份实现是后端接入任务，单纯升级 Harbor 不会替代它。

验证建议仍是：兼容层的真实配置/计划测试 → 插件事件和结果测试 → 目标环境的文件/执行/清理测试 → 单任务经 Proxy 输出可用 Sample。当前仅静态对照，没有运行兼容性验证或实施升级。

来源：v0.25.0 的 src/harbor/models/job/plugin.py、src/harbor/cli/job_plugins.py、src/harbor/environments/base.py；Dressage 的 compat.py、plugin.py、environment.py，以及上节列出的固定源码。


<a id="environment-entry-local-recheck-20261113"></a>

## 2026-11-13：Step 013 环境接入点与本地实现复核

用户明确目标是 kubernetes-sigs/agent-sandbox，询问是否应在 BaseEnvironment/start 这里接入、Harbor 是否已有代码。本轮全部为本地读取，未联网。

- Harbor v0.25.0 发布提交 fdba28fc411e47e8765420a1a063b4918fce3def 的内置环境注册表与 src/harbor/examples 配置中，未找到 k8s_agent_sandbox_harbor 或 AgentSandboxEnvironment。内置 GKE、ACK、OpenShift 等后端不等同于此目标；ACK 的 Claim 为 OpenKruise agents.kruise.io。
- 接入机制确实存在：EnvironmentFactory.create_environment_from_config 在 config.import_path 非空时，调用 create_environment_from_import_path，导入模块中的类并实例化（factory.py:327–359、407–422）。该对象保存到 Trial.agent_environment；后续 start/exec/文件/stop 由此具体实现提供。应实现或复用 BaseEnvironment 对应的具体后端，不把 Agent Sandbox 专属操作写进抽象 start。
- Agent Sandbox 当前本地提交仍为 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。examples/harbor-terminal-bench/configs/sample.yaml:12 指向 k8s_agent_sandbox_harbor:AgentSandboxEnvironment，README 要求安装 clients/integrations/harbor；本地该目录不存在。此结论限定当前 checkout，不代表已查询上游最新发布或外部包。
- 已有 slime_api_data_collecting 的 UpstreamK8sSandbox 可作底层能力复用候选，但它当前面向 Slime 风格接口，不是已验证的 Harbor BaseEnvironment 实现。需要核对 __aenter__/__aexit__、exec、文件接口与 Harbor start/stop/upload/download 的映射及缺口。
- Dressage 的 Harbor 集成采用自定义 Harbor 环境时应沿 native 路径保留 Job 环境配置；bwrap 模式会覆盖环境 import_path。Harbor 0.25 与 Dressage 原版本门禁的兼容性仍是独立实施检查，接口位置明确不等于已经可运行。

当前只定位接缝与缺口，没有实现适配类、安装包、启动沙箱或进行集群验证。具体后端启动逻辑应在已找到或准备实现的适配类中阅读，不能把示例里引用的类当成已存在源码。
