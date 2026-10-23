# 01 · 阅读范围：CLI 请求怎样交到 _run_turn

[步骤入口](README.md) · [本步函数](02-short-term-memory/overview.md) · [前一步 task flow](../step-008-harness-communication/05-task-flow.md) · [Step 1：模型请求处理](../step-001-harness-to-adapter/01-scope.md)

## 1. 阅读目标

继续理解 Coding Agent / Coding RL。本步接清 **CLI 的 HTTP 请求 → Adapter 服务 → 路由处理器 → `request` / `body` → 已读模型处理链**。

前一步已经说明 CLI 怎样取得 `adapter_url` 并启动。本步把“服务已经收到请求”这一前提拆开：服务何时监听，URL 怎样对应到函数，以及谁把请求对象传入 `_run_turn`。当前只看正常请求；沿用 Claude Code / Anthropic Adapter / E2B 场景。

## 2. 找到指挥官函数

整体入口仍是 `examples/coding_agent_rl/generate.py::generate`。本步涉及同一任务中的两个时机：

| 时机与入口 | 本步读它的用途 |
| --- | --- |
| CLI 启动前：`generate.py::_AdapterService.__init__`，137–171 行 | 准备 Adapter 的应用与监听服务，提供后续交给 CLI 的 `adapter_url`；[旧卡已调入本步](02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md) |
| CLI 请求到达后：`slime/agent/adapters/common.py::BaseAdapter._run_turn`，318–393 行 | 组织一次模型请求的处理；[旧卡已调入本步](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md)，重点回看 325 行之前的来路 |

**第一个补读点**是 `slime/agent/adapters/anthropic.py::AnthropicAdapter._register_routes:48–50`：它给出了 URL 与处理函数的直接对应。它负责登记这项关系；一次模型请求的处理锚点仍是 `_run_turn`。

注意文件分工：`harness/common.py::BaseHarness.run` 组织 CLI 运行，`adapters/common.py::BaseAdapter._run_turn` 处理收到的模型请求。二者通过正在运行的 CLI 与 HTTP 相连。

源码固定于 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。旧卡用于唤起已读职责，不能据此认定监听、路由或 CLI 内部发送机制已经掌握。

## 3. 给出真正干活的核心骨架

### 3.1 继承完整骨架：本步发生在哪里

下面是 `evaluation=False` 正常路径的教学裁剪，省略通用配置解析、检查、日志计时、异常及失败包装。服务初始化因直接关联本步问题而保留；单例初始化细节按需回查。

```python
state = _AdapterService(args)                            # 启动前：取得含监听服务的 Adapter
state.adapter.open_session(...)                          # 1. 登记会话；Step 5
async with boot_agent_sandbox(...) as sb:                 # 2. 沙箱与 CLI 就绪；Step 6
    await swe.prepare_workspace(...)                     # 3. 工作区与题目准备；Step 7
    agent_exit_code = await HARNESS_CLS().run(...)        # 4. 启动与等待；Step 8
    # ↑ 等待期间：CLI --HTTP--> Step 9 接收与路由
    #                        --> Step 1 模型处理与回复 --HTTP--> CLI
    diff_text = await swe.git_diff(...)                   # 5. CLI 结束后取得改动

reward, applied_cleanly = await swe.run_evaluation(...)   # 6. 独立评测；Step 3
samples = await state.adapter.finish_session(...)        # 7. 导出训练样本；Step 4
...  # 结果检查、附加元数据与外层清理暂时折叠
return samples
```

这里的 Step 编号表示阅读顺序。**Step 1 位于第 4 项等待期间**，对应 `_run_turn` 中已读的模型请求处理；Step 9 补齐进入这段处理之前的接收链。[Step 1 的 `_run_turn` 卡片已调入本步](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md)。

### 3.2 局部路径：先登记并监听，请求到达后再处理

下面分开标出实际函数所在文件；它们发生在不同时间，不能拼成一个同步执行的函数体。

**服务准备期**：沿已调入的 `_AdapterService.__init__`，只回查应用、路由和监听的交接。

```text
_AdapterService.__init__                          generate.py:150–171
├─ 创建具体 Adapter
│  └─ BaseAdapter.__init__                        adapters/common.py:159–175
│     ├─ self.app = web.Application(...)
│     └─ self._register_routes(self.app)
│        └─ AnthropicAdapter._register_routes    adapters/anthropic.py:49
│           app.router.add_post("/v1/messages", self._run_turn)
└─ run_app_in_thread(self.adapter.app, ...)       generate.py:161–170
   └─ 启动监听并持续处理事件                      aiohttp_threaded.py:69–81
```

**CLI 运行期**：HTTP 到达上述监听服务后，才进入已经登记的处理器。

```text
沙箱中的 CLI
  └─ HTTP POST <adapter_url>/v1/messages，带 JSON 正文
     └─ aiohttp 按方法与路径找到处理器
        └─ BaseAdapter._run_turn(request)        adapters/common.py:318
           ├─ body = await request.json()        325：得到 Python 字典
           ├─ 校准正文、识别 sid、取得 Session   326–337：接回既有会话
           └─ 接回 Step 1：转换 → 编码 → 请求 SGLang → 解析、回复与轨迹记录
```

`request` 是服务框架交给处理器的请求对象，`body` 在处理器内读取。`call_sglang_generate` 随后构造的是发往 SGLang 的另一份请求。完整的两次往返说明见[已有参考](references/run-communication-path.md#adapter-request-entry)。

<a id="adapter-entry-navigation"></a>

### 3.3 局部导航与停止位置

| 先看哪里 | 本轮只弄清什么 | 读完接到哪里 |
| --- | --- | --- |
| [AnthropicAdapter._register_routes:48–50](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L48-L50) | `POST /v1/messages` 登记哪个处理器；登记与实际调用的时机 | 回查这项登记何时完成 |
| [BaseAdapter.__init__:159–175](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L159-L175) → [服务初始化旧卡](02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md) | 同一个 app 怎样经过路由登记，再交给监听服务 | `generate.py:161` 的 `run_app_in_thread` |
| [run_app_in_thread:65–88](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/aiohttp_threaded.py#L65-L88)，按需补前置 | 监听启动与请求处理持续运行；先不展开线程、循环的全部实现 | 请求到达，进入已登记的处理器 |
| [_run_turn:318–344](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) | `request → body`，再沿 sid 与已有 Session 接到转换、编码及生成 | 回到本页局部路径，区分两次 HTTP 往返 |

每次只展开当前缺失的一项交接，调用下钻最多两层，随后返回这张导航。尚未展开的接收侧函数先链接源码；`02` 先放本步需要的旧卡。

**停止位置**：能从 CLI 的目标地址说到监听、路由、`request` 与 `body`，并接回“Adapter 请求 SGLang，组织回复后交回 CLI”。Step 1 已有的模型生成、解析及轨迹算法只回顾交接；完整 SDK、CLI HTTP 客户端实现、服务线程机制和异常恢复保留为后续具体问题。
