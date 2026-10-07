---
title: "Lecture 2 · 从行为克隆到 DAgger"
description: "用监督学习拟合专家动作之后，为什么自己跑起来还会出错？先看整讲主线，再逐行拆解 20 条公式。"
date: 2026-10-07
weight: 20
math: true
ShowToc: false
tags: [CS285, 模仿学习, Behavioral Cloning, DAgger]
---

## 先看清这一讲在做什么 {#lecture-thread}

本讲主题：**Supervised Learning of Behaviors（行为的监督学习）**。

从监督学习走到 BC，再追问训练与执行分布为什么不同。**量化时先定义错误，得到单步犯错率，再写出整条轨迹的期望总错误；随后统一分解“此前无错／曾经出错”，先比较分布，再拆解错误。**

{{< lecture-mindmap id="lecture-argument-map" cards="argument-cards.json" >}}

### 把这条主线读成一段话

我们先从专家轨迹里学一个 $\pi_\theta(a\mid o)$；离散动作可以用 softmax，连续动作可以用高斯分布表示。训练目标会鼓励策略在**专家数据中的观测**上给正确动作高似然。

但部署时，策略要自己选动作。这些动作会影响未来状态，所以它实际遇到的输入分布 $p_{\pi_\theta}$ 可能偏离专家分布 $p_{\mathrm{data}}$。**同一个策略，换了一套加权它表现的状态分布**，就是长推导要处理的矛盾。

证明先把“犯错”变成 0/1 代价，再估计两个状态分布的距离，最后把部署误差拆成“专家分布上的基础误差”与“分布差异带来的额外项”。额外项的上界随时间步增长，对时间求和就出现平方级上界。DAgger 则把采集环节接回策略：自己去走，请专家在这些状态上标正确动作，然后重新拟合。

### 第一次读与回来复习，走两条路径

| 当前目标 | 阅读路线 | 读完要能说出什么 |
|---|---|---|
| 第一次建立理解 | 图 1 → 公式 5 → 公式 10 → 图 2 → 公式 20 | 为什么 BC 的拟合目标与部署表现之间有缺口 |
| 卡在数学细节 | 图中对应节点 → 下方该公式 → 前后相邻公式 | 已知条件、这一行做的变换、交给下一步的结论 |
| 回来复习 | 只看图 1，复述事件分解、分布距离与误差拆账 → 做页尾自测 | 不看长推导也能解释平方级上界从哪来 |

这一版把概览也做成**初学入口**；读到卡点才下钻。下方保留原笔记的符号解释、例子和逐行推导，复习时可以直接回到图中检查关系。

<details>
<summary>展开全页目录与公式索引</summary>

{{< chapter-outline id="lecture-outline" title="Lecture 2 阅读位置" >}}

</details>

## 逐行拆解前，先认清几个对象 {#notation}

下面的主体整理自本地笔记《Lecture2 公式逐行拆解》，沿用公式 1–20 与原笔记的 Slide 编号。网页中补充了每条公式的用途，并校正几处简写的条件；不同年份课件的页码可能不同。

| 符号 | 读法 | 意思 |
|---|---|---|
| $\theta$ | theta | 神经网络的参数（权重），就是要学的东西 |
| $\pi$ | pi | policy（策略） |
| 下标 $t$ | t | 时间步（一条轨迹里的第几步） |
| 上标 $(i)$ | i | 第几条轨迹 / 第几个样本 |
| $\mid$ | "given / 给定" | 条件概率的竖线 |
| $\mathbf{x}, y$ | x, y | 监督学习的输入、输出 |
| $\mathbf{o}_t$ | o_t | observation，时刻 t 的观测（看到的，比如图片） |
| $\mathbf{a}_t$ | a_t | action，时刻 t 的动作 |
| $\mathbf{s}_t$ | s_t | state，时刻 t 的真实状态（世界的"真相"） |
| $\pi^\star$ | pi-star | 专家策略（模仿的参照；不要求全局最优） |
| $H$ | — | horizon，轨迹长度 |
| $N$ | — | 轨迹/样本数量 |
| $\epsilon$ | epsilon | 单步犯错概率（一个很小的数） |
| $\sim$ | "服从 / 采样自" | $x\sim p$ 表示 x 从分布 p 里抽出来 |
| $\mathbb{E}$ | "期望 expectation" | 加权平均 |

---

## Part 1：从监督学习到模仿学习


### 公式 1 · Slide 3：监督学习 = 最大似然估计 {#formula-1}

> **这条公式在整讲中的任务：** 建立整讲共用的训练工具：让模型给示范中的正确输出更高的似然。后面的 BC 直接复用它。

$$\arg\max_\theta \;\sum_{i=1}^N \log p_\theta\big(y^{(i)}\mid \mathbf{x}^{(i)}\big)$$

**怎么读**："找到那个 θ，使得『对所有样本求和的 log p_θ(y given x)』最大。"

**逐符号拆**
- $\arg\max_\theta$ —— 注意是 **arg** max，不是 max。
  - $\max$ 返回**最大值本身**（一个数）。
  - $\arg\max_\theta$ 返回**取得最大值的那个 θ**。我们要的是参数，所以用 arg max。
- $p_\theta(y\mid\mathbf{x})$ —— 模型认为"输入是 $\mathbf{x}$ 时，输出为 $y$"的概率。下标 θ 表示这是网络算的。
- $\log$ —— 取对数。作用：把"概率连乘"变成"log 连加"（$\log(ab)=\log a+\log b$），既防数值下溢，又不改变最大值位置。
- $\sum_{i=1}^N$ —— 对 N 个样本逐个相加，$i$ 是第几个样本。

**直觉**：让模型对每个训练样本都给"正确答案"尽量高的概率，全部加起来一起最大化 —— 这就是**最大似然估计（MLE）= 监督学习**。

---

#### ❓ 为什么 log 是负数，还能"最大化"？（最常卡的一步）

> **常见困惑**：log 是单调增的我懂，可一个概率 0.9 上了 log 还是负数（$\log 0.9\approx-0.105$），把一堆负数加起来，"最大化"到底在最大化什么概率？

**范围先说清：本段以离散标签为例，概率不超过 1。连续动作使用的是概率密度，密度可以超过 1，log 密度也可以为正；最大似然的优化方向仍相同。**

**① 先认清：slide 上写的是"连加 ∑"，不是"连乘"。** 连乘是 log **之前**的那个东西，它有两副面孔：

- **原始 likelihood（似然）—— 这才是连乘**：
$$L(\theta)=\prod_{i=1}^N p_\theta\big(y^{(i)}\mid x^{(i)}\big)=p_\theta(y^{(1)}\mid x^{(1)})\times p_\theta(y^{(2)}\mid x^{(2)})\times\cdots$$
- **取 log 之后 —— 变成连加（=公式 1 本体）**：用 $\log(ab)=\log a+\log b$，连乘就摊成了 $\sum_i\log p_\theta$。

所以公式 1 的 ∑ **已经是"log 之后"的形态**，连乘是它的前身。

**② 负数没关系，关键是认知转弯：**
$$\boxed{\text{"最大化一个负数" = 让它尽量靠近 }0\text{（尽量不那么负）}}$$
因为概率 $p\le1$，所以 $\log p\le0$ **永远成立**，这个 ∑ 几乎总是负数。但绝对值大小没意义，**我们只关心它能不能更大（更靠近上限 0）**：

| 模型表现 | 给正确答案的概率 $p$ | $\log p$ | 含义 |
|---|---|---|---|
| 完美 | $p\to1$ | $\to 0$ | 达到上限，最好 |
| 一般 | $p=0.9$ | $-0.105$ | 还行 |
| 很差 | $p\to0$ | $\to-\infty$ | 掉无底洞，最差 |

一句话：**最大化 $\sum\log p$ = 把模型分配给每个正确答案的概率尽量往 1 推**，推到极限 sum = 0。

**③ 用数字看 log 单调如何保证"位置不变"**：3 个样本，某 θ 给正确答案的概率是 0.9, 0.8, 0.7 → 换一个更好的 θ′ 变成 0.95, 0.9, 0.85：

| | 连乘 $\prod p$（likelihood） | 连加 $\sum\log p$（log-likelihood） |
|---|---|---|
| θ | $0.9\cdot0.8\cdot0.7=0.504$ | $-0.105-0.223-0.357=-0.685$ |
| θ′ | $0.95\cdot0.9\cdot0.85=0.727$ ⬆️ | $-0.051-0.105-0.163=-0.319$ ⬆️（更靠近 0） |

