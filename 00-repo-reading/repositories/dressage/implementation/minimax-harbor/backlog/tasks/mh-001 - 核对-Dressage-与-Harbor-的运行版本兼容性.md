---
id: MH-001
title: 核对 Dressage 与 Harbor 的运行版本兼容性
status: Done
assignee:
  - '@codex'
created_date: '2026-11-17 06:48'
updated_date: '2026-11-17 11:57'
labels:
  - phase-1
  - compatibility
dependencies: []
references:
  - /home/hongshi/projects/Dressage/pyproject.toml
  - >-
    /home/hongshi/projects/agent-api-integration/third_party/dressage/pyproject.toml
  - /home/hongshi/projects/agent-api-integration/USAGE.md
documentation:
  - backlog/docs/doc-003 - 接口调查与待确认事项.md
  - backlog/docs/doc-002 - 总体路线与验收边界.md
  - backlog/docs/doc-001 - 迁移前原文快照.md
  - backlog/decisions/decision-001 - 先完成无-GPU-API-评测链路，再接-Agent-Sandbox.md
  - backlog/docs/doc-004 - 消息-API-Adapter-接口约定与测试案例.md
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
- [x] #1 记录 Dressage 提交、实际 Python 与 Harbor 版本；若尚未安装，明确缺失并给出可执行的环境准备方式。
- [x] #2 核对依赖声明和运行时版本门禁，明确首轮采用的 Harbor 版本，以及与已读 v0.25.0 的区别。
- [x] #3 在选定环境执行不调用模型 API、不创建沙箱的导入或版本门禁检查，保存命令与输出；未通过时保留阻碍，不标记完成。
- [x] #4 把版本结论及其对后续接入的影响关联到现有设计记录；不将静态核对或此项通过描述为整条链路已跑通。
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
- [x] 使用 uv 与 Python 3.12 创建独立 .venv-harbor，并加入 Git 忽略；原 .venv 包清单不变。
- [x] 从固定 Dressage 3820149 导出临时快照，普通安装 Dressage/blackbox，安装 Harbor 0.18.0、已解析依赖及 editable 集成仓库。
- [x] 检查112包依赖一致性、插件发现、运行时版本及真实模块导入；109项离线测试通过。
- [x] 在 USAGE.md 保存安装与使用方式，将版本结论关联 doc-003/doc-004；真实 Trial 交由 MH-007，不以本任务替代。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-17 用户询问完整 Harbor Trial 就绪情况，按 Step 014 Gateway / RolloutLLMProxy → Step 006 central Proxy 回查。实施虚拟环境 Python 3.12.3；importlib.metadata 显示 harbor、dressage、dressage-blackbox-server 均未安装，harbor.plugins 无入口。实际 require_harbor_runtime() 返回 HarborCompatibilityError: Harbor is not installed; install the Dressage Harbor optional dependency。compat.py 固定 Harbor==0.18.0、Python>=3.12；首轮应沿固定版本，不能将阅读 checkout v0.25.0 视为已安装依赖。补充：PYTHONPATH 指向 third_party/dressage 时，本地 blackbox_server.proxy.rollout_llm_proxy.RolloutLLMProxy 可成功导入，不能把发行包缺失误称为没有这层源码。机器发现 docker/bwrap/claude/node 可执行文件，但未验证守护进程、镜像或环境启动。原 run_harbor_rollout_qwen3.5_4b.sh 会启动 router、SGLang worker 与 token Proxy；API 路线须使用自有 serve:create_api_app，保留最后 harbor run --config ... --plugin dressage 的任务入口。当前仅调查，未安装依赖或启动 Trial。

2026-11-17 任务审计：实施仓库 HEAD=53423621e2bb146638e9a187c52d67803def071d，Dressage gitlink=3820149ebfc0536b213ec120b43ec090f09b3fcd。当前 .venv 为 Python 3.12.3；运行 .venv/bin/python -m pip show harbor dressage dressage-blackbox-server，三者均未安装。运行 PYTHONPATH=third_party/dressage .venv/bin/python -c 'from dressage.integrations.harbor.compat import require_harbor_runtime; print(require_harbor_runtime())'，仍返回 HarborCompatibilityError: Harbor is not installed。保留 In Progress 与尚未完成的验收项；此次未安装依赖或启动 Trial。下一交付为准备固定依赖并通过运行时检查；真实单题验收由 MH-007 承接。

2026-11-17 下一步交付边界：先完成不调用模型、不创建沙箱的运行准备核对，明确隔离环境与固定依赖安装方案，检查实际依赖解析、Harbor 0.18.0/Python>=3.12 版本门禁和 dressage 插件发现。不要直接向当前可用 adapter 环境盲装整套训练依赖，也不因仅有配置文件而宣称运行环境就绪。本轮只记录要求，未安装或启动。MH-007 的任务正文已记录短规格 v0.1；本任务通过后，再补齐其具体 Agent、任务、环境和网络配置，正式领取时记录实施计划。

