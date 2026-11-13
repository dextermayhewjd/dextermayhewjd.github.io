# Agent Sandbox 阅读约定

以下为本项目的局部约定，依据用户于 2026-11-05 的最新授权，优先于此前参照 Slime 拟定的跨主题编号与继承方案。

1. 当前主题是 `topics/kubernetes-sandbox-control/`，目标见 `references/tencent-k8s-learning-scope.md`。它聚焦 Kubernetes 沙箱资源与生命周期，不继续扩展 Python 训练调度专题。
2. 每个主题独立编号。Kubernetes 主题从自己的 Step 000 开始；引用步骤时同时写明主题，避免与旧 Fleet Step 000 混淆。
3. 用户于 2026-11-05 随后要求将原有步骤也归为主题。旧 Step 000、001 已整体移入 `topics/fleet-environment-orchestration/steps/`，原目录后缀、原话、未知与完成状态保留；不因新主题开始或目录整理而标记旧步骤完成。
4. 不自动跨主题合并记忆。新主题首步的 `03-long-term-memory` 暂无前序继承；旧记录仅在当前问题需要时引用或调取，并保留来源。本主题内部后续步骤仍按前一步 `03 + 02` 继承，除非用户另有调整。
5. scope 保存完整主线及稳定的面包屑导航，推进时保留前面经过的入口。详细函数解释归短期卡；未实际阅读的函数不提前建卡。
6. 项目 `README.md` 是唯一实时进度来源，主题 README 只说明目标、规则和步骤索引。
7. 2026-11-05 经用户确认，通用 Kubernetes 基础统一维护在 `../kubernetes/`；当前函数卡保留主体并引用共享解释，项目特有策略与岗位范围仍留在本项目。共享资料不替代函数记忆，也不改变已读和未知状态。

这些约定只应用于 Agent Sandbox，不改写 Slime、Dressage 或通用 skill 的规则。
