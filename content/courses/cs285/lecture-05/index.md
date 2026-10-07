---
title: "Lecture 5 · 从期望回报到策略梯度"
description: "先逐步推导 REINFORCE，再解释 baseline、reward-to-go 与伪损失。每个知识节点旁都有公式，点击可进入详细拆解。"
date: 2026-10-07
weight: 50
math: true
ShowToc: false
tags: [CS285, Policy Gradients, REINFORCE]
---

## 先看清这一讲在做什么 {#lecture-thread}

本讲主题：**Policy Gradients（策略梯度）**。Lecture 2 用专家动作当标签；这一讲只有策略自己采到的轨迹与奖励，要找到参数朝哪个方向移动，才能提高**期望回报**。

主线按推导依赖展开：**定义目标与轨迹分布 → 按期望定义展开为积分 → 对积分求导 → 代入 log-derivative trick → 认出期望结构 → 写回期望 → 展开轨迹概率、留下策略项 → 采样更新 → 降噪与实现。** 每一步先明确缺什么，再引入解决它的公式。

本页沿用原笔记的记号：$r(\tau)$ 是整条轨迹的总奖励，$\hat Q_t$ 是从当前步开始的剩余回报。策略的 log 概率梯度始终完整写成 $\nabla_\theta\log\pi_\theta(a_t\mid s_t)$。

{{< lecture-mindmap id="policy-gradient-flow" cards="argument-cards.json" width="1660" caption="先把目标变成可采样的梯度，再检查估计器的噪声。期望展开、求导、代入恒等式、识别期望结构与写回期望分别成节点。baseline 与因果性各自证明后，再合并到原笔记的伪目标。蓝色为定义和改写，橙色为困难与降噪，紫色为梯度结果和实现。点击节点阅读逐行拆解，窄屏可在图内左右滑动。" >}}

### 把这条主线接成一段话

参数变化不仅改变动作概率，还会改变实际采到哪些轨迹，因此求导必须处理 $p_\theta(\tau)$。log-derivative trick 将 $\nabla p_\theta$ 变为 $p_\theta\nabla\log p_\theta$，使积分重新具有期望的形状。

再展开轨迹的 log 概率：固定轨迹时，初始分布与环境转移不显式依赖策略参数，留下 $\sum_t\nabla\log\pi_\theta$。把它乘以回报并求样本平均，就得到最基本的 REINFORCE 更新。

接下来解决样本噪声。baseline 改变参考值，reward-to-go 去掉当前动作之前的奖励；两者都要先说明合法条件，再合并成每步权重。最后构造伪目标，再取负值作为优化器的 loss，并停止权重梯度，让自动微分完成同一个更新。

