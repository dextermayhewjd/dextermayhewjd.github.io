# 01 · Kubernetes Step 006：取得环境后怎样访问、排障与回收连接

[主题入口](../../README.md) · [项目唯一进度](../../../../README.md#current-reading) · [前一步 scope](../step-005-claim-ownership/01-scope.md) · [共享 Kubernetes 基础](../../../../../kubernetes/README.md)

本页预先定义一条 SDK 访问路径与一个权限观察点，不表示已执行真实命令、部署安全配置或完成排障。

## 1. 阅读目标

**把“Claim 已经 Ready”接到“调用方能够执行命令、读写文件”，并分清 API 权限、运行入口和沙箱内权限。**

1. 看 SDK 怎样等待 Claim、取得 Sandbox 名称并返回一个可操作句柄。
2. 沿一个短命令和一份小文件，看连接方式、请求目标及结果怎样交回调用方。
3. 只选一项具体失败观察：调用者缺少 Kubernetes 对象读取/观察权限时，在哪层失败；与沙箱命令自身的非零退出码分开。

## 2. 指挥官、选定场景与停止位置

操作入口是 [SandboxClient.create_sandbox](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/clients/python/agentic-sandbox-client/k8s_agent_sandbox/sandbox_client.py#L126)。主要下钻 [CommandExecutor.run](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/clients/python/agentic-sandbox-client/k8s_agent_sandbox/commands/command_executor.py#L90)，连接来源按需要回查。

先选 SDK 的 legacy HTTP runtime 与 SandboxLocalTunnelConnectionConfig，对照实际模板、router 和监听端口。只用不依赖 cwd/env 覆盖的短命令；本版本这些覆盖在 legacy 分支不受支持。sandboxd 的 gRPC 与 in-cluster 模式只标明差异入口，不把两套协议同时深入。

**停止位置**：能说明句柄不等于 Pod、本地连接不等于 K8s 资源；命令返回退出码/stdout/stderr，文件读取返回 bytes；关闭连接与删除 Claim 的效果不同。留下正常操作与一个权限故障的验证方案，本页准备阶段不实际执行。

## 3. 整体位置与本步阅读

### 3.1 本步在 Kubernetes 沙箱主线中的位置

以下是 API、控制器与数据访问的关系示意，不是可执行程序：

```python
SandboxTemplate + SandboxWarmPool.spec
  -> SandboxWarmPoolReconciler   # 已有范围：维持备用环境。
       -> Sandbox
Sandbox.spec
  -- watch --> SandboxReconciler # 已有范围：协调 Pod / Service / PVC 与状态。
       -> Kubernetes API: Pod / Service / PVC
            -> scheduler / kubelet / runtime  # 调度和运行 Pod，不是直接调度 Sandbox CR。

caller creates SandboxClaim
  -- watch --> SandboxClaimReconciler
       -> assigned Sandbox + Claim.status.Ready

SandboxClient waits for Claim, returns Sandbox handle  # Step 006：接入访问路径。
  -> commands / files -> connector -> runtime service  # Step 006：命令与文件结果。
  -> close_connection                                  # Step 006：只关本地连接。
  -> terminate -> delete Claim                         # Step 006：接回资源回收。
```

权限观察覆盖当前请求经过的三处：调用者访问 Kubernetes API 的 RBAC、connector 到运行入口的网络路径、命令在容器中运行时的身份。只定位它们的边界，不把此步扩展成完整安全课程。

### 3.2 本步调用骨架与阅读顺序

下面是准备阅读的 SDK 使用骨架，参数省略，不是可直接运行的验证脚本。失败处理与测试条件需在实际执行时补齐。

```python
sandbox = client.create_sandbox(...)  # 创建/等待 Claim，取得可操作句柄。
result = sandbox.commands.run(...)   # 一次短命令，取得退出码与输出。
sandbox.files.write(...)             # 一份小文件写入。
content = sandbox.files.read(...)    # bytes 返回给调用方。
sandbox.terminate()                  # 关闭连接，并删除所关联的 Claim。
```

下层按所选 legacy 分支定位：

```python
# CommandExecutor.run：构建请求并通过 connector 发送。
payload, read_timeout = _execute_request(...)
response = self.connector.send_request("POST", "execute", ...)
result = ExecutionResult(**response.json())
return result

# SandboxConnector：连接策略选择入口，再进行 HTTP 请求。
# 请求跨越本地进程与运行服务，不是 SDK 直接调用容器内的 Python 函数。
```

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. 取得句柄 | [create_sandbox:126](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/clients/python/agentic-sandbox-client/k8s_agent_sandbox/sandbox_client.py#L126) | 跟到 _create_claim、_wait_for_claim_ready 和 Sandbox 构造；只回查 Claim 名与 Sandbox 名的交接 |
| 2. 句柄保存的访问入口 | [Sandbox.__init__:53](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/clients/python/agentic-sandbox-client/k8s_agent_sandbox/sandbox.py#L53) | 看到 connector、commands、files 怎样组合，不把句柄当作新创建的 Pod |
| 3. 执行短命令 | [CommandExecutor.run:90](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/clients/python/agentic-sandbox-client/k8s_agent_sandbox/commands/command_executor.py#L90) | 先选 legacy 分支，读到 HTTP 请求与 ExecutionResult 返回；超时参数只解释当前调用用途 |
| 4. 回查连接方式 | [SandboxConnector._connection_strategy:731](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/clients/python/agentic-sandbox-client/k8s_agent_sandbox/connector.py#L731) 与 [send_request:902](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/clients/python/agentic-sandbox-client/k8s_agent_sandbox/connector.py#L902) | 只跟本地 tunnel 的实际目标、router 及身份 header，再返回命令结果；集群内方式按对照定位 |
| 5. 一份文件往返 | [Filesystem.write:165](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/clients/python/agentic-sandbox-client/k8s_agent_sandbox/files/filesystem.py#L165) 与 [read:266](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/clients/python/agentic-sandbox-client/k8s_agent_sandbox/files/filesystem.py#L266) | 读清安全相对路径、写入与返回 bytes；目录递归和大文件流式传输先留接口边界 |
| 6. 连接与资源的结束 | [close_connection:226 / terminate:262](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/clients/python/agentic-sandbox-client/k8s_agent_sandbox/sandbox.py#L226) | 区分关本地 tunnel/session 和删除 Claim；回查前一步的 OwnerReference 回收关系 |
| 7. 一个权限观察点 | 调用者 kubeconfig/ServiceAccount 与 API 请求 | 准备一次缺少 get/watch 权限的定位方案：API 错误、对象状态与客户端日志交叉核对；不把它误判成 Agent 或命令失败 |

安全配置只作最小映射：控制器 RBAC 决定其资源写权限；调用者 RBAC 决定其 API 操作；securityContext/RuntimeClass 影响容器进程身份与运行时隔离。NetworkPolicy 是否生效依赖集群网络实现，创建 Sandbox 并不自动代表所有隔离能力已启用。

与平台接入的对应入口是 [Dressage/Harbor 的 Environment 适配 scope](../../../../../dressage/topics/02-harbor-integration/steps/step-013-harbor-kubernetes-environment/01-scope.md)。这里只交出“实际支持哪些操作与参数”的边界；Harbor 目录传输、统一 exec 合同与完整跨组件验证留在接入主题，不重复实现控制器。

<details>
<summary>源码与准备状态</summary>

- 固定版本：Agent Sandbox 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。SDK 符号和 legacy/sandboxd 分支已静态核对；访问模式需与实际部署的 runtime 一致。
- [安全模板](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/warmpool-quickstart/secure-sandboxtemplate.yaml)仅供字段对照，不把它当作已经包含命令服务、router 或完整 RBAC 的运行案例。
- 本次只生成 scope，不创建资源、不发命令、不修改权限，也不预生成故障验证结论。

</details>
