# Harbor 已有的 Kubernetes 后端与 Agent Sandbox 接缝

[Harbor 接入主题](../topics/02-harbor-integration/README.md) · [环境接入 scope](../topics/02-harbor-integration/steps/step-013-harbor-kubernetes-environment/01-scope.md)

2026-11-08，针对“Harbor 是否集成 K8s”重新核对官方固定版本源码。结论是：**Harbor 已有 Kubernetes 相关环境实现；不能把需要接入特定 Agent Sandbox 的问题，说成 Harbor 没有 K8s 支持。**

### 这里的“后端”是什么意思

这里说的是 **Environment 环境后端**：Harbor 用它创建任务环境、运行命令、传文件和清理资源。不是模型后端，也不是要求把所有后端同时部署。

| 当前固定版本已核对的实现 | 对应平台 | 如何理解 |
| --- | --- | --- |
| GKEEnvironment | Google Kubernetes Engine | 面向 Google 的托管 Kubernetes 环境 |
| ACKEnvironment | Alibaba Cloud Container Service for Kubernetes | 面向阿里云 ACK；其中的 SandboxClaim 路径使用 Kruise 资源 |
| OpenshiftEnvironment | Red Hat OpenShift | 面向 OpenShift Kubernetes 平台 |

三者都是 Harbor Environment 接口下的实现，各自具有平台、认证或资源约束；不能仅据名称断言任意本地 Kubernetes 都可直接使用。用户目标的 kubernetes-sigs/agent-sandbox 是另一个资源控制方案，需要核对或补齐专用 Environment 适配，不能与 ACK 的同名 Claim 混同。

## 1. 锁定版本里已经有什么

Dressage 当前依赖 Harbor 0.18.0。本次打开此前绑定的提交 527d50deb63a5d279e8c20593c18a2cbc7f61f9e，确认 [EnvironmentFactory 的内置注册表](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/factory.py)包含：

1. GKEEnvironment。
2. ACKEnvironment。
3. OpenshiftEnvironment。

这不是仅有接口声明。[GKE 实现](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/gke.py)使用 Kubernetes 客户端创建、观察和删除 Pod，并提供 exec、文件传输等能力。它仍有 GKE 相关的配置与依赖，不能据此保证任意集群都能原样使用。

## 2. 已有 K8s 后端，不等于已接上指定的 Agent Sandbox

[ACK 实现](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/ack.py)还包含 SandboxSet / SandboxClaim 路径，但它使用 agents.kruise.io/v1alpha1。

我们此前阅读的 kubernetes-sigs/agent-sandbox 使用 agents.x-k8s.io 与 extensions.agents.x-k8s.io，资源和归属合同不同。名字都叫 SandboxClaim，不能直接认为两者互换，也不能据此认为 Harbor 已支持该项目的 WarmPool/Claim。

因此要分别判断：

| 目标 | 应先做什么 |
| --- | --- |
| 只需在 K8s 中运行 Harbor 任务 | 先检查现成后端的集群、镜像、执行与清理要求，优先复用满足条件的实现 |
| 明确使用 kubernetes-sigs/agent-sandbox 的预热与领取 | 核对该项目的 Environment 适配、版本和 CRD 合同；再决定复用、修改或补齐哪些部分 |
| 任意本地或其他云集群都要支持 | 单独核对云依赖、凭据、镜像构建和网络行为，不凭“使用 Kubernetes 客户端”就宣称通用 |

## 3. 对当前阅读计划的修正

Step 013 仍是环境接入边界，但先增加现有实现的复用判断，再做 BaseEnvironment 与项目能力的映射。不是预先决定从零写 K8s 后端。

Dressage 自带的 environment.py 是 bwrap Environment；其 native 模式可以使用 Harbor 自带的环境提供方。因此“Dressage 自己的 Environment 是 bwrap”不代表整条 Harbor 路线只能本地运行。

此前 Agent Sandbox 示例要求 Harbor 的另一版本，并引用当时未取得的适配目录；这一兼容性问题仍需保留。它不否定 Harbor 自身已有其他 K8s 后端。

## 4. 核对边界

- 本次通过官方仓库的固定提交核对 factory.py、gke.py、ack.py；也查看了主分支注册表，但不将主分支接口混入锁定版本。
- CRD group 对照来自本地 Agent Sandbox 的 api/v1beta1/groupversion_info.go 与 extensions/api/v1beta1/groupversion_info.go。
- 这里只确认源码包含的能力与接口差异，没有部署这些环境，未证明某个目标集群已兼容。



<a id="gke-agent-and-job-goal"></a>

## 2026-11-09：GKE 环境、Agent 选择与岗位实践

再次在线核对固定 Harbor 提交 527d50deb63a5d279e8c20593c18a2cbc7f61f9e：GKEEnvironment 的单容器路径连接已有 GKE 集群，准备镜像、创建并等待 Pod，通过 Kubernetes exec 和文件传输操作环境，stop 按删除参数清理。它包含 Google Cloud 的凭据/项目/镜像仓库约定，不是无配置即可通用于任意集群的后端。

来源：[GKEEnvironment](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/gke.py)，重点定位 start（源码约573）、exec（约812）、创建和删除 Pod。上述只概括单容器路径，Compose/DinD 与加速器细节不作为当前入门前置。

Agent 与 Environment 是独立选择。工厂包含 ClaudeCode、Codex、Terminus2、Oracle 等；CLI Agent 的安装和命令执行通过 Environment。选 Claude Code/Codex 可以采用用户所说的黑盒 CLI 运行方式，但 Harbor 不仅支持此类 Agent，也不必因此串入 Dressage 原生 BlackboxServer。

来源：[AgentFactory](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/agents/factory.py)、[BaseInstalledAgent](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/agents/installed/base.py)；Dressage 本地 terminal-bench-2-e2b.yaml 将 environment.type=e2b 与 agent.name=claude-code 分开配置。

面向岗位的建议：用一个真实任务和现成 Agent 验证 K8s Environment 的创建、执行、文件/结果和回收，留下部署配置、运行关联及故障排查证据，再按需要增加预热/并发。GKE 可作接口实现参考，不要求为了岗位专门部署 Google Cloud，也不要求把其全部平台特性重写到目标适配层。是否满足具体招聘评估不能由代码阅读或一次启动推断。

本次为源码/目标核对，没有新建 GKE 集群、Pod 或模型调用。
