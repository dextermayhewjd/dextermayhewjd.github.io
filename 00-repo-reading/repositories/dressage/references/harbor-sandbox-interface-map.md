# Harbor 到 Agent Sandbox：先明确接缝

2026-11-17 静态核对。Harbor 本地 `/home/hongshi/projects/harbor`，提交 `fdba28fc411e47e8765420a1a063b4918fce3def`（v0.25.0），工作区干净。本文件保存接口对照与候选阅读入口，不表示适配已完成或已运行验证。

本轮后续系统问题见[预热、领取与 Kubernetes 对接](sandbox-supply-prewarm-and-kubernetes.md)：解释接口背后怎样供给环境。

## 当前要解决什么

用户希望知道 Harbor 调用了哪些沙箱能力、现成例子在哪里，以及怎样接入 Agent Sandbox。回到 Step 013 的环境接缝；不继续扩展 Step 016 清理 helper。

```text
Harbor 的 Trial / Agent / Verifier
    ↓ 调用共同接口
具体 Environment 对象（继承 BaseEnvironment）
    ↓ 把接口翻译为后端操作
Agent Sandbox 资源管理 + 容器命令执行/文件传输
    ↓
承载本次任务的 Pod
```

`BaseEnvironment` 是共同约定；真正创建沙箱的是具体子类。Harbor 可以用 `environment.import_path = "module.path:ClassName"` 加载外部子类，不必把类塞进内置注册表。

## 先记七个操作，不把它们当作七次调用

| Harbor 要做什么 | 后端必须提供的方法 | 已读链路中的用途 |
| --- | --- | --- |
| 准备可用环境 | `start(force_build)` | `_start_agent_environment` 等待环境可用，再安装/运行 Agent |
| 在环境中执行命令 | `exec(command, cwd, env, timeout_sec, user)` | 健康检查、安装 Agent、运行 Agent、执行评测脚本；返回 `ExecResult(stdout, stderr, return_code)` |
| 放入一个文件 | `upload_file(source_path, target_path)` | 安装脚本等：宿主机 → 沙箱 |
| 放入一个目录 | `upload_dir(source_dir, target_dir)` | skills、tests、solution 等：宿主机 → 沙箱 |
| 取回一个文件 | `download_file(source_path, target_path)` | 单文件结果：沙箱 → 宿主机 |
| 取回一个目录 | `download_dir(source_dir, target_dir)` | 日志、轨迹、产物和评测输出：沙箱 → 宿主机 |
| 收尾 | `stop(delete)` | 正常退出和取消后的资源收尾；实现必须明确保留/删除策略 |

这是操作种类，不是一次 Trial 的调用次数；`exec`、传输可能重复，也不一定每次都用到全部七种。

本版本共有九个抽象方法：上述七个，另加 `type()` 和 `_validate_definition()`。`capabilities` 有默认实现，但自定义后端应如实声明能力；不能仅因类能实例化，就认为资源、网络、挂载语义已经兼容。Compose 等可选能力还有额外接口，不列为当前单容器路径的必读范围。

特别需要保留：`exec` 不能只转发 command。官方模板要求使用 `_merge_env()` 和 `_resolve_user()`，并落实 cwd、timeout、stdout/stderr、退出码的语义。继承的健康检查等工具会继续使用这些底层接口。

## 现成材料，按用途选

1. **先看官方最小子类模板**：[custom-sandboxes.mdx](/home/hongshi/projects/harbor/docs-mintlify/sandboxes/custom-sandboxes.mdx)。它把接口、环境变量与默认用户处理、import_path 配置放在一起，最适合本轮建立整体形状。
2. **只用一个完整实现看翻译方式**：[E2BEnvironment](/home/hongshi/projects/harbor/src/harbor/environments/e2b.py:256)。例如 `upload_file` 读取本地 bytes 后调用后端 `files.write`；`exec` 把后端结果转成 `ExecResult`。它示范适配方法，不是 Agent Sandbox 的实现。
3. **Kubernetes 细节按需对照**：[GKEEnvironment](/home/hongshi/projects/harbor/src/harbor/environments/gke.py:739)。创建、exec、tar 文件传输可作参考，不必全文精读。ACK 使用 OpenKruise，不能把它的 Claim 当成 kubernetes-sigs/agent-sandbox 的 Claim。
4. **Agent Sandbox 的目标流程**：[官方 Terminal-Bench 示例](https://github.com/kubernetes-sigs/agent-sandbox/blob/main/examples/harbor-terminal-bench/README.md)。其文档描述由适配层创建/复用 Template、WarmPool，创建 Claim 并等可执行，通过 Pod exec 和 tar 执行/传输，最后删除或保留 Claim。该示例使用 `k8s_agent_sandbox_harbor:AgentSandboxEnvironment`。

**示例文档存在，不等于当前已拿到可用适配包。** 本机 `/home/hongshi` 下本轮限定深度搜索未找到 Agent Sandbox 源码 checkout（仅找到阅读资料）。在线能读取上述 README，但它引用的 `clients/integrations/harbor/pyproject.toml` 返回 404，其 README/实现未成功取得；在线目录结果还可能带缓存。因此目前只能确认有目标流程示例，不能确认该适配包可安装运行，也不能据此断言所有分支都没有实现。过去 checkout 缺少此目录的结论保留在兼容性 reference 中，不冒充本机最新核对。

## 下一次精读入口与停止位置

建议先打开官方最小子类模板，把这七个操作与已经读过的 Trial/Agent/Verifier 对上；然后仅看一个具体 `exec` 的输入与 `ExecResult` 输出。理解共同接口怎样翻译为后端调用后，再核对 Agent Sandbox 的实际实现/SDK。此次未新建任何未读方法卡。

最小接入验证候选：创建环境 → 上传一个文件 → 执行命令读取并生成输出 → 下载输出 → 停止/删除 → 检查资源。先验证这一小圈，再加入真实 Agent 与评测。此为建议，尚未启动实验。

Dressage 当前仍锁定 `harbor==0.18.0`，本轮阅读的是 Harbor v0.25.0；正式连起来运行前需要处理版本合同，不能只安装新版就算完成。详见[兼容性记录](agent-sandbox-harbor-compatibility.md)。

## 源码核对入口

- [BaseEnvironment](/home/hongshi/projects/harbor/src/harbor/environments/base.py:861)：类型、能力、定义检查；1108 起生命周期/传输；1359 起 exec。
- [EnvironmentFactory](/home/hongshi/projects/harbor/src/harbor/environments/factory.py:327)：导入并实例化外部类。
- [Trial](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:1856)：start；817/824 日志下载，1830 skills 上传，2045 stop。
- [Verifier](/home/hongshi/projects/harbor/src/harbor/verifier/verifier.py:220)：上传 tests、执行、下载评测日志。
- [Installed Agent](/home/hongshi/projects/harbor/src/harbor/agents/installed/base.py:1097)：脚本上传与命令执行。
