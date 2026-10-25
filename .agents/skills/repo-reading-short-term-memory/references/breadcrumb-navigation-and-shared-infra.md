# 源码阅读参考：面包屑链路与通用底层基座（Breadcrumbs & Shared Infrastructure）

- 确认时间：2026-10-23，由用户明确认可并指示沉淀为标准参考（Reference）。
- 典型案例：[`run_agent`](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/common.py/run_agent.md)（特化上层调用者）与 [`exec_and_wait`](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md)（通用底层基础设施）。

---

## 1. 为什么需要面包屑与分层参考？

在大型分布式或智能体框架中，函数调用往往跨越多个层次（如业务编排层 → 框架调度层 → 通用基座层）。在此类调用下钻过程中，经常出现两个认知痛点：

1. **信息过载与职责漂移**：
   上层业务函数（例如仅 15 行的 `run_agent`）若在卡片中塞入底层复杂的实现细节（脱机脚本、`setsid` 会话隔离、5 秒轮询保活等），会导致当前卡片严重失焦，掩盖了上层函数真正的 15 行直接职责。
2. **底层脱节与迷失上下文**：
   当为底层工具单独建卡后，读者极易产生孤立感（“我从哪一步跳过来的？读完该回哪？”），甚至产生严重误解，**误以为底层通用函数仅仅为当前这一个上游服务**。实际上，底层工具（如 `exec_and_wait`）同时服务于安装工具（Step 5）、运行 Agent（Step 7）以及评测验证等多个阶段。

因此，必须通过**“面包屑链路（Breadcrumb Trail）”**和**“特化上层 vs 通用基座”**的分层范式来规范卡片。

---

## 2. 规范三要素

### 要素一：特化上游 vs 通用基座分工

| 层次 | 典型代表 | 核心特征与卡片写法 |
| :--- | :--- | :--- |
| **特化上游（Specialized Caller）** | `run_agent` | 1. 严格收敛在自身源码范围（如 15 行）；<br>2. 仅记录自身的数据转换（root 创建目录、指定 `user="agent"`、输出定向到 `trajectory.jsonl`）；<br>3. 留下前进的面包屑跳转链接，不代写底层轮询细节。 |
| **通用基座（Shared Infra）** | `exec_and_wait` | 1. 明确声明自身是跨模块通用的底层基础设施；<br>2. 在“使用场合”与“LLM 整理”中列出已被哪几个步骤/函数调用（如 Step 5 安装与 Step 7 运行）；<br>3. 完整梳理其独立解决的核心工程痛点（防长连接断开、心跳防闲置 GC）。 |

---

### 要素二：卡片顶部的统一面包屑导航条（Breadcrumb Trail）

在每张函数卡片的一级标题下方，统一加入引用块形式的面包屑导航条：

#### 上层调用者（Caller）示例：
```markdown
# run_agent

> **调用链面包屑**：[Step 7 范围](../../../../01-scope.md) > [02 短期概览](../../overview.md) > [BaseHarness.run](BaseHarness.run.md) → [ClaudeCodeHarness.launch_and_wait](../claude_code.py/ClaudeCodeHarness.launch_and_wait.md) → **run_agent** → [exec_and_wait](../../sandbox.py/exec_and_wait.md)
```

#### 底层通用基座（Callee）示例：
```markdown
# exec_and_wait

> **调用链面包屑**：[Step 7 范围](../../../01-scope.md) > [02 短期概览](../../overview.md) > 调用来源：[run_agent](../harness/common.py/run_agent.md)（本步 Agent 运行） · [install_npm_cli（Step 5 安装工具）](../../../../../../03-long-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md) → **exec_and_wait**
```

- **加粗突出**：当前函数用 `**函数名**` 加粗，前后链路用超链接连接；
- **多来源标注**：底层通用函数显式注明不同的调用来源及其业务阶段。

---

### 要素三：精确的相对链接与“读完返回（Read & Return）”跳转表

所有的跨卡链接必须使用**精确的相对路径**（经由目录层级计算），严禁使用未经计算的占位路径。

在底层卡片的“本场景输入与输出”末尾，必须使用跳转表明确交代返回去向：

```markdown
| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [run_agent，107–122](../harness/common.py/run_agent.md)：上层调用入口（本步） | 拿到 `exit_code`，返回给上游 `launch_and_wait` |
| [install_npm_cli，82–100](../../../../../../03-long-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md)：上层调用入口（Step 5） | 拿到 `(exit_code, last_log)`，判断重试或进入下一步 |
```

---

## 3. 标准模版示例对照

### 上游特化卡片（以 `run_agent` 为例）：
```markdown
# run_agent

> **调用链面包屑**：[Step 7 范围](../../../../01-scope.md) > [02 短期概览](../../overview.md) > [BaseHarness.run](BaseHarness.run.md) → [ClaudeCodeHarness.launch_and_wait](../claude_code.py/ClaudeCodeHarness.launch_and_wait.md) → **run_agent** → [exec_and_wait](../../sandbox.py/exec_and_wait.md)

- 源码定位：[slime/agent/harness/common.py:107–122](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L107-L122)

## 本场景的输入与输出
...
### 2. 降权委派 exec_and_wait 脱机执行并返回退出码（111–122）
...
| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [exec_and_wait，82–145](../../sandbox.py/exec_and_wait.md)：脱机脚本生成、后台启动与完成标记轮询 | 取得 `(exit_code, _)`，接住退出码并直接返回调用方 |
```

### 下游基座卡片（以 `exec_and_wait` 为例）：
```markdown
# exec_and_wait

> **调用链面包屑**：[Step 7 范围](../../../01-scope.md) > [02 短期概览](../../overview.md) > 调用来源：[run_agent](../harness/common.py/run_agent.md)（本步 Agent 运行） · [install_npm_cli（Step 5 安装工具）](../../../../../../03-long-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md) → **exec_and_wait**

- 源码定位：[slime/agent/sandbox.py:82–145](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L82-L145)

## LLM 整理：使用场合、具体内容与心智模型
1. **使用场合（通用长任务基础设施）**：
   本函数是 Slime 底层的通用设施，被多个阶段调用：
   - Step 5 工具安装：`install_npm_cli`（指定 `want_output=True` 捕获日志并配合重试）；
   - Step 7 运行 Agent：`run_agent`（指定 `want_output=False` 重定向轨迹文件）；
   - 其他耗时命令。
```
