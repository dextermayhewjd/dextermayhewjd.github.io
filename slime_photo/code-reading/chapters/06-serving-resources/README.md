# 第 6 章 模型服务、Ray 资源与容器边界

[阅读路线](../../repo-reading-route.md) · [总目录](../../README.md)

**目录 ID：** `06-serving-resources`
**产物状态：** planned
**学习状态：** 统一见[阅读路线的当前接续](../../repo-reading-route.md#当前接续)。

**问题：** 谁部署模型、分配资源、发现服务、检查健康、处理故障，并回收任务与推理资源？

**前置：** 01、05；知道执行环境与并发预算的边界。

**图文对照：** 4.3、4.4、2.1；Kubernetes 为独立实践。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 分布式资源布局 | [slime/ray/placement_group.py · create_placement_groups](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/placement_group.py#L123) | trace | Ray placement group 与 GPU 布局；不是 Kubernetes Pod 或集群调度器。 |
| 推理部署组装 | [slime/backends/sglang_utils/deployment.py · start_rollout_servers](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/sglang_utils/deployment.py#L79) | trace | 配置、router、engine group 和服务进程；模型内部算子后置。 |
| 外部模型服务发现 | [slime/backends/sglang_utils/external.py · discover_external_engines](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/sglang_utils/external.py#L95) | trace | 外部 SGLang 引擎信息与控制接口，不等同于任意 Chat Completions API。 |
| 模型服务所有权 | [slime/ray/serving.py · ServingCluster.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/serving.py#L38)、[slime/ray/serving.py · ServingCluster.dispose](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/serving.py#L294) | trace | 服务与队列可以跨训练尝试保留；失败、detach、正常成功退出的政策不同。 |
| 生成服务管理与清理 | [slime/ray/rollout.py · RolloutManager.dispose](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/rollout.py#L160) | trace | 借用 ray/serving.py 中 ServingCluster 的模型服务，dispose 只清理自有资源；服务完整回收另由所有者负责。 |
| 容器构建参考 | [docker/Dockerfile](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/docker/Dockerfile#L1) | locate | 镜像、依赖与补丁；集群控制器、沙箱后端和网络存储仍需独立实践。 |

**章内顺序：**

1. 画运行位置：训练 actor、rollout worker、模型 HTTP 服务、Adapter、Agent CLI 与沙箱。
2. 追 placement group → deployment → engine/router → health/recovery → dispose 的职责交接。
3. 选择一个模型服务不可达或 CLI 无法回连 Adapter 的情景，定位地址、端口、会话、日志与清理者。
4. 另做 Kubernetes 实践：Pod 创建/就绪、资源限制、命令与文件操作、网络回连、日志与结果保存、取消和清理；该任务只是建议，尚未执行。

**验收问题：** Ray、Kubernetes、Sandbox 和模型服务各管理什么？要换 Kubernetes 沙箱，需要满足哪些操作与失败语义？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](../../repo-reading-route.md#当前接续)。