**两边一致判定 θ′ 更好**。这就是 log 单调递增的意义 —— 让 $\prod p$ 最大的 θ，和让 $\sum\log p$ 最大的 θ 是**同一个**；换 log 纯为**防数值下溢 + 乘法变加法好求导**，不改变要找的那个 θ。

**④ 那"最大化的概率"到底是什么？** 就是 likelihood：
> **给定训练输入、按条件独立的标签模型计算整组观测标签的似然。**

每个因子 $p_\theta(y^{(i)}\mid x^{(i)})$ = 模型认为"输入 $x^{(i)}$ 时输出正好是真实标签 $y^{(i)}$"的概率；连乘 = 一次性产出整套正确标签的概率。训练选择使这组观测标签最有可能的参数；受模型容量与标签冲突限制，似然不一定能达到 1。

**⑤ 打通到代码里的 loss**（以后一定遇到）：实践里常写成**最小化一个正数**，加个负号即可，完全等价：
$$\underbrace{\max_\theta\ \textstyle\prod p}_{\text{概率最大}}\iff\underbrace{\max_\theta\ \textstyle\sum\log p}_{\text{公式 1}}\iff\underbrace{\min_\theta\ -\textstyle\sum\log p}_{\text{代码里的 NLL / 交叉熵 loss}}$$

---

### 公式 2 · Slide 5：策略 policy {#formula-2}

> **这条公式在整讲中的任务：** 把监督学习的“输入→标签”换成“观测→动作”，明确我们到底在学什么。

$$\pi_\theta(\mathbf{a}_t\mid\mathbf{o}_t)$$

**怎么读**："在观测到 $\mathbf{o}_t$ 的情况下，采取动作 $\mathbf{a}_t$ 的概率。"

> 🔑 **和公式 1 并排看**：$p_\theta(y\mid\mathbf{x})\ \leftrightarrow\ \pi_\theta(\mathbf{a}_t\mid\mathbf{o}_t)$
> 只是 $\mathbf{x}\to\mathbf{o}_t$、$y\to\mathbf{a}_t$、$p\to\pi$。**数学骨架完全一样** —— 这就是"从监督学习到模仿学习"整句话的含义。

---

### 公式 3 · Slide 6：马尔可夫性 + 转移 + 观测模型 {#formula-3}

> **这条公式在整讲中的任务：** 补上行为学习的闭环：动作通过环境影响下一个状态，观测由状态产生。这是后面分布偏移的来源。

**马尔可夫性**
$$\mathbf{s}_{t+1}\ \perp\ \mathbf{s}_{t-1}\ \mid\ \mathbf{s}_t$$
- $\perp$ 读作"**独立**（independent）"。
- 整句："**给定**当前状态 $\mathbf{s}_t$，下一个状态 $\mathbf{s}_{t+1}$ 与上一个状态 $\mathbf{s}_{t-1}$ 独立。"
- 直觉：**未来只取决于现在，不取决于过去**。知道了"现在"，"过去"就不再提供额外信息。

> ⚠️ **符号是简写**：这里只写了 $\mathbf{s}_{t-1}$，但马尔可夫性的**完整定义**是"给定 $\mathbf{s}_t$，未来与**全部历史** $\mathbf{s}_{t-1},\mathbf{s}_{t-2},\dots,\mathbf{s}_1$ 都独立"，不只是上一个。slide 用 $\mathbf{s}_{t-1}$ 当"整串过去"的代表符。上面那句中文"不取决于过去"才是完整口径。

**转移（动力学）**
$$p(\mathbf{s}_{t+1}\mid\mathbf{s}_t,\mathbf{a}_t)$$
读："在状态 $\mathbf{s}_t$ 做了动作 $\mathbf{a}_t$ 后，转移到 $\mathbf{s}_{t+1}$ 的概率。"

**观测模型**
$$p(\mathbf{o}_t\mid\mathbf{s}_t)$$
读："由真实状态 $\mathbf{s}_t$ 生成观测 $\mathbf{o}_t$ 的概率。"

---

### 公式 4 · Slide 7：完全可观测 {#formula-4}

> **这条公式在整讲中的任务：** 解释为什么后半段用状态 s，而前半段用观测 o；完全可观测时两者可以合并。

$$\mathbf{o}_t=\mathbf{s}_t \quad\Rightarrow\quad \pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)$$
- 当"看到的"就是"真相"（observation = state），策略可以直接写成依赖状态 $\mathbf{s}_t$。
- slide 框出一句：$p(\mathbf{o}_t\mid\mathbf{s}_t)$ 和 $p(\mathbf{s}_{t+1}\mid\mathbf{s}_t,\mathbf{a}_t)$ 这两个你 **typically don't need to know（通常不需要知道）**。因为 BC 只是纯监督地拟合 $\mathbf{o}_t\to\mathbf{a}_t$，没用到环境怎么转移。

---

### 公式 5 · Slide 8：数据 + Behavioral Cloning 目标 {#formula-5}

> **这条公式在整讲中的任务：** 把训练规则落到专家轨迹上：两层求和收集每条轨迹、每个时间步的动作拟合项。

**数据 = 示范轨迹**
$$\Big\{\big(\mathbf{o}_1^{(i)},\mathbf{a}_1^{(i)},\dots,\mathbf{o}_H^{(i)},\mathbf{a}_H^{(i)}\big)\Big\}_{i=1}^{N}$$
- 最外层 $\{\cdots\}_{i=1}^N$：一个**集合**，里面有 $N$ 条轨迹。
- 每一项 $(\mathbf{o}_1,\mathbf{a}_1,\dots,\mathbf{o}_H,\mathbf{a}_H)$：**一整条轨迹**，从第 1 步到第 $H$ 步的（观测, 动作）对。

> 🔑 **两个指标别混**（最容易错）：
> - **上标 $(i)$** 数"第几条轨迹"（共 $N$ 条）
> - **下标 $t$** 数"轨迹里第几步"（共 $H$ 步）

**Behavioral Cloning 目标**
$$\arg\max_\theta \;\sum_{i=1}^{N}\sum_{t=1}^{H}\log \pi_\theta\big(\mathbf{a}_t^{(i)}\mid\mathbf{o}_t^{(i)}\big)$$
- **两个求和号**：外层 $\sum_{i=1}^N$ 遍历 N 条轨迹，内层 $\sum_{t=1}^H$ 遍历每条轨迹的 H 步。
- 对比公式 1：监督学习只有**一个** $\sum_i$；BC 有**两个** $\sum$，因为每个"样本"是一整条轨迹，要把每一步都拿来拟合。
- 直觉：把专家每条轨迹、每一步的动作都当"标准答案"去最大化它的 log 概率。**BC 本质就是套在序列数据上的监督学习。**

---

## Part 2：Behavioral Cloning 算法（动作分布怎么表示）

### 公式 6 · Slide 13：离散动作 = softmax {#formula-6}

> **这条公式在整讲中的任务：** 为离散动作构造合法的概率分布，让公式 5 的对数似然有具体的计算方式。

$$p(a_t=1\mid\mathbf{o}_t)=\frac{\exp\big(f_1(\mathbf{o}_t)\big)}{\sum_{i=1}^{A}\exp\big(f_i(\mathbf{o}_t)\big)}$$

**怎么读**："动作取第 1 个的概率 = 第 1 个的 exp，除以所有 A 个的 exp 之和。"

**逐符号拆**
- $f_i(\mathbf{o}_t)$ —— 网络对第 $i$ 个动作输出的 **logit（原始分数，可正可负）**。
- $\exp(\cdot)$ —— 指数函数，把任意实数变成正数。
- 分母 $\sum_{i=1}^A\exp(f_i)$ —— 把 A 个 exp 加起来做**归一化**，保证所有概率加起来 = 1。
- $A$ —— 动作总数（比如 Atari 的按键数）。

**直觉**：这就是 **softmax**。网络吐出一排分数（logits），softmax 把它们变成一个合法的概率分布。用于离散动作（LLM 的 token、游戏按键）。

---

### 公式 7 · Slide 13：连续动作 = 高斯分布 {#formula-7}

> **这条公式在整讲中的任务：** 为连续动作提供一种密度模型：网络输出均值和协方差，而不是把所有动作列成类别。

$$p(\mathbf{a}_t\mid\mathbf{o}_t)=\mathcal{N}\big(\mathbf{a}_t\mid\mu(\mathbf{o}_t),\,\Sigma(\mathbf{o}_t)\big)$$

**怎么读**："给定 $\mathbf{o}_t$，动作 $\mathbf{a}_t$ 服从一个均值为 $\mu(\mathbf{o}_t)$、协方差为 $\Sigma(\mathbf{o}_t)$ 的高斯分布。"

