# 07a · Dressage 接管连接时，怎样让地址和凭证配套？

**状态**　实现、回归测试与文档已作为 `73347a1` 推送至个人 Dressage 仓库的 `compat/harbor-0.26` 分支。此前只处理 Claude Code 地址的 `0b3d570` 已撤回。

## 一个问题

Dressage 给主 Agent 的模型 API key 是当前执行尝试（attempt）的路由 token。Gateway 用它找到这次尝试的路由。向后端 Proxy 转发时，服务端按后端配置使用独立的凭证。

以 Codex 为例。用户在 Agent 配置里填写了其他 `base_url`，并用 `model_api_key_name` 指定了自己的凭证变量。Dressage 接管这次 Trial 后，客户端应使用同一条路由的两项数据。修前在只接管凭证的工作区草稿上，离线回归先检查了密钥，再检查地址，第二项失败。

| 检查项 | 修前草稿交给 Codex 的值 | 本次预期 |
| --- | --- | --- |
| 请求地址 | 用户填写的 `https://previous.example/v1` | 本次 Gateway 的 `/v1` 地址 |
| 请求凭证 | 本次 Trial 的凭证 | 同一个 Trial 的凭证 |

原因是 Harbor 0.26 独立解析两项输入。显式的顶层地址和显式的凭证选择器分别优先于环境中的候选。只改选择器，会留下原地址。[Harbor 的地址选择](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/agent_auth_resolution.py#L719-L727) · [Harbor 的凭证选择](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/agent_auth_resolution.py#L674-L691)

## 一个解法

在 `_inject_agent_routing()` 准备好 Trial 副本的环境后，由 `_bind_trial_model_connection()` 将目标地址与凭证来源一起交给 Harbor 解析，再检查两项结果。用户原始配置保留原值。若解析出的任一值与本次路由不符，Job 启动失败。

| 输入条件 | 处理 |
| --- | --- |
| 单一协议 | OpenAI 取 Gateway 的 `/v1` 地址。Anthropic 默认取 Gateway 根地址。OpenCode 和 MiMo 使用内置 Anthropic provider 或 `@ai-sdk/anthropic` 时，SDK 在 `<gateway>/v1` 后追加 `/messages`。 |
| `both` | 先确认 Harbor 选中了本次 Gateway 的一个入口。Codex 和 Qwen 使用 `<gateway>/v1`。Claude Code 在根地址后追加 `/v1/messages`。OpenCode 和 MiMo 按选中的 SDK 确定基础路径。 |
| 原选择器指向 Agent 环境里的旧值 | 从 Trial 副本移除旧值，避免它以明文写入 `config.json`。 |
| Harbor 支持显式凭证选择器，并把 token 交给 `OPENAI_API_KEY` 等可脱敏变量 | `model_api_key_name` 指向 Dressage 为本次 Trial 创建的环境变量。 |
| Harbor 会把 token 写入执行日志无法脱敏的变量，例如 Codex 原生 provider 的 `env_key = "INFERENCE_PASS"` | Dressage 在 Job 启动检查中抛出 `RoutingPolicyError`，随后释放资源。 |
| Harbor 拒绝显式覆盖 | 当前实现捕获任意 `ValueError`，清空副本的两个顶层覆盖，再核对从环境解析出的地址和凭证。已验证需要回退的场景是 OpenCode 开启 `skip_model_parsing`、使用裸模型名且没有默认 provider。 |
| Agent 没有 Harbor 模型连接，例如 Oracle | 沿用已有环境注入，跳过顶层模型连接覆盖 |

## 验收

先跑 Codex 回归，从装有 Harbor 0.26 的 Dressage 工作区执行：

```bash
python -m pytest -q tests/integrations/harbor/test_execution.py -k 'harness_uses_trial_gateway and codex and other-key'
```

此前的 25 项定向用例覆盖 Claude Code、Codex、Qwen Code、OpenCode 和 OpenClaw 的常规配置，并核对了启动环境或生成的 provider 配置。

**Claude Code 的 `both` 回归。** 模型为 `openai/gpt-4.1` 时，Harbor 先从 `OPENAI_BASE_URL` 取到 `<gateway>/v1`，再把它交给 Claude Code 的 `ANTHROPIC_BASE_URL`。新增用例在修前得到 `http://localhost/v1`，预期是 `http://localhost`。修后同一个模型交给 Claude Code 时得到 Gateway 根地址，交给默认 Codex 时得到 Gateway 的 `/v1` 地址。可单独运行这三个对照用例。

```bash
python -m pytest -q tests/integrations/harbor/test_execution.py -k both_protocols_select_the_harness_gateway
```

**Claude Code 实际请求。** 在只有回环网络的环境中，用 Harbor 0.26.0 生成的启动环境运行本机 Claude Code 2.1.293。本地假 Gateway 收到 `POST /v1/messages`，请求的模型为 `gpt-4.1`，Bearer 凭证与该 trial 的合成凭证一致。客户端收到了固定回复 `ok`。

**OpenCode 的 Anthropic 地址。** 修前，用户填写的 `<gateway>/v1` 会在 Harbor 生成的 `opencode.json` 中变成 `<gateway>`。修后，Dressage 根据选中的 adapter 确定路径。Harbor 对内置 Anthropic provider 可能返回空的 `model_api_format`，此时要读取选中的 provider 和它配置的 `npm` 包。回归测试对照内置 provider、显式 adapter、使用原生默认 provider 的裸模型名和采用其他 SDK 的同名 provider，并检查生成的 `options.baseURL` 和凭证引用。

```bash
python -m pytest -q tests/integrations/harbor/test_execution.py -k 'opencode or both_protocols_select'
```

**OpenCode 实际请求。** 用 Dressage Dockerfile 固定的 OpenCode 1.17.4 加载 Harbor 生成的配置。内置 Anthropic provider 使用 `anthropic` 模式，自定义名称 `team` 的 `@ai-sdk/anthropic` provider 使用 `both` 模式。两次运行中，本地假 Gateway 收到的模型请求全部为 `POST /v1/messages`，认证头与各自的 trial 测试凭证匹配，客户端都收到固定回复 `ok`。

**为什么同一个 `INFERENCE_PASS` 名字会有两种结果？** `model_api_key_name` 指定 Harbor 从哪个环境变量读取凭证。Dressage 接管后，它可以清掉 Trial 副本里用户原先放在 `INFERENCE_PASS` 的旧值，让默认 Codex 从 `OPENAI_API_KEY` 接收当次 token。Codex 原生 provider 的 `env_key` 则指定客户端接收凭证的变量。如果它明确要求 `INFERENCE_PASS`，Harbor 的执行日志无法按这个目标名打码。Dressage 直接拒绝这份配置。[Harbor 的 Codex 目标变量](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/installed/codex.py#L269-L279) · [Harbor 的执行日志](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/installed/base.py#L1049-L1063)

默认 Codex 的回归使用合成凭证和 Harbor 的真实执行日志。首次构建 Agent 和模拟凭证轮换后再次构建时，模拟沙箱都收到当次 token，日志中的 `OPENAI_API_KEY` 已打码，宿主机的同名变量保留原值。另两项回归从 `on_job_start()` 传入指向 `INFERENCE_PASS` 的原生 provider 配置。用户原来的凭证来源分别是 `INFERENCE_PASS` 和 `LEGACY_INPUT`。此前的重绑定逻辑接受了这两种配置。删掉重绑定后，两者都在注册 Trial 回调和路由之前报错，并调用了 Job 凭证清理和 Gateway 释放逻辑。

文件形式的 Codex TOML 由 Trial 使用一份已核对的临时副本，避免重试重新读取原文件时改变 `env_key`。Job 结束时清理这份副本。若 Harbor 解析出的模型连接还包含另一个携带同一 token 且无法打码的环境变量，Dressage 在 Job 启动阶段报错。

```bash
python -m pytest -q tests/integrations/harbor/test_execution.py -k 'exec_log_masks or unmasked_codex_credential_destination or file_keeps_the_checked or unmasked_extra_credential'
```

这 5 项回归已通过。Harbor 集成套件共 119 项通过，8 项外部端到端测试按仓库默认配置排除。

**边界**　检查发生在真实 `Job.create()` 之后；创建阶段缺少用户指定的凭证仍可能提前报错。客户端原生配置还有独立的选择顺序：离线复核中，默认 Codex 的最终地址与凭证配套，另选 provider 的活动 profile 仍保留另一组值。这类配置不在 07a 已验收的范围内。[创建阶段调查](../../../../investigations/06-agent-credential-preflight/README.md) · [07b · Claude 原生 settings](07b-claude-settings.md) · [07c · Codex 活动 profile](07c-codex-profile.md)

**Codex 文件配置的复跑边界。** Job 内的重试读取同一份 TOML 快照。Job 关闭后，原文件和 Job 级配置中的原路径仍在，单个 trial 的配置和结果却指向已经清理的快照。仅凭 trial 记录恢复当时的 TOML 仍是待处理项。

## 本轮评审核对

以下对照记录问题 3、4、5 各自修复前的表现，修后结果见本页末尾。

在 Dressage 管理的 rollout 和训练中，Harbor Job YAML 可以选择任务和 Agent，Dressage 的集成配置可以指定 Gateway 的可达地址。主 Agent 的模型请求必须经过这个 Gateway，使用 Dressage 为当前 attempt 签发的路由凭证。NeMo 的 `config_file` 是 NeMo 自己执行的工作流 YAML。用它指定独立的推理服务超出了这个路由约定。[Dressage 集成契约](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docs/harbor.md#L25)

**NeMo 的两条 P1。** 随仓配置默认不会启用 NeMo，但显式设置 `agent_protocol_overrides` 可以选中它。提供工作流 YAML 时，Harbor 会拒绝显式覆盖地址。Dressage 捕获这个错误，改从环境解析后可能放行。NeMo 运行时仍读取原样上传的文件，因此文件里的模型地址可能生效。让 Harbor 自动生成 YAML 时，需要 API key 的 provider 会把当次 token 写入 YAML，再将 YAML 放进执行命令。Harbor 分别处理命令文本和环境变量，DEBUG 命令日志因此可能包含 token。这两项依据固定版本源码。[外部工作流](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/installed/nemo_agent.py#L337-L348) · [地址覆盖限制](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/installed/nemo_agent.py#L508-L517) · [凭证写入 YAML](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/installed/nemo_agent.py#L563-L567) · [执行命令](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/installed/nemo_agent.py#L672-L690) · [命令日志](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/installed/base.py#L1049-L1063)

本轮把 NeMo 列为 Dressage rollout 和训练暂不支持的 harness。Dressage 的 `docs/harbor.md` 在 `agent_protocol_overrides` 附近说明了两种工作流的风险。启动拦截暂缓，显式选择协议后仍可能启动 NeMo，两条 P1 保留为已知限制。

| P2 场景 | C06（`a1087bb`）与当前 07a 在 Harbor 0.26.0 上的离线对照 | 待修行为 |
| --- | --- | --- |
| Codex、Qwen Coder 在 `both` 模式使用 `anthropic/…` 模型 | 用户显式填写 `<gateway>/v1` 时，C06 保留这个地址。07a 将它覆盖为根地址，按 Codex 的 TOML 和 Qwen 的执行环境推得 `/responses` 和 `/chat/completions`。省略显式地址时两版都缺 `/v1`。07a 在单一 `openai` 模式下的两条路径均正确。 | 先处理这一项。Harbor 已分别报告 `openai_responses` 和 `openai_chat_completions`。用客户端的请求格式选取 Gateway 的 `/v1`，核对两种初始地址。 |
| MiMo 选择 `@ai-sdk/anthropic` | 在 `anthropic` 与 `both` 下，显式填写 `<gateway>/v1` 的 MiMo 配置在 C06 可得 `/v1/messages`，07a 则得到 `/messages`。省略显式地址时两版都缺 `/v1`。07a 的 OpenCode 使用相同自定义 provider，两种模式都得到 `/v1/messages`。 | 显式启用的 MiMo 也有原本正确的配置。让同一 SDK 的地址规则读取 `mimo_config` 中选中的 provider。 |
| 同一 Job 的第二个 trial 在插件启动时失败 | 07a 在第二个 trial 校验失败后释放了凭证槽和 TOML 快照。只修第二个再挂载，第一个会报 `FileNotFoundError`。恢复第一个的原配置即可重新挂载。另用相同故障做两版对照，让第二个 trial 分配凭证槽失败。C06 保留了第一个 trial 的原 TOML 路径，同一个 Job 可以重新挂载。07a 留下已删除的临时路径。 | 将失败恢复作为 Codex 文件快照的验收条件。所有 trial 校验通过后再写回副本，或在启动失败时恢复之前替换的配置。 |

本轮重跑现有的 `both` 地址选择、OpenCode provider 和 Codex TOML 快照回归，12 项通过。其中 Codex 的 `both` 用例使用 `openai/gpt-4.1`。上表的地址核对使用 Harbor 生成的客户端配置和 Dressage Gateway 的路由表。双 trial 实验只执行到插件挂载，全程未启动沙箱或 GPU 训练。[Harbor 的 MiMo provider 配置](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/installed/mimo.py#L466-L480)

### Agent 省略 `base_url` 时的启动检查

从真实 `Job.create()` 和 `on_job_start()` 进入，Agent 配置均省略 `base_url`，也没有通过 Agent 环境填写地址。10 组路由配置各检查两次，一次由测试 Gateway 返回回环地址，一次在 Dressage 部署配置中填写另一个回环地址。20 次都选中了预期的 Gateway 主机和端口，Harbor 解析出的凭证均与当前 trial 一致。下面的路径由客户端配置和它追加的后缀推得，实验没有发送模型请求。

| 检查项 | 触发条件 | 对照结果 |
| --- | --- | --- |
| 3 · Codex / Qwen Coder | 同一 `anthropic/…` 模型，显式选 `both` 时分别得到 `/responses` 和 `/chat/completions`，均缺 `/v1`。 | 保留默认协议时两条路径都正确。保留 `both` 并改用 `openai/…` 模型时也正确。 |
| 4 · MiMo | 选用 `@ai-sdk/anthropic` 的自定义 provider，在 `anthropic` 和 `both` 模式都得到 `/messages`。 | 同一份 provider 配置交给 OpenCode，两种模式都是 Gateway 提供的 `/v1/messages`。 |
| 5 · 第二个 trial 校验失败 | 两个 Codex trial 均省略地址，第一个使用文件形式的 TOML。只修正第二个，再挂载同一个 Job，第一个因快照已删除而报 `FileNotFoundError`。 | 用原 TOML 和修正后的第二份配置重新 `Job.create()`，两个 trial 均通过插件启动检查。 |

### 问题 5 · 启动失败后复用同一个 Job

普通 Codex trial 可以省略 `kwargs.config`。Harbor 从空配置开始，将运行时选定的 Gateway 地址写入沙箱里的 `$CODEX_HOME/config.toml`。只有用户提供宿主机 TOML 路径时，07a 才保存一份经过检查的输入快照，供本次 Job 使用。07c 单独检查活动 profile 选中了哪个 provider。[Harbor 读取可选输入](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/installed/codex.py#L1948-L1978) · [Harbor 生成运行配置](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/installed/codex.py#L2166-L2179) · [07c · 活动 profile](07c-codex-profile.md)

修复后，`on_job_start()` 先准备所有 trial 的 Agent 副本，等校验通过、回调注册完成，再统一写回 Job。第二个 trial 校验失败时会释放本次启动创建的快照和凭证槽，第一个 trial 仍指向用户原文件。

回归 `test_failed_job_start_preserves_trial_configs_for_reattach` 在修前读到了已删除的快照路径，修后通过。另用 Harbor 0.26.0 的真实 `Job.create()` 验证，只修第二个 trial，用新插件挂载同一个 Job 即可成功。第一个 trial 获得新的有效快照，第二个 trial 省略配置文件也能生成含 Gateway 地址的运行配置。关闭插件后原文件仍在，临时快照已清理。

### 问题 3、4 · 按客户端选择 Gateway 的基础路径

Agent 可以省略 `base_url`。在 `both` 模式，Harbor 可能因 `anthropic/…` 模型名前缀先选到 Gateway 根地址。Dressage 核对它属于本次 Gateway 后，按客户端的请求格式绑定基础地址。Codex 和 Qwen 均使用 `<gateway>/v1`。OpenCode 和 MiMo 共用一条 SDK 判断规则，分别读取 `opencode_config` 和 `mimo_config`。选用 `@ai-sdk/anthropic` 或 `@ai-sdk/openai-compatible` 时，两者都从 `<gateway>/v1` 开始拼接路径。代理端继续沿用已有的协议转换。

首批 55 个定向配置用例中，修前有 24 个失败。复查补验了显式 OpenAI Chat 格式和 MiMo 参数优先级。若有效的顶层地址覆盖了 `kwargs` 里的空地址，单一 Anthropic 模式会先绑定本次连接，再按生效的 SDK 选择路径。最终 66 个定向用例全部通过。另从真实 `Job.create()` 和插件启动入口检查分别由运行时或部署配置提供 Gateway 地址的 20 种组合。按最终客户端配置推得的路径均命中 Gateway 注册的路由。本轮检查截至客户端配置生成，没有向模型服务发出请求。
