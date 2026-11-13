# 共享 Kubernetes 基础专题与下一处源码入口

2026-11-05：依据用户关于“下一步读什么、是否把 Agent Lightning 的 k8s 独立出来”的提问形成的建议。随后用户确认“好的 那么就按照这个方式来处理吧”，方案已落实；原建议正文保留，实施记录见文末。

## 1. 建议

先将 Kubernetes 通用基础从单个项目下提取为共享专题，随后继续 Agent Sandbox 的 Pod 创建阅读。两者互相引用：基础专题解释概念，各仓库保留概念在具体实现中怎样使用的证据和个人阅读记录。

沿用用户提出的同级位置，可使用 `00-repo-reading/repositories/kubernetes/`。入口明确说明它是跨仓库基础知识专题，并非已绑定 `kubernetes/kubernetes` 源码 checkout 的逐函数阅读项目，不照搬源码项目的 Step 和 02/03 结构。

```text
00-repo-reading/repositories/
├── kubernetes/                    # shared concepts and references
├── agent-lightning/               # source reading and project mappings
└── agent-sandbox/                 # source reading and project mappings
```

## 2. 为什么已有材料适合提取

现有 [Agent Lightning 的 k8s 目录](../../kubernetes/README.md)包含 20 份 Markdown，已经按通用职责组织：

1. 00-overview：整体任务与组件交接。
2. 01-architecture：API Server、控制器与协调循环。
3. 02-resource-model：metadata、spec、status、namespace、labels。
4. 03-workloads：Pod、Job、状态与 Pod 模板。
5. 04-runtime-environment：计算、网络、存储和配置的职责，已有镜像与环境变量正文。
6. 05-security-and-isolation：权限及隔离边界。
7. 06-operations：状态、事件、日志与排查。
8. 90-clients：客户端工具，已有 kr8s 基础。

主体已经不依赖 Agent Lightning 的 Gateway 或具体函数调用。提取时保持这八类目录，不另造一套分类。已有空缺随实际遇到的问题补充，不把目录完整度变成新增课程任务。

## 3. 本轮哪些内容进入共享专题

| 已接触的内容 | 共享专题落点 | 仍由 Agent Sandbox 卡片保存 |
| --- | --- | --- |
| 协调是观察需求、执行必要动作、再观察 | 01-architecture/reconciliation.md，扩充既有正文 | Reconcile 的真实调用顺序、特殊分支、返回值 |
| API 对象、内存表示、metadata/spec/status；读取与写回的区别 | 02-resource-model，复用对象模型，按需补版本和写入说明 | oldStatus、oldResourceVersion 及 updateStatus 的具体补丁选择 |
| 标签、选择器与所有者关系 | 02-resource-model，保留标签正文，补已遇到的归属概念 | NameHash 的具体算法、标签键和多个所属 Pod 的冲突策略 |
| Pod、Node、IP 与 Ready 的基本关系 | 03-workloads；组件职责链接 01-architecture | Sandbox.Status 的字段赋值与项目自己的 Ready 判定 |
| Volume、PVC、挂载目录；申请对象与实际存储的区别 | 04-runtime-environment，补最小存储说明 | volumeClaimTemplates 如何生成命名、资源与 Pod 引用 |
| Service 与访问入口；对象存在不等于连接已验证 | 04-runtime-environment，补最小网络说明 | 本项目何时创建、保留或删除 Service，如何检查其可用状态 |

当前尚未深入的 PV 供给算法、存储驱动、CNI、完整调度器等不随之展开。已有客户端笔记仍保留各自版本；后续确实阅读相关 Go API 时，再补对应客户端用法。

## 4. 内容分工与保留方式