**逐符号拆**
- $\mathcal{N}(\cdot\mid\mu,\Sigma)$ —— 花体 N = 正态（高斯）分布。
- $\mu(\mathbf{o}_t)$ —— **均值**，由网络根据观测算出（动作的"中心值"）。
- $\Sigma(\mathbf{o}_t)$ —— **协方差**（读 Sigma），描述动作的"不确定性/散布范围"。

**直觉**：连续动作（开车的方向盘角度）常用高斯密度表示：网络输出**分布的参数**（均值+协方差），再从中采样或取均值执行。也可以离散化后使用 softmax；高斯只是这里的一种选择。

---

### 公式 8 · Slide 13：高斯的特例 → 平方误差 {#formula-8}

> **这条公式在整讲中的任务：** 把高斯假设接到熟悉的平方误差 loss，解释“概率模型”和“回归损失”为什么能对应起来。

$$\log p(\mathbf{a}_t\mid\mathbf{o}_t)=-\tfrac12\big\lVert \mathbf{a}_t-\mu(\mathbf{o}_t)\big\rVert^2+\text{常数}\qquad(\text{当 }\Sigma(\mathbf{o}_t)=I)$$

**怎么读**："当协方差固定为单位阵时，log 概率 = **负的**半个距离平方（加一个常数）。"

**逐符号拆**
- $\lVert\,\cdot\,\rVert^2$ —— 向量的**平方范数**（各分量平方再求和），即欧氏距离的平方。
- $I$ —— 单位矩阵（identity）；$\Sigma=I$ 意味着"各方向不确定性相同、固定"。
- **负号 $-$（最关键）** —— 动作 $\mathbf{a}_t$ 离均值 $\mu$ 越远 → 距离平方越大 → log 概率越**小**（越不可能）。**方向千万别读反**。

> ⚠️ **为什么标题要带负号（slide 偷懒了）**：slide 上把它写成 $\log p=\lVert\mathbf{a}_t-\mu\rVert^2$，**丢了负号、$\tfrac12$ 和常数**，那个 "=" 严格说并不成立。若照字面读"log 概率 = 距离平方"，等于说"动作越偏离越可能"，**方向是反的**。正确的就是上面这行。
> **结论**：因为有负号，"**最大化** log 似然" ⟺ "**最小化** $\lVert\mathbf{a}_t-\mu\rVert^2$"。所以协方差固定为 $I$ 的高斯最大似然 ≡ 普通的**最小二乘回归**——这就是平方误差和高斯假设是一回事的原因。
> 🔗 这正是公式 1 那条链 $\max\sum\log p\iff\min(-\sum\log p)$ 的一个具体特例。
> 🔗 **$\mathcal{N}(\mathbf{a}_t\mid\mu,\Sigma)$ 这个多元高斯从哪来、$\Sigma$ 和 $\Sigma^{-1}$ 到底在干嘛？** 从一维高斯一步步搭起的完整推导 → 《00 · 一页地图（一维高斯 → CS285 高斯策略）》（本地补充笔记）（本页对应 《05 · 读懂 lec-2 第12页（网络吐的不是动作，是分布的参数）》（本地补充笔记）；马氏范数 《04 · 让维度相关起来（一般协方差 Σ 与马氏范数）》（本地补充笔记））

---

## Part 3：BC 会出什么问题（distributional shift）

### 公式 9 · Slide 19：分布偏移的定义 {#formula-9}

> **这条公式在整讲中的任务：** 先定义一般的训练／测试输入分布差异，再追问行为学习里这个差异由谁造成。

$$\underbrace{p_\theta(y\mid\mathbf{x})\ \text{训练于}\ \mathbf{x}\sim p_{\text{train}}(\mathbf{x})}_{\text{训练}}\qquad \underbrace{\text{测试于}\ \mathbf{x}\sim p_{\text{test}}(\mathbf{x})}_{\text{测试}}$$
$$p_{\text{test}}(\mathbf{x})\ \neq\ p_{\text{train}}(\mathbf{x})$$

**怎么读**："训练时输入服从 $p_{\text{train}}$，测试时却服从 $p_{\text{test}}$，而两者不相等。"

**直觉**：你照着数学复习，结果考的是古希腊文学。训练分布和测试分布对不上，模型当然崩。

---

### 公式 10 · Slide 20：BC 里的分布偏移特殊在哪 {#formula-10}

> **这条公式在整讲中的任务：** 指出整讲的矛盾：训练目标在专家分布上，而部署表现要在策略自己诱导的分布上评价。

**训练目标（在专家数据分布下）**
$$\max_\theta\ \mathbb{E}_{\mathbf{o}_t\sim p_{\text{data}}(\mathbf{o}_t)}\big[\log\pi_\theta(\mathbf{a}_t\mid\mathbf{o}_t)\big]$$
- $\mathbb{E}_{\mathbf{o}_t\sim p_{\text{data}}}$ —— 在"观测来自专家数据分布 $p_{\text{data}}$"的前提下取期望（平均）。

> ⚠️ **期望省了一层（忠于 slide）**：式子里只对 $\mathbf{o}_t$ 取期望，但里面的 $\mathbf{a}_t$ **也是随机的**——它来自专家 $\mathbf{a}_t\sim p_{\text{data}}(\mathbf{a}_t\mid\mathbf{o}_t)$。严格的完整写法是 $\mathbb{E}_{(\mathbf{o}_t,\mathbf{a}_t)\sim p_{\text{data}}}\big[\log\pi_\theta(\mathbf{a}_t\mid\mathbf{o}_t)\big]$。读的时候记住：这里的 $\mathbf{a}_t$ 默认就是"专家在 $\mathbf{o}_t$ 下给的那个动作"。

**部署时的真实分布**
$$p_{\text{data}}(\mathbf{o}_t)\ \neq\ p_{\pi_\theta}(\mathbf{o}_t)$$
- $p_{\pi_\theta}(\mathbf{o}_t)$ —— **你自己的策略跑起来后，诱导出来的观测分布**。

> 🔑 **BC 比普通监督学习更糟的根源**：普通 SL 的 $p_{\text{test}}$ 是外部固定给的；而 BC 的"测试分布" $p_{\pi_\theta}$ 是**你自己的错误一步步制造出来的**。你越错 → 进入没见过的状态 → 更容易错 → 雪球越滚越大。

---

## Part 4：到底能有多糟（核心长推导 ⭐）


### 先看证明的分工：每个工具到底交给谁 {#proof-route}

这段的起点是一个“分布不匹配”：已知条件只约束**专家足迹上的平均错误**，而目标量使用**学生自己跑出的足迹**。因此不能直接给每一步填上 $\epsilon$。

{{< lecture-map id="lecture-proof-map" src="images/proof-map.svg" cards="proof-cards.json" label="公式 11 到 17 的证明依赖关系" caption="图 2：上排先定义待控制的量，再拆账；下排给出两个可用上界，最后汇入求和。箭头表示数学依赖，不是算法执行。" arrows="已知条件或中间结论，被后续步骤使用" >}}

读每行前，先问：**当前在哪个分布下取期望？手里的上界能否用于这个分布？** 这两个问题能把公式 11–17 接起来。

本段假定初始状态分布相同，专家策略确定，$p_{\mathrm{train}}(s_t)$ 表示第 $t$ 步专家访问状态的分布；$\epsilon$ 是在这个分布上的真实平均误差上界。仅测到有限训练集上的低误差，还需要泛化分析才能得到这个假定。


> 这是全课最硬的一段。我们一行一行来。**目标**：证明哪怕单步错误率只有 $\epsilon$，序列里总错误数最坏会涨到 $O(\epsilon H^2)$。

### 公式 11 · Slide 25：把"犯错"变成可计算的量 {#formula-11}

> **这条公式在整讲中的任务：** 定义固定状态上的局部犯错率，供公式 12 对状态和时间进一步平均。

**分析范围：这里以确定性专家和离散动作的精确匹配来定义犯错。连续动作若直接比较“是否完全相等”，通常不适合评价高斯采样策略；实际连续任务可用回归损失或误差阈值。本段 0/1 理论模型与公式 8 的平方误差要分开读。**

**代价函数（0/1 cost）**
$$c(\mathbf{s}_t,\mathbf{a}_t)=\begin{cases}0 & \text{if }\mathbf{a}_t=\pi^\star(\mathbf{s}_t)\\[4pt] 1 & \text{otherwise}\end{cases}$$
- 读："动作跟专家 $\pi^\star$ 一样 → 代价 0；不一样 → 代价 1。"