| 当前卡点 | 去哪里看 |
|---|---|
| 为什么要对分布求导 | [公式 1](#formula-1) → [公式 2](#formula-2) → [公式 5](#formula-5) |
| log-trick 为什么成立、为什么要用 | [公式 4](#formula-4) → [链式法则精读](#log-derivative-detail) |
| 环境未知怎么还能算梯度 | [公式 6](#formula-6) → [公式 7](#formula-7) |
| baseline 与未来奖励为什么可以改 | [baseline 证明](#baseline-proof) → [公式 13](#formula-13) |
| 公式怎样变成一个 loss | [公式 14](#formula-14) → [完整更新](#implementation-loop) |

<details>
<summary>展开全页目录与公式索引</summary>

{{< chapter-outline id="lecture5-outline" title="Lecture 5 阅读位置" >}}

</details>

## 先认清符号与推导范围 {#notation}

本页按本地《Lecture5 公式逐行拆解》的 14 条公式组织，并收录配套的链式法则精读。Slide 编号沿用原笔记，未据此指定课件年份。

分析采用有限时域、无折扣回报；策略可微，初始分布、环境转移和奖励在固定轨迹时不显式依赖策略参数。默认满足交换求导与积分所需的正则条件，log-trick 用于正密度的支持上。轨迹包含最后一次转移后的状态 $s_{H+1}$。

| 符号 | 读法 | 意思 |
|---|---|---|
| $\theta$ | theta | 策略网络的参数，要学的东西 |
| $\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)$ | pi-theta | 策略：状态 $\mathbf{s}_t$ 下选动作 $\mathbf{a}_t$ 的概率 |
| $\tau$ | tau | **一整条轨迹（含终止状态）** $(\mathbf{s}_1,\mathbf{a}_1,\dots,\mathbf{s}_H,\mathbf{a}_H,\mathbf{s}_{H+1})$，一个符号代表一整串 |
| $p_\theta(\tau)$ | — | 用 $\pi_\theta$ 跑出轨迹 $\tau$ 的概率（策略+环境共同决定） |
| $r(\mathbf{s}_t,\mathbf{a}_t)$ | — | 单步奖励 |
| $r(\tau)$ | — | 整条轨迹的总奖励 $=\sum_{t=1}^H r(\mathbf{s}_t,\mathbf{a}_t)$（简写） |
| $J(\theta)$ | — | RL 目标函数：期望总奖励 |
| $\nabla_\theta$ | nabla / 梯度 | 对 $\theta$ 求梯度（一个和 $\theta$ 同形状的向量） |
| $\alpha$ | alpha | 学习率（步长） |
| $H$ | — | horizon，轨迹长度 |
| $N$ | — | 采样的轨迹条数 |
| 上标 $(i)$ | i | 第几条轨迹；下标 $t$：轨迹里第几步 |
| $\hat{Q}_t^{(i)}$ | Q-hat | reward-to-go：第 $i$ 条轨迹从第 $t$ 步起的剩余奖励 |
| $b$ | — | baseline（基线），从奖励里减掉的参考值 |
| $\sim$ | "采样自" | $\tau\sim p_\theta(\tau)$：轨迹从分布 $p_\theta$ 里抽出来 |
| $\mathbb{E}$ | 期望 | 加权平均 |
| $\int\cdots d\tau$ | 积分 | 连续版的"对所有可能轨迹求和" |

---

## Part 1：REINFORCE——最基本的策略梯度

### 公式 1 · Slide 3：RL 的目标函数 {#formula-1}

> **这条公式在整讲中的任务：** 定义真正要优化的量，并看清轨迹分布本身也依赖参数。

$$\theta^\star=\arg\max_\theta\;\mathbb{E}_{\tau\sim p_\theta(\tau)}\left[\sum_{t=1}^H r(\mathbf{s}_t,\mathbf{a}_t)\right]$$

**怎么读**："找到那个 θ，使得『按 $p_\theta$ 采样轨迹时，轨迹总奖励的期望』最大。"

**逐符号拆**
- $\arg\max_\theta$ —— 返回**取得最大值的那个 θ**（不是最大值本身）。
- $\mathbb{E}_{\tau\sim p_\theta(\tau)}[\cdot]$ —— 期望的下标写明：轨迹 $\tau$ 是**用当前策略自己跑出来的**。这是 RL 和监督学习最大的不同——**数据分布依赖于 θ 本身**。
- $\sum_{t=1}^H r(\mathbf{s}_t,\mathbf{a}_t)$ —— 把一条轨迹每一步的奖励加起来 = 总奖励。

> 🔑 **和 lec2 公式 1 对照**：监督学习最大化 $\sum\log p_\theta(y\mid x)$，数据分布固定；RL 最大化 $\mathbb{E}_{\tau\sim p_\theta}[r]$，**θ 一变，期望底下的分布也跟着变**。整讲的数学难点全部来自这一点。

> **与期望法则的连接：**直接在轨迹分布上计算 $\mathbb E[r(\tau)]=\int p_\theta(\tau)r(\tau)d\tau$，可以保留策略参数如何改变轨迹权重。先求回报分布也是合法的期望计算方式，本讲使用轨迹形式来推梯度。

---

### 公式 2 · Slide 3：轨迹的概率（链式分解） {#formula-2}

> **这条公式在整讲中的任务：** 把轨迹概率拆成策略因子与环境因子，为后面识别哪些项有梯度做准备。

$$\underbrace{p_\theta(\mathbf{s}_1,\mathbf{a}_1,\dots,\mathbf{s}_H,\mathbf{a}_H,\mathbf{s}_{H+1})}_{p_\theta(\tau)}=p(\mathbf{s}_1)\prod_{t=1}^{H}\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)\,p(\mathbf{s}_{t+1}\mid\mathbf{s}_t,\mathbf{a}_t)$$

**怎么读**："一条轨迹的概率 = 初始状态的概率 × 每一步『策略选这个动作的概率 × 环境转到下个状态的概率』连乘。"

**逐符号拆**
- $p(\mathbf{s}_1)$ —— 初始状态分布，**环境给的，跟 θ 无关**。
- $\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)$ —— **唯一带 θ 的因子**。记住这一点，公式 6 划掉两项的魔法全靠它。
- $p(\mathbf{s}_{t+1}\mid\mathbf{s}_t,\mathbf{a}_t)$ —— 环境转移（dynamics），**也跟 θ 无关，而且我们不知道它**。
- $\prod_{t=1}^H$ —— 连乘号，沿时间步把每一步的两个因子乘起来。

**直觉**：轨迹是"我选一步 + 世界回一步"交替出来的，所以概率就是两种因子交替连乘。马尔可夫性保证每个因子只看当前一步。

> ⚠️ **slide 小笔误**：Slide 6 上同一个式子左边写成 $p_\theta(\mathbf{s}_1,\mathbf{a}_1,\dots,\mathbf{s}_T,\mathbf{a}_T)$（用了 $T$），连乘上限却是 $H$。$T$ 和 $H$ 是同一个东西（horizon），本笔记统一用 $H$。

---

### 公式 3 · Slide 4：评估目标 = 蒙特卡洛采样 {#formula-3}

> **这条公式在整讲中的任务：** 把不可直接精确计算的期望，接到实际运行策略得到的样本平均。

$$J(\theta)=\mathbb{E}_{\tau\sim p_\theta(\tau)}\left[\sum_{t=1}^H r(\mathbf{s}_t,\mathbf{a}_t)\right]\;\approx\;\frac1N\sum_{i=1}^N\sum_t r(\mathbf{s}_t^{(i)},\mathbf{a}_t^{(i)})$$

**怎么读**："期望算不出来？那就真的去跑 N 条轨迹，把每条的总奖励平均一下来近似。"

**逐符号拆**
- $\approx$ —— **约等于**：右边是左边的蒙特卡洛估计，在独立采样、可积等条件下，增大 N 通常提高估计精度。
- $\frac1N\sum_{i=1}^N$ —— 对 N 条采样轨迹取平均（期望的"样本版"）。
- 上标 $(i)$ / 下标 $t$ —— 老规矩：$(i)$ 数第几条轨迹，$t$ 数第几步（lec2 公式 5 同款）。

**直觉**：$p_\theta(\tau)$ 里藏着我们不知道的环境转移，**期望通常无法直接精确计算**；但"从 $p_\theta$ 采样"很容易——**跑一遍策略就是采样一次**。"期望 ≈ 样本平均"是整门课反复用的招。

---

### 公式 4 · Slide 5：convenient identity（log-derivative trick）⭐ {#formula-4}

> **这条公式在整讲中的任务：** 提供关键恒等式，把概率的导数改写成概率乘以 log 概率的导数。

$$p_\theta(\tau)\,\nabla_\theta\log p_\theta(\tau)=p_\theta(\tau)\,\frac{\nabla_\theta p_\theta(\tau)}{p_\theta(\tau)}=\nabla_\theta p_\theta(\tau)$$

**怎么读**："p 乘以『log p 的梯度』，等于 p 的梯度。"

**逐步看为什么**
1. 微积分链式法则：$\nabla\log f=\dfrac{\nabla f}{f}$（log 的导数是 $\frac1f$，再乘内层导数 $\nabla f$）。
2. 把 $\nabla_\theta\log p_\theta=\dfrac{\nabla_\theta p_\theta}{p_\theta}$ 代入左边，分母 $p_\theta$ 和外面乘的 $p_\theta$ **约掉**，剩 $\nabla_\theta p_\theta$。

**直觉**：这是个"变形器"。**从右往左用**才是它的用途：把不好处理的 $\nabla_\theta p_\theta$ **换成** $p_\theta\nabla_\theta\log p_\theta$——一旦式子里重新出现"$p_\theta\times(\cdots)$"的形状，就能把积分**重新打包回期望**，期望就能采样估计。整讲最重要的一行恒等式。

> 💡 一句话：**log-derivative trick = 把"分布的梯度"变成"分布 × log 梯度"，好让期望形状复活。**

---

### 公式 5 · Slide 5：从期望展开到积分，再写回期望 {#formula-5}

> **这条公式在整讲中的任务：** 把每个转换单独展开；先按定义写成积分，求导并改写，再认出期望的结构。

#### 第一步：期望按定义展开为积分 {#expectation-to-integral}

$$\begin{aligned}
J(\theta)&=\mathbb E_{\tau\sim p_\theta(\tau)}[r(\tau)]\\
&=\int\underbrace{p_\theta(\tau)}_{\text{这条轨迹的概率权重}}\,
\underbrace{r(\tau)}_{\text{这条轨迹的回报}}\,d\tau.
\end{aligned}$$

这里**还没有求导**。期望就是对各种可能的轨迹，用它们的概率权重给回报加权求和；连续情形写成积分。轨迹离散时，将积分换成求和，后面的思路相同。

#### 第二步：对这个积分求梯度 {#differentiate-integral}

$$\begin{aligned}
\nabla_\theta J(\theta)
&=\nabla_\theta\int p_\theta(\tau)r(\tau)d\tau\\
&=\int\nabla_\theta p_\theta(\tau)\,r(\tau)d\tau.
\end{aligned}$$

在允许交换梯度与积分的正则条件下，把导数移进去。**固定轨迹时**，奖励函数没有显式的参数依赖，因此导数作用在 $p_\theta(\tau)$ 上。

现在的难点是：$\nabla_\theta p_\theta(\tau)$ **不是一个概率分布**。它是概率随参数的变化率，不能直接当作我们采样的概率权重。

#### 第三步：把 log-derivative trick 代回积分 {#substitute-identity}

先用公式 4：
$$\nabla_\theta p_\theta(\tau)=p_\theta(\tau)\nabla_\theta\log p_\theta(\tau).$$

再替换第二步积分中的那一项：
$$\begin{aligned}
\nabla_\theta J(\theta)
&=\int \nabla_\theta p_\theta(\tau)\,r(\tau)d\tau\\
&=\int p_\theta(\tau)\nabla_\theta\log p_\theta(\tau)\,r(\tau)d\tau.
\end{aligned}$$

这一步做的是**代数替换**。此时结果仍然写成积分，还没有直接跳到期望。

#### 第四步：检查改写后的形状是否符合期望定义 {#match-expectation}

$$\nabla_\theta J(\theta)=
\int\underbrace{p_\theta(\tau)}_{\text{概率权重}}\,
\underbrace{\left[\nabla_\theta\log p_\theta(\tau)\,r(\tau)\right]}_{\text{新的被平均的量}}\,d\tau.$$

和第一步对照：

| 部分 | 原目标的期望 | 现在这个积分 |
|---|---|---|
| 概率权重 | $p_\theta(\tau)$ | 仍是 $p_\theta(\tau)$ |
| 被平均的量 | $r(\tau)$ | $\nabla_\theta\log p_\theta(\tau)\,r(\tau)$ |
| 对谁积分 | 轨迹 $\tau$ | 仍是轨迹 $\tau$ |

**权重重新变成概率密度，剩下的整体正是要被平均的量。** 因而现在的结构确实符合“期望 = 概率权重 × 被平均的量，再积分”的定义。

#### 第五步：确认结构吻合后，写回期望 {#back-to-expectation}

$$\boxed{\nabla_\theta J(\theta)=
\mathbb E_{\tau\sim p_\theta(\tau)}
\left[\nabla_\theta\log p_\theta(\tau)\,r(\tau)\right].}$$

现在才可以说：运行当前策略得到轨迹，再计算括号里的量，取样本平均。

> **整段连起来：**期望定义 → 积分 → 对概率求导 → 替换成“概率 × log 概率的梯度” → 识别期望结构 → 写回期望。回到期望不是新增恒等式，而是按同一个定义重新打包。

---

### 公式 6 · Slide 6：展开 log p_θ(τ)，环境项消失 ⭐⭐ {#formula-6}

> **这条公式在整讲中的任务：** 展开轨迹的 log 概率，剔除不依赖参数的项，留下每个动作的 log 概率梯度。

对公式 2 两边取 log（连乘变连加，lec2 公式 1 的老朋友）：
$$\log p_\theta(\tau)=\log p(\mathbf{s}_1)+\sum_{t=1}^{H}\Big[\log\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)+\log p(\mathbf{s}_{t+1}\mid\mathbf{s}_t,\mathbf{a}_t)\Big]$$

对 θ 求梯度——**逐项看谁含 θ**：

| 项 | 含 θ 吗 | $\nabla_\theta$ 后 |
|---|---|---|
| $\log p(\mathbf{s}_1)$ | ❌ 初始分布是环境的 | $0$（slide 红笔划掉） |
| $\log\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)$ | ✅ **唯一幸存者** | $\nabla_\theta\log\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)$ |
| $\log p(\mathbf{s}_{t+1}\mid\mathbf{s}_t,\mathbf{a}_t)$ | ❌ 环境转移是环境的 | $0$（slide 红笔划掉） |

