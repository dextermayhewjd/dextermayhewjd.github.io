---
id: MH-001
title: 核对 Dressage 与 Harbor 的运行版本兼容性
status: In Progress
assignee: []
created_date: '2026-11-17 06:48'
updated_date: '2026-11-17 11:23'
labels:
  - phase-1
  - compatibility
dependencies: []
references:
  - /home/hongshi/projects/Dressage/pyproject.toml
documentation:
  - backlog/docs/doc-003 - 接口调查与待确认事项.md
  - backlog/docs/doc-002 - 总体路线与验收边界.md
  - backlog/docs/doc-001 - 迁移前原文快照.md
  - backlog/decisions/decision-001 - 先完成无-GPU-API-评测链路，再接-Agent-Sandbox.md
priority: high
type: spike
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
来源：现有问题 Q04。Dressage 固定提交 3e3142fe 声明并检查 Harbor 0.18.0，而此前阅读的是本地 Harbor v0.25.0；不能把阅读版本自动当作可运行依赖。本任务确认首轮 MiniMax × Harbor 实践应使用的版本及运行前提，不因版本不同就默认升级，也不要求调用模型 API 或启动沙箱。已有记录只提供静态证据，尚未证明实际安装与导入成功。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 记录 Dressage 提交、实际 Python 与 Harbor 版本；若尚未安装，明确缺失并给出可执行的环境准备方式。
- [x] #2 核对依赖声明和运行时版本门禁，明确首轮采用的 Harbor 版本，以及与已读 v0.25.0 的区别。
- [ ] #3 在选定环境执行不调用模型 API、不创建沙箱的导入或版本门禁检查，保存命令与输出；未通过时保留阻碍，不标记完成。
- [ ] #4 把版本结论及其对后续接入的影响关联到现有设计记录；不将静态核对或此项通过描述为整条链路已跑通。
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-17 用户询问完整 Harbor Trial 就绪情况，按 Step 014 Gateway / RolloutLLMProxy → Step 006 central Proxy 回查。实施虚拟环境 Python 3.12.3；importlib.metadata 显示 harbor、dressage、dressage-blackbox-server 均未安装，harbor.plugins 无入口。实际 require_harbor_runtime() 返回 HarborCompatibilityError: Harbor is not installed; install the Dressage Harbor optional dependency。compat.py 固定 Harbor==0.18.0、Python>=3.12；首轮应沿固定版本，不能将阅读 checkout v0.25.0 视为已安装依赖。补充：PYTHONPATH 指向 third_party/dressage 时，本地 blackbox_server.proxy.rollout_llm_proxy.RolloutLLMProxy 可成功导入，不能把发行包缺失误称为没有这层源码。机器发现 docker/bwrap/claude/node 可执行文件，但未验证守护进程、镜像或环境启动。原 run_harbor_rollout_qwen3.5_4b.sh 会启动 router、SGLang worker 与 token Proxy；API 路线须使用自有 serve:create_api_app，保留最后 harbor run --config ... --plugin dressage 的任务入口。当前仅调查，未安装依赖或启动 Trial。
<!-- SECTION:NOTES:END -->
