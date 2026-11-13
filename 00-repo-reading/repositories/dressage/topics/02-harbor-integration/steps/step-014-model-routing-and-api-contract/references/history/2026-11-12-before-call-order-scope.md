# 01 · Dressage Step 014：连接 Agent 模型请求、Gateway 与采集合同

[主题入口](../../../../README.md) · [项目进度](../../../../../../README.md) · [整体规划](../../../../../../references/topics-and-step-scopes-after-step006.md) · [前一范围](../../../step-013-harbor-kubernetes-environment/01-scope.md) · [后一范围](../../../step-015-harbor-results-and-samples/01-scope.md)

> 状态：按已确认规划预先准备 scope；尚未据此开始逐函数阅读或实施验证。本步未创建短期、长期记忆及完成记录。

## 1. 阅读目标

**追踪一次模型请求的实际路径，判断现有商业 API 后端与 Dressage 默认 Proxy 合同之间需要补哪些适配。**

## 2. 指挥官、入口条件与边界

1. **指挥官与入口**：[DressageHarborPlugin.on_job_start](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L261) 组织路由准备；核心入口是其调用的模块函数 [_inject_agent_routing](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1031)。
2. **进入前已有**：已有一个 Task、所选 Agent 与可用环境的接口约定。模型配置与路由配置由当前集成提供；只选 Claude/Anthropic 或 Codex/OpenAI 的一条请求路线先读。
3. **停止位置**：画出请求和响应的方向，关联 trial/attempt/session；列出模型请求、会话收尾、轨迹读取三类合同及真实 token/logprob 的可用性，形成可验证的适配缺口。
4. **本轮不展开**：不同时追所有协议、流式分支、复杂路由策略或完整 Trace 平台。API-only 可执行不等于可训练，缺失数据不能补成假证据。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

这是稳定的职责图，不是把所有异步回调合成同一调用栈。原生 blackbox_dispatch/Paddock/BlackboxServer 路线作为前序背景，不嵌入本图。

```python
# 关系示意，不是可执行代码；标记的是本步观察位置。
Slime 的 rollout hook
  -> generate_rollout_harbor_sync                 # 训练入口；API-only 路线不必执行这里。
       -> _run_harbor_rollout -> _run_partition
            -> plugin.on_job_start(job)          # 挂接路由配置与生命周期回调。
            -> Harbor Job.run
                 -> Trial.run                    # 一次尝试的组织者。
                      -> _prepare                # 环境与 Agent 准备。
                           -> Environment.start
                                -- 目标接缝 --> K8s 适配 -> Agent Sandbox -> Pod  # 待对齐/验证。
                           -> Agent.setup        # 按配置准备所选 Agent。
                      -> _run
                           -> Agent.run          # Step 014 本步：执行任务，并在过程中请求模型。
                           -> Verifier.verify    # 收集评测结果。
                      -> _finalize               # 清理环境并发出生命周期事件。
                           == END 事件 ==> plugin._on_end
                                            -> commit_attempt
            <- JobResult 与插件结果
            -> _bundle_samples                   # 训练路线的结果转换。
       <- Sample 组与 metrics
  <- RolloutFnTrainOutput

# Agent.run 期间的模型交互，不是等 Trial 结束才发请求：
Agent == HTTP ==> Gateway -> Dressage Proxy -> 模型服务
# 只做 API 评估时，调用方也可以从 Harbor Job 进入，不启动 Slime 训练。
```

<a id="reading-navigation"></a>

### 3.2 本步骨架与阅读顺序

配置修改、运行时 HTTP 请求、执行结束后的控制请求分开展示。Proxy 的控制接口必须单独对齐，不能仅改变 Agent 的模型 URL。

```python
DressageHarborPlugin.on_job_start
  -> _inject_agent_routing(...)       # 修改所选 Agent 的地址和凭据引用。
Trial START 事件 -> plugin._on_start
  -> GatewayLease.register(...)
       -> GatewayRuntime._register(...)
            -> _create_proxy(...)    # 在路由登记时创建，不是每条模型请求都创建。

# Agent 运行中的模型请求使用已经登记的路由：
Agent.run == HTTP ==> Gateway -> RolloutLLMProxy
  == HTTP ==> Dressage Proxy -> SGLangRouterClient -> 模型
  <== 模型回复 ==

# Trial 收尾阶段另用这些控制接口，不是普通聊天请求：
ProxyClient.finalize_session(...)     # /session/finalize
ProxyClient.read_trajectory(...)      # /trajectory/read
```

<a id="reading-sequence"></a>

下表数字只表示本步阅读顺序。原始源码、调用方、子调用与返回位置分别列出；未读方法只链接源码，不预建函数卡。

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. 入口配置从哪里来 | [on_job_start](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L261) | 只追一个 Agent 的路由准备；区分配置地址与已发送请求。 |
| 2. 选择并注入模型协议 | [_inject_agent_routing](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1031) | 看 base URL、凭据引用与模型设置怎样进入 Agent 配置；返回插件。 |
| 3. 一次尝试的代理归属 | [GatewayRuntime._create_proxy](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/gateway.py#L670) | 从 plugin._on_start 的 register 接到代理创建，对上 RouteSpec、trial/session 与 upstream；不深入全部线程和容量实现。 |
| 4. 默认模型后端 | [SGLangRouterClient.generate](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/sglang_client.py#L176) | 确认 token IDs 请求与普通商业 messages API 的差别。 |
| 5. 已有 API 后端接缝 | [make_call_api_generate](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/models/api_backend.py:201) | 对照协议、流式/错误行为、token 与 logprob 来源；不要把函数替换点当成天然 HTTP Proxy。 |
| 6. 执行结束后的控制合同 | [ProxyClient](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L42) | 复用原生 topic 已读的 finalize/read 概念，列出缺失接口与验证方法；然后进入结果提交。 |

最小边界：关闭 require_trainable_tokens 不能自动取消 finalize/read 的接口要求；只有真实生成数据才能证明训练语义。模型请求被接受也不等于本次轨迹能够正确收尾。

**读后接续**：读后进入 Step 015，追踪 Trial 结果、奖励、轨迹与 Sample 的提交关系。

<details>
<summary>源码版本与准备状态</summary>

- Dressage 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；本轮通过本地源码定位入口、调用与返回边界。
- Harbor 使用 0.18.0 / 527d50deb63a5d279e8c20593c18a2cbc7f61f9e；沿用[前次固定版本证据](../../../../../../references/agent-sandbox-harbor-integration-evidence.json)。本轮未找到此前临时 Harbor 源码，也未重新下载，正式逐函数阅读时先恢复并核对该版本。
- 现有项目参考 /home/fredkeira/projects/slime_api_data_collecting，登记提交 151db30d1f4533773948695f4033ebe4353521d8；接口匹配以实际分支行为为准。
- [适配研究与版本差异](../../../../../../references/agent-sandbox-harbor-integration-research.md)保留来源。相关外部文档示例不自动证明当前版本可导入或可运行。
- 本页只有预备 scope。未执行 Harbor、模型、Kubernetes 或训练实验，不把范围准备当作用户已读、已掌握或验证完成。

</details>
