# 第 1 章 完整任务、Harness 与执行环境

[阅读路线](../../repo-reading-route.md) · [总目录](../../README.md)

**目录 ID：** `01-task-execution`
**产物状态：** ready
**学习状态：** 统一见[阅读路线的当前接续](../../repo-reading-route.md#当前接续)。

**问题：** 代码任务怎样启动 CLI、让 CLI 回连模型入口、收集补丁、独立评分并释放资源？

**前置：** 00；已知道任务、请求和训练的区别。

**图文对照：** 4.1 的动作 4、5、6、7；7.1。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 任务生命周期 | [examples/coding_agent_rl/generate.py · generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L182) | trace | 分别追踪训练与 evaluation 分支；不是通用的独立任务平台。 |
| 调用方的模型入口准备 | [_AdapterService.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L138)（examples/coding_agent_rl/generate.py） | trace | 细读 tokenizer/解析配置、Adapter 内部状态、HTTP 线程、监听/回连地址和进程复用；返回调用方继续任务、Session、环境和题目准备。 |
| 启动骨架 | [slime/agent/harness/common.py · BaseHarness.run](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L81) | trace | 配置和 CLI 启动可替换；CLI 内部工具循环在外部软件包。 |
| 沙箱操作合同 | [slime/agent/sandbox.py · Sandbox](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L28) | trace | 当前实现为 E2B；Kubernetes 后端需独立实现和验证操作语义。 |
| 长命令等待 | [slime/agent/sandbox.py · exec_and_wait](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L82) | explain | 区分等待超时、进程退出和外层环境回收，不能假设返回超时就已杀死进程。 |
| 补丁的独立评估 | [examples/coding_agent_rl/swe.py · run_evaluation](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/swe.py#L239) | trace | 评分环境与 Agent 工作环境分开；继续定位 _grade_scaleswe/_grade_swebench。 |

**章内顺序：**

1. 先读 generate()，记录创建者、持有者、收集者和清理者。
2. 依次读 Harness.run、Sandbox 操作合同、exec_and_wait；再定位 Claude/Codex Harness 的模型地址和会话身份配置。
3. 补读 4.1 的动作 7 Make API Calls，接到 BaseAdapter._run_turn 的 HTTP 入口；模型处理留到 02。
4. 回到 swe.git_diff 和 run_evaluation，辨认工作环境退出后在新评估环境应用补丁并运行测试。
5. 沿超时、CLI 非零退出、空轨迹、评分失败和 finally 追踪结果与清理；用 tests/test_agent 中的 fake 测试理解可验证边界。

**验收问题：** 如果换 Agent CLI 或沙箱后端，分别修改哪层？CLI 的退出码为什么不等于任务 reward？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](../../repo-reading-route.md#当前接续)。