**一步的期望代价 = 犯错概率**
$$\mathbb{E}_{\mathbf{a}_t\sim\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)}\big[c(\mathbf{s}_t,\mathbf{a}_t)\big]
=\sum_{\mathbf{a}_t}\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)\,c(\mathbf{s}_t,\mathbf{a}_t)
=\pi_\theta\big(\mathbf{a}_t\neq\pi^\star(\mathbf{s}_t)\mid\mathbf{s}_t\big)$$

**逐步看为什么**
1. $\mathbb{E}_{\mathbf{a}_t\sim\pi_\theta}[\cdot]$：对"从策略 $\pi_\theta$ 里抽出的动作"求期望（加权平均）。
2. 期望 = 把每个动作的概率 × 它的代价，再求和 → $\sum_{\mathbf{a}_t}\pi_\theta\cdot c$。
3. 因为代价非 0 即 1，"加权平均"就退化成"代价=1 的那些动作的总概率" = **犯错的概率**。

> 💡 一句话：**0/1 代价的期望，就是犯错的概率。**

---

### 公式 12 · Slide 26：总错误数 {#formula-12}

> **这条公式在整讲中的任务：** 写出真正要控制的量：用策略实际到达的状态分布计算整条轨迹的总错误。

$$\sum_{t=1}^{H}\ \mathbb{E}_{\,\mathbf{a}_t\sim\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t),\ \mathbf{s}_t\sim p_{\pi_\theta}(\mathbf{s}_t)}\big[c(\mathbf{s}_t,\mathbf{a}_t)\big]$$

**怎么读**："从 t=1 到 H，把每一步的犯错概率加起来" = **整条轨迹的期望总错误次数**。

#### 🔑 公式 11 → 公式 12，到底多了什么（最容易搞混）

先破一个常见误会：公式 11 **并没有**把 s 和 a 两个分布都写出来。看它期望的下标 $\mathbb{E}_{\,\mathbf{a}_t\sim\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)}[\,\cdot\,]$ —— 下标里**只有 $\mathbf{a}_t\sim\pi_\theta$ 一个分布**。$\mathbf{s}_t$ 虽然到处出现，但它一直待在竖线 $\mid$ 右边当**条件**，是**被给定、固定**的，没有被平均掉；求和号 $\sum_{\mathbf{a}_t}$ 也是对**动作**遍历，不是对状态。所以公式 11 只回答一件很局部的事：**「站在某个确定的状态 $\mathbf{s}_t$ 上，这一步犯错的概率是多少。」**

公式 12 相对公式 11 **只加了两样东西**：

| | 公式 11 | 公式 12 |
|---|---|---|
| **时间范围** | 只看**一步**（某个固定的 $t$） | $\sum_{t=1}^H$：把**整条轨迹 H 步**都加起来 |
| **状态 $\mathbf{s}_t$** | **固定/给定**，不平均 | 多了 $\mathbf{s}_t\sim p_{\pi_\theta}(\mathbf{s}_t)$，**状态本身也变随机、要平均** |

- **第①个新增 $\sum_{t=1}^H$（不烧脑）**：一步的犯错率 → 把每一步加起来，就成了整条轨迹的总错误。
- **第②个新增 $\mathbf{s}_t\sim p_{\pi_\theta}(\mathbf{s}_t)$（灵魂）**：公式 11 是"假设已经站在某状态上"算错率；但第 t 步**你会站在哪个状态本身就是随机的**，且由你前面所有动作决定，所以必须对"实际会遇到哪些状态"也取期望。下标特意写 $p_{\pi_\theta}$ 而不是 $p_{\text{train}}$，强调这是**你自己策略跑出来诱导的状态分布**。

一句话连起来：
$$\underbrace{\pi_\theta(\mathbf{a}_t\neq\pi^\star\mid\mathbf{s}_t)}_{\text{公式 11：一步、定点的犯错率}}\ \xrightarrow{\ \text{对 }\mathbf{s}_t\text{ 也取期望}\ +\ \sum_t\ }\ \underbrace{\sum_{t=1}^H\mathbb{E}_{\mathbf{s}_t\sim p_{\pi_\theta}}[\,c\,]}_{\text{公式 12：整条轨迹的期望总错误}}$$
公式 11 答"**在这个状态**上错的概率"，公式 12 答"**整条路跑下来**总共预期错几次"。

**最关键的地方**：期望下面的 $\mathbf{s}_t\sim p_{\pi_\theta}(\mathbf{s}_t)$
- 它表示：第 t 步会遇到什么状态，**不是固定的，而是由你前面所有动作决定的**（slide: "note that this depends on past actions"）。
- 普通监督学习里输入分布是外部给的；这里**你的错误会反过来改变以后见到的输入** —— 这就是 BC 和 SL 最大的数学区别。

---

### 公式 13 · Slide 27：最坏情况 → $O(\epsilon H^2)$ 的直觉 {#formula-13}

> **这条公式在整讲中的任务：** 先用“第一次犯错会影响后面一段”的最坏模型，建立平方级上界的直觉。

**假设**（点态版）
$$\pi_\theta\big(\mathbf{a}\neq\pi^\star(\mathbf{s})\mid\mathbf{s}\big)\le\epsilon,\qquad \forall\,\mathbf{s}\in\mathcal{D}_{\text{train}}$$
读："只要状态还在训练分布里，单步犯错概率最多 $\epsilon$。"

**结论结构**

下面用一个最坏简化过程建立上界：在此前无错时，每一步的条件犯错率都取到 $\epsilon$，一旦第一次犯错，后面每步代价都为 1。下面的乘积概率属于这个过程，不是任意真实策略的精确犯错概率。

左半边就是公式 12（整条轨迹的期望总错误）。右半边 slide 上写的其实是一个**嵌套（递归）式**，不是简单的"$\epsilon H$ 加 $H$ 次"：
$$\underbrace{\sum_{t=1}^{H}\ \mathbb{E}_{\,\mathbf{a}_t\sim\pi_\theta,\ \mathbf{s}_t\sim p_{\pi_\theta}}\big[c(\mathbf{s}_t,\mathbf{a}_t)\big]}_{O(\epsilon H^2)}\ \le\ \epsilon H+(1-\epsilon)\Big(\epsilon(H-1)+(1-\epsilon)\big(\epsilon(H-2)+\cdots\big)\Big)$$

把这个嵌套的每一层写成通项：
$$\text{右半边}=\sum_{t=1}^{H}\underbrace{(1-\epsilon)^{t-1}\epsilon}_{\text{前 }t-1\text{ 步没错、第 }t\text{ 步才第一次错}}\times\underbrace{(H-t+1)}_{\text{从第 }t\text{ 步起最多还能错的步数}}$$

> ⚠️ **"右半边到底应该是什么"——三种写法是层层放粗的关系**
> $$\underbrace{\sum_t(1-\epsilon)^{t-1}\epsilon(H-t+1)}_{\text{(1) 简化模型的嵌套式}}\ \le\ \underbrace{\epsilon\sum_t(H-t+1)=\epsilon\tfrac{H(H+1)}{2}}_{\text{(2) 丢掉 }(1-\epsilon)^{t-1}\le1\text{ 后的闭式}}\ \le\ \underbrace{\epsilon H\cdot H=\epsilon H^2}_{\text{(3) 每项顶到 }\epsilon H\text{ 的粗上界}}$$
> - **③（笔记最初那行 $\epsilon H+\dots+\epsilon H$）怎么来的**：通项里 $(1-\epsilon)^{t-1}\le1$、$(H-t+1)\le H$，所以**每一项 $\le\epsilon H$**；一共 **$H$ 项**（$t=1\dots H$，每步都可能是"第一次犯错"的位置）→ $H\times\epsilon H=\epsilon H^2$。所以"$H$ 项、每项 $O(\epsilon H)$"的准确含义是：**不是每项都恰好等于 $\epsilon H$，而是每项都被 $\epsilon H$ 压住。**
> - **三者都受 $O(\epsilon H^2)$ 上界控制**；精确模型的错误数最多为 $H$，不意味着对固定 $\epsilon$、任意大的 $H$ 都按平方增长。② 约 $\tfrac12\epsilon H^2$，③ 是 $\epsilon H^2$。② 的 $\sum_t(H-t+1)=H+(H-1)+\dots+1=\tfrac{H(H+1)}{2}$ 正是公式 17 收尾用的同一个求和。

**走钢丝的直觉**（slide 配的就是走钢丝图）
- 想象走钢丝：只要某一步掉下去，后面**剩下的所有步**都算错。
- 第 $t$ 步以概率 $\sim\epsilon$ 第一次犯错，一旦犯错就掉进训练没覆盖的区域，之后**最多还有 $H-t+1$ 步**全错 → 这一步"贡献"约 $\epsilon\times(H-t+1)\le\epsilon H=O(\epsilon H)$ 个错误。
- 一共有 $H$ 个时间步都可能这样 → 总数 $H\times O(\epsilon H)=O(\epsilon H^2)$。

