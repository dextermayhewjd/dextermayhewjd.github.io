# 原生 Dressage 单任务闭环

[项目入口与唯一进度](../../README.md) · [后续主题：Harbor 接入](../02-harbor-integration/README.md) · [整体接入规划](../../references/integration-reading-plan.md)

## 本主题解决什么问题

一份题目怎样通过原生 blackbox_dispatch.generate 取得环境、执行 Agent、读取 Proxy 轨迹、转换成 Sample，并完成退出清理。

本主题保留 Paddock → BlackboxServer 的原生路线。它是后续 Harbor 接入的对照，不会再次嵌进每个 Harbor Trial。

## 步骤索引

| 步骤 | 本步问题 | 入口 | 资料状态 |
| --- | --- | --- | --- |
| Step 000 | generate 怎样串起完整任务？ | [scope](steps/step-000-slime-bridge-and-interfaces/01-scope.md) | 保留既有记录 |
| Step 001 | 任务身份与运行参数从哪里来？ | [scope](steps/step-001-task-identity-and-parameters/01-scope.md) | 保留既有记录 |
| Step 002 | 怎样取得 Proxy 客户端并领取预热结果？ | [scope](steps/step-002-proxy-client-and-prewarm-claim/01-scope.md) | 保留既有记录 |
| Step 003 | 未命中后怎样更新身份并取得 Paddock？ | [scope](steps/step-003-paddock-selection/01-scope.md) | 保留既有记录 |
| Step 004 | 环境需求怎样成为可用的 state？ | [scope](steps/step-004-paddock-environment-preparation/01-scope.md) | 保留既有记录 |
| Step 005 | 已有环境怎样完成 Agent 注册准备？ | [scope](steps/step-005-agent-registration/01-scope.md) | 保留既有记录 |
| Step 006 | 题目怎样交给 Agent，执行结果怎样返回？ | [scope](steps/step-006-agent-execution/01-scope.md) | 保留既有记录 |
| Step 007 | Agent 结束后怎样收尾并取得 Proxy 轨迹？ | [scope](steps/step-007-proxy-finalization-and-trajectory/01-scope.md) · [本步记录](steps/step-007-proxy-finalization-and-trajectory/README.md) | 已首轮收束；有任务链路总结 |
| Step 008 | 轨迹段怎样成为 Sample 并保留任务归属？ | [scope](steps/step-008-segments-to-samples/01-scope.md) | 已首轮收束；有任务链路总结 |
| Step 009 | 正常、失败和取消时谁回收资源？ | [scope](steps/step-009-rollout-cleanup/01-scope.md) | 正常回收主线首轮收束；其他路径保留回查 |

## 记录与编号

1. 原 Step 000–006 整体迁入本主题；文件名、源码版本、原话、未知和历史记录保留。目录迁移不改变学习状态。
2. Step 007 已按正常主线首轮收束，保存实际使用的函数记录、本步过程与任务链路总结；Step 008 已首轮收束，Step 009 的正常回收主线已首轮收束；未读 helper 与完整失败路径保留回查。
3. Dressage 的 Step 编号跨主题连续。实际进入下一步时继续采用原有 03 + 02 的继承方式；当前预备 scope 不提前生成长期记忆。
4. 3.1 保留本步在主题主线中的位置；3.2 的图表达执行关系，连续编号表表达阅读顺序与返回位置。
5. 实际阅读位置只在项目 README 维护。