1. **共享专题保存通用概念的一份正文。** 例如 PVC 表达存储申请、ownerReferences 表达对象归属。正文不把特定项目的策略写成 Kubernetes 的普遍规则。
2. **项目函数卡保存当前场景、代码、输入输出、原话和未知。** 仍保留就近的最小术语说明，链接共享正文；不因为提取基础就删除现有卡片的主体。
3. **项目 references 保存对应关系。** 例如 Sandbox 控制器直接协调 Pod，Agent Lightning 协调 Job；这是两个项目的用法差异，不把它混入通用定义。
4. **个人阅读进度仍属于各项目。** 移动基础资料不会改变已读/未知、Step 编号或 02/03 的继承关系，也不新增一份竞争的进度记录。
5. **历史来源保留。** 共同正文可以链接首次遇到问题的步骤；新增源码例子标明各自版本，不把一次静态阅读写成运行证据。

## 5. 迁移时的实际处理

1. 将现有 20 份 Markdown 及八类相对结构整体迁到 kubernetes，不复制成两份继续维护。
2. 更新所有指向旧目录的引用，包括函数卡、步骤、项目 references、方法入口和本仓库的相关路径约定。历史记录只重定位链接，不改写原话或当时状态。
3. 旧 k8s/README.md 留一个简短的迁移入口；深层链接仍须全部更新，不能只靠入口页替代。
4. 两个项目入口都链接共享专题。Agent Lightning 的岗位范围和项目映射继续留在它的 references；Agent Sandbox 的主题与步骤保持现有位置。
5. 校验迁移前后正文、来源和链接目标，再按本轮实际遇到的缺口补充基础。结构搬迁和内容补充分开核对，以便确认没有丢失材料。

## 6. 源码下一步：聚焦 reconcilePod 的正常创建路径

当前 Step 000 的范围是 Reconcile 外层闭环与 reconcileChildResources 的职责骨架。两者已经实际展开；updateStatus 已按接口理解。用户反馈“问题差不多了”，可以按这个深度准备收束，不要求把每个辅助函数读完，也不把具体未知改成已掌握。

下一处建议为 [SandboxReconciler.reconcilePod](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L1674)，另一个具体阅读单元只解决：

> Sandbox 已存在、要求 Running，但对应 Pod 还不存在时，怎样把 podTemplate 变成真正提交给 Kubernetes 的 Pod 对象？

1. 来路：reconcileChildResources:538 交入同一个 Sandbox、nameHash 和 wd。
2. 观察重点：如何确认当前没有所属 Pod；如何组装 Pod；如何设置归属；哪里执行 Create。
3. 结果：返回 Pod 对象、延迟和错误，再由调用者摘取字段并计算状态。
4. 停止位置：分清创建 API 对象与节点启动容器，回到子资源协调主线。
5. 当前暂不展开：已有 Pod 接纳、挂起、失败重建、退避和所有元数据修复细节。

此处是下一步候选，尚未创建 Step 001、函数卡或标记开始阅读；现阶段也不把共享专题整理变成继续读源码的强制前置课程。

## 7. 本次提问

> 好的 我觉得问题差不多了
> 那么现在需要考虑一下
> 下一步应该看什么了呢?
> 还是说当前这一步里面的内哦能够哪些适合进入
> k8s的专题?
> 我们是否需要吧k8s的部分单独拿出来呢?
> 也就是吧agent-lightning里面的k8s单独拿出来放在repositories里面
> 这样子可以把这里的接触到的k8s相关的内容放进去了?

## 8. 用户确认后的实施

1. 原 20 份资料整体迁到 [Kubernetes 共享专题](../../kubernetes/README.md)，八类结构和原正文保留；旧入口仅留迁移说明。
2. 迁移阶段重定位 147 处链接，随后补入已接触的对象写回与版本、所有者关系、Pod 状态、PVC 和 Service 基础。各项目函数卡继续保留主体并增加回查入口。
3. [Step 000 总结](../topics/kubernetes-sandbox-control/steps/step-000-sandbox-reconcile/05-task-flow.md)按原 scope 深度收束，[Step 001 scope](../topics/kubernetes-sandbox-control/steps/step-001-pod-creation/01-scope.md)已建立。
4. Step 001 的 03 完整继承前一步两张函数卡及其来源、原话、未知。02 暂无新卡；建立范围不表示 Pod 创建实现已掌握。
5. 共同知识不另维护源码阅读进度，Agent Sandbox 的实时位置仍只在项目 README。没有集群运行或部署操作。
