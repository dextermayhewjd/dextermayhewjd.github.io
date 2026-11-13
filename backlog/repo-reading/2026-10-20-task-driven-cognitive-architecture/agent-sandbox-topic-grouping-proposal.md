# Agent Sandbox：按问题区分主题，保留既有步骤

> 最新落实：2026-11-05 用户随后要求把旧记录也整理到 topics 下。原 Step 000、001 已整体迁入 [Fleet 主题](../../../00-repo-reading/repositories/agent-sandbox/topics/fleet-environment-orchestration/README.md)，Kubernetes 主题保持独立；下方“原位保留”的表述属于此前决定，旧内容与编号本次均保留。

> 2026-11-05 更新：用户授权不必延续 Slime 规则。现已创建独立 Kubernetes 主题及其 Step 000，旧步骤原位保留，跨主题按需引用，不自动整套继承。下文的 Step 002 编号与迁移方案保留为历史；现行规则见 [Agent Sandbox 局部约定](../../../00-repo-reading/repositories/agent-sandbox/AGENTS.md)。

[制度讨论入口](README.md) · [已采用的 Slime 主题规则](slime-topic-grouping-proposal.md) · [Agent Sandbox 当前进度](../../../00-repo-reading/repositories/agent-sandbox/README.md#current-reading)

2026-11-04，用户询问转向 Kubernetes 后原有 step 是否仍算数，以及是否应参考 Slime 分 topic。本文件保存具体建议，尚未移动目录、建立新主题或创建 Step 002。

## 1. 原有步骤保留，学习历史不作废

1. Step 000 的整体调用骨架已经按当时范围收束，保留完成层次和全部记录。
2. Step 001 已实际接触 setup、start_warmpools，并讨论预热与任务需求的边界；这些内容继续有效。_warm_entries、_warm_entry 的逐函数阅读尚未完成，保留当前未知，不因转向别的主题标记全部完成。
3. Dressage 对比修正的是后续阅读投入，不会抹掉 Fleet、Task、资源计划和预热之间已经建立的关系。

## 2. 建议分为两个主题

| 建议主题 | 主要问题 | 步骤归属 |
| --- | --- | --- |
| 01 · 训练侧怎样使用和编排沙箱环境 | 配置与任务怎样进入 Fleet、选择策略、请求准备和使用环境 | 原 Step 000、Step 001 整体保留，原编号及目录后缀不改 |
| 02 · Kubernetes 怎样落实沙箱资源与生命周期 | Sandbox 如何形成 Pod/Service/PVC、状态如何回传、WarmPool 如何补池、Claim 如何分配与回收 | 下一次实际开始时建立 Step 002，先定位 SandboxReconciler.Reconcile → reconcileChildResources |

主题按问题划分，不机械地按 Python 与 Go 或目录边界分类。同一个资源、文件或方法可在不同主题按不同问题回查。Dressage 仍是独立仓库，其比较材料可从主题入口引用，不迁入 Agent Sandbox 的函数记录。

拟采用的目录形式与 Slime 相同：

```text
repositories/agent-sandbox/
  README.md
  references/
  topics/
    01-fleet-environment-orchestration/
      README.md
      steps/
        step-000-warmpool-reconcile/
        step-001-start-warmpools/
    02-kubernetes-sandbox-control/
      README.md
      steps/
        step-002-.../  # only when the reading step actually starts
```

这是可供确认的目标结构，不表示目录已经建立。旧的 step-000-warmpool-reconcile 后缀属于历史命名，单纯分主题不顺便重命名。

## 3. 编号、继承与进度沿用原规则

1. 项目级 step 编号连续；新主题从 Step 002 接续，不重新编号为 Step 000。
2. 新步骤的 03 合并前一实际步骤的 03 + 02，即使两步属于不同主题。当前若从 Step 001 进入新主题，应继承其六张已有记录加本步两张方法卡，共八个函数/类记录；原话、来源和未知全部保留。
3. 03 包含记录不代表全部掌握；02 只放本步实际阅读使用的记录，不能因为新主题出现控制器名字就预建整套卡片。
4. 主题 README 保存问题、入口与步骤索引，不另建主题级 memory；项目 README 继续作为唯一实时进度。
5. 采用时整体迁移原步骤及历史、备用资料，重算所有相对链接；不抽出或删除“不再重点读”的原话和函数卡，不把新主题源码覆盖到 Step 001 的 scope。

依据：通用 workflow 的按主题组织规则，以及 Slime 已确认采用的主题方案。当前仅提出并记录方案；原 scope、步骤目录与学习状态保持不变。


## 4. Kubernetes 主题与岗位的关系

已按用户要求回查完整腾讯混元 JD：要求 3 明确包括 Kubernetes、容器化和集群实践，职责 4 明确包括并发、资源及行为一致性。因此新主题直接补充已有 Agent/RL 阅读的基础设施能力；不表示岗位转为纯集群运维，或所有 Kubernetes 内部机制都必须通读。具体对照见 [岗位分析](../../../00-repo-reading/repositories/agent-sandbox/references/rl-environments-and-jd.md#kubernetes-priority-for-tencent)。主题迁移仍未执行。


## 5. 学习目标已确认，具体路线已保存

用户明确要求以补足腾讯混元岗位的 Kubernetes 沙箱工程能力为目标。已保存[五项核心阅读与实践范围](../../../00-repo-reading/repositories/agent-sandbox/references/tencent-k8s-learning-scope.md)，并将其接入项目唯一进度；单个 Sandbox、WarmPool、Claim 是实现主线，访问/隔离与部署排障用代表案例验证。目标确认不等于所有子函数或所有实验已开始，原步骤保持，主题目录尚未迁移。


## 2026-11-05 · Topic 与 Step 的关系再澄清

用户再次确认关注点：是否应参照 Slime 新开 topic，而不是只在原层次加一个 step。

判断保持不变：这次应先增加 Kubernetes 主题，再把具体阅读步骤放在该主题内。Topic 与 Step 不是二选一；Topic 表达一类持续学习问题，Step 表达一次有边界的实际阅读。

1. Topic 01 保留 Fleet/训练侧环境使用的 Step 000、001，已有内容和未完成问题不清零。
2. Topic 02 围绕 Kubernetes 沙箱资源与生命周期；第一步仍按项目全局编号使用 Step 002，后续按实际阅读再创建。
3. 单个 Sandbox、WarmPool、Claim、隔离与排障是新主题下的内容范围，不直接预生成为五个完成步骤。
4. 跨主题仍继承上一实际步骤的 03 + 02，主题不增加另一套 memory 或实时进度。

本轮明确组织判断，未执行目录迁移或创建 Step 002；学习范围继续采用已确认的腾讯岗位导向目标。


## 2026-11-05 · 按用户授权建立独立主题

用户表示可以不延续 Slime 规则，并授权助手选择合适方式开启 topic 与第一个 step、确定 scope。最终选择：旧目录不迁移，创建 topics/kubernetes-sandbox-control/steps/step-000-sandbox-reconcile；编号只在主题内连续，本步 03 为空，旧记录仅按问题引用。

第一步以 SandboxReconciler.Reconcile 的普通运行路径为入口，建立读取需求、协调子资源、状态写回与后续事件之间的关系。当前只建 scope 和记录入口，不预建未读函数卡。项目 README 保持唯一实时进度；此例的独立主题规则不改写 Slime 或通用 skill。