代回公式 5，得到**本讲最核心的公式（策略梯度）**：

$$\boxed{\;\nabla_\theta J(\theta)=\mathbb{E}_{\tau\sim p_\theta(\tau)}\left[\left(\sum_{t=1}^{H}\nabla_\theta\log\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)\right)\left(\sum_{t=1}^{H}r(\mathbf{s}_t,\mathbf{a}_t)\right)\right]\;}$$

**怎么读**："策略梯度 = 期望下的『整条轨迹 log 概率梯度之和 × 整条轨迹总奖励』。"

> 🔑 **环境项的显式梯度为零。** 被划掉的是**不显式依赖策略参数**的初始分布与环境转移项。所以策略梯度是 **model-free** 的：不需要知道环境怎么运作，只要能（a）算自己策略的 $\nabla\log\pi_\theta$、（b）真的去环境里跑出轨迹和奖励。这就是"为什么 RL 可以不学环境模型也能优化"的数学原因。

> 💡 直觉：括号一是"这条轨迹里我做的所有决定，往哪个方向调 θ 能让它们更可能发生"；括号二是"这条轨迹值多少分"。**单项权重为正时，沿增加这条轨迹对数概率的方向推；权重为负时，方向相反。** 回报只是较低但仍为正，不会自动产生负方向；减 baseline 后才变成相对参考值的正负。

---

### 公式 7 · Slide 7：采样估计 + REINFORCE 算法 {#formula-7}

> **这条公式在整讲中的任务：** 将理论期望变成有限轨迹的梯度估计，真正执行一次策略更新。

**梯度的样本估计**（期望 → 平均，公式 3 同款操作）：
$$\nabla_\theta J(\theta)\approx\frac1N\sum_{i=1}^{N}\left(\sum_{t=1}^{H}\nabla_\theta\log\pi_\theta(\mathbf{a}_t^{(i)}\mid\mathbf{s}_t^{(i)})\right)\left(\sum_{t=1}^{H}r(\mathbf{s}_t^{(i)},\mathbf{a}_t^{(i)})\right)$$

**梯度上升一步**：
$$\theta\leftarrow\theta+\alpha\nabla_\theta J(\theta)$$
- 注意是 **+**（梯度**上升**）：我们在**最大化**奖励，不是最小化 loss。

**REINFORCE 算法**（slide 绿色循环框）：
$$\begin{aligned}
&1.\ \text{采样：跑策略 }\pi_\theta\text{，收集 }N\text{ 条轨迹 }\{\tau^{(i)}\}\\
&2.\ \text{估计梯度：}\nabla_\theta J(\theta)\approx\frac1N\textstyle\sum_i\big(\sum_t\nabla_\theta\log\pi_\theta(\mathbf{a}_t^{(i)}\mid\mathbf{s}_t^{(i)})\big)\big(\sum_t r(\mathbf{s}_t^{(i)},\mathbf{a}_t^{(i)})\big)\\
&3.\ \text{更新：}\theta\leftarrow\theta+\alpha\nabla_\theta J(\theta)\quad(\text{回到第 1 步循环})
\end{aligned}$$