> 💡 不是"每步只错 $\epsilon$ 那么简单"，而是**一次错误会毁掉后面一整段**，所以错误是平方级增长。

更准确地说，这种无法恢复的最坏过程会给出平方级的上界；现实任务中的错误数不一定照这个速度增长。

---

### 公式 14 · Slide 28：更一般的假设 + 状态分布分解 ⭐ {#formula-14}

> **这条公式在整讲中的任务：** 给出可以使用的已知条件：在每个时间步的专家状态分布上，平均局部误差不超过 epsilon。

**假设**（平均版，比上一页更合理）
$$\mathbb{E}_{\mathbf{s}_t\sim p_{\text{train}}(\mathbf{s}_t)}\big[\pi_\theta(\mathbf{a}_t\neq\pi^\star(\mathbf{s}_t)\mid\mathbf{s}_t)\big]\le\epsilon$$
读："**从训练分布里随机抽一个状态**，平均来看犯错概率不超过 $\epsilon$"（不要求每个状态都满足）。

#### ❗ 先认清 $p_{\pi_\theta}(\mathbf{s}_t)$ 是什么（极易和策略混）

它**不是**"在状态 $\mathbf{s}_t$ 下按 policy 执行某动作的概率"—— 那个是 $\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)$。区别在于**谁是随机变量**：

| 符号 | 随机变量 | 读法 |
|---|---|---|
| $\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)$ | 动作 $\mathbf{a}_t$（$\mathbf{s}_t$ 是给定条件） | "**已经站在** $\mathbf{s}_t$ 上时，选 $\mathbf{a}_t$ 的概率"——每一步**怎么走**的局部规则 |
| $p_{\pi_\theta}(\mathbf{s}_t)$ | 状态 $\mathbf{s}_t$ 自己 | "用 $\pi_\theta$ 从头跑，**第 $t$ 步恰好落在 $\mathbf{s}_t$** 的概率"——跑 $t$ 步后**人散布在哪**的全局结果 |

$p_{\pi_\theta}(\mathbf{s}_t)$ 全名叫**策略诱导的状态边缘分布 / 足迹分布**（state visitation）：下标 $\pi_\theta$ 表示"这分布是谁跑出来的"。它由"初始状态 + 我的策略 $\pi_\theta(\mathbf{a}\mid\mathbf{s})$ + 环境转移 $p(\mathbf{s}_{t+1}\mid\mathbf{s}_t,\mathbf{a}_t)$"一步步滚出来：
$$p_{\pi_\theta}(\mathbf{s}_{t+1})=\sum_{\mathbf{s}_t,\mathbf{a}_t}\underbrace{p(\mathbf{s}_{t+1}\mid\mathbf{s}_t,\mathbf{a}_t)}_{\text{环境转移}}\,\underbrace{\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)}_{\text{我的策略}}\,\underbrace{p_{\pi_\theta}(\mathbf{s}_t)}_{\text{上一步的足迹}}$$

🚗 类比：$\pi_\theta(\mathbf{a}\mid\mathbf{s})$ = "这一下方向盘打多少"；$p_{\pi_\theta}(\mathbf{s}_t)$ = "真开 $t$ 秒后，车可能在哪些位姿、各占多大概率"。策略爱往右偏，这个分布就整体挪向"车在右路肩"。

**先保留原来的直觉：分成“此前从未偏离”与“此前已经偏离”两部分。**

课件／原笔记使用下面这幅简化图景：
$$p_{\pi_\theta}(s_t)=(1-\epsilon)^t p_{\mathrm{train}}(s_t)+\bigl(1-(1-\epsilon)^t\bigr)p_{\mathrm{mistake}}(s_t).$$

这里 $(1-\epsilon)^t$ 是“每步都有相同的条件犯错率 $\epsilon$”的简化模型中，连续 $t$ 次不犯错的概率；只知道平均错误率不超过 $\epsilon$，不能直接推出这个等式。

**更需要小心的是分布本身。** 令 $E_t$ 表示到第 $t$ 步之前没有犯错，$q_t=P(E_t)$。总概率公式确实给出：
$$p_{\pi_\theta}(s_t)=q_t p_{\pi_\theta}(s_t\mid E_t)+(1-q_t)p_{\pi_\theta}(s_t\mid E_t^c).$$

**图中采用的统一式**把这两个互补事件直接写在同一个公式里：
$$p_{\pi_\theta}(s_t)=\underbrace{q_t p_{\pi_\theta}(s_t\mid E_t)}_{\text{此前一次都没有错}}+\underbrace{(1-q_t)p_{\pi_\theta}(s_t\mid E_t^c)}_{\text{此前至少错过一次}}.$$
两种情况的权重加起来为 1；这里的“此前”指前 $t-1$ 步。下一步比较执行与专家状态分布时，要先把二者放到同一个耦合中。

但 $p_{\pi_\theta}(s_t\mid E_t)$ 一般不等于无条件的专家分布 $p_{\mathrm{train}}(s_t)$：较容易犯错的轨迹被“此前无错”这个条件筛掉了。**即使到现在没错，也不能把条件分布自动替换为原始专家分布。**

> **这版采用的严格路线：**保留混合式帮助想象“偏离事件”，实际的距离上界用下一条公式中的**耦合 + union bound**来证明，不依赖上面那个固定权重等式。

---

### 公式 15 · Slide 29：用 total variation 证 $D_{TV}\le\epsilon t$ ⭐⭐ {#formula-15}

> **这条公式在整讲中的任务：** 把“走偏”变成可用的分布距离上界，给公式 16 的差价项提供一个尺度。

**总变差距离的定义**
$$D_{\mathrm{TV}}(p,q)=\frac12\sum_x\big|p(x)-q(x)\big|\ \le\ 1$$
- 衡量两个分布差多远；恒在 $[0,1]$ 之间（因为两个概率分布最多差到完全不重叠）。
- 那个 $\tfrac12$ 不是随便放的：两分布各自加起来都 = 1，"多出来的"和"少掉的"一样多，$\sum|p-q|$ 把同一笔差距数了**两遍**，除以 2 正好。
- 一句话直觉：**"要把 p 这堆沙子搬成 q，至少得搬走多少比例的沙。"**

**目标**：量化专家状态分布 $p_{\mathrm{train}}(s_t)$ 与策略状态分布 $p_{\pi_\theta}(s_t)$ 的距离。

#### 第一步：让两次执行共享随机性（耦合）

想象同时运行专家和学生：从同一个初始状态出发，共享环境的随机性。只要学生还没选出与专家不同的动作，两者就进入相同的下一个状态。

因此，**第 $t$ 步出现不同状态，需要在前 $t-1$ 步至少出现一次动作分歧**。构造这样的联合执行方式，不会改变专家与学生各自的边缘状态分布。

**统一分解怎样得到分布之差？** 在这个耦合下，$E_t$ 发生时，两条执行的当前状态相同，因此它们共享同一个条件分布 $p_{\mathrm{ok}}$。分别记 $E_t^c$ 下学生、专家的条件状态分布为 $p_{\mathrm{err}}^\pi$、$p_{\mathrm{err}}^\star$（这里“出错”一直指学生）：
$$\begin{aligned}
p_{\pi_\theta}&=q_t p_{\mathrm{ok}}+(1-q_t)p_{\mathrm{err}}^\pi,\\
p_{\mathrm{train}}&=q_t p_{\mathrm{ok}}+(1-q_t)p_{\mathrm{err}}^\star.
\end{aligned}$$
两式相减，**此前一直没错的共同部分消掉**：
$$p_{\pi_\theta}-p_{\mathrm{train}}=(1-q_t)(p_{\mathrm{err}}^\pi-p_{\mathrm{err}}^\star).$$
所以
$$D_{\mathrm{TV}}(p_{\pi_\theta},p_{\mathrm{train}})=(1-q_t)D_{\mathrm{TV}}(p_{\mathrm{err}}^\pi,p_{\mathrm{err}}^\star)\le1-q_t.$$
零权重分支的条件分布可以任意选取；它对上述混合没有贡献。

#### 第二步：用 union bound 估计分歧概率

在每条专家轨迹的第 $k$ 步，让学生对那个专家状态试选一个动作；记与专家不同的事件为 $B_k$。公式 14 的平均假设给出 $P(B_k)\le\epsilon$。耦合中的第一次分歧一定属于这些事件之一，所以：
$$1-q_t=P(E_t^c)\le P\!\left(\bigcup_{k=1}^{t-1}B_k\right)\le\sum_{k=1}^{t-1}P(B_k)\le(t-1)\epsilon.$$

