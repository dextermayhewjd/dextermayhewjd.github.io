# Dressage × Harbor 接入与验证

[项目入口与唯一进度](../../README.md) · [前一主题：原生单任务闭环](../01-native-agent-rollout/README.md) · [Kubernetes 沙箱主题](../../../agent-sandbox/topics/kubernetes-sandbox-control/README.md)

## 本主题解决什么问题

复用 Dressage 的 Harbor 集成、Harbor 的任务与 Agent 生命周期、现有项目的 K8s 能力，把不同任务、模型请求、评测和结果采集接成可验证的一条链。

Harbor Job/Trial 是这条路线的任务编排者；原生 Paddock/BlackboxServer 的知识用于对照，不把它们强行串入同一次 Trial。模型请求发生在 Agent 运行期间，插件通过生命周期事件处理路由与结果。

## 先从 Dressage 自己的集成代码进入

本主题从 Dressage 的 dressage/integrations/harbor 开始，再沿实际调用进入 Harbor 源码。以下模块已为规划做过源码定位，不表示已经与用户逐函数读完。

| Dressage 内部文件 | 负责什么 | 对应阅读范围 |
| --- | --- | --- |
| rollout.py、data_source.py | 接住批量输入，创建并运行 Harbor Job，整理输出交回 Slime | Step 010，返回转换在 Step 015 |
| plugin.py | 将路由、开始、结束、取消等处理接入 Harbor 生命周期 | Step 011、014–016 |
| gateway.py | 为尝试建立模型请求路由，并关联会话和访问资料 | Step 014 |
| artifacts.py | 收尾会话、取得轨迹、合并 Trial 结果并保存产物 | Step 015 |
| environment.py | 提供 Dressage 自带的 bwrap Environment 实现，可用于对照环境合同 | Step 013；Agent Sandbox/K8s 接缝仍需单独对齐 |
| config.py、compat.py | 集成配置与固定 Harbor 版本的兼容处理 | 在对应主线按需回查 |

训练示例通过 rollout-function-path 指向 generate_rollout_harbor_sync；独立 rollout 示例使用 harbor run --plugin dressage。两个入口都确实使用 Dressage 自带的集成层。入口配置见 [Step 010 scope](steps/step-010-harbor-rollout-entry/01-scope.md)。

Harbor 自身已有 GKE、ACK、OpenShift 等 K8s 相关后端；Step 013 先判断现成实现能否复用，再补特定 Agent Sandbox 接缝，详见[已有 K8s 后端核对](../../references/harbor-kubernetes-backends.md)。

当前 Agent Sandbox 示例与 Dressage 的直接组合仍有[适配实现缺失和 Harbor 版本冲突](../../references/agent-sandbox-harbor-compatibility.md)，不把示例存在当作已经集成可用。

## 步骤索引

各步资料状态如下；当前接续以[项目唯一进度](../../README.md)为准，目录建立不代表已读。2026-11-12 的 scope 已统一校准普通调用交接；012–015 沿正常主线，016 回看故障，017 做整合验证。

| 步骤 | 本步问题 | 入口 | 资料状态 |
| --- | --- | --- | --- |
| Step 010 | Slime 怎样交给 Dressage 的 Harbor 入口？ | [scope](steps/step-010-harbor-rollout-entry/01-scope.md) | 主线已收束，未通读全部内部实现 |
| Step 011 | 一次 Harbor Trial 怎样完成准备、执行与结束？ | [scope](steps/step-011-harbor-trial-lifecycle/01-scope.md) | 首轮生命周期与正常结果返回已收束；保留内部未知 |
| Step 012 | 运行配置怎样得到 Task 与 Agent 对象？ | [scope](steps/step-012-task-agent-verifier/01-scope.md) | [首轮创建主线已收束](steps/step-012-task-agent-verifier/05-task-flow.md)，停在环境入口；保留具体工厂等未知 |
| Step 013 | Environment 怎样创建、启动并接到 Agent Sandbox？ | [scope](steps/step-013-harbor-kubernetes-environment/01-scope.md) | 已确认开始，当前阅读 start 接口调用与超时包装；具体后端、适配与验证未展开 |
| Step 014 | Agent 怎样准备、执行，并在运行中请求模型？ | [scope](steps/step-014-model-routing-and-api-contract/01-scope.md) | 仅 scope，未展开 |
| Step 015 | 产物怎样评测，再与轨迹一起形成最终结果？ | [scope](steps/step-015-harbor-results-and-samples/01-scope.md) | 仅 scope，未展开 |
| Step 016 | 回看一种取消/失败，资源与结果怎样收尾？ | [scope](steps/step-016-cancellation-and-retries/01-scope.md) | 仅 scope，未展开 |
| Step 017 | 怎样整合局部验证并复跑接入链？ | [scope](steps/step-017-integration-validation/01-scope.md) | 仅 scope，未展开 |

## 与其他主题怎样衔接

从本主题转入 [Agent Sandbox 导航入口](../03-agent-sandbox/README.md) 的位置明确如下：

| 本主题位置 | 去哪里、解决什么 | 读完返回哪里 |
| --- | --- | --- |
| Step 010–012 | 先看批次入口、Trial 主线和任务/Agent 对象来源 | 进入 Step 013 的 Environment 合同 |
| Step 013 的资源实现接缝 | 转入 Agent Sandbox，按已有进度接状态写回、WarmPool、Claim 和执行访问 | 返回同一个 Step 013，完成接口映射与冷创建验证的准备 |
| Step 014–016 | 从 Agent 执行接模型请求、产物评测与结果，再回看一条故障；资源语义按需回查 | 进入 Step 017 的具体整合与验收 |
| Step 017 | 在现有 slime_api_data_collecting 项目里落实适配与固定任务验证 | 根据实际故障修复或结束本轮，不自动追加新阅读主题 |

1. 先完成原生主题的执行、轨迹、Sample 与清理主线，再从 Step 010 建立新路线的入口位置。
2. Step 013 在 Environment 边界引用 Agent Sandbox 的独立 K8s 主题；资源控制器、WarmPool、Claim 不在这里重复建立另一套步骤。
3. 冷创建合同清楚后即可开展局部验证；Step 017 负责串联和补齐证据，不意味着此前只能阅读不能验证。
4. Step 编号沿 Dressage 连续使用 010–017。scope 准备完成不表示开始阅读或完成实践；实际进度只在项目 README 维护。
5. Harbor 阅读以 v0.25.0 发布提交为准；Dressage 仍固定原依赖，运行兼容性需独立验证。Step 013 已按用户确认进入创建入口；Step 014–017 的 scope 准备不表示已读或完成实现。