> 🔑 这就是 lec4 那张橙绿蓝循环图的实例化：**generate samples**（第 1 步）→ **estimate return**（第 2 步的绿括号）→ **improve policy**（第 3 步）。
> **语言模型中的类比：**采样一批回答、为回答打分、再更新策略，也有“采样 → 估计 → 更新”的结构。这里解释最基本的策略梯度，不把后续带约束的算法全部等同于 REINFORCE。

---

## Part 2：理解策略梯度——它到底在干什么

### 公式 8 · Slide 10：和最大似然并排看 ⭐ {#formula-8}

> **这条公式在整讲中的任务：** 用与最大似然的局部对照，解释回报如何成为每项梯度的权重。

$$\begin{aligned}
\text{policy gradient:}\quad&\nabla_\theta J(\theta)\approx\frac1N\sum_{i=1}^N\left(\sum_{t=1}^H\nabla_\theta\log\pi_\theta(\mathbf{a}_t^{(i)}\mid\mathbf{s}_t^{(i)})\right)\left(\sum_{t=1}^H r(\mathbf{s}_t^{(i)},\mathbf{a}_t^{(i)})\right)\\[6pt]
\text{maximum likelihood:}\quad&\nabla_\theta J_{\mathrm{ML}}(\theta)\approx\frac1N\sum_{i=1}^N\left(\sum_{t=1}^H\nabla_\theta\log\pi_\theta(\mathbf{a}_t^{(i)}\mid\mathbf{s}_t^{(i)})\right)
\end{aligned}$$

**对同一批固定样本的梯度表达式而言**，策略梯度多乘了一个总奖励。数据来源也不同：BC 使用专家示范，REINFORCE 使用当前策略自己的采样。这个局部梯度类比不意味着两者有相同的全局目标。

| | 数据从哪来 | 每条轨迹的权重 |
|---|---|---|
| 最大似然 / BC | 专家给的 | 全部 = 1（无条件模仿） |
| 策略梯度 | **自己跑的** | $=r(\tau^{(i)})$（按好坏加权） |

> 💡 一句话：**策略梯度在固定样本上的梯度形式，可以看成“回报加权的最大似然”。** 正权重给单项正向推动，负权重给反向推动；较低但仍为正的回报不会自动变成负方向。

---

### 公式 9 · Slide 11：高斯策略的 log 概率与梯度 {#formula-9}

> **这条公式在整讲中的任务：** 给出连续高斯策略中 log 概率梯度的具体计算，并核对系数与矩阵形状。

先把高斯的三个位置写全：**在哪里求密度、均值是多少、协方差是多少**。
$$\pi_\theta(\mathbf a\mid\mathbf s)=\mathcal N(\mathbf a\mid f(\mathbf s),\Sigma),\qquad\Sigma\text{ 固定且正定}.$$
$$\log\pi_\theta(\mathbf a\mid\mathbf s)=-\frac12(f(\mathbf s)-\mathbf a)^\top\Sigma^{-1}(f(\mathbf s)-\mathbf a)+\text{const}.$$

**逐符号拆**

- $f(\mathbf s)$：网络输出的动作均值。
- $\Sigma$：固定协方差，控制各方向的距离如何加权。
- 马氏距离平方：$(f-\mathbf a)^\top\Sigma^{-1}(f-\mathbf a)$；$\Sigma=I$ 时就是普通欧氏距离平方。
- $\partial f(\mathbf s)/\partial\theta$：若动作维度为 $D$、参数数目为 $P$，它的形状是 $D\times P$。

**逐步求导：先对均值求导，再接网络的雅可比。**
$$\nabla_f\log\pi_\theta=-\Sigma^{-1}(f-\mathbf a).$$
$$\boxed{\nabla_\theta\log\pi_\theta=\left(\frac{\partial f(\mathbf s)}{\partial\theta}\right)^\top\Sigma^{-1}(\mathbf a-f(\mathbf s)).}$$

最后一式采用**列向量梯度**：$(P\times D)(D\times D)(D\times1)=P\times1$。若采用行向量导数，也可写成 $-(f-\mathbf a)^\top\Sigma^{-1}\frac{\partial f(\mathbf s)}{\partial\theta}$；两套约定应保持一致。

> **原笔记中需要校正的一行：**梯度前面的 $1/2$ 会与二次项求导产生的 2 抵消；矩阵乘法还需要正确的转置。这里把正确结果放在主公式里。若协方差也由网络学习，则还要计算它对应的梯度项。

**直觉**：只看这一项，$\nabla\log\pi$ 会让均值靠近采到的动作；乘上正权重后沿这个方向推，乘负权重则反向。共享参数与批量更新会叠加多项影响。

**一维小检查**：$\mu=2,\ a=3,\ \sigma^2=4$ 时，$\partial\log\pi/\partial\mu=(a-\mu)/\sigma^2=1/4$，而不是 $1/8$。

[回看 Lecture 2 的高斯与平方误差](../lecture-02/#formula-7)。

---

### 公式 10 · Slide 12：试错的形式化 {#formula-10}

> **这条公式在整讲中的任务：** 把奖励加权的梯度翻译成试错的直觉，同时分清权重正负。

把内层和缩写成轨迹级（$\nabla_\theta\log\pi_\theta(\tau)\equiv\sum_t\nabla_\theta\log\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)$）：
$$\nabla_\theta J(\theta)\approx\frac1N\sum_{i=1}^N\nabla_\theta\log\pi_\theta(\tau^{(i)})\,r(\tau^{(i)})$$

slide 三连：
- **good stuff is made more likely**（好东西概率被拉高）
- **bad stuff is made less likely**（坏东西概率被压低）
- **simply formalizes the notion of "trial and error"!**（这就是"试错"二字的数学化）

> 💡 整页就一句话：**策略梯度没有任何神秘的东西，它就是把"多做带来好结果的事"写成了梯度。**

---

### 公式 11 · Slide 13：部分可观测——使用观测或历史条件 {#formula-11}

> **这条公式在整讲中的任务：** 说明同一似然比推导可用于观测或历史条件下的策略。

$$\nabla_\theta J(\theta)\approx\frac1N\sum_{i=1}^N\left(\sum_{t=1}^H\nabla_\theta\log\pi_\theta(\mathbf{a}_t^{(i)}\mid\mathbf{o}_t^{(i)})\right)\left(\sum_{t=1}^H r(\mathbf{s}_t^{(i)},\mathbf{a}_t^{(i)})\right)$$

- 和公式 7 唯一区别：策略条件从 $\mathbf{s}_t$ 换成 $\mathbf{o}_t$（观测）。
- slide 两句话：**"Markov property is not actually used!"**、**"Can use policy gradient in partially observed MDPs without modification."**

