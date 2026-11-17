# MiniMax × Harbor：Dressage 改造实践

[项目入口](../../README.md) · [总体路线](backlog/docs/doc-002%20-%20总体路线与验收边界.md) · [已确认决策](backlog/decisions/decision-001%20-%20先完成无-GPU-API-评测链路，再接-Agent-Sandbox.md) · [任务看板](http://127.0.0.1:6420)

## 目标与运行边界

**已确认目标（2026-11-17）：从 Slime 发起，沿 Dressage → Harbor 调用 MiniMax，在 Agent Sandbox 中运行有代表性的任务，完成工具执行、Verifier 评分、日志与产物保存、结果返回和资源清理，并验证少量并发与预热行为。**

先在可用后端跑通 API 与任务基线，再替换为 Agent Sandbox。学习重点是：为什么能运行、失败发生在哪里、结果是否对应正确、资源是否释放。不是以读完多少函数或跑过多少 benchmark 为完成标准。

本地没有 GPU，不部署模型、不更新权重。本项目验证的是 **Agent 任务执行与评测链路**，不能宣称已验证策略训练和权重更新闭环。

### 本轮范围与收尾条件

| 范围 | 收尾时需要的证据 |
| --- | --- |
| ① 原有链路基线 | MiniMax → Agent 工具执行 → Verifier → 日志、产物、结果返回；完整验收包含 Slime 发起 |
| ② 环境后端适配 | Harbor 通过 Agent Sandbox 创建/领取环境、执行命令、传输文件、释放资源 |
| ③ 任务兼容性 | 最小任务、依赖特定环境的代码任务、失败或超时用例；列明支持与不支持的环境能力 |
| ④ 集群运行行为 | 少量并发下结果归属正确；观察预热命中与池耗尽；记录启动/执行故障定位及资源清理检查 |

任务/benchmark 表达“做什么和怎么评分”，任务环境表达“需要什么依赖或服务”，沙箱后端表达“在哪里执行”。支持一个新后端不等于支持 Harbor 的所有任务；多容器、GUI 等特殊能力不自动纳入本轮。

验收材料保存代码版本、镜像版本或 digest、任务配置、模型与采样配置、复现命令及运行结果。可复现指配置与过程可重跑，不承诺远端模型输出逐位一致。

**停止边界：**本轮不自研调度器、镜像存储系统、任意状态快照，不追求千级并发，不通读所有后端。SDK 在真实链路稳定后再评估是否提取，不作为本轮完成条件。具体工作以 [总体路线](backlog/docs/doc-002%20-%20总体路线与验收边界.md) 为准；旧讨论中的建议不自动增加任务。

这里维护实施任务，不重启一套源码阅读。已读函数直接引用原卡片。2026-11-17 用户确认改用独立集成仓库：`/home/hongshi/projects/agent-api-integration`，自己的 adapter、配置和测试放在该仓库；`third_party/dressage` 固定引入 Dressage。确实缺少扩展入口时才在 Dressage fork 做小补丁。现有 `/home/hongshi/projects/Dressage` 保留为阅读 checkout，不删除或搬迁。Slime 的启动适配若需要代码修改，另在清单中明确，不能预先承诺只改 Dressage 即可。

<a id="baseline"></a>

## 已确认的基线

| 项目 | 固定记录 |
| --- | --- |
| Dressage 本地目录 | `/home/hongshi/projects/Dressage` |
| 固定提交 | `3e3142fe8ea07e4504c3b20a936a4c201a3de44c` |
| 最近检查 | 2026-11-17：`main`，工作区干净 |
| 本地 origin 配置 | `git@github.com:dextermayhewjd/Dressage.git`；未联网验证远端状态 |
| Slime 运行基线待统一 | Dressage 固定子模块 `aaf5c209`（本地未初始化）；此前独立 checkout 为 `18868a79`，不得混用版本证据 |
| Harbor 依赖 | Dressage 声明 `harbor==0.18.0`；已读的 v0.25.0 不能视为已验证替代版本 |
| 模型后端 | MiniMax；具体模型名、账户 Base URL 尚待确定 |

## 当前入口与记录分工

2026-11-17：Q01–Q04 已迁入 Backlog。当前只完成记录迁移，未执行这些核对任务；状态、验收、依赖和实施结果以任务卡为准，不在本页另建完成列表。

| 原问题 | 当前任务 |
| --- | --- |
| Q04 | [MH-001：Harbor 版本兼容性](backlog/tasks/mh-001%20-%20核对-Dressage-与-Harbor-的运行版本兼容性.md) |
| Q01 | [MH-002：MiniMax 消息接入边界](backlog/tasks/mh-002%20-%20核对-MiniMax-消息接入边界与初始化依赖.md) |
| Q02 | [MH-003：缺少训练字段时的结果合同](backlog/tasks/mh-003%20-%20核对-API-缺少训练字段时的结果记录合同.md) |
| Q03 | [MH-004：Slime 无 GPU 发起路径](backlog/tasks/mh-004%20-%20核对-Slime-无-GPU-发起路径与实际版本.md) |

当前先沿 MH-002 从已有阅读步骤确认消息接入边界；需要运行验证时再处理 MH-001 的环境兼容性，并结合 MH-004 核对 Slime 启动。四项均为调查任务，未设置强制依赖；实际实现或联合验证需要前置结果时，再按真实关系添加依赖。MiniMax 模型名、账户 Base URL 和首轮可用环境仍需确定。

| 需要查看什么 | 唯一维护位置 |
| --- | --- |
| 两阶段路线、A–H 工作范围与整体验收 | [doc-002](backlog/docs/doc-002%20-%20总体路线与验收边界.md) |
| 已确认目标、理由与停止边界 | [decision-001](backlog/decisions/decision-001%20-%20先完成无-GPU-API-评测链路，再接-Agent-Sandbox.md) |
| 源码位置、版本差异与候选方案 | [doc-003](backlog/docs/doc-003%20-%20接口调查与待确认事项.md) |
| 消息 API adapter 接口、职责与待实现测试案例 | [doc-004](backlog/docs/doc-004%20-%20消息-API-Adapter-接口约定与测试案例.md) |
| 迁移前原文，只供追溯、不维护状态 | [doc-001](backlog/docs/doc-001%20-%20迁移前原文快照.md) |

## 使用 Backlog

本机版本 **1.54.0**。进入本目录后运行：

```bash
backlog task view MH-001 --plain
backlog task list --ready --plain
backlog browser --no-open --port 6420
```

看板地址：[http://127.0.0.1:6420](http://127.0.0.1:6420)。服务需在当前机器运行；其他机器先安装对应工具，再从此目录启动。

`--ready` 只表示已记录的任务依赖满足，不代表所有现实条件已验证。用 `--dep` 保存真实直接依赖，由工具计算阻塞关系；不要另维护反向 blocks 列表。

使用 CLI 管理任务与文档。1.54.0 的 CLI 不支持决策正文编辑，这部分通过自带网页编辑器/API 保存；不手改受管理文件。开始前运行 `backlog instructions overview`，再读对应操作指南。

工具采用文件模式，不自动提交、不访问远端或扫描其他分支、不创建嵌套 Git。文件仍随当前学习仓库版本管理；实际代码和测试在独立集成仓库，必要的框架补丁在对应 fork，任务中记录来源与验证证据。

```text
minimax-harbor/
├── README.md             # 目标、边界与入口
├── AGENTS.md             # 本地维护约定
├── backlog.config.yml    # 工具配置
└── backlog/
    ├── tasks/            # 问题、验收、实施计划与结果
    ├── decisions/        # 已确认的重要选择
    └── docs/             # 总体路线、调查与迁移来源
```

原 issues、decisions、plans 三个外部目录已移除，内容去向见上表。函数卡、源码阅读步骤和外层 discussion 参考资料不在本次迁移范围内。

## 补充参考

- [原始 discussion 的完整提取](../references/sandbox-infra-discussion-extraction.md)
- [discussion 事实核对](../references/sandbox-infra-discussion-fact-check.md)
- [此前实施范围评估](../references/implementation-scope-assessment.md)：历史评估材料，不能代替本页已确认边界或增加任务。
- [用户提供的讨论原文](../references/sandbox-infra-discussion-original.md)
- [更早的方案演变快照](../../references/history/2026-11-17-minimax-plan-before-implementation.md)
