# BlackboxAgentPaddock.register_agent

[本步 scope](../../../../../../../../../01-scope.md#reading-navigation) → [generate 的注册位置](../../../rollout/generate/blackbox_dispatch.py/generate.md#agent-registration) → 本函数 → 返回 generate 的前置命令阶段。

- 源码定位：[paddock.py:153–182](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L153)。
- 首次单独展开：Step 005，2026-11-06；此前只定位用途和调用位置。
- 最近认识更新：用户要求重点区分它与其他阶段；尚无本函数的直接理解复述。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：generate 已通过预热领取或 init 取得环境与 state，现在为这个环境配置 Agent 后端和本次执行身份。
2. **具体内容**：根据 state 找到环境入口，整理 Agent 类型、后端选项、会话/任务标识和模型代理地址，通过 BlackboxServerClient 发送注册请求。
3. **建议构建的心智模型**：

   > init 已经取得环境及其中的 BlackboxServer；注册要求所选 Agent 程序已可用，但不保证任意任务镜像都包含它，也不是 init 自动安装了它。程序可用后，还需完成本次运行的配置。
   >
   > register_agent 请求这个服务为本次会话准备指定 Agent。以 Claude Code 为例，首次正常注册会选择对应适配器、准备运行目录、启动模型请求代理、写入 settings.json，并建立绑定会话；准备成功后返回回复。
   >
   > 这一步配置的是已安装的 Agent，不负责安装 Claude Code/Codex/OpenCode 程序本体；对应程序找不到时会报错。它完成本次 Agent 运行准备，题目的 messages 之后才通过 call_agent 提交。

4. **调用代码**（generate:232–241）：

   ```python
   await maybe_await(
       paddock.register_agent(
           state,
           instance_id=instance_id,
           session_id=session_id,
           router_url=proxy_url(),
           blackbox_type=blackbox_type,
           backend_options=backend_options,
       )
   )
   ```

## 本场景的输入与输出

教学场景：已有环境 sandbox-42，对应 state.trajectory_id="run-a"；本次 instance_id="question-1"、session_id="run-a"，选择 blackbox_type="claude_code"。地址与标识是示意值，未发送真实请求。

| 传入内容 | 用途 |
| --- | --- |
| [state](../../../../../classes/dressage/paddock/blackbox/common/state.py/SandboxState.md) | 找到本次环境的 [lease](../../../../../classes/dressage/sandbox/types.py/SandboxLease.md) 与 blackbox endpoint |
| instance_id、session_id | 注册时绑定任务实例与执行会话 |
| blackbox_type | 让服务端选择 Claude Code、Codex 等 Agent 适配器 |
| backend_options | 本次后端选项，再与该类型默认值合并 |
| router_url | 沙箱一侧应访问的模型代理地址，不是下面 HTTP 注册请求的目标地址 |
| 未传的可选参数 | router_api_path 默认 /v1，system_prompt_file 默认 None |

正常返回：BlackboxServer 注册响应解析后的字典，包含 status、binding、capabilities、config 等信息。当前 generate 没有保存该返回值，只等待调用正常完成，再继续 before_agent 命令；失败会向调用方传播。

### 完整函数

```python
async def register_agent(
    self,
    state: SandboxState | str,
    *,
    instance_id: str,
    session_id: str,
    router_url: str | None = None,
    blackbox_type: str = DEFAULT_BLACKBOX_TYPE,
    backend_options: Any = None,
    router_api_path: str = "/v1",
    system_prompt_file: str | None = None,
) -> dict[str, Any]:
    state = self._resolve_state(state)
    lease = self._leases.get(state.trajectory_id)
    endpoint = self._endpoint_for_state(state, lease)
    router = _validate_public_proxy_url(router_url or self._proxy_public_url)
    blackbox_type = normalize_blackbox_type(blackbox_type)
    return await self._client.register_agent(
        endpoint,
        trajectory_id=state.trajectory_id,
        instance_id=instance_id,
        session_id=session_id,
        router_url=router,
        blackbox_type=blackbox_type,
        backend_options=merge_backend_options(blackbox_type, backend_options),
        server_config=_server_config_for_provider(self._provider.name, blackbox_type),
        router_api_path=router_api_path,
        system_prompt_file=system_prompt_file,
        sandbox_id=state.sandbox_id,
    )
```

### 按三步跟随

1. **定位已有环境（165–167 行）**：本场景 state 已是 SandboxState，_resolve_state 直接使用它；再通过 trajectory_id 从 Paddock 的实例字典找 lease。_endpoint_for_state 优先取 lease 中的 blackbox 入口及 headers，缺失时用 state.sandbox_url 构造无额外请求头的入口。没有在这里重新创建环境。
2. **整理本次配置（168–169 行及调用参数）**：校验模型代理 URL；规范化 Agent 类型；合并 backend_options；准备服务端配置。若没有显式传 router_url，就使用 Paddock 保存的 _proxy_public_url。
3. **委派客户端发送请求（170–182 行）**：[BlackboxServerClient.register_agent](../client.py/BlackboxServerClient.register_agent.md) 将这些参数组装为 JSON，向 endpoint 对应服务的 /v1/rollout/register 发送 POST，并把响应返回。客户端重试实现本轮不展开。

**两个地址的方向**：endpoint 是“这次注册请求发给谁”；router_url 是请求里携带的配置，告诉环境里的 Agent 代理“后续模型请求发给谁”。

服务端收到注册后会选择适配器、绑定身份与配置并初始化 Agent 后端；是否启动常驻进程取决于后端。相同绑定可能直接复用，服务端完整注册实现以后再读。本次题目消息由后面的 call_agent 传入。

### 和相邻阶段的区别

| 位置 | 本次实际做什么 |
| --- | --- |
| 前面的 backend_options 整理 | 在本地准备配置，没有发送注册请求 |
| Paddock.init | 通过 provider 取得环境，返回 state |
| **Paddock.register_agent** | **向环境中的 BlackboxServer 发送身份和 Agent 配置，等待注册处理** |
| ProxyClient.register_session_context | 向另一个服务 Dressage Proxy 登记会话路由状态 |
| Paddock.call_agent | 提交 messages，让配置好的 Agent 处理本次任务 |

**读完返回**：generate 接着执行 before_agent 命令，再按接口能力登记 Proxy 会话上下文，最后才到 call_agent。本轮先停在注册调用的输入、发送方向和返回边界。

<details>
<summary>Agent 安装的准确位置：镜像构建不属于 Paddock.init</summary>

当前 Paddock.init 是通用流程，实际 provider 由配置决定，不能据此推断某个任务镜像已经含有 Agent。

1. **Docker 部署**：docker/build.sh 调用 docker build，执行 docker/Dockerfile。第 39 行安装 Claude Code，第 52–62 行安装 Codex，第 30 行安装 OpenCode，第 67–68 行安装 Dressage/BlackboxServer。这些发生在运行镜像构建时，不在 Paddock.init 的 Python 调用链内。
2. **默认 local_bwrap**：外层环境先装好程序，默认 runner 挂载系统/工具路径。LocalBwrapSandboxProvider.create 向已有 Ray 管理器 acquire 槽位并返回 lease，不是每次按任务 image 执行一次 Docker 安装。
3. **SWE-Gym 的 E2B 路径**：prepare_swegym_data.py:656–663 要求预构建模板包含 Claude Code 与 BlackboxServer，并要求 sandbox_image_map。provider.create 消费这个准备好的模板；从原始题目镜像制作合格模板是部署前置，不能由通用 init 推断用户的模板已安装所有程序。
4. **另有可配置引导方式**：同脚本的 _claude_install_command:196、wheel_bootstrap:213 产生安装命令，packaged_bootstrap:224 下载便携包。它们不是 register_agent 自动执行的安装；该脚本当前 E2B 分支还明确拒绝运行时 bootstrap URL 参数。

若没有在最终运行镜像/模板或兼容的挂载/引导方式中提供 CLI，注册会因找不到可执行文件失败。注册负责本次会话配置，不补做安装。

源码入口：[Dockerfile](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docker/Dockerfile#L39)、[build.sh](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docker/build.sh)、[E2B 模板要求](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/data/swegym/prepare_swegym_data.py#L656)。仅静态核对，未构建镜像或安装程序。

</details>

## 我的直接表述（原话）

> 好的 那么我们继续吧
> 看一下这里的paddock register agent吧
> 我比较想要知道这里和别的地方的区别具体是什么

本次明确阅读入口和对比重点。后续用户反馈：

> 我属于是完全不能理解
> 这里到底在做什么?
> 我可以理解之前的paddock是在通过provider获取环境和服务入口
> 那么这里的register
> agent我应该从哪一个function开始阅读呢?

当前不能据已有讲解推断注册职责已理解；当前先用客户端函数卡接清 HTTP 请求，再考虑服务端正常注册路径，详见本步过程。

## 尚不清楚

- 注册实际完成了什么，用户仍不理解；建议从 BlackboxServer.register 的首次成功注册路径补具体行为。
- 服务端复用或拒绝重绑定的完整规则尚未展开。
- 客户端如何处理重试、超时与失败。
- 后续前置命令和 Proxy 会话登记的完整交接，本步继续时展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- Paddock 方法及 _resolve_state/_endpoint_for_state；[客户端请求](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L60)；[服务端注册](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L241)、RegisterResponse 数据模型。服务端只回查行为边界，不计为完整精读。
- [原始讨论](../../../../../../../../../04-flow.md)。例子为静态说明，没有启动 Agent、环境或发网络请求。

</details>
