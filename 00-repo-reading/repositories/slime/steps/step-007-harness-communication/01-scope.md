# 01 · 阅读范围：Harness 启动与跨组件通信

[步骤入口](README.md) · [本步函数](02-short-term-memory/overview.md) · [前序记忆](03-long-term-memory/overview.md)

## 1. 阅读目标

继续理解 Coding Agent / Coding RL。本步弄清准备好的 Adapter、沙箱与工作区怎样接到一次真实的启动流程上：谁在哪里运行、通过什么接口把什么数据交给谁，以及模型回复和 CLI 退出分别回到哪里。

前序准备作为已有输入使用，有疑问时回查对应卡片。这里不重新讲解安装、工作区初始化或 `_run_turn` 的全部转换细节，也不把准备记录存在当成用户已掌握全部实现。

## 2. 找到指挥官函数

整体指挥官仍是 `examples/coding_agent_rl/generate.py::generate`。本步聚焦它第 205 行的 `HARNESS_CLS().run(...)`，局部组织入口是 [BaseHarness.run](02-short-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md)，定义在 `slime/agent/harness/common.py:81–104`。

当前 `HARNESS_CLS` 是 `ClaudeCodeHarness`，它继承共同的 `run`，具体的 `write_config` 与 `launch_and_wait` 在 `harness/claude_code.py`。`run` 串联用户准备、运行上下文、CLI 配置和启动等待；首先深入 [ClaudeCodeHarness.launch_and_wait](02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md)，因为它直接决定启动什么程序，以及程序拿到哪个 API 地址。

源码固定于 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。当前前提是：CLI 已安装，题目文件已放入工作目录，Adapter 已监听，会话已登记，Adapter 持有 SGLang Router 地址。上述服务的实际可达性未运行验证。

## 3. 给出真正干活的核心骨架

### 3.1 继承整体骨架，定位第 4 项

以下沿用 `evaluation=False` 正常路径的教学裁剪。按五类过滤规则折叠通用配置解析、前置检查、日志计时、超时异常和失败包装；保留业务顺序、返回值与上下文嵌套。局部涉及目标地址和会话标识的配置是本步问题，继续保留。

```python
state.adapter.open_session(...)                          # 1. 登记会话；Step 4
async with boot_agent_sandbox(...) as sb:                 # 2. 沙箱与 CLI 就绪；Step 5
    await swe.prepare_workspace(...)                     # 3. 工作区与题目准备；Step 6
    agent_exit_code = await HARNESS_CLS().run(...)        # 4. 本步：启动 CLI，接清运行期间的通信
    diff_text = await swe.git_diff(...)                   # 5. CLI 结束后取得改动

reward, applied_cleanly = await swe.run_evaluation(...)   # 6. 独立评测；Step 2
samples = await state.adapter.finish_session(...)        # 7. 导出训练样本；Step 3
...  # generate 的结果检查、附加元数据与外层清理暂时折叠
return samples
```

### 3.2 展开本地启动的局部骨架

进入 `BaseHarness.run` 时，`sb` 仍是 Slime 一侧的本地对象。`adapter_url`、`session_id`、`workdir` 和 `prompt` 均由 `generate:205–212` 传入；具体输入与返回值见函数卡片。

```python
await _sandbox.ensure_agent_user(...)       # 97：复用用户与目录准备
ctx = HarnessContext(...)                  # 98–102：组合运行上下文
await self.write_config(...)               # 103：ClaudeCodeHarness 写 CLI 配置
return await self.launch_and_wait(...)      # 104：交给具体实现启动，等待并返回退出码
```

第 104 行进入 `ClaudeCodeHarness.launch_and_wait:57–71`：组装 `cmd`，把 Adapter 地址和会话标识放入 `env`，再交给 `run_agent`。`run_agent` 进一步调用 `exec_and_wait`，由沙箱接口写启动脚本并执行。CLI 整体退出后，退出码沿这条本地调用链返回 `generate:205`，随后才进入 213 行的改动提取。

### 3.3 运行期间的通信分支

下面是交互导航，不是 Python 函数直接调用树。第一条经沙箱 SDK；后两条分别是不同发送方发起的 HTTP 请求，发生在 CLI 运行期间。

```text
Slime 的 Harness ── sb / SDK：命令、环境变量 ──→ 远端沙箱中的 CLI
                                                  │
                            HTTP /v1/messages：消息、工具定义
                                                  ↓
                                          Slime 的 Adapter
                                                  │
                             HTTP /generate：token ID、采样参数
                                                  ↓
                                            SGLang 服务
```

SGLang 结果先回 Adapter，经已读的 `_run_turn` 处理后回应 CLI。CLI 继续任务，可能再次请求模型；Harness 等待的是整次 CLI 运行结束。运行位置、地址传递和对应源码放在[通信路径参考](references/run-communication-path.md)，这里保持导航层的深度。

<a id="harness-local-navigation"></a>

### 3.4 阅读导航与停止位置

局部接续沿 `run:97 → 98–102 → 103 → 104`：`ensure_agent_user` 已在 Step 6 读过，先短回顾；接着说明 `ctx` 如何组合输入、`write_config` 写入什么，再深入启动与通信。下表的“首先深入”表示重点展开处，前面的交接仍按顺序说明。

| 顺序 | 从哪里进入 | 本轮看清什么，读完回到哪里 |
| --- | --- | --- |
| 1 · 定位局部组织 | [BaseHarness.run，81–104](02-short-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md) | 接清输入、`ctx`、两个具体实现与退出码；用户准备复用旧卡，重点停在 104 行 |
| 2 · 首先深入 | [ClaudeCodeHarness.launch_and_wait，57–71](02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) | `prompt → cmd`，`adapter_url / session_id → env`，随后交给 `run_agent`；返回值仍是退出码 |
| 3 · 接上远端启动 | [run_agent，107–122](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L107-L122) → [exec_and_wait，82–145](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L82-L145) | 先定位写脚本、传环境、启动和等待标记；若展开，以 `launch_and_wait` 为局部起点最多追这两层，`sb.exec` 的底层通信作为接口边界 |
| 4 · 请求进入 Adapter | [Anthropic 路由，48–53](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L48-L53) → [已有 _run_turn 卡片](03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) | CLI 的 URL、请求头和 JSON 对应哪个处理器；恢复既有输入输出后回到通信图 |
| 5 · 请求模型并返回 | [已有 call_sglang_generate](03-long-term-memory/functions/slime/agent/adapters/common.py/call_sglang_generate.md) → [已有 _respond](03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._respond.md) | 区分两次 HTTP 往返：模型结果回 Adapter，协议响应回 CLI；不重讲 token 或协议字段的全部实现 |
| 6 · 整次运行结束 | `exec_and_wait → run_agent → launch_and_wait → run → generate:205` | 退出码回到外层，接续 213 行 `swe.git_diff`；一次模型回复与 CLI 整体退出分开 |

**停止位置**：能用当前源码说明三条通信路径各自的发送方、目标来源、传递内容与返回方向，并解释为什么外层 `run` 等待期间仍能发生多轮模型请求。更深的 CLI 工具循环、SDK 网络编码、Router 选 worker 和完整超时重试留待后续具体问题，不因列入导航就预建函数卡片。