> 🔑 **为什么不用马尔可夫性**：回看推导——公式 6 划掉环境项只用了"轨迹概率能链式分解"，而链式分解（按时间顺序逐步条件化）对**任何**序列分布都成立，不需要"未来只看现在"。所以 POMDP 下策略梯度公式照用，只是策略只能看见 $\mathbf{o}_t$。
> （注意：奖励 $r(\mathbf{s}_t,\mathbf{a}_t)$ 仍写状态——奖励是环境按真实状态发的，你不需要"看见"它，只需要收到分数。）

---

> **这里优化的是给定的策略类。** 使用 $\pi_\theta(a_t\mid o_t)$ 可以得到反应式策略的有效梯度；部分可观测任务若需要记忆，可改用以过去的观测与动作作为条件的策略。只看当前观测未必足以表示最优策略。环境仍通过访问到的状态和收到的奖励影响梯度样本。

### 为什么梯度估计会有高方差 {#variance}

slide 用"固定开局的国际象棋"举例（$R=+1$ 赢，$-1$ 输）：

| 想要的 | 实际得到的 |
|---|---|
| 好棋 → 正乘子，坏棋 → 负乘子 | **运气好的开局**也得正乘子、运气差的开局得负乘子 |
| | 一步好棋，因为**后面**下臭了 → 被打负乘子 |
| | 一步坏棋，因为对手**后面**随机失误 → 被打正乘子 |

- 整条轨迹共享**同一个**总奖励乘子 → 功劳/黑锅分不清（credit assignment 全靠平均）。
- slide：这些问题"average out with enough samples"（样本够多会平均掉，所以**期望**没错），但"we might need a very large number of samples"。
- 🟨 slide 黄框：**"high variance"** —— 单次估计噪声极大。这是策略梯度的原罪，Part 3 和之后整整几讲（actor-critic、PPO）都在治这个病。

---

## Part 3：方差缩减

### 公式 12 · Slide 17：Baseline——先减参考值，再证明能减 {#formula-12}

> **这条公式在整讲中的任务：** 提出减参考值的改造，并先证明哪种基线不会改变梯度期望。

**改造**：先取一个在采样前已确定、或与当前整条轨迹独立的标量基线 $b$：
$$\nabla_\theta J(\theta)\approx\frac1N\sum_{i=1}^N\nabla_\theta\log p_\theta(\tau^{(i)})\,[r(\tau^{(i)})-b].$$

比 $b$ 好的轨迹权重为正，比 $b$ 差的为负。接下来要回答：**减去参考值，会不会改变我们真正要估计的梯度？**

#### 为什么 baseline 项的期望为零 {#baseline-proof}

$$\begin{aligned}
\mathbb E[\nabla_\theta\log p_\theta(\tau)\,b]
&=\int p_\theta(\tau)\nabla_\theta\log p_\theta(\tau)\,b\,d\tau\\
&=\int \nabla_\theta p_\theta(\tau)\,b\,d\tau\\
&=b\,\nabla_\theta\int p_\theta(\tau)d\tau\\
&=b\,\nabla_\theta1=0.
\end{aligned}$$

1. 先把期望摊成积分。
2. 用公式 4，把 $p_\theta\nabla\log p_\theta$ 收回 $\nabla p_\theta$。
3. $b$ 相对这条轨迹是固定值，可以提出；在正则条件下交换梯度和积分。
4. 无论参数怎样变化，概率总和始终为 1，所以导数为 0。

> **同一个 trick，两个方向：**推策略梯度时，把 $\nabla p$ 展开成 $p\nabla\log p$；证明 baseline 时，把它收回去，最终对常数 1 求导。

**推广到状态基线**：给定状态，基线不能再依赖本次选出的动作：
$$\mathbb E_{a_t\sim\pi_\theta(\cdot\mid s_t)}
[\nabla_\theta\log\pi_\theta(a_t\mid s_t)\,b_t]
=b_t\nabla_\theta\int\pi_\theta(a\mid s_t)da=0.$$