2026-11-17 用户同意按既定路线推进；本轮开始无安装的依赖预检，使用 uv pip compile 对集成仓库和固定 Dressage pyproject.toml 解析 harbor/bridge/test extras，目标 Python 3.12，公开 PyPI，禁止源码构建，输出 /tmp/agent-harbor-preflight/requirements.txt。不会修改当前 .venv、运行容器或调用模型。长期方向引用已有 decision-001，预检结果及后续环境准备记录在本任务。

2026-11-17 依赖解析实际结果：第一轮仅以集成仓库和 Dressage 根 pyproject.toml 为输入，uv pip compile 报公开 PyPI 找不到 dressage-blackbox-server==1.1.0。静态核对确认固定子模块 blackbox_server/pyproject.toml 就是该发行包，版本 1.1.0；docs/quickstart.md 亦说明从 blackbox_server/ 本地安装。第二轮在 /tmp/agent-harbor-preflight/local-source.in 指定该固定源码的 file URI，重新运行 uv pip compile pyproject.toml third_party/dressage/pyproject.toml /tmp/agent-harbor-preflight/local-source.in --extra harbor --extra bridge --extra test --python-version 3.12 --no-build --default-index https://pypi.org/simple --cache-dir /tmp/agent-harbor-preflight/cache --output-file /tmp/agent-harbor-preflight/requirements.txt --quiet，退出 0。结果保留 Harbor 0.18.0、Ray 2.55.1、Transformers 5.12.1，blackbox 解析至同一固定子模块源码。完整标准依赖仍包含 Ray/Transformers；本轮未安装、未构建、未修改子模块或当前 .venv，不能勾选运行时验收。解析结果为本机临时产物，含绝对源码路径，不直接作为跨机器锁文件发布。下一步在独立环境中安装已核对依赖并注册两个本地发行包，运行 pip check、harbor plugins list、require_harbor_runtime()，成功后才更新 AC；若失败先保留真实阻碍。此项属于既定路线下的依赖来源核对，记录在任务即可，不新增架构决策。

2026-11-17 独立环境安装完成：用户明确授权使用 uv 安装。uv 0.13.8 + /usr/bin/python3.12 创建 /home/hongshi/projects/agent-api-integration/.venv-harbor，Python 3.12.3。使用前次已解析 requirements，将 blackbox 源码地址改为固定 Dressage 3820149 的 git archive 临时副本 /tmp/agent-harbor-install.apHmZ4/dressage/blackbox_server；普通安装 dressage 0.1.0、dressage-blackbox-server 1.1.0，editable 安装集成仓库。实际命令：uv pip install --python .venv-harbor/bin/python --cache-dir /tmp/agent-harbor-preflight/cache --default-index https://pypi.org/simple -r /tmp/agent-harbor-install.apHmZ4/requirements.txt /tmp/agent-harbor-install.apHmZ4/dressage -e .。共安装112包，含 harbor 0.18.0、ray 2.55.1、transformers 5.12.1，未安装模型权重或启动推理。
验证：uv pip check --python .venv-harbor/bin/python -> All installed packages are compatible；.venv-harbor/bin/harbor plugins list 显示 dressage；require_harbor_runtime() 返回 Python (3,12,3)、Harbor 0.18.0；harbor.job.Job、DressageHarborPlugin、GatewayRuntime、RolloutLLMProxy 导入成功。dressage 与 blackbox_server 实际导入路径均在新环境 site-packages，非临时源码或原环境。timeout 60 .venv-harbor/bin/python -m pytest -q 在沙箱外运行 -> 109 passed in 0.95s，供应商 HTTP 模拟；tests/conftest.py 仍按设计测试固定源码，不能将该套件称为真实 Trial。
原 .venv 安装前后 pip freeze 经 cmp 相同；git -C third_party/dressage status --short 为空；git diff --check 通过。新环境已加入 .gitignore，包清单保存在该环境内 installed-requirements.txt。USAGE.md 的“独立 Harbor 运行环境（uv）”保存从 gitlink 导出、依赖解析、安装、检查及使用方式。
版本结论：实际采用 0.18.0，与 doc-003 的固定版本约束一致，未使用阅读 checkout 0.25.0；与 doc-004 的消息合同一起构成 MH-007 的运行前提。只完成安装/导入/离线测试，未运行真实 Gateway 网络、Agent、Verifier、容器、Harbor Trial、Slime 或K8s；相关验收仍属于 MH-007/MH-004。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
已在独立 .venv-harbor 安装并验证 Python 3.12.3、Harbor 0.18.0、固定 Dressage 3820149 的发行包和本地 blackbox 1.1.0。112包依赖一致，Harbor 发现 dressage 插件，版本门禁及 Job/插件/Gateway/协议代理导入通过，109项离线测试通过。原 .venv 与子模块未改动。安装方式见集成仓库 USAGE.md，版本约束关联 doc-003/doc-004；真实 Trial、Agent/Verifier、网络和环境清理仍由 MH-007 验证。
<!-- SECTION:FINAL_SUMMARY:END -->
