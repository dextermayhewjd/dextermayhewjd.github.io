# 05 · 任务链路：提交题目，执行 Agent，再把结果交回 generate

> generate 把题目与已有环境资料交给 Paddock，客户端向沙箱服务提交调用；服务端在后台运行 Claude 并保存结果，客户端查询并取回结果字典。generate 接住它，整理结果字符串并检查失败状态，本步停在 after_agent 之前。

[本步 scope](01-scope.md) · [函数卡片](02-short-term-memory/overview.md) · [形成过程](04-flow.md#step006-first-pass-closure) · [项目进度](../../../../README.md)

## 1. 本步在任务中的位置

前一步已准备环境访问资料 state、会话标识、Agent 配置、before_agent 命令和 Proxy 会话登记。本步采用 Claude Code、客户端默认 async 提交的正常路径。

入口是 generate:259 的 paddock.call_agent；终点是 generate:283–291 的结果字符串整理与结构化失败检查。此时 Agent 调用已结束，整个 generate 还没有返回训练 Sample。

## 2. 已读部分怎样完成交接

### 2.1 客户端提交和查询是一条线

下图用 Python 高亮显示注释，是关系示意。HTTP 箭头表示跨到沙箱服务，不能当成客户端的普通 Python 子调用。

```python
generate
  -> BlackboxAgentPaddock.call_agent  # 使用已有 state 找到沙箱服务入口。
       -> BlackboxServerClient.call_agent  # 准备本次 turn_id。
            -> _post_agent_with_retry
                 == POST messages ==> api.sessions.send_message
                                        -> BlackboxServer.submit_turn
                                             -> create_task(_run_turn(...))  # 安排下方的后台任务。
                                        <- submission
                 <== HTTP 202 ==  # 接受提交；不等待后台 Agent 做完。
            <- submit_response
            -> _poll_turn  # 查询同一个 session_id、turn_id。
                 -> _get_turn_with_retry -> get_json_with_retry
                      == GET turn ==> 沙箱服务查询调用记录
                      <== 状态与结果 ==
                 # 未结束继续查询；终止失败状态报错。
                 -> _committed_call_payload  # committed 时整理结果字段。
            <- 结果字典
       <- 结果字典
  <- call_payload  # generate 这时才接到本次 Agent 调用结果。
```

1. _post_agent_with_retry 交回的是提交请求的 HTTP 响应。
2. _poll_turn 交回的是调用完成后的结果字典；它可以与后台执行同时进行。
3. HTTP 请求失败后的重试，由公共请求层处理；HTTP 成功但调用未结束后的再次查询，由 _poll_turn 处理。

回查：[Paddock.call_agent](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.call_agent.md) · [客户端 call_agent](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.call_agent.md) · [POST 与重试](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._post_agent_with_retry.md) · [接收路由](02-short-term-memory/functions/blackbox_server/api/sessions.py/send_message.md) · [submit_turn](02-short-term-memory/functions/blackbox_server/core/server.py/BlackboxServer.submit_turn.md)。

查询部分：[轮询](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._poll_turn.md) · [GET 与重试](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._get_turn_with_retry.md) · [结果字段整理](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._committed_call_payload.md)。

### 2.2 服务端在另一项后台任务里执行

```python
BlackboxServer._run_turn  # submit_turn 安排的后台 Task。
  # 取得本次 TurnRecord，标记 INFLIGHT，然后释放会话锁。
  -> ClaudeCodeAdapter.send_message  # 经等待器执行；准备 Claude 会话与请求归属。
       -> _run_claude_turn  # 经 Task 与等待器执行。
            -> 启动 Claude CLI  # 使用已有工作目录、参数和环境变量。
            -> 读取 stdout，写日志并解析事件
            -> 等待进程退出，整理结果
       <- outputs, trace_events, usage
       # 等代理请求收尾，组织 AdapterResponse，并完成 finally 清理。
  <- AdapterResponse
  # 重新取得会话锁；若记录仍是 INFLIGHT，就保存结果并标记 COMMITTED。
  # 锁外设置 Event，然后移除属于当前 Task 的活跃登记。
  # 后台函数返回 None；结果留在 TurnRecord 中供查询。
```

1. **Task 负责运行，TurnRecord 保存状态和结果，Event 负责通知。** 移除活跃 Task 登记不会删除已保存的结果。
2. stdout 是 CLI 报告的运行事件，经管道交给 Python。模型 HTTP 请求同时经过代理，这是另一条记录通道。
3. 后台任务结束不再沿最初的 POST 返回答案；客户端通过后续 GET 读取结果。

回查：[_run_turn 的结果保存段](02-short-term-memory/functions/blackbox_server/core/server.py/BlackboxServer._run_turn.md#save-result-and-notify) · [适配器 send_message](02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.send_message.md) · [CLI 执行](02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md) · [stdout 与模型 API 的区别](../../../../references/cli-output-and-model-api.md)。

### 2.3 generate 接住结果后继续处理

1. call_payload 接住选取后的调用结果字段，包含标识、outputs、backend、usage 等。
2. agent_response_text 将它整理成字符串。当前标准返回里是复数 outputs，而该函数只查找 response、content、message、text、output，因此这条路径会落到 str(call_payload)。不能把它当作已经提取了纯粹的最终回答。
3. failure_from_payload_state 检查结构化状态，识别到失败则记录并抛出；它不判断答案对错。正常通过后，本步结束在 after_agent 之前。

回查：[generate 的本步结果处理段](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#return-agent-result)。

## 3. 本步结果的含义与去向

| 内容 | 保存或交付在哪里 | 表示什么 |
| --- | --- | --- |
| HTTP 202 提交回复 | 客户端 call_agent 的 submit_response | 服务端接受提交，不保证 Agent 此刻已完成 |
| AdapterResponse | 服务端 TurnRecord.response | 适配器交回的输出、事件、用量及后端会话资料 |
| call_payload | 返回到 generate | 客户端整理后的调用结果字典，不包含整份 Proxy 训练轨迹 |
| agent_response | generate 的局部字符串变量 | 当前返回结构的字符串形式；候选字段选择不涉及新的 Agent 执行 |

Agent 调用完成与整个 rollout 完成是两个位置。当前 Agent 已执行结束；后续 generate 还需要完成执行后处理、读取 Proxy 轨迹、转换 Sample 和最终清理。

## 4. 本步收束与后续衔接

按首轮阅读目标，本步已经覆盖从题目提交到结果返回及基本状态检查的主线，可以在这里收束。用户曾对若干部位表示大概理解，并持续纠正阅读导航；本页是助手对已发生阅读的总结，不代表用户已掌握所有内部机制。

以下继续保留为按需回查，不作为结束本步的新增必读要求：

1. CLI 事件转换的所有分支、全部参数和后端会话恢复选项。
2. 暂停、取消、超时、重试退避及并发状态变化的完整协作。
3. Proxy 的全部记录机制与失败恢复；本轮只接清其与 CLI 输出的职责区别。

后续候选从 generate 的 after_agent 调用继续，围绕执行后处理和轨迹到 Sample 的交接确定下一步范围。仍沿[接入阅读规划](../../../../references/integration-reading-plan.md)先收拢原生 generate，再进入 Harbor 接入路线；本次没有提前创建下一 Step。

<details>
<summary>源码、形成依据与验证范围</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 外层入口与终点：[blackbox_dispatch.py:259](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L259)、[结果处理与后续边界](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L283)。
- 提交与查询：[client.py:97](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L97)；后台保存：[server.py:577](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L577)。
- CLI 执行：[claude_code.py:528](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/adapters/claude_code.py#L528)。
- 源码与函数卡经过静态核对；标准库管道小例子和两个源码提取的纯函数有局部验证，证据留在对应卡片。未执行真实 Agent、沙箱 HTTP 请求或训练，不以局部检查代替端到端验证。
- 采用 repo-reading-task-flow 的四部分结构；本步跨 HTTP 与后台任务的关系分开展示，阅读编号只保留在 scope 表格。

</details>
