# Launch Agent：源码与材料校验

本文件对应已采用正文的 C01–C09。正式章节与 Harness.run 兼容入口共用该正文；旧讲解与旧图保留在存档。

## 固定依据

- 持续使用已确认仓库 `/home/fredkeira/projects/slime`，阅读快照为 `22a89f96835969a47055a659c588f46151f8b07a`。
- 原示例来自 `8c17b676cb57af1d17ee4402e91e9209af84b60b`；本章相关五个源码文件逐字相同，正文源码链接固定到该本地阅读快照。
- 本章先读 Claude Code；Codex 仅作接口对照。
- 原示例中的命令、地址和会话标识是教学值；CLI、Sandbox 和模型均未真实启动。
- 官方 main 核对记录单独存入 `upstream-check.json`；本轮不更新源码。

## C01

**核对事实：** generate 在工作区准备后调用 Harness；公共 run 先确认用户，再创建上下文、写配置、启动等待。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 调用方准备完成并进入 run | `examples/coding_agent_rl/generate.py:203` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L203-L213) |
| 公共 run | `slime/agent/harness/common.py:81` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L81-L104) |
| 选择 Harness 与 Adapter | `examples/coding_agent_rl/generate.py:45` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L45-L52) |


## C02

**核对事实：** 用户准备通过 sb.exec 执行，以 root 请求创建或确认 agent 用户、目录所属与 Git safe.directory；不创建新沙箱。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| run 内调用 | `slime/agent/harness/common.py:97` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L97-L97) |
| 用户准备 helper | `slime/agent/sandbox.py:390` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L390-L399) |


## C03

**核对事实：** HarnessContext 是冻结 dataclass，保存三个传入字段与默认模型标签；不含 sb、prompt 或预算。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 上下文定义 | `slime/agent/harness/common.py:42` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L42-L54) |
| 构造上下文 | `slime/agent/harness/common.py:98` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L98-L102) |


## C04

**核对事实：** Claude write_config 接口接收 ctx，但本实现不读取它；只写两项静态启动设置并设置文件所属。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 公共配置调用 | `slime/agent/harness/common.py:103` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L103-L103) |
| Claude 配置实现 | `slime/agent/harness/claude_code.py:44` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/claude_code.py#L44-L55) |


## C05

**核对事实：** Claude 使用 shlex.quote 引用 prompt，添加固定启动 flags；ctx 进入 env，额外环境最后可覆盖已有键。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 公共启动调用 | `slime/agent/harness/common.py:104` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L104-L104) |
| Claude 命令和环境 | `slime/agent/harness/claude_code.py:57` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/claude_code.py#L57-L71) |
| 固定 flags 和环境 | `slime/agent/harness/claude_code.py:18` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/claude_code.py#L18-L34) |


## C06

**核对事实：** run_agent 创建日志目录后调用 exec_and_wait；只取 exit_code，把下层返回的 output 丢弃。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 运行 helper | `slime/agent/harness/common.py:107` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L107-L122) |
| 执行接口签名与返回约定 | `slime/agent/sandbox.py:82` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L82-L105) |
| 返回结果处理 | `slime/agent/sandbox.py:139` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L139-L145) |


## C07

**核对事实：** 外层取得进程状态后收集diff，离开工作沙箱上下文，再在独立评估中计算reward。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 接收状态并收集/评估 | `examples/coding_agent_rl/generate.py:203` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L203-L219) |
| 等待预算耗尽 | `slime/agent/sandbox.py:62` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L62-L79) |
| 工作沙箱退出与回收 | `examples/coding_agent_rl/generate.py:131` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L131-L134) |


## C08

**核对事实：** 预算/异常/输出边界分别由底层等待、Sandbox操作和外层上下文承担。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 等待预算返回 | `slime/agent/sandbox.py:62` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L62-L79) |
| 运行输出处理 | `slime/agent/sandbox.py:139` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L139-L145) |
| 外层工作沙箱生命周期 | `examples/coding_agent_rl/generate.py:95` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L95-L134) |
| 外层时间保护 | `examples/coding_agent_rl/generate.py:200` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L200-L203) |


## C09

**核对事实：** BaseHarness保留统一扩展接口；Codex在自己的实现中消费ctx并构造不同CLI启动参数。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| Harness扩展接口 | `slime/agent/harness/common.py:57` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L57-L79) |
| Codex配置与启动 | `slime/agent/harness/codex.py:56` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/codex.py#L56-L86) |


## 图和示例

- `flow.svg` 是本次已采用的新局部图，聚焦 run 的四步与执行接口；原纵向图、架构图保持不变。
- 图中的调用是简化的阅读骨架，完整命名参数和 await 见正文源码。
- `示例.json` 与原材料完全相同；其中同时保存 Claude 和 Codex 分支，原始 revision 不改写。
- `.harness/trajectory.jsonl` 是 CLI 标准输出／错误文件，不是 Adapter 保存的模型 token 轨迹。
- `run_agent` 只返回整数，丢弃 exec_and_wait 的 output。`-1` 表示等待预算耗尽，不等于观测到真实进程退出。

## 本轮实际验证

- 用真实源码提取的 AST 与记录器检查 Claude 路径，捕获到的 sb.exec 请求及 exec_and_wait 参数与原示例一致。
- 用单一事件列表检查用户准备、配置、日志目录、执行委派的实际调用顺序。
- 用模拟返回 0、7、-1 验证整数沿 Harness 返回；-1 只验证传播，不是运行真实计时超时。
- 模拟配置写入异常，验证异常传播且不继续运行 CLI。
- Sandbox 与 exec_and_wait 都是替身，SingletonABCMeta 使用 ABCMeta 替代，环境变量字典固定为空。未运行真实 CLI、远端命令、网络请求、模型或训练。

结果详见同目录 `validation.json`。原始文件的保留哈希及获批稿记录见 `adoption-manifest.json`。


## 网页与保留检查

13 项章节检查通过。浏览器已确认两侧分别打开原 Harness.run 讲解与候选页，新图和六项输入表可读，9 个源码组默认折叠且可键盘展开，示例和校验文件返回 200，窄屏无页面横向溢出。上述为定稿阶段检查；正式页已在用户确认后采用，原讲解与材料保留。


## 正式采用检查

用户确认新稿后，第 4 章、原 harness-run 兼容地址及预览共用本目录 reading.md。侧栏保留一个入口；旧正文保存在对比页左侧。浏览器已检查 9 个默认收起的源码组、键盘展开、资源返回 200 及窄屏；13 项章节检查通过。
