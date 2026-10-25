> 2026-10-24 更新 Step 005 scope 前的完整快照，源码归属 `2f231865`。正文保留，仅调整相对链接。当前范围见 [01-scope.md](../01-scope.md)。

---

# 01 · 阅读范围：登记本次 Agent 执行的会话配置

[本步入口](../README.md) · [Step 0 核心骨架](../../step-000-coding-agent/01-scope.md) · [前序函数记忆](../03-long-term-memory/overview.md)

## 1. 阅读目标

沿用理解 Coding Agent / Coding RL 的目标。本步以 `adapter.open_session` 的登记为核心，回答：**一次 Agent 执行开始前，在哪个 Adapter 对象中、按哪个 `sid` 登记会话配置，供后续模型请求和样本导出使用？**

先在调用处认清 `state.adapter` 和 `session_id` 的来路，再看使用新 `sid` 的正常登记路径。按用户本轮提出的编号问题，展开 `_session_id` 的三种返回规则。采样默认值和最大上下文长度作为当前已有配置；完整服务初始化、样本索引的上游分配、沙箱与工作区准备暂不展开。

## 2. 指挥官函数与本步入口

整体指挥官仍是 `examples/coding_agent_rl/generate.py::generate`（182 行）。先看其 **184–199 行**中对象、编号和调用的关系，再进入 [BaseAdapter.open_session](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md)，定义在 `slime/agent/adapters/common.py:210–223`。

此前读过 `_run_turn` 使用会话配置，以及 `finish_session` 取出配置。本步回到这份配置的登记处，把它们接起来；`open_session` 的职责就是这一项。

源码固定为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`；沿用[已核对的版本边界](../../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前源码与已有材料的版本边界)。

## 3. 给出真正干活的核心骨架

### 3.1 继承整体骨架，定位第 1 项

沿用 Step 001–003 的组织方式：保留整体位置，只展开本步选中的调用。以下为 `evaluation=False` 正常路径的教学裁剪：省略参数、配置解析、前置检查、日志计时、超时异常与失败包装，暂不展开外层清理；保留真实顺序与环境上下文。

```python
state.adapter.open_session(...)                          # 1. 本步：登记会话配置
async with boot_agent_sandbox(...) as sb:                 # 2. 启动执行环境
    await swe.prepare_workspace(...)                     # 3. 准备工作区
    agent_exit_code = await HARNESS_CLS().run(...)        # 4. 运行 Agent；接回 Step 1 的模型请求
    diff_text = await swe.git_diff(...)                   # 5. 取得改动

reward, applied_cleanly = await swe.run_evaluation(...)   # 6. 独立评测；Step 3
samples = await state.adapter.finish_session(...)        # 7. 导出训练样本；Step 4
...  # generate 检查空结果，并给每个样本补 agent_exit_code
return samples
```

<a id="adapter-to-open-session"></a>

### 3.2 从 Adapter 的来路接到 open_session

下面是阅读用的面包屑导航，省略参数和无关准备。沿当前 Claude Code 路径，`ADAPTER_CLS` 选中 `AnthropicAdapter`（`generate.py:45–52`）。首次初始化时创建 Adapter；已有服务状态可复用，不表示每次 `generate` 都重新创建一个 Adapter。

```text
generate                                                   # generate.py:182
├─ state = _AdapterService(...)                             # 184：取得服务状态
│  └─ 首次初始化：_AdapterService.__init__                   # 138
│     └─ self.adapter = ADAPTER_CLS(...)                     # 150–156：创建并持有 Adapter
├─ ...                                                     # 185–192：题目信息与检查
├─ session_id = base_sample.session_id = _session_id(...)    # 194：取得本次执行编号
│  └─ _session_id                                           # 308–313：沿用编号或生成字符串
└─ state.adapter.open_session(...)                          # 195–199：把编号和配置交给该 Adapter
   └─ BaseAdapter.open_session                              # common.py:210–223：实际方法实现
```

`state` 持有 `state.adapter`；进入 `open_session` 后，`self` 指的就是这个 Adapter。调用方的 `session_id` 在方法里叫 `sid`。当前 `AnthropicAdapter` 继承 `BaseAdapter` 的登记方法，因此从这里进入共同实现。

调用处的 `base_sample`、`protocol`、`md`、`instance_id` 与 `session_id` 分别有独立说明，可从[输入背景参考目录](generate-input-context.md)按需进入。

| 按顺序看哪里 | 本步只解决什么 | 带着什么继续 |
| --- | --- | --- |
| [_AdapterService.__init__ 函数卡片](../02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md) | 保留服务初始化的整体职责；本轮展开 150–156 行，认清 `state.adapter` 是谁、保存在什么对象里 | 知道下面的方法由哪个对象接收 |
| [_session_id 函数卡片](../02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_session_id.md)与[已有 sid 说明](../../step-004-trajectory-to-samples/references/session-id.md) | 哪些字段参与编号，何时沿用、按索引拼接或使用随机串 | 返回编号字符串，由调用方保存后交给登记方法 |
| [open_session 函数卡片](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md) | `sid` 与配置如何形成 `Session`、怎样登记、重复编号如何处理 | 返回 `None`；配置留在这个 Adapter 的 `store[sid]` 中 |

下游只回接已有关系：[_run_turn](../03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md)按 `sid` 使用配置；[finish_session](../03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md)取出并移除配置。这里按需回查，不重新展开这两个函数。

**停止位置**：能沿“哪个 Adapter → 哪次执行的编号 → 登记后的配置”说明本次调用，并接清返回值与后续用途，即结束本步。初始化内部的 tokenizer 加载、HTTP 服务启动和单例机制按需另读；源码接下来的 `boot_agent_sandbox` 与工作区准备仍只作整体定位。