这一步不要求错误事件独立，也不要求每个状态都有相同犯错率。

#### 第三步：把执行差异变成分布距离

总变差距离不超过任意耦合下“两个随机变量不同”的概率。因此：
$$\boxed{D_{\mathrm{TV}}\bigl(p_{\mathrm{train}}(s_t),p_{\pi_\theta}(s_t)\bigr)\le\min\{1,(t-1)\epsilon\}\le\epsilon t.}$$

这里 $t-1$ 来自“到状态 $s_t$ 时已经执行了多少次动作”。原笔记采用较松的 $\epsilon t$，公式 16–17 沿用它即可，不影响平方级上界。

> **一句话接回主线：**原来只知道专家足迹上每步错得少；现在知道学生的足迹最多能偏离多少。这个距离正是下一步“差价项”需要的量。

这条路线是本页补充的逐时刻证明。原始上界证明同样区分“此前无错”条件下的状态分布与无条件专家分布，并累计各步分歧概率；核对见 [Ross 与 Bagnell（2010）的补充证明，Theorem 2.1](https://www.cs.cmu.edu/~sross1/publications/Ross-AIStats10-sup.pdf)。这里进一步用耦合的语言把它接到总变差距离。

<details>
<summary>回看原笔记的代数推导：固定权重混合模型下怎样得到同一个松上界</summary>

若额外假定公式 14 的简化混合等式成立，令 $\alpha=1-(1-\epsilon)^t$，则
$$\begin{aligned}
D_{\mathrm{TV}}(p_{\mathrm{train}},p_{\pi_\theta})
&=\frac12\sum_s\left|p_{\mathrm{train}}-(1-\alpha)p_{\mathrm{train}}-\alpha p_{\mathrm{mistake}}\right|\\
&=\alpha\cdot\frac12\sum_s|p_{\mathrm{train}}-p_{\mathrm{mistake}}|\\
&=\alpha D_{\mathrm{TV}}(p_{\mathrm{train}},p_{\mathrm{mistake}})\\
&\le\alpha=1-(1-\epsilon)^t\le\epsilon t.
\end{aligned}$$

关键凑项仍是 $p_{\mathrm{train}}-(1-\alpha)p_{\mathrm{train}}=\alpha p_{\mathrm{train}}$，再把 $\alpha$ 从绝对值里提出。

最后使用的是**伯努利不等式** $(1-\epsilon)^t\ge1-t\epsilon$。在等条件错误率的简化模型下，也可以用“至少一次错误”的 union bound 理解 $1-(1-\epsilon)^t\le t\epsilon$。

这段代数本身没有问题；限制在于第一行使用的混合等式需要额外条件。

</details>

---

### 公式 16 · Slide 30：把总错误拆成两块 {#formula-16}

> **这条公式在整讲中的任务：** 用加减同一项，把按学生分布计算的错误改写为按专家分布计算的错误，再单独计算差价。

$$\begin{aligned}
&\sum_{t=1}^{H}\mathbb{E}_{\mathbf{a}_t\sim\pi_\theta,\ \mathbf{s}_t\sim p_{\pi_\theta}}\big[c(\mathbf{s}_t,\mathbf{a}_t)\big]\\[4pt]
=\ &\sum_{t=1}^{H}\sum_{\mathbf{s}_t}p_{\pi_\theta}(\mathbf{s}_t)\,\mathbb{E}_{\mathbf{a}_t\sim\pi_\theta}\big[c(\mathbf{s}_t,\mathbf{a}_t)\big] &&\text{(期望写成对状态加权求和)}\\[4pt]
=\ &\sum_{t=1}^{H}\sum_{\mathbf{s}_t}\big(\,p_{\text{train}}(\mathbf{s}_t)+\underbrace{p_{\pi_\theta}(\mathbf{s}_t)-p_{\text{train}}(\mathbf{s}_t)}_{\text{加一项又减一项}}\,\big)\,\mathbb{E}\big[c\big] &&\text{(加 }p_{\text{train}}\text{ 再减 }p_{\text{train}}\text{)}\\[4pt]
\le\ &\sum_{t=1}^{H}\sum_{\mathbf{s}_t}\big(\,p_{\text{train}}(\mathbf{s}_t)+\big|p_{\pi_\theta}(\mathbf{s}_t)-p_{\text{train}}(\mathbf{s}_t)\big|\,\big)\,\mathbb{E}\big[c\big] &&\text{(取绝对值做上界)}\\[4pt]
=\ &\sum_{t=1}^{H}\Big[\underbrace{\sum_{\mathbf{s}_t}p_{\text{train}}(\mathbf{s}_t)\mathbb{E}[c]}_{\text{第一块：训练分布上的基础误差}}+\underbrace{\sum_{\mathbf{s}_t}\big|p_{\pi_\theta}(\mathbf{s}_t)-p_{\text{train}}(\mathbf{s}_t)\big|\,\mathbb{E}[c]}_{\text{第二块：分布偏移带来的额外误差}}\Big]
\end{aligned}$$

**这一步在干嘛**：用"加一项又减一项"的经典技巧，把"在错误分布 $p_{\pi_\theta}$ 上的误差"拆成
**"假装还在训练分布上的误差" + "因为偏离训练分布而多出来的误差"**。

> 🎯 **为什么非要拆（笔记最该记的动机）**：我们手上两个武器各自只认**自己的分布**——
> - 公式 14 的"犯错率 $\le\epsilon$"只在 $p_{\text{train}}$ 上成立；
> - 但公式 12 的总错误是按 $p_{\pi_\theta}$ 加权的。
>
> 矛盾：想用 $\le\epsilon$，它却只认 $p_{\text{train}}$。加减项就是把"按 $p_{\pi_\theta}$ 加权"**硬掰回"按 $p_{\text{train}}$ 加权" + 付一笔差价**。这笔差价 $|p_{\pi_\theta}-p_{\text{train}}|$ 恰好就是公式 15 量好的 $2D_{TV}$。所以公式 16 本质是个**转接头**：把总错误接到 14 和 15 这两个已备好的上界上。

> 🔧 **两个小步的细节**：
> - **第 2 行**（期望→加权求和）：$\mathbb{E}_{\mathbf{s}_t\sim p_{\pi_\theta}}[\cdot]=\sum_{\mathbf{s}_t}p_{\pi_\theta}(\mathbf{s}_t)[\cdot]$，里面那块 $\mathbb{E}_{\mathbf{a}_t\sim\pi_\theta}[c]$ 正是公式 11 的"该状态犯错率"。
> - **第 4 行**（出现 $\le$）：$p_{\pi_\theta}-p_{\text{train}}$ 可能为负，但 $\mathbb{E}[c]\ge0$，换成绝对值 $|p_{\pi_\theta}-p_{\text{train}}|$ 只会变大→合法上界；换绝对值也正是为了凑出公式 15 的 $D_{TV}=\tfrac12\sum|\cdot|$ 形状。

> 🔜 **两块各等谁来收**：第一块 $\sum p_{\text{train}}\mathbb{E}[c]\le\epsilon$（公式 14）；第二块里 $\sum|p_{\pi_\theta}-p_{\text{train}}|=2D_{TV}\le2\epsilon t$（公式 15）。公式 17 代数字收口成 $O(\epsilon H^2)$。

#### 🔢 具象版：用一组数字把每一步"看见"

设第 $t$ 步只可能落在 3 个状态：**A、B（熟悉的路）** 和 **C（没训练过的野地）**。三样东西如下表——注意野地 C 犯错率高达 0.9，专家几乎不去（0.1），但**学生老往 C 飘（0.5）**，这就是分布偏移：

| 状态 | 该状态犯错率 $\mathbb{E}_{a\sim\pi}[c]$ | 专家足迹 $p_{\text{train}}$ | 学生足迹 $p_{\pi_\theta}$ | 差 $p_{\pi_\theta}-p_{\text{train}}$ |
|---|---|---|---|---|
| A（熟） | 0.1 | 0.5 | 0.2 | −0.3 |
| B（熟） | 0.2 | 0.4 | 0.3 | −0.1 |
| C（野地） | **0.9** | 0.1 | **0.5** | **+0.4** |

**第 2 行**——学生真实犯错率（按 $p_{\pi_\theta}$ 加权，纯改写）：
$$0.2(0.1)+0.3(0.2)+0.5(0.9)=0.02+0.06+0.45=\mathbf{0.53}$$

**卡住点**——我们唯一能证的上界（按 $p_{\text{train}}$ 加权，公式 14）只到：
$$0.5(0.1)+0.4(0.2)+0.1(0.9)=0.05+0.08+0.09=\mathbf{0.22}$$
学生真实错 0.53，武器只管到 0.22，差的 0.31 全因"站错地方"（老去 C）。

**第 3 行**——加减 $p_{\text{train}}$，把 0.53 **精确**劈成两半（等号，一分不差）：
$$0.53=\underbrace{0.22}_{\sum p_{\text{train}}\mathbb{E}[c]}+\underbrace{(-0.3)(0.1)+(-0.1)(0.2)+(0.4)(0.9)}_{=\,-0.03-0.02+0.36\,=\,0.31}$$

**第 4 行**——差价取绝对值，0.31 放大成上界 0.41（这里才出现 $\le$）：
$$\sum|p_{\pi_\theta}-p_{\text{train}}|\,\mathbb{E}[c]=(0.3)(0.1)+(0.1)(0.2)+(0.4)(0.9)=0.03+0.02+0.36=\mathbf{0.41}\ \ge\ 0.31$$
因为 $\mathbb{E}[c]\ge0$，负差换成正的只会变大 → 合法上界；且带上绝对值后 $\sum|p_{\pi_\theta}-p_{\text{train}}|=0.8=2D_{TV}$，才能接公式 15。

**第 5 行**——分两块、各自交人：$\text{学生的错}\le\underbrace{0.22}_{\le\epsilon\,(\text{公式 14})}+\underbrace{0.41}_{\le\,2D_{TV}\le2\epsilon t\,(\text{公式 15})}$

| 行 | 动作 | 这例子里 | 性质 |
|---|---|---|---|
| 2 | 期望摊成加权和 | 学生真实错 = 0.53 | 纯改写 |
| 3 | 加减 $p_{\text{train}}$ | 0.53 = 0.22 + 0.31 | **精确**等号 |
| 4 | 差价取绝对值 | 0.31 → 0.41 | 放大成**上界 $\le$** |
| 5 | 分两块 | $\le$ 0.22 + 0.41 | 各交公式 14 / 15 |

> 💡 一句话：**公式 16 把"学生站错地方导致的多余错误"单独拎出来记账**，好让公式 14 管"基础错"、公式 15 管"站错地方的差价"。

---

### 公式 17 · Slide 31：收尾 → $O(\epsilon H^2)$ ⭐⭐⭐ {#formula-17}

> **这条公式在整讲中的任务：** 分别压住两项，再对时间求和，把所有局部工具收成总错误上界。

> **更紧的常数（可选）：**对 $0\le f(s)\le1$，两分布下期望之差可直接用 $D_{\mathrm{TV}}$ 而非 $2D_{\mathrm{TV}}$ 控制。原笔记取绝对值的路线较松，但合法，足以得到本讲关心的量级。

**第一块**（基础误差）正好是公式 14 的假设：
$$\sum_{\mathbf{s}_t}p_{\text{train}}(\mathbf{s}_t)\,\mathbb{E}[c]=\mathbb{E}_{\mathbf{s}_t\sim p_{\text{train}}}\big[\pi_\theta(\mathbf{a}_t\neq\pi^\star\mid\mathbf{s}_t)\big]\le\epsilon$$

**第二块**（分布偏移误差）：因为代价 $\mathbb{E}[c]\le 1$，
$$\sum_{\mathbf{s}_t}\big|p_{\pi_\theta}-p_{\text{train}}\big|\cdot\mathbb{E}[c]\ \le\ \sum_{\mathbf{s}_t}\big|p_{\pi_\theta}-p_{\text{train}}\big|\ =\ 2\,D_{\mathrm{TV}}(p_{\pi_\theta},p_{\text{train}})\ \le\ 2\epsilon t$$
（最后一步用了公式 15 的 $D_{TV}\le\epsilon t$；前面的 2 是因为 $D_{TV}$ 定义里有个 $\tfrac12$，去掉就乘 2。）

**所以第 $t$ 步的误差上界**：
$$\epsilon\ +\ 2\epsilon t$$

**对 $t=1$ 到 $H$ 求和**：
$$\sum_{t=1}^{H}(\epsilon+2\epsilon t)
=\epsilon H+2\epsilon\sum_{t=1}^{H}t
=\epsilon H+2\epsilon\cdot\frac{H(H+1)}{2}
=\epsilon H+\epsilon H(H+1)
=O(\epsilon H^2)$$

$$\boxed{J(\pi_\theta)\le\min\{H,\epsilon H+\epsilon H(H+1)\}=O(\epsilon H^2).}$$

> **读上界时的限制：**这是允许最坏后果的上界，不是每个任务都恰好有这么多错误。0/1 代价下总错误最多为 $H$；当平方项大于 $H$ 时，上界变得宽松。

> 🟨 slide 黄框结论：**error increases quadratically with horizon（误差随 horizon 平方增长）。**
> 用到的求和公式：$\sum_{t=1}^H t=\dfrac{H(H+1)}{2}$。
> 出处：Ross et al., *"A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning"*（即 DAgger 论文）。

**一句话浓缩整段**：
$$\text{总错误}=\underbrace{\text{训练分布上的基础错误}}_{\text{每步}\approx\,\epsilon}+\underbrace{\text{分布偏移的额外错误}}_{\text{每步}\approx\,O(\epsilon t)}\ \Rightarrow\ O(\epsilon H^2)$$

---

### 公式 18 · Slide 32：为什么这个上界"偏悲观" {#formula-18}

> **这条公式在整讲中的任务：** 读清上界的含义：它允许犯错后无法恢复；实际能恢复时，表现可以明显好于这个最坏上界。

- 这套分析默认得很坏：**一旦犯一次错，就掉进任意糟的 $p_{\text{mistake}}$，之后一路错。**
- 现实里很多系统**能从偏差里恢复**（车偏了，好司机能打方向盘救回来）。slide: "In reality, we can often recover from mistakes."
- 但 BC 未必学得到恢复能力 —— 如果训练数据全是"专家完美轨迹"，模型根本没见过"偏了怎么救"。
- **反直觉结论（slide 黄框）**：数据里**包含更多 mistakes and recoveries，模仿学习反而可能更好**，因为模型这才见过"恢复动作"长什么样。

---

## Part 5：能不能做得比 BC 更好（DAgger）

### 公式 19 · Slide 36：我们到底想要什么 {#formula-19}

> **这条公式在整讲中的任务：** 把失败原因翻成修复目标：训练数据应覆盖策略自己真正会遇到的输入。

$$\text{can we make}\quad p_{\text{data}}(\mathbf{o}_t)=p_{\pi_\theta}(\mathbf{o}_t)\ ?$$
- 既然问题是"训练分布 $p_{\text{data}}$ ≠ 执行分布 $p_{\pi_\theta}$"，那能不能干脆让两者**相等**？

### 公式 20 · Slide 37：DAgger 算法 {#formula-20}

> **这条公式在整讲中的任务：** 实现这个修复目标：学习者访问状态，专家提供标签，数据聚合后重新训练。

> **核心思路**：与其费劲改造 $p_{\pi_\theta}$（让策略别偏），不如反过来改造 $p_{\text{data}}$ —— **让训练数据本身就来自 $p_{\pi_\theta}$**。
> DAgger = **D**ataset **Agg**regation（数据集聚合）。

$$\begin{aligned}
&1.\ \text{用人类数据 }\mathcal{D}=\{\mathbf{o}_1,\mathbf{a}_1,\dots,\mathbf{o}_N,\mathbf{a}_N\}\ \text{训练 }\pi_\theta(\mathbf{a}_t\mid\mathbf{o}_t)\\
&2.\ \text{跑 }\pi_\theta(\mathbf{a}_t\mid\mathbf{o}_t)\ \text{收集观测 }\mathcal{D}_\pi=\{\mathbf{o}_1,\dots,\mathbf{o}_M\}\\
&3.\ \text{请专家标注动作，形成 }\widetilde{\mathcal{D}}_\pi=\{(\mathbf{o}_j,\mathbf{a}_j^\star)\}_{j=1}^M\\
&4.\ \text{聚合：}\ \mathcal{D}\leftarrow\mathcal{D}\cup\widetilde{\mathcal{D}}_\pi\quad(\text{回到第 1 步循环})
\end{aligned}$$

**为什么针对了问题**：第 2 步收集的观测来自**当前策略自己跑出的分布**；第 3 步给这些观测配上专家动作。它逐轮扩展“策略真正会遇到的状态”的覆盖。

**聚合时存的是专家标签对：**令 $\widetilde{\mathcal D}_\pi=\{(o_j,a_j^\star)\}_{j=1}^M$，再做 $\mathcal D\leftarrow\mathcal D\cup\widetilde{\mathcal D}_\pi$；只存学生自己选的动作，不能提供正确的恢复标签。这里假定专家能够根据观测或相应状态提供动作。

**分布相等是动机，不是每轮的保证。**聚合数据包含历次策略的访问分布，策略本身也在改变；有限轮训练不会自动保证 $p_{\mathrm{data}}=p_{\pi_\theta}$。原始算法也允许早期混合专家与学习者执行，并逐步减弱专家的参与。理论保证需要在线学习等相应条件。
- 痛点（slide "What's the problem?"）：第 3 步要人类**对策略跑出来的观测逐个标注动作**，很费人力、且有些状态人类离线标也很别扭。
- 常见变体（slide）：不让人事后标，而是**让人在策略跑的过程中随时接管（take over）**，把人接管时的 $(\mathbf{o}_t,\mathbf{a}_t)$ 存下来当数据。

---


## 全公式速查：从目的找公式 {#formula-index}

| 公式 | 它在整讲中的任务 | 关键对象或结论 |
|---|---|---|
| [1](#formula-1) | 建立监督学习训练规则 | 最大化标签的对数似然 |
| [2](#formula-2) | 定义待学习的策略 | $\pi_\theta(a_t\mid o_t)$ |
| [3](#formula-3) | 说明动作影响未来输入 | 转移模型与观测模型 |
| [4](#formula-4) | 接通观测与状态的写法 | 完全可观测时 $o_t=s_t$ |
| [5](#formula-5) | 在专家轨迹上拟合动作 | $\sum_i\sum_t\log\pi_\theta(a_t^{(i)}\mid o_t^{(i)})$ |
| [6](#formula-6) | 表示离散动作分布 | softmax |
| [7](#formula-7) | 表示连续动作密度 | $\mathcal N(a_t\mid\mu(o_t),\Sigma(o_t))$ |
| [8](#formula-8) | 把密度模型接到回归损失 | $\log p=-\frac12\|a-\mu\|^2+\mathrm{const}$，固定 $\Sigma=I$ |
| [9](#formula-9) | 定义分布偏移 | $p_{\mathrm{train}}\ne p_{\mathrm{test}}$ |
| [10](#formula-10) | 找到 BC 的关键缺口 | 专家足迹与学生足迹不同 |
| [11](#formula-11) | 定义局部错误 | 0/1 代价的期望等于犯错概率 |
| [12](#formula-12) | 定义部署时的目标量 | 在学生足迹上累计 $H$ 步代价 |
| [13](#formula-13) | 建立误差累积直觉 | 第一次错会影响后面一段 |
| [14](#formula-14) | 提供专家分布上的已知条件 | 每步平均误差 $\le\epsilon$；混合式需额外条件 |
| [15](#formula-15) | 量化状态分布差异 | $D_{\mathrm{TV}}\le\epsilon t$，采用耦合与 union bound |
| [16](#formula-16) | 把目标量接到已知条件 | 加减 $p_{\mathrm{train}}$，拆成基础项与差价项 |
| [17](#formula-17) | 收口整段证明 | $J(\pi_\theta)=O(\epsilon H^2)$ 的最坏上界 |
| [18](#formula-18) | 解释上界与现实的距离 | 恢复能力与恢复数据 |
| [19](#formula-19) | 提出修复目标 | 数据覆盖策略实际遇到的状态 |
| [20](#formula-20) | 把修复变成算法 | 自己访问 → 专家标注 → 聚合 → 再训练 |

## 自测：先接主线，再核对局部 {#self-check}

先盖住答案。只看图 1，试着讲清事件分解、分布距离与误差拆账；再选择自己卡住的题目。

<div class="lecture-checks">

<details>
<summary>主线 1：BC 明明在做监督学习，为什么单步预测好还不够？</summary>

BC 的拟合方法是监督学习，但部署输入由自己的动作逐步影响。专家状态分布上的低错误率，不能直接保证在学生自己的状态分布上也低。

</details>

<details>
<summary>主线 2：为什么公式 16 要加一项又减一项？</summary>

待控制的总错误按 $p_{\pi_\theta}$ 加权；已知的 $\epsilon$ 只适用于 $p_{\mathrm{train}}$。加减项把它拆成一个能用已知条件的基础项，再用分布距离支付差价。

</details>

<details>
<summary>主线 3：平方级上界里的两次“时间”分别来自哪里？</summary>

到第 $t$ 步之前出现分歧的机会随 $t$ 增加，分布距离上界是 $O(\epsilon t)$；再把各步的代价上界从 1 加到 $H$，就得到 $O(\epsilon H^2)$。它是最坏上界，总错误数仍不超过 $H$。

</details>

<details>
<summary>主线 4：DAgger 采到学生的错误动作后，直接拿它当标签吗？</summary>

采集学生访问到的状态／观测，请专家为这些输入提供正确动作，再聚合训练。访问分布来自学生，标签来自专家。

</details>

<details>
<summary>局部 1：arg max 和 max 分别返回什么？</summary>

max 返回最大值，arg max 返回取得该值的参数。我们要学习的是参数 $\theta$，所以用 arg max。

</details>

<details>
<summary>局部 2：策略里的竖线是什么？上标 (i) 与下标 t 又分别数什么？</summary>

$\mid$ 表示“给定”条件。$\pi_\theta(a_t\mid o_t)$ 是给定观测时的动作分布；$(i)$ 数第几条轨迹，$t$ 数轨迹内第几步。

</details>

<details>
<summary>局部 3：BC 为什么有两层求和？</summary>

外层遍历 $N$ 条轨迹，内层遍历每条轨迹的 $H$ 步；每个观测与对应的专家动作都产生一个拟合项。

</details>

<details>
<summary>局部 4：0/1 代价的期望为什么等于犯错概率？</summary>

只有犯错动作的代价是 1，其余是 0。概率乘代价再相加，只留下全部犯错动作的概率之和。

</details>

<details>
<summary>局部 5：一直没错的概率一定是 (1−ε) 的 t 次方吗？</summary>

若每一步在此前无错条件下的犯错率都恰好为 $\epsilon$，可用概率链式法则得到这个乘积。仅有专家分布上的平均误差上界时，不能直接写等号；无错条件下的状态分布也不能自动当作无条件专家分布。

</details>

<details>
<summary>局部 6：DAgger 想改变谁的分布，靠哪一步？</summary>

它通过“运行当前策略、收集其观测、请专家标注”扩展训练数据的覆盖，使训练关注策略实际遇到的状态。聚合后的分布不保证每轮都与当前策略分布严格相等。

</details>

</div>

## 这版学习结构，接下来怎样一起改 {#learning-method}

这次沿用 Learn Claude Code 的“整体定位 → 局部展开 → 回到主线”，把局部展开的单位换成公式。当前试用的读法是：**先讲清问题，找到公式的位置，再逐行检查，最后闭卷接回前后两步。**

要判断这种结构是否适合这门课，可以先看两个结果：读完顶部后，能否说出 BC 到 DAgger 的因果链；读完核心推导后，能否解释“为什么要换分布、为什么要加减一项”。这比只检查是否认识每个符号，更能检验整讲有没有连起来。

如果主线仍散，就优先改顶部图的节点与箭头；如果主线已经清楚、局部仍卡，就从那条公式加入更多数值例子或中间步骤。当前是一版可共同修改的组织方式，学习效果要在实际阅读中检验。

[回到整讲主线 ↑](#lecture-thread) · [回到证明关系图 ↑](#proof-route)

## 材料与校正范围 {#sources}

主体来自你的《Lecture2 公式逐行拆解》，保留 20 条公式及主要的符号释义、直觉和数值例子；本地拓展笔记仅保留名称，尚未迁入网站。主线图、公式用途、证明关系图是这一版新增的阅读组织。

网页版本校正了连续密度与离散概率的区别、公式 14 的混合式条件、公式 15 的有效证明路线、平方级上界的适用解释，以及 DAgger 的专家标签与聚合分布。原始本地笔记保持原样。

核对参考：[Ross、Gordon、Bagnell 的 DAgger 原论文](https://publications.ri.cmu.edu/storage/publications/pub_files/2011/4/Ross-AISTATS11-NoRegret.pdf)（专家分布与策略分布、行为克隆上界及聚合算法），[CS285 课程入口](https://rail.eecs.berkeley.edu/deeprlcourse-fa23/)（课程主题参考；本页页码沿用本地笔记）。