这就是之后把 baseline 写成状态函数的依据。可对照 [Spinning Up 的 baseline 推导](https://spinningup.openai.com/en/latest/spinningup/rl_intro3.html#baselines-in-policy-gradients)。

#### 平均奖励 baseline 要区分两种情况 {#batch-baseline}

原笔记使用 $b=\frac1N\sum_{j=1}^N r(\tau^{(j)})$，把“好坏”改成相对平均水平。但若第 $i$ 条轨迹也参与计算自己的基线，基线就与该轨迹有关，不能直接套前面把 $b$ 提出积分的证明。

对于独立同分布的 $N$ 条完整轨迹，直接将这个批均值代入：
$$\begin{aligned}
&\mathbb E\!\left[
\frac1N\sum_{i=1}^N\nabla_\theta\log p_\theta(\tau^{(i)})
\left(r(\tau^{(i)})-\frac1N\sum_{j=1}^N r(\tau^{(j)})\right)\right]\\
&\qquad=\left(1-\frac1N\right)\nabla_\theta J(\theta).
\end{aligned}$$

这里 $i$、$j$ 都在数第几条轨迹。$N=1$ 时，自己减自己会把估计变成 0。

<details>
<summary>把多减掉的那一项展开看</summary>

不同轨迹相互独立，而 $\mathbb E[\nabla_\theta\log p_\theta(\tau^{(i)})]=0$，所以
$$\begin{aligned}
&\mathbb E\!\left[\nabla_\theta\log p_\theta(\tau^{(i)})
\left(\frac1N\sum_{j=1}^N r(\tau^{(j)})\right)\right]\\
&=\frac1N\mathbb E\!\left[\nabla_\theta\log p_\theta(\tau^{(i)})\,r(\tau^{(i)})\right]\\
&\quad+\frac1N\sum_{j\ne i}
\mathbb E[\nabla_\theta\log p_\theta(\tau^{(i)})]\,\mathbb E[r(\tau^{(j)})]\\
&=\frac1N\nabla_\theta J(\theta).
\end{aligned}$$

一种避免自身依赖的做法是：第 $i$ 条轨迹使用其余 $N-1$ 条轨迹的平均回报
$$\frac1{N-1}\sum_{j\ne i}r(\tau^{(j)}),\qquad N>1,$$
作为基线。也可以使用采样前已确定的参考值。

</details>

#### 用原来的数字例子理解权重居中

两条轨迹的奖励为 1001 和 999，参考值取 1000：

| | 轨迹 A | 轨迹 B |
|---|---|---|
| 原回报权重 | +1001 | +999 |
| 减去参考值后 | +1 | −1 |

权重现在表达相对好坏。这个表展示了**权重如何居中**；它没有给出 log 概率梯度，不能仅据此算出梯度方差减少多少。合适的 baseline 通常有助于降噪，任意 baseline 并不保证降低方差。

---

### 公式 13 · Slide 18：Causality——每个动作只乘未来回报 {#formula-13}

> **这条公式在整讲中的任务：** 保留完整的策略 log 概率梯度，说明为什么过去奖励项可以去掉。

先把公式 6 中的两层求和写开：
$$\nabla_\theta J(\theta)=
\mathbb E_{\tau\sim p_\theta(\tau)}\left[
\sum_{t=1}^H\nabla_\theta\log\pi_\theta(a_t\mid s_t)
\left(\sum_{t'=1}^H r(s_{t'},a_{t'})\right)\right].$$

**过去的奖励为什么可以去掉？** 固定选当前动作之前的历史，过去奖励已经发生，而对当前动作取平均时，
$$\mathbb E\!\left[\nabla_\theta\log\pi_\theta(a_t\mid s_t)
\mid\text{选动作前的历史}\right]=0.$$

所以
$$\begin{aligned}
&\mathbb E\!\left[
\nabla_\theta\log\pi_\theta(a_t\mid s_t)
\left(\sum_{t'=1}^{t-1}r(s_{t'},a_{t'})\right)\right]\\
&=\mathbb E\!\left[
\left(\sum_{t'=1}^{t-1}r(s_{t'},a_{t'})\right)
\mathbb E\!\left[\nabla_\theta\log\pi_\theta(a_t\mid s_t)
\mid\text{选动作前的历史}\right]\right]\\
&=0.
\end{aligned}$$

被去掉的交叉项是在**期望中**为零，不是每个样本上都等于零。当前动作只能影响当前及后续奖励。

#### 使用原笔记的剩余回报记号 {#reward-to-go}

$$\hat Q_t^{(i)}=\sum_{t'=t}^H r(s_{t'}^{(i)},a_{t'}^{(i)}).$$

内层从当前步 $t$ 开始，包括当前奖励。需要减基线时直接写 $\hat Q_t^{(i)}-b_t$；$b_t$ 表示当前步使用的参考值，可以依据当前状态确定，但不能依赖本次选出的动作。

完整的样本估计为
$$\boxed{
\nabla_\theta J(\theta)\approx
\frac1N\sum_{i=1}^N\sum_{t=1}^H
\nabla_\theta\log\pi_\theta(a_t^{(i)}\mid s_t^{(i)})
\left(\hat Q_t^{(i)}-b_t\right).
}$$

**按顺序看发生了什么：**先从整条回报中去掉过去奖励，得到 $\hat Q_t$；再减去合法的基线。每步梯度始终是原来的 $\nabla_\theta\log\pi_\theta$，只改变它后面乘的权重。

这些合法改写不改变期望，通常用于减小噪声；方差是否严格变小还要考虑基线选择与协方差，不能仅从项数减少推出。

[对照 reward-to-go 的标准推导](https://spinningup.openai.com/en/latest/spinningup/rl_intro3.html#don-t-let-the-past-distract-you)。

---

## Part 4：实现——构造梯度正确的标量损失

### 公式 14 · Slide 20：pseudo-loss——交给自动微分 {#formula-14}

> **这条公式在整讲中的任务：** 沿用原笔记的 $\tilde J$，让自动微分给出上一节的完整梯度估计。

上一节每一项都是“$\nabla_\theta\log\pi_\theta$ 乘以权重”。因此构造一个标量，只要对它求导能得到相同的形式即可：
$$\tilde J(\theta)=
\frac1N\sum_{i=1}^N\sum_{t=1}^H
\log\pi_\theta(a_t^{(i)}\mid s_t^{(i)})
\left(\hat Q_t^{(i)}-b_t\right).$$

对参数求导时，**采到的状态、动作，以及括号中的权重都视作常量**：
$$\begin{aligned}
\nabla_\theta\tilde J(\theta)
&=\frac1N\sum_{i=1}^N\sum_{t=1}^H
\nabla_\theta\log\pi_\theta(a_t^{(i)}\mid s_t^{(i)})
\left(\hat Q_t^{(i)}-b_t\right)\\
&\approx\nabla_\theta J(\theta).
\end{aligned}$$

第一行是对本批数据构造的伪目标求导，第二行表示它是原目标梯度的样本估计。若不减基线，直接把权重换回原笔记的 $\hat Q_t^{(i)}$。

**代码中的负号：**常用优化器做梯度下降，因此令 loss 为 $-\tilde J$。离散动作的 $-\log\pi_\theta$ 对应交叉熵，固定单位协方差的高斯对应平方误差；再乘上每步的权重。

#### 接回一次完整更新 {#implementation-loop}

~~~text
trajectories = sample(current_policy, N)
returns_to_go = sum_future_rewards(trajectories)
weights = stop_gradient(returns_to_go - baselines)
log_probs = policy_log_probs(states, actions)      # shape: [N, H]
loss = -mean_over_trajectories(sum_over_time(log_probs * weights))
gradient_descent_step(loss)
# Next iteration: sample again with the updated policy.
~~~

时间维度先求和，再对轨迹取平均。固定 $H$ 时，直接对全部时间步平均会多一个 $1/H$ 缩放；可变长度时需明确归一化方式并处理 mask。

停止权重梯度，是为了避免导出上一节公式里没有的额外项。更新后轨迹分布也会变化，下一轮用新的策略重新采样。

> **伪目标的值不是期望回报。** 它用于构造当前采样策略处的梯度估计；判断策略是否进步仍要看实际回报，而不是只看 loss 是否下降。

[Spinning Up 对伪损失的说明](https://spinningup.openai.com/en/latest/spinningup/rl_intro3.html#implementing-the-simplest-policy-gradient)区分了这两个角色。

---

### 实践提示：看回报与噪声 {#practice}

- **记住梯度方差很大**——"This isn't the same as supervised learning!"，梯度会非常噪。
- **用大得多的 batch**（方差靠样本量硬压）。
- **学习率很难调**：ADAM 这类自适应步长"OK-ish 能用"；策略梯度专用的步长调节方法（自然梯度 / TRPO / PPO）后面的课讲。

---


## 补充精读：链式法则最常卡的一步 {#log-derivative-detail}

这里保留配套笔记的逐层展开。核心是**对 log 使用链式法则，再约掉一个概率因子**。式子两边相等，但在策略梯度与 baseline 证明中使用方向相反。

在概率为正、允许相应求导的范围内阅读下面的等式；“可采样”指从概率分布取样后计算被积函数，而不是直接从一个梯度向量取样。

### 🎯 先看结论：你要打通的就这一行

$$p_\theta(\tau)\,\nabla_\theta\log p_\theta(\tau)=p_\theta(\tau)\,\frac{\nabla_\theta p_\theta(\tau)}{p_\theta(\tau)}=\nabla_\theta p_\theta(\tau)$$

这三段连等其实只有**两个动作**：

$$\underbrace{\text{(1) 代入 log 的链式法则}}_{\text{唯一的数学}}\quad\longrightarrow\quad\underbrace{\text{(2) 约分}}_{\text{小学算术}}$$

不是三个动作。难的部分只在 ①，下面单独把它吃透。

---

### 第一步：先把 `∇_θ` 的恐惧拆掉

`∇_θ`（读 nabla-theta）这个符号看着唬人，但**你完全可以先把它当成高中的 `d/dx` 来理解**。

| | `d/dx` | `∇_θ` |
|---|---|---|
| 对谁求导 | **一个**数 `x` | **一排**数 `θ`（网络几百万个参数） |
| 结果 | 一个数 | 一排数（每个参数一个偏导） |
| 求导规则 | 链式法则、乘除、约分 | **完全一样**（对每个分量分别成立） |

> 🔑 所以下面我全程用 `d/dx` 的脑子想，最后换个符号即可。**不要被 `∇` 吓住，它就是个"多分量版的导数"。**

---

### 第二步：核心只有一条——`log` 怎么求导 ⭐

这是整行唯一需要的数学事实，先单独吃透。

**基本导数（记住它）：**
$$\frac{d}{dx}\log x=\frac{1}{x}$$
例：`x=2` 时，`log` 的斜率 `= 1/2 = 0.5`。

**关键一步**：如果 `log` 里面不是光秃秃的 `x`，而是**一个函数** `f(x)`，就要用**链式法则**。链式法则一句话：

> **外层导数 × 内层导数**

$$\frac{d}{dx}\log f(x)=\underbrace{\frac{1}{f(x)}}_{\text{外层：log 的导数}}\times\underbrace{f'(x)}_{\text{内层：f 自己的导数}}=\frac{f'(x)}{f(x)}$$

- **外层**是 `log`，导数是 `1/(里面那坨)` = `1/f(x)`；
- **内层**是 `f(x)`，对它再求一次导 = `f'(x)`；
- 两个**相乘**。

换成本讲符号（`f → p_θ`，`' → ∇_θ`）：

$$\boxed{\;\nabla_\theta\log p_\theta(\tau)=\frac{\nabla_\theta p_\theta(\tau)}{p_\theta(\tau)}\;}$$

> 💡 **难的部分到这里就结束了。** 后面全是小学算术。你之所以觉得这块弱，几乎可以肯定卡的就是"log 套了个函数要用链式法则"这一下。

---

### 第三步：约分（小学算术）

把第二步的等式**两边同时乘以 `p_θ(τ)`**：

$$p_\theta(\tau)\cdot\nabla_\theta\log p_\theta(\tau)=p_\theta(\tau)\cdot\frac{\nabla_\theta p_\theta(\tau)}{p_\theta(\tau)}$$

看右边：前面**乘**一个 `p_θ`，分母上又**除**一个 `p_θ`，一乘一除**约掉**。就像：
$$5\times\frac{x}{5}=x$$

所以右边 `= ∇_θ p_θ(τ)`，得到最终恒等式：

$$\boxed{\;p_\theta(\tau)\,\nabla_\theta\log p_\theta(\tau)=\nabla_\theta p_\theta(\tau)\;}$$

> 一句话：**链式法则 → 约分，就两步，没有第三个动作。**

---

### 第四步：用真实数字验一遍（消除"我是不是被忽悠了"）

取 $0\lt\theta\lt1$，用 $p_\theta(\tau)=\theta^3$ 表示某个事件的概率，两条路各算一遍，看是否真相等：

**左路（绕 log）**
$$\log p_\theta=\log(\theta^3)=3\log\theta\;\Rightarrow\;\nabla_\theta\log p_\theta=3\cdot\frac1\theta=\frac3\theta\;\xrightarrow{\times\,p_\theta}\;\theta^3\cdot\frac3\theta=3\theta^2$$

**右路（直接求导）**
$$\nabla_\theta p_\theta=\nabla_\theta(\theta^3)=3\theta^2$$

**两边都是 $3\theta^2$ ✅**。恒等式是真的，不是文字游戏。

---

### 第五步：那绕这一圈到底图什么？——「从右往左用」的灵魂 ⭐⭐

前面讲"怎么成立"，这一步讲"**为什么要它**"。

推策略梯度（[Lecture 5 逐行拆解](#formula-4) 公式 5）时会撞到：
$$\nabla_\theta J=\int \nabla_\theta p_\theta(\tau)\,r(\tau)\,d\tau$$

**大麻烦**：`∇_θ p_θ(τ)` **不是概率分布**（它是概率的变化率，可正可负，加起来也不等于 1）→ **不能把它本身当作概率分布采样**。本讲采用的近似手段是"采样求平均"。

什么积分才能变成"采样求平均"？**本讲使用的目标形状**：
$$\int \underbrace{p_\theta(\tau)}_{\text{权重}}\cdot[\text{某东西}]\,d\tau=\mathbb{E}_{\tau\sim p_\theta}[\text{某东西}]$$

积分号里**必须有个 `p_θ(τ)` 当权重**，它才等于期望，期望才能"跑几条轨迹平均一下"来估。可 `∇_θ p_θ` 偏偏把这个 `p_θ` 藏进了导数里，**权重不见了**。

**恒等式就是来把权重变回来的。从右往左读：**
$$\underbrace{\nabla_\theta p_\theta(\tau)}_{\text{手上有的、没法采样}}\;\longrightarrow\;\underbrace{p_\theta(\tau)\,\nabla_\theta\log p_\theta(\tau)}_{\text{重新长出 }p_\theta\text{ 权重，能采样了}}$$

代回积分，`p_θ` 权重复活，积分立刻变回期望：
$$\nabla_\theta J=\int p_\theta(\tau)\,\big[\nabla_\theta\log p_\theta(\tau)\,r(\tau)\big]\,d\tau=\mathbb{E}_{\tau\sim p_\theta}\big[\nabla_\theta\log p_\theta(\tau)\,r(\tau)\big]$$

而期望就能"跑 N 条轨迹取平均"估出来了。

> 💡 **一句话总括**：`∇p` 没法采样，可以从 `p` 采样，再计算 `∇log p`——而这俩**相等**。这条恒等式的全部作用，就是把"不能采样的形态"换成"能采样的形态"。

---

### 🔁 同一把钥匙，两个方向各开一次锁

| | 方向 | 在哪用 | 目的 |
|---|---|---|---|
| 公式 5（策略梯度推导） | **右 → 左** | $\nabla p_\theta\to p_\theta\nabla\log p_\theta$ | **复活** `p_θ` 权重，把积分凑回期望好采样 |
| 公式 12（baseline 无偏证明） | **左 → 右** | $p_\theta\nabla\log p_\theta\to\nabla p_\theta$ | **消掉** `p_θ`，把梯度提到积分外打在常数 1 上（得 0） |

> 🔑 同一行恒等式，正反都能用。看到 `∇p` 想采样 → 往右拆出权重；看到 `p∇log p` 想化简 → 往左收回 `∇p`。

---

### 🗂️ 速记卡

1. **真正的数学只有一条**：`log` 链式法则 $\nabla\log f=\dfrac{\nabla f}{f}$（外层 `1/f` × 内层 `∇f`）。卡点就这一个。
2. **`∇_θ` 先当 `d/dx`**：规则一样，只是 θ 是一排数。
3. **三段连等 = 链式法则 + 约分**，两个动作。
4. **战略意义**：采样化"变形器"——`∇p`（不能采样）⟷ `p∇log p`（能采样），二者相等。

---

### ✅ 自测（盖住答案）

1. $\dfrac{d}{dx}\log f(x)$ 等于什么？用"外层×内层"说一遍。
2. `∇_θ` 和 `d/dx` 本质区别在哪？理解恒等式时能不能先当成一样的？
3. 那行三段连等 `p∇log p = p(∇p/p) = ∇p` 一共做了几个动作？分别是什么？
4. 为什么 `∇_θ p_θ(τ)` 不能直接采样估计，而 `p_θ∇_θ log p_θ` 可以？
5. 公式 5 里恒等式从哪个方向用、为了什么？公式 12 里又是哪个方向、为了什么？

<details>
<summary>参考答案</summary>

1. $\dfrac{f'(x)}{f(x)}$。外层 `log` 的导数是 `1/f(x)`，内层 `f` 的导数是 `f'(x)`，相乘。

2. `d/dx` 对一个数求导、出一个数；`∇_θ` 对一排参数求导、出一排偏导。但求导规则（链式、乘除、约分）完全一样，理解恒等式时可以先当成一样的。

3. 两个动作：① 把链式法则 `∇log p = ∇p/p` 代入中间项；② 前面的 `p` 和分母的 `p` 约分，得 `∇p`。

4. 因为只有"$\int p_\theta(\tau)\cdot[\cdots]d\tau$"这种**带 `p_θ` 权重**的积分才等于期望 $\mathbb{E}_{\tau\sim p_\theta}[\cdots]$，期望才能用采样平均估。`∇p` 不是概率分布、没有这个权重，所以不能；`p∇log p` 把权重 `p` 显式摆在前面，所以能。

5. 公式 5：**右→左**，把 `∇p` 换成 `p∇log p`，复活权重凑成期望好采样。公式 12：**左→右**，把 `p∇log p` 换回 `∇p`，好把梯度提出积分、打在 $\int p_\theta d\tau=1$ 这个常数上得到 0（证明 baseline 无偏）。
</details>

## 全公式速查 {#formula-index}

| 公式 | 在主线里的任务 |
|---|---|
| [1](#formula-1) | 定义期望回报与优化目标 |
| [2](#formula-2) | 分解轨迹概率 |
| [3](#formula-3) | 用轨迹平均评估回报 |
| [4](#formula-4) | 链式法则得到 log-derivative trick |
| [5](#formula-5) | 对积分求导，凑回可采样的期望 |
| [6](#formula-6) | 展开 log 概率，留下策略项 |
| [7](#formula-7) | 采样估计梯度并更新参数 |
| [8](#formula-8) | 对照奖励加权的最大似然梯度 |
| [9](#formula-9) | 算一个具体的高斯策略的 log 概率梯度 |
| [10](#formula-10) | 解释权重正负与试错 |
| [11](#formula-11) | 使用观测或历史条件下的策略 |
| [12](#formula-12) | baseline 及其无偏条件 |
| [13](#formula-13) | 去掉过去奖励，定义 reward-to-go |
| [14](#formula-14) | 停止权重梯度的伪损失 |

## 串起主线的自测 {#self-check}

<div class="lecture-checks">

<details>
<summary>1. 为什么不能把采到的回报直接当成普通 loss，对 θ 反向传播？</summary>

固定样本的回报数值没有体现“参数改变后会采到不同轨迹”这一影响。似然比推导通过 $p_\theta(\tau)$ 的导数处理它，再转成可以采样计算的 log 概率梯度乘以回报。

</details>

<details>
<summary>2. log-trick 在求梯度与 baseline 证明中分别做什么？</summary>

求梯度时把 $\nabla p$ 写成 $p\nabla\log p$，恢复期望形式；baseline 证明时将其收回 $\nabla p$，再对概率积分恒等于 1 的事实求导。

</details>

<details>
<summary>3. 环境项的梯度为零，是否意味着环境不影响梯度？</summary>

没有显式的参数导数，不等于没有影响。环境决定访问状态和得到的奖励，仍然影响每个梯度样本。

</details>

<details>
<summary>4. 回报较低的轨迹，是否一定被反向推？</summary>

看权重的正负。较低但仍为正的回报仍给正权重；减去 baseline 后，低于参考值才给负权重。完整更新还会叠加其他样本的影响。

</details>

<details>
<summary>5. 为什么同批均值 baseline 不能直接套“b 是常数”的证明？</summary>

它包含当前样本自己的回报。独立轨迹下，包含自身的批均值会产生 $(1-1/N)$ 的缩放偏差；按整条轨迹留一等方式可以避免这项依赖。

</details>

<details>
<summary>6. reward-to-go 与减基线后的权重是同一个量吗？</summary>

$\hat Q_t=\sum_{t'=t}^H r(s_{t'},a_{t'})$ 是剩余回报；需要减参考值时，直接写成 $\hat Q_t-b_t$。

</details>

<details>
<summary>7. 去掉过去奖励，为什么期望不变？</summary>

给定选动作前的历史，过去奖励已经确定，而当前动作的 log 概率梯度的条件期望为零。因此它们的乘积期望为零。

</details>

<details>
<summary>8. policy loss 为什么有负号，还要对权重 stop-gradient？</summary>

负号把最大化回报改写为优化器的梯度下降；停止权重梯度避免引入不属于目标估计器的额外导数。新一轮通常要用更新后的策略重新采样。

</details>

</div>

## 材料与本版校正 {#sources}

主体来自本地《Lecture5 公式逐行拆解》《Lecture5 一页地图》和《Lecture5 链式法则最常卡的一步》，保留公式 1–14 与主要的逐符号、逐行解释。原 Obsidian 文件保持原样；其他本地拓展笔记只保留名称。

本版统一了轨迹终止状态、高斯梯度的系数与转置、baseline 的独立性条件、reward-to-go 与减基线后的权重写法，以及伪损失的负号、停止梯度和采样条件。批均值 baseline 的有限样本偏差在本页单独推导。

参考 [CS285 课程入口](https://rail.eecs.berkeley.edu/deeprlcourse-fa23/) 与 [Spinning Up 的策略优化推导](https://spinningup.openai.com/en/latest/spinningup/rl_intro3.html)。顶部图按“目标 → 变形 → 估计 → 改善 → 实现”的依赖关系组织，不是课件页码的机械排列。

[回到 Lecture 5 主线 ↑](#lecture-thread) · [回看 Lecture 2](../lecture-02/)
