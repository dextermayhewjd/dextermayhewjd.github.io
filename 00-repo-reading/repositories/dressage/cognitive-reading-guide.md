# Dressage 源码阅读指南：认知心理学心智构建与两段式骨架心法

[返回 Dressage 阅读入口](README.md) · [两仓区别与必读模块清单](job-and-repo-comparison.md) · [通用工作流](../../workflow.md) · [认知顺序 Skill 规范](../../../.agents/skills/repo-reading-order/SKILL.md)

记录日期：2026-10-22。

本文专门沉淀针对 Dressage 架构的**认知心理学阅读方法论**，确立执行器编排（剧本流）与抽象契约（角色卡）的认知顺序，并作为后续会话与 Skill 的统一判断基准。

---

## 一、认知负荷理论（Cognitive Load Theory）与代码心智模型

根据认知负荷理论（Sweller, 1988），人类工作记忆（Working Memory）容量极其有限（4±1 个组块）。面对复杂的分布式 Agent RL 系统，大脑面临三种负荷：
1. **内在负荷（Intrinsic Load）**：RL 多轮决策、沙箱隔离、Token 级轨迹切段本身的复杂度；
2. **外在负荷（Extraneous Load）**：信息呈现顺序不合理导致的无效认知损耗（例如脱离上下文去生啃抽象接口、去猜变量从哪冒出来的）；
3. **关联负荷（Germane Load）**：大脑真正用来将代码模式（Schema）沉淀为长久直觉的有效思考。

> **核心原则**：将“外在负荷”降为 0，让工作记忆完全投入到“关联负荷”。

---

## 二、两部分骨架在大脑中的认知分工

在 Dressage 中，我们最关注的两个部分在大脑中对应着完全不同的认知表征：

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. 执行器编排骨架（The Flow Skeleton，如 blackbox_dispatch.generate）   │
│    • 认知类型：时间链（Timeline） / 情节记忆（Episodic Memory）        │
│    • 大脑提问：“发生什么事？然后呢？最后怎么收场？”                    │
│    • 核心抓手：识别生命周期（try...finally RAII）+ 提取无缩进动词序列 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ 产生悬念与情境锚点（Anchor）
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. 接口契约骨架（The Contract Skeleton，如 provider.py + interface.py） │
│    • 认知类型：空间图（Spatial Map） / 语义记忆（Semantic Memory）     │
│    • 大脑提问：“谁负责什么？谁不可逾越什么界限？换掉它成本多大？”      │
│    • 核心抓手：正交分解（Where it runs vs What to do）+ 依赖倒置（DIP） │
└────────────────────────────────────────────────────────────────────────┘
```

### 为什么不能先看抽象接口？（锚定与脚手架理论）
如果脱离调用情境直接看 180 行 `provider.py`（Protocol）和 `interface.py`（ABC），大脑处于“无锚点悬空状态”，必须凭空脑补“这个接口会被谁调用、数据长什么样”，外在负荷瞬间拉满，导致眩晕。

相反，**先花 10 分钟看执行器骨架（建立时间线因果锚点）→ 大脑产生具体疑问（“这个 paddock.init 底下怎么拿到容器的？”）→ 带着疑问翻开 180 行接口（挂载角色卡解惑）**，认知负荷最低，心智模型瞬间闭环。

---

## 三、Dressage 的具体阅读推进路线

基于上述心智规律，Dressage 的阅读分为两阶段：

### 阶段一：建立时间线锚点（执行器与任务闭环）
1. **Step 1 · 黑盒调度指挥官主线**：
   - 目标：用剪枝法读通 [`dressage/rollout/generate/blackbox_dispatch_swegym.py :: generate`](file:///Users/dextermayhew/projects/Dressage/dressage/rollout/generate/blackbox_dispatch_swegym.py#L88) 的正常路径；
   - 重点提取：`paddock.init` → `paddock.register_agent` → `paddock.call_agent` → `proxy.finalize` → `expand_segments_to_samples` 动词序列；
   - 产出短期记忆：1 张指挥官执行器卡片。
2. **Step 2 · 白盒循环对比与两条主线汇合**：
   - 目标：对比读通 [`dressage/rollout/generate/whitebox_agent.py :: make_generate`](file:///Users/dextermayhew/projects/Dressage/dressage/rollout/generate/whitebox_agent.py#L322)，看 Python 自己跑 `for step in range(max_steps)` 是怎样与黑盒汇合到同一套样本转换上的；
   - 产出短期记忆：白盒执行器卡片。

### 阶段二：挂载空间结构契约（接口与正交解耦）
3. **Step 3 · 180 行两层接口契约解惑**：
   - 目标：带着前两步对 `paddock` 的调用疑问，解剖 [`provider.py`](file:///Users/dextermayhew/projects/Dressage/dressage/sandbox/provider.py)（66 行）与 [`interface.py`](file:///Users/dextermayhew/projects/Dressage/dressage/paddock/interface.py)（120 行）；
   - 重点理解：为什么“沙箱在哪（Where it runs）”和“Agent 怎么交互（What to do）”必须正交拆开；
   - 产出短期记忆：`SandboxProvider` 协议卡 + `Paddock` 体系卡。

---

## 四、与 Slime Repo Reading 的关系：平行独立、零冲突

### 1. Slime 中早已应用了相同的认知规律
在 Slime 仓库阅读历史中，早已经沉淀了相同的认知方法：
- 见 [`.agents/skills/repo-reading-order/references/inside-out-method.md`](../../../.agents/skills/repo-reading-order/references/inside-out-method.md)（**原子核向心跳跃法**）：Slime 在 Step 0 确立 7 步骨架后，并不是线性读前 3 步脚手架，而是直奔步骤 4（`Harness.run`）和步骤 1 的 `_run_turn` 核心请求，读通心脏后再回补 Step 4/5/6/7 的管线。
- **Dressage 的“先时间线动词，后空间图契约”正是这一认知规律的精准延续。**

### 2. 物理与逻辑双重隔离，绝不冲突
- **文件目录物理隔离**：
  - Slime 的全部步骤与累计记忆保存在：`00-repo-reading/repositories/slime/steps/`
  - Dressage 的全部步骤与累计记忆保存在：`00-repo-reading/repositories/dressage/steps/`
- **阅读主线独立接续**：
  - Slime 的唯一接续点在 `slime_photo/code-reading/repo-reading-route.md#当前接续`（当前在 Step 7 研究跨组件通信）；
  - Dressage 的唯一接续点在 `00-repo-reading/repositories/dressage/README.md#步骤索引`；
  - 两者互不引用彼此的 `02/03` 记忆卡片，各有一套独立演进的学习历史。
