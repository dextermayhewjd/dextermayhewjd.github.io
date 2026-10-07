---
title: "Lecture 9 · 从旧样本复用到 PPO"
description: "逐步拆开换分布、轨迹重要性权重、因果性、单步替代目标与 clip/min，保留公式逐行拆解和四篇卡点精读。"
date: 2026-10-07
weight: 90
math: true
ShowToc: false
tags: [CS285, Policy Gradients, Importance Sampling, PPO]
---

## 先看清这一讲在做什么 {#lecture-thread}

**Lecture 5 解决“怎样从奖励得到策略梯度”；Lecture 9 接着问：“一批采来的轨迹，能不能多用几次？”** 参数一更新，策略会改变动作分布，也会改变后续状态分布。旧数据仍有价值，但不能直接当作新策略采出的数据。

先完整看已有的六步循环：**1 采样 → 2 算 critic 目标 → 3 拟合 critic → 4 算 GAE → 5 估计策略梯度 → 6 更新策略 → 回到 1 重新采样。** 图中将这整个循环放在一个框里，右侧集中列出 1–6 步公式。瓶颈就在第 6 步之后：前四步得到的一批数据，只用于做一次第 5–6 步。

本讲从这里问：**能否跳过重新采样，直接把同一批数据再做几次第 5–6 步？** 接着依次解决分布不匹配、轨迹权重、单步替代目标与 clip/min，最后将原来的循环改为“采一批、更新多次、再采一批”的 PPO 循环。

原始循环、复用旧批次后的循环、最终 PPO 循环，各用一个框与一组完整公式呈现，方便对照改动发生在哪里。其余推导仍保持小节点与旁侧公式，期望展开、插入比值、识别期望结构分别成一步。**从旧状态分布构造替代目标开始，已经进入局部近似；clip/min 又进一步改变了优化目标。**

{{< lecture-mindmap id="ppo-flow" cards="argument-cards.json" width="1660" caption="三版完整循环各占一个框，旁边集中列出全部编号公式：原始 1–6 步 → 旧批次复用的 1–8 步 → PPO 的 1–8 步。先比较策略更新的目标与重复次数，再沿小节点阅读改造依据。每个编号步骤尽量保持一行；虚线表示该组算法刷新数据后回到采样。点击框或节点进入拆解，窄屏可在图内左右滑动。" >}}

### 把这条主线接成一段话

重要性采样先解决“用谁的样本”这个问题：把目标分布下的期望展开成积分，乘上采样密度与它的倒数，重新认出采样分布下的期望。套到轨迹上，环境因子约掉，只剩新旧动作概率之比的连乘。

因果性允许每条奖励只保留到自身时刻的权重，但长连乘依然存在。接下来转到状态—动作边缘分布，明确区分**路径权重**与**状态概率比**，再用旧状态分布、旧优势构造在旧参数处匹配梯度的局部替代目标。到这里，才得到常见的单步动作比值。

同一批数据更新多次后，策略可能偏离采样策略。plain clip 把两端都变平，会连“朝错误方向移动”的纠正梯度一起抹掉；min 按优势正负保留该保留的那一支。把这个目标配上固定的旧概率、GAE 和多轮更新，就是本页的 PPO-Clip。

| 当前卡点 | 阅读位置 |
|---|---|
| 原来的 1–6 步循环，究竟卡在哪 | [完整六步](#formula-2) → [更新后分布错位](#formula-3) |
| 为什么不能把旧数据直接当新数据 | [公式 3](#formula-3) |
| 从期望到积分，再到另一分布的期望 | [公式 4](#formula-4) |
| 新旧策略究竟谁固定、谁求导 | [公式 5](#formula-5) → [公式 7](#formula-7) |
| 权重为什么也能用因果性 | [公式 8](#formula-8) → [因果性精读](#causality-detail) |
| 长连乘到单步比值省了哪些条件 | [公式 9](#formula-9) → [一阶近似精读](#first-order-detail) |
| clip 后为什么还要 min | [公式 11](#formula-11) → [四格表](#clip-cases) → [clip 精读](#clip-detail) |

<details>
<summary>展开全页目录与公式索引</summary>

{{< chapter-outline id="lecture9-outline" title="Lecture 9 阅读位置" >}}

</details>

## 先认清符号与推导范围 {#notation}

本页整理本地《Lecture9 公式逐行拆解》与四篇配套精读，保留原笔记的 **公式 1–13 和公式 10b**。Slide 编号沿用原笔记，不据此指定课件年份。前置是 [Lecture 5 策略梯度](../lecture-05/) 和 Lecture 6 的 actor-critic、GAE；后者需要的式子在公式 1–2 补齐。

| 符号 | 本页含义 |
|---|---|
| $\theta$、$\pi_\theta$ | 采集当前这批数据的旧参数、旧策略；内层更新时固定 |
| $\theta'$、$\pi_{\theta'}$ | 正在优化的新参数、新策略；每批开始时令 $\theta'=\theta$ |
| $p_\theta(\tau)$ | 旧策略与环境共同决定的一整条轨迹的概率 |
| $p_\theta(s_t)$、$p_\theta(s_t,a_t)$ | 第 $t$ 步的状态边缘分布、状态—动作联合分布 |
| $\pi_\theta(a_t\mid s_t)$ | 给定状态后的动作分布；和 $p_\theta(s_t)$ 区分 |
| $H$、$N$、$K$ | 每条轨迹的步数、轨迹条数、同批数据的内层更新次数 |
| $r(\tau)$ | 整条轨迹总奖励；主要 IS 推导取 $\sum_{t=1}^H r(s_t,a_t)$ |
| $A^{\pi_\theta}$、$\hat A_t^{(i)}$ | 旧策略的真实优势、用旧批数据算出的优势估计；内层当作常数 |
| $\hat V_\phi^\pi$、$\delta_t$ | critic 估值、TD 残差；定义见公式 2 |
| $\gamma$、$\lambda$ | 折扣因子、GAE 的衰减参数 |
| $w(\tau)$ | 讨论轨迹 IS 时使用的全轨迹比值 $p_{\theta'}(\tau)/p_\theta(\tau)$ |
| $w$、$w_c$ | clip 局部分析里的单步动作比值、它裁剪后的系数；使用前重新明确范围 |
| $\epsilon$ | 裁剪半径，本页数字例取 $0.1$；与 Lecture 2 的错误率不是同一含义 |
| $\mathcal L_{\mathrm{CLIP}}$、$\mathcal H$ | PPO 裁剪目标、策略熵 |

**推导条件。** 新旧策略共享初始分布和环境转移；固定轨迹时奖励不显式依赖策略参数。默认策略可微，允许交换求导与积分，且目标分布的支持被采样分布覆盖。有限时域下价值与优势随时刻变化，本页沿用原符号，把时刻视为状态的一部分。

**折扣约定。** 公式 1–2 回顾含 $\gamma$ 的 GAE；从公式 3 起的主要等式采用有限时域、无折扣目标。若改为从起点计算的折扣目标 $\mathbb E[\sum_t\gamma^{t-1}r_t]$，逐时刻梯度也需配套外层 $\gamma^{t-1}$，不能只在 reward-to-go 里加入折扣。

## Part 1：策略梯度已有了，旧样本怎样继续用

### 公式 1 · Slide 3：Monte Carlo 优势与 baseline {#formula-1}

> **这条公式的任务：** 回顾 critic 作为 baseline 时，为什么不必精确也能保持梯度期望。

$$\hat A^\pi_{\mathrm{MC}}(s_t,a_t)=\sum_{t'=t}^{H}\gamma^{t'-t}r(s_{t'},a_{t'})-\hat V^\pi_\phi(s_t)$$

**怎么读：** 从当前步起，把实际奖励折扣相加，再减掉 critic 对当前状态的估值。

- 第一项是实际轨迹上的 reward-to-go，条件期望是 $Q^\pi(s_t,a_t)$。
- 第二项只依赖状态；这里把 baseline 固定，并停止它在 actor 更新中的梯度。
- $\lambda=1$ 的 GAE 在真实终止、末端价值为零时会望远镜消去中间 critic 项，得到这个 MC 形式。若只是 rollout 截断而未终止，还留有末端 bootstrap 项。

**先分清“优势无偏”和“梯度无偏”。** 当 critic 不准时：

$$\mathbb E[\hat A^\pi_{\mathrm{MC}}(s_t,a_t)\mid s_t,a_t]=Q^\pi(s_t,a_t)-\hat V^\pi_\phi(s_t)$$

右边一般不等于真实的 $A^\pi=Q^\pi-V^\pi$。但 baseline 对策略梯度的贡献为零：

$$\mathbb E_{a_t\sim\pi_\theta(\cdot\mid s_t)}[\nabla_\theta\log\pi_\theta(a_t\mid s_t)\hat V^\pi_\phi(s_t)]=\hat V^\pi_\phi(s_t)\nabla_\theta\sum_{a_t}\pi_\theta(a_t\mid s_t)=0$$

因此，在 on-policy 采样、固定的状态 baseline 和相应正则条件下，**减 baseline 不改变梯度期望**。这不是说任意 critic 都能给出无偏优势，也不是说任意 $\lambda\lt1$ 的 GAE 都无偏。若 baseline 拟合与同批动作噪声相关，还要单独考虑估计依赖，不能只靠停止自动微分就推出严格无偏。

**小检查：** critic 学偏了，首先偏的是哪个估计？为什么它乘上 log 概率梯度后，偏移项可以消掉？详见 [score 精读](#score-detail)。

### 公式 2 · Slide 4：现有的 on-policy actor-critic + GAE {#formula-2}

> **这条公式的任务：** 把本讲要改造的循环摆出来：采样、估值、算优势，然后更新策略。

#### 第 1 步：用当前策略采样 {#on-policy-step-1}

$$\{\tau^{(i)}\}_{i=1}^N,\qquad\tau^{(i)}\sim p_\theta(\tau)$$

运行当前策略，得到每一步的状态、动作、奖励及终止信息。此时样本分布与要求的当前策略分布一致。

#### 第 2 步：计算 critic 的训练目标 {#on-policy-step-2}

$$y_t^{(i)}=r(s_t^{(i)},a_t^{(i)})+\gamma\hat V^\pi_\phi(s_{t+1}^{(i)})$$

当前奖励加下一状态的折扣估值。真实终止状态的后续价值取零；时间截断则按任务语义决定 bootstrap。

#### 第 3 步：把 critic 拟合到目标 {#on-policy-step-3}

$$\min_\phi\frac1N\sum_{i=1}^N\sum_{t=1}^H\left(\hat V^\pi_\phi(s_t^{(i)})-y_t^{(i)}\right)^2$$

优化这个平方误差来更新 $\phi$，使当前状态的估值接近第 2 步的目标。拟合时固定当前 $y_t^{(i)}$；这里更新的是 critic 参数，策略参数 $\theta$ 还没有改变。

#### 第 4 步：计算 TD 残差与 GAE 优势 {#on-policy-step-4}

$$\delta_t^{(i)}=r(s_t^{(i)},a_t^{(i)})+\gamma\hat V^\pi_\phi(s_{t+1}^{(i)})-\hat V^\pi_\phi(s_t^{(i)})$$

$$\hat A^\pi_{\mathrm{GAE}}(s_t^{(i)},a_t^{(i)})=\sum_{t'=t}^{H}(\gamma\lambda)^{t'-t}\delta_{t'}^{(i)}$$

先用奖励与 critic 算单步 TD 残差，再按 $(\gamma\lambda)^{t'-t}$ 加权累加成优势。后面的 $\hat A_t^{(i)}$ 就使用这批优势估计。

#### 第 5 步：用当前批次估计策略梯度 {#on-policy-step-5}

$$\nabla_\theta J(\theta)\approx\frac1N\sum_{i=1}^N\sum_{t=1}^{H}\nabla_\theta\log\pi_\theta(a_t^{(i)}\mid s_t^{(i)})\hat A_t^{(i)}$$

动作的 log 概率梯度乘优势，再对轨迹平均。按本页的无折扣主线读取这个更新；回顾 GAE 时保留 $\gamma$，无折扣特例取 $\gamma=1$。

#### 第 6 步：更新策略，然后回到第 1 步 {#on-policy-step-6}

$$\theta'\leftarrow\theta+\alpha\nabla_\theta J(\theta)$$

这里用已有的 $\theta'$ 记录更新后的参数，保留 $\theta$ 作为这批数据的采样参数，方便比较更新前后的分布。原来的 on-policy 循环随后执行：

$$\theta\leftarrow\theta',\qquad\tau^{(i)}\sim p_\theta(\tau)\quad\text{重新执行第 1–4 步}$$

**瓶颈就在这里：** 原算法用第 1–4 步准备一批数据，只做一次第 5–6 步，就要重新采样与准备优势。若改为保留这批数据并重复第 5–6 步，就保留 $\theta$ 作为旧采样参照，用 $\theta'$ 表示当前策略；不执行原回路中覆盖采样参照、重新采样的分支。下一次求梯度时，当前策略已经是 $\pi_{\theta'}$，样本却仍来自 $\pi_\theta$。下一条公式精确写出这个错位；后面的 IS 与 PPO 都是在改造第 5–6 步，让它们能在同批数据上多次执行。

### 公式 3 · Slide 5：参数变了，期望底下的分布也变了 {#formula-3}

> **这条公式的任务：** 定位复用旧样本的障碍：需要新分布下的平均，却只有旧分布的样本。

先用真实优势写精确的无折扣策略梯度：

$$\nabla_{\theta'}J(\theta')=\sum_{t=1}^H\mathbb E_{(s_t,a_t)\sim p_{\theta'}}[\nabla_{\theta'}\log\pi_{\theta'}(a_t\mid s_t)A^{\pi_{\theta'}}(s_t,a_t)]$$

把每一步的期望摊开，离散情形得到：

$$\nabla_{\theta'}J(\theta')=\sum_{t=1}^H\sum_{s_t,a_t}p_{\theta'}(s_t,a_t)\nabla_{\theta'}\log\pi_{\theta'}(a_t\mid s_t)A^{\pi_{\theta'}}(s_t,a_t)$$

**看三个位置：**

1. $\nabla_{\theta'}\log\pi_{\theta'}$ 可以在旧样本的状态、动作上重新计算。
2. $p_{\theta'}(s_t,a_t)$ 是新策略实际会遇到哪些状态、选择哪些动作的权重；旧批样本来自 $p_\theta$。
3. $A^{\pi_{\theta'}}$ 也属于新策略。实际复用的旧 GAE 并不会随新参数自动变成这个量。

$$p_\theta(s_t,a_t)=p_\theta(s_t)\pi_\theta(a_t\mid s_t)\quad\ne\quad p_{\theta'}(s_t)\pi_{\theta'}(a_t\mid s_t)$$

这个不等式表示一般情形，刚初始化 $\theta'=\theta$ 时两者当然相同。问题不是“旧样本绝对不能再用”，而是**直接把旧样本平均当成新分布期望，通常不再正确**。

下一步先用完整轨迹回报绕开未知的新优势：给旧轨迹乘分布修正系数。完整的 $\nabla_{\theta'}\log\pi_{\theta'}$ 始终保留；“单步 score”只是它的名称，见 [术语精读](#score-detail)。

## Part 2：换分布、展开轨迹，再走到单步近似

### 公式 4 · Slide 7：重要性采样，逐步认出新的期望 {#formula-4}

> **这条公式的任务：** 用 $q$ 的样本计算 $p$ 下的平均，每一个等号都要说明依据。

**第 1 步：按期望定义，展开成积分。**

$$\mathbb E_{x\sim p}[f(x)]=\int p(x)f(x)\,dx$$

**第 2 步：在需要积分的地方乘 $q(x)/q(x)=1$。**

$$\int p(x)f(x)\,dx=\int q(x)\frac{p(x)}{q(x)}f(x)\,dx$$

条件方向不能写反：**只要 $p(x)\gt0$，就要有 $q(x)\gt0$**（几乎处处）。目标分布想统计的区域，采样分布必须能到达；否则丢失的区域不能靠给已有样本加权补回来。

**第 3 步：先与期望结构逐项对应。**

$$\int\underbrace{q(x)}_{\text{采样密度}}\underbrace{\left[\frac{p(x)}{q(x)}f(x)\right]}_{\text{被平均的量}}\,dx$$

现在才出现“密度 $q$ × 一个函数，对 $x$ 积分”的结构，所以可按定义写回：

$$\mathbb E_{x\sim p}[f(x)]=\mathbb E_{x\sim q}\left[\frac{p(x)}{q(x)}f(x)\right]$$

**逐符号拆：** 分子 $p$ 是想要的分布；分母 $q$ 是实际采样的分布；$f$ 是要平均的量。$q$ 相对抽多的地方权重小，抽少的地方权重大。离散空间将积分替换成求和，逻辑相同。

**两个容易混淆的层次：** 等式讨论总体期望；有限样本的加权平均仍有误差。分布相差大时，即使等式完全正确，估计方差也可能很大。

### 公式 5 · Slide 7：套到轨迹上，环境因子约掉 {#formula-5}

> **这条公式的任务：** 得到可用新旧策略概率计算的轨迹权重，不需要环境模型。

全页统一旧参数 $\theta$、新参数 $\theta'$，不再为旧策略另起横杠记号。对照公式 4，令 $p=p_{\theta'}$、$q=p_\theta$、$f=r(\tau)$：

$$J(\theta')=\mathbb E_{\tau\sim p_{\theta'}}[r(\tau)]=\mathbb E_{\tau\sim p_\theta}\left[\frac{p_{\theta'}(\tau)}{p_\theta(\tau)}r(\tau)\right]$$

含最后一次转移的轨迹概率为：

$$p_\theta(\tau)=p(s_1)\prod_{t=1}^H\pi_\theta(a_t\mid s_t)p(s_{t+1}\mid s_t,a_t)$$

新旧概率相除，再消去相同因子：

$$\frac{p_{\theta'}(\tau)}{p_\theta(\tau)}=\frac{p(s_1)\prod_{t=1}^H\pi_{\theta'}(a_t\mid s_t)p(s_{t+1}\mid s_t,a_t)}{p(s_1)\prod_{t=1}^H\pi_\theta(a_t\mid s_t)p(s_{t+1}\mid s_t,a_t)}=\prod_{t=1}^H\frac{\pi_{\theta'}(a_t\mid s_t)}{\pi_\theta(a_t\mid s_t)}$$

**为什么能约：** 比较的是**同一条轨迹**在两个策略下的概率。初始分布、环境转移完全相同，只有动作概率不同。因此实际只需保存旧动作概率，再计算新策略对同一动作的概率。

**隐患在哪里：** 剩下 $H$ 个比值连乘。沿某条路径若每项是 $1.1$，乘积就是 $1.1^H$；若每项是 $0.9$，则是 $0.9^H$。这说明可能出现指数级放大或缩小，不表示每条真实路径都必然如此。

### 公式 6 · Slide 8：同一个 log-derivative 恒等式 {#formula-6}

> **这条公式的任务：** 把概率导数换成概率乘 log 概率导数，方便代回重要性采样目标。

$$\nabla_{\theta'}\log p_{\theta'}(\tau)=\frac{\nabla_{\theta'}p_{\theta'}(\tau)}{p_{\theta'}(\tau)}$$

两边乘 $p_{\theta'}(\tau)$：

$$\nabla_{\theta'}p_{\theta'}(\tau)=p_{\theta'}(\tau)\nabla_{\theta'}\log p_{\theta'}(\tau)$$

先用 log 的链式法则，再乘回概率。这与 Lecture 5 的使用方向相同：把 $\nabla p$ 换成 $p\nabla\log p$。**这里没有新增梯度缩写。**

### 公式 7 · Slide 8：只对新参数求导 {#formula-7}

> **这条公式的任务：** 分清采样分布、分母、奖励固定，只有分子带待优化参数。

先再次展开为积分，明确导数作用在哪：

$$J(\theta')=\int p_\theta(\tau)\frac{p_{\theta'}(\tau)}{p_\theta(\tau)}r(\tau)\,d\tau$$

把梯度移入积分：

$$\nabla_{\theta'}J(\theta')=\int p_\theta(\tau)\frac{\nabla_{\theta'}p_{\theta'}(\tau)}{p_\theta(\tau)}r(\tau)\,d\tau$$

代入公式 6，再认出 $p_\theta(\tau)$ 乘整个被平均量：

$$\nabla_{\theta'}J(\theta')=\int p_\theta(\tau)\left[\frac{p_{\theta'}(\tau)}{p_\theta(\tau)}\nabla_{\theta'}\log p_{\theta'}(\tau)r(\tau)\right]\,d\tau$$

因此：

$$\nabla_{\theta'}J(\theta')=\mathbb E_{\tau\sim p_\theta}\left[\frac{p_{\theta'}(\tau)}{p_\theta(\tau)}\nabla_{\theta'}\log p_{\theta'}(\tau)r(\tau)\right]$$

**逐项拆：** 旧分布告诉我们从哪里取样；比值把旧样本重新加权；log 概率梯度告诉参数往哪里动；总回报告诉这条轨迹的权重。

**自洽性检查：** 在 $\theta'=\theta$ 处，比值为 $1$，得到：

$$\left.\nabla_{\theta'}J(\theta')\right|_{\theta'=\theta}=\mathbb E_{\tau\sim p_\theta}[\nabla_\theta\log p_\theta(\tau)r(\tau)]$$

正好接回 Lecture 5。总体等式是精确的；用有限旧样本估计它，仍可能方差很大。

### 公式 8 · Slide 9：完整 off-policy 梯度与因果性 {#formula-8}

> **这条公式的任务：** 展开轨迹权重与回报，严格说明每条奖励究竟需要保留到哪一步。

将公式 7 的三部分分别展开：

$$\nabla_{\theta'}J(\theta')=\mathbb E_{\tau\sim p_\theta}\left[\left(\sum_{t=1}^H\nabla_{\theta'}\log\pi_{\theta'}(a_t\mid s_t)\right)\left(\prod_{k=1}^H\frac{\pi_{\theta'}(a_k\mid s_k)}{\pi_\theta(a_k\mid s_k)}\right)\left(\sum_{t'=1}^H r(s_{t'},a_{t'})\right)\right]$$

这里 $t$ 标记求梯度的动作，$t'$ 标记某条奖励，$k$ 只是权重乘积的下标。

**先在目标上用因果性：** 第 $t'$ 步奖励不依赖其后的动作；未来权重在给定前缀后的条件期望为 $1$。于是：

$$J(\theta')=\mathbb E_{\tau\sim p_\theta}\left[\sum_{t'=1}^H\left(\prod_{k=1}^{t'}\frac{\pi_{\theta'}(a_k\mid s_k)}{\pi_\theta(a_k\mid s_k)}\right)r(s_{t'},a_{t'})\right]$$

**对前缀乘积求导：** 它的 log 导数只含 $1,\ldots,t'$：

$$\nabla_{\theta'}J(\theta')=\mathbb E_{\tau\sim p_\theta}\left[\sum_{t'=1}^H\left(\prod_{k=1}^{t'}\frac{\pi_{\theta'}(a_k\mid s_k)}{\pi_\theta(a_k\mid s_k)}\right)\left(\sum_{t=1}^{t'}\nabla_{\theta'}\log\pi_{\theta'}(a_t\mid s_t)\right)r(s_{t'},a_{t'})\right]$$

**交换求和顺序：** 原来先选奖励 $t'$，再选它之前的动作 $t$；现在先选动作 $t$，再选它之后的奖励 $t'$：

$$\nabla_{\theta'}J(\theta')=\mathbb E_{\tau\sim p_\theta}\left[\sum_{t=1}^H\nabla_{\theta'}\log\pi_{\theta'}(a_t\mid s_t)\sum_{t'=t}^H\left(\prod_{k=1}^{t'}\frac{\pi_{\theta'}(a_k\mid s_k)}{\pi_\theta(a_k\mid s_k)}\right)r(s_{t'},a_{t'})\right]$$

最后把每条奖励的权重拆成两段，补全原笔记略去的部分：

$$\nabla_{\theta'}J(\theta')=\mathbb E_{\tau\sim p_\theta}\left[\sum_{t=1}^H\nabla_{\theta'}\log\pi_{\theta'}(a_t\mid s_t)\left(\prod_{k=1}^{t}\frac{\pi_{\theta'}(a_k\mid s_k)}{\pi_\theta(a_k\mid s_k)}\right)\sum_{t'=t}^H\left(\prod_{k=t+1}^{t'}\frac{\pi_{\theta'}(a_k\mid s_k)}{\pi_\theta(a_k\mid s_k)}\right)r(s_{t'},a_{t'})\right]$$

- 外层乘积覆盖 $1,\ldots,t$，修正直到当前动作的前缀。
- 内层乘积覆盖 $t+1,\ldots,t'$，修正从当前动作之后到这条奖励的未来。
- **内层从 $t+1$ 开始。** 若再从 $t$ 开始，会把当前动作比值算两次；当 $t'=t$ 时，内层空乘积为 $1$。
- 删除 $t'$ 以后的权重是严格等式；再忽略内层 $t+1,\ldots,t'$ 的权重，就引入了额外近似。

两种因果性都出现了：动作只配当前及未来奖励；每条奖励只配到自身时刻的概率比。完整的条件期望证明与两步例子见 [因果性精读](#causality-detail)。

### 公式 9 · Slide 10：从长连乘到单步替代目标 {#formula-9}

> **这条公式的任务：** 明确“边缘化是等式，替换状态分布与固定旧优势是局部近似”，不能把两者合成一步。

**第 1 步：对状态—动作联合分布做精确分解。**

$$\frac{p_{\theta'}(s_t,a_t)}{p_\theta(s_t,a_t)}=\frac{p_{\theta'}(s_t)}{p_\theta(s_t)}\frac{\pi_{\theta'}(a_t\mid s_t)}{\pi_\theta(a_t\mid s_t)}$$

第一个因子修正“来到这个状态”的概率；第二个因子修正“到这里后选择这个动作”的概率。注意状态分布写 $p(s_t)$，动作条件分布才写 $\pi(a_t\mid s_t)$。

**第 2 步：说明路径连乘与状态边缘比值的关系。**

$$\frac{p_{\theta'}(s_t)}{p_\theta(s_t)}=\mathbb E_{\tau\sim p_\theta}\left[\left.\prod_{k=1}^{t-1}\frac{\pi_{\theta'}(a_k\mid s_k)}{\pi_\theta(a_k\mid s_k)}\right|s_t\right]$$

多条前缀都可能走到同一个状态。**先对这些前缀取条件平均，才得到状态比值；一条具体路径的连乘通常不等于它。** 图中把这层桥接单列出来。

**第 3 步：保留两个比值时，精确梯度还需要新策略优势。**

$$\nabla_{\theta'}J(\theta')=\sum_{t=1}^H\mathbb E_{(s_t,a_t)\sim p_\theta}\left[\frac{p_{\theta'}(s_t)}{p_\theta(s_t)}\frac{\pi_{\theta'}(a_t\mid s_t)}{\pi_\theta(a_t\mid s_t)}\nabla_{\theta'}\log\pi_{\theta'}(a_t\mid s_t)A^{\pi_{\theta'}}(s_t,a_t)\right]$$

状态概率比难算，新策略优势也还没有。于是进入局部替代目标：**沿用旧状态分布，使用固定的旧策略优势**，只让动作分布变化。

$$\sum_{t=1}^H\mathbb E_{s_t\sim p_\theta}\left[\sum_{a_t}\pi_{\theta'}(a_t\mid s_t)A^{\pi_\theta}(s_t,a_t)\right]=\sum_{t=1}^H\mathbb E_{(s_t,a_t)\sim p_\theta}\left[\frac{\pi_{\theta'}(a_t\mid s_t)}{\pi_\theta(a_t\mid s_t)}A^{\pi_\theta}(s_t,a_t)\right]$$

这两个式子之间是动作层面的 IS 等式；**整个表达式作为真实回报改变量的替代，则是近似**。由性能差异恒等式可证明，它在 $\theta'=\theta$ 处的梯度等于真实目标梯度；离开该点后一般不再相等。具体原因见 [一阶近似精读](#first-order-detail)；这一性质对应 [TRPO 原论文的局部替代目标](https://proceedings.mlr.press/v37/schulman15.pdf)。

**第 4 步：用固定的旧 GAE 估计优势，再对经验目标求导。**

$$\nabla_{\theta'}\left[\frac1N\sum_{i=1}^N\sum_{t=1}^H\frac{\pi_{\theta'}(a_t^{(i)}\mid s_t^{(i)})}{\pi_\theta(a_t^{(i)}\mid s_t^{(i)})}\hat A_t^{(i)}\right]=\frac1N\sum_{i=1}^N\sum_{t=1}^H\frac{\pi_{\theta'}(a_t^{(i)}\mid s_t^{(i)})}{\pi_\theta(a_t^{(i)}\mid s_t^{(i)})}\nabla_{\theta'}\log\pi_{\theta'}(a_t^{(i)}\mid s_t^{(i)})\hat A_t^{(i)}$$

左边是明确写出的**经验替代目标梯度**，右边由 log-trick 得到。不要直接把它标成任意 $\theta'$ 处的精确 $\nabla_{\theta'}J$。有限批次、GAE 误差和局部近似，是三件不同的事。

### 公式 10b · Slide 11：同一批数据更新 K 次 {#formula-10b}

> **这条公式的任务：** 把公式 9 放入循环；原笔记编号为 10b，这里保留它的位置。

1. 用旧策略 $\pi_\theta$ 采样，保存每个动作的旧 log 概率。
2. 拟合 critic、计算 $\hat A_t^{(i)}$；用于当前 actor 内循环的优势固定。
3. 初始化 $\theta'\leftarrow\theta$。
4. 重复下面这个更新 $K$ 次：

$$\theta'\leftarrow\theta'+\alpha\nabla_{\theta'}\left[\frac1N\sum_{i=1}^N\sum_{t=1}^H\frac{\pi_{\theta'}(a_t^{(i)}\mid s_t^{(i)})}{\pi_\theta(a_t^{(i)}\mid s_t^{(i)})}\hat A_t^{(i)}\right]$$

5. 令 $\theta\leftarrow\theta'$，再采下一批。

**三个固定量：** 样本、分母里的旧概率、优势。**一个变化量：** 分子里的新策略概率，随 $\theta'$ 更新重新计算。

如果每个内层小步都把分母改成当前策略，比值会重新变成 $1$，就丢掉了相对“采集这批样本的策略”的参照。另一方面，更新越多，局部近似越可能变差；因此还要处理下一部分的问题。

## Part 3：单步权重仍会漂移，clip 和 min 分别解决什么

### 公式 10 · Slide 13–14：权重波动与有限样本估计 {#formula-10}

> **这条公式的任务：** 分清总体恒等式和估计器稳定性，解释为什么“可以算”还不够。

回到轨迹 IS，沿用原笔记已有的记号：

$$w(\tau)=\frac{p_{\theta'}(\tau)}{p_\theta(\tau)},\qquad J(\theta')=\mathbb E_{\tau\sim p_\theta}[w(\tau)r(\tau)]$$

这是精确换分布表达式；公式 9 使用旧状态分布与旧优势的目标，才是本页讨论的局部 surrogate。不要因为都含比值，就将这两者视为同一个等式。

对于独立轨迹样本，且二阶矩存在：

$$\operatorname{Var}\left[\frac1N\sum_{i=1}^Nw(\tau^{(i)})r(\tau^{(i)})\right]=\frac1N\left(\mathbb E_{p_\theta}[w(\tau)^2r(\tau)^2]-J(\theta')^2\right)$$

**看平方项：** 少量很大的权重可能让二阶矩变大，使一小撮样本主导结果。梯度估计还乘着 $\nabla\log p$，稳定性同样取决于完整乘积。不是任何一个权重离 $1$ 远，就必然“方差爆炸”。

单步比值避免了长连乘，但新旧动作分布差得太远时也可能出现集中在少数样本上的权重。[clip 精读](#clip-detail) 用 ESS 的五样本数字例展示这一点。

### 公式 11 · Slide 14：clip 裁的是目标里的系数 {#formula-11}

> **这条公式的任务：** 看清嵌套 min/max 如何裁剪，区分裁剪系数与真实概率比值。

从这里开始讨论**单个状态—动作样本**，用原笔记已有的 $w,w_c$ 分析分段函数：

$$w=\frac{\pi_{\theta'}(a_t\mid s_t)}{\pi_\theta(a_t\mid s_t)},\qquad w_c=\operatorname{clip}(w,1-\epsilon,1+\epsilon)=\max\{1-\epsilon,\min\{1+\epsilon,w\}\}$$

**从内往外读：** 里层 min 给系数设上界；外层 max 给系数设下界；原始的 $w$ 没有被重新定义。

$$w_c=\begin{cases}1-\epsilon,&w\lt1-\epsilon\\w,&1-\epsilon\le w\le1+\epsilon\\1+\epsilon,&w\gt1+\epsilon\end{cases}$$

若暂时只用 plain clip 目标 $w_c\hat A$，且优势固定，那么区间外这一项对 $w$ 的导数为零：

$$\frac{\partial(w_c\hat A)}{\partial w}=0\qquad(w\lt1-\epsilon\ \text{或}\ w\gt1+\epsilon)$$

**但两件事不能混：**

$$w_c\in[1-\epsilon,1+\epsilon]\quad\not\Rightarrow\quad w\in[1-\epsilon,1+\epsilon]$$

新策略是一张共享参数的网络。别的样本梯度、softmax 归一化和一次有限步长，都能把这个样本的真实比值推到区间外。clip 改的是优化目标的激励，并没有把参数投影回某个硬约束集合。[PPO 官方教学文档](https://spinningup.openai.com/en/latest/algorithms/ppo.html) 也明确区分这一点，并介绍基于 KL 的提前停止。

### 公式 12 · Slide 15：min 恢复朝错误方向移动时的梯度 {#formula-12}

> **这条公式的任务：** 按优势正负分析：哪一端该变平，哪一端必须继续付代价。

plain clip 在两端都变平。如果一个优势为负的动作，概率反而被别的样本更新推高到区间外，这一项已经没有纠正梯度。优势为正的动作被挤到下界之外，也有同样问题。

PPO 对每个样本取：

$$\min\{w\hat A,\ w_c\hat A\}$$

**逐项拆：** 第一项保留原始比值，第二项使用裁剪系数；目标要最大化，所以取较小值让“账面结果”更保守。这个值逐点不大于未裁剪的 surrogate 项，**不能据此称它为真实回报 $J$ 的通用下界**。

#### 先按优势正负拆，再看越界方向 {#clip-cases}

当 $\hat A\gt0$，乘正数保序：

$$\min\{w\hat A,w_c\hat A\}=\hat A\min\{w,1+\epsilon\}$$

好动作概率升到上界之后不再额外奖励；若概率被压低，原始斜率仍在，仍希望把它提高。

当 $\hat A\lt0$，乘负数翻转大小关系：

$$\min\{w\hat A,w_c\hat A\}=\hat A\max\{w,1-\epsilon\}$$

坏动作概率降到下界之后不再额外奖励；若概率反而增大，原始斜率仍在，仍希望把它压低。$\hat A=0$ 时这项恒为零。

取 $\epsilon=0.1$、$\hat A=\pm2$。下表导数针对 $w$，避开不可微的裁剪边界；实际参数梯度还要乘 $\nabla_{\theta'}w$：

| 情形 | $w$ | $\hat A$ | $w\hat A$ | $w_c\hat A$ | min 结果 | plain clip 导数 | PPO 导数 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 好动作，已经提高过头 | 1.5 | $+2$ | 3.0 | 2.2 | **2.2** | 0 | **0** |
| 坏动作，已经降低过头 | 0.7 | $-2$ | -1.4 | -1.8 | **-1.8** | 0 | **0** |
| 好动作，反而被压低 | 0.7 | $+2$ | 1.4 | 1.8 | **1.4** | 0 | **+2** |
| 坏动作，反而被提高 | 1.5 | $-2$ | -3.0 | -2.2 | **-3.0** | 0 | **−2** |

**min 的作用是恢复后两格的纠正梯度。** 让超出区间的项变平，plain clip 已经做到了；min 让“有利方向走得足够远”的那一端平，“不利方向”的那一端继续保留斜率。

再看坏动作 $\hat A=-2$：

| $w$ | 1.1 | 1.5 | 3.0 | 10 |
|---|---:|---:|---:|---:|
| plain clip 的贡献 | -2.2 | -2.2 | -2.2 | -2.2 |
| PPO min 的贡献 | -2.2 | -3.0 | -6.0 | -20 |

这表示代价不会在裁剪边界被封住。对固定离散动作，实际还受 $w\le1/\pi_\theta(a_t\mid s_t)$ 约束；表中数值仅在原概率允许时可达，不能理解成任意离散样本的比值都无上界。

### 公式 13 · Slide 16：完整的 PPO-Clip 目标与循环 {#formula-13}

> **这条公式的任务：** 将单步动作比值、固定优势、clip/min 与多次更新装在一起。

$$\mathcal L_{\mathrm{CLIP}}(\theta')=\frac1N\sum_{i=1}^N\sum_{t=1}^H\min\left\{\frac{\pi_{\theta'}(a_t^{(i)}\mid s_t^{(i)})}{\pi_\theta(a_t^{(i)}\mid s_t^{(i)})}\hat A_t^{(i)},\ \operatorname{clip}\left(\frac{\pi_{\theta'}(a_t^{(i)}\mid s_t^{(i)})}{\pi_\theta(a_t^{(i)}\mid s_t^{(i)})},1-\epsilon,1+\epsilon\right)\hat A_t^{(i)}\right\}$$

**怎么读：** 对每条旧轨迹的每一步，同时计算未裁剪和裁剪后的“比值 × 优势”，取较小者，再求和并对轨迹平均。实际代码常对全部有效时间步取平均；固定 $H$ 时只差常数缩放，学习率与其他 loss 权重也需使用一致约定。

**现在优化的就是这个目标：**

$$\theta'\leftarrow\theta'+\alpha\nabla_{\theta'}\mathcal L_{\mathrm{CLIP}}(\theta')$$

它是裁剪替代目标的梯度，通常不等于真实回报梯度。核心结构与 [PPO 原论文](https://arxiv.org/abs/1707.06347) 的裁剪目标一致。

#### 一轮更新里谁固定、谁变化 {#implementation-loop}

1. **采样。** 用 $\pi_\theta$ 跑环境，保存状态、动作、奖励、终止标记和旧动作 log 概率。
2. **算估计量。** 用 critic 与 GAE 得到当前批次的优势和价值目标。
3. **固定参照。** 令 $\theta'=\theta$；旧 log 概率、actor 使用的优势不参与这轮 actor 的自动微分。
4. **重复优化。** 对同一批数据取 minibatch，重新算新 log 概率、概率比和 $\mathcal L_{\mathrm{CLIP}}$，走若干梯度步。若使用最小化优化器，actor loss 取 $-\mathcal L_{\mathrm{CLIP}}$。
5. **更新采样策略。** 本批内层训练结束后令 $\theta\leftarrow\theta'$，采集新数据。

比值在实现中通常由 log 概率之差计算，保持同一动作、同一采样分布参照：

$$\frac{\pi_{\theta'}(a_t\mid s_t)}{\pi_\theta(a_t\mid s_t)}=\exp\big(\log\pi_{\theta'}(a_t\mid s_t)-\log\pi_\theta(a_t\mid s_t)\big)$$

**两个配套组件：** critic 用价值损失训练；可在最大化目标中加入熵奖励，以鼓励策略保留随机性。离散动作熵是：

$$\mathcal H(\pi_{\theta'}(\cdot\mid s_t))=-\sum_a\pi_{\theta'}(a\mid s_t)\log\pi_{\theta'}(a\mid s_t)$$

若采用熵系数 $\beta$，可最大化 $\mathcal L_{\mathrm{CLIP}}+\frac{\beta}{N}\sum_{i,t}\mathcal H(\pi_{\theta'}(\cdot\mid s_t^{(i)}))$。这是额外训练项，不属于 clip/min 恒等变形。

**分类上仍要分清：** 本讲从 off-policy 校正推到旧批次内多次更新，但 PPO 通常归为 **on-policy 算法**；它依靠近期采样并及时刷新，不能因此任意复用非常陈旧的 replay 数据。[算法分类与实现说明](https://spinningup.openai.com/en/latest/algorithms/ppo.html)

## 四个最容易卡住的地方，展开精读

### 精读 1：为什么 ∇ log π 叫“单步 score” {#score-detail}

**先认名字。** “score”在这里是统计学中对数概率对参数的梯度，不是奖励，也不是模型给动作打的分数：

$$\nabla_\theta\log\pi_\theta(a_t\mid s_t)$$

它是一个与参数同维的向量。“单步”指只取一个时刻的动作条件概率；整条轨迹则是各步之和：

$$\nabla_\theta\log p_\theta(\tau)=\sum_{t=1}^H\nabla_\theta\log\pi_\theta(a_t\mid s_t)$$

这是展开轨迹 log 概率后的精确恒等式，环境项不显式依赖参数而消失。每步都完整写出梯度，不为它新设字母。

#### 性质一：在自己的分布下平均为零

固定状态，允许交换求导与求和、支持不随参数产生边界项时：

$$\mathbb E_{a\sim\pi_\theta(\cdot\mid s)}[\nabla_\theta\log\pi_\theta(a\mid s)]=\sum_a\pi_\theta(a\mid s)\frac{\nabla_\theta\pi_\theta(a\mid s)}{\pi_\theta(a\mid s)}=\nabla_\theta\sum_a\pi_\theta(a\mid s)=0$$

第一步展开期望；第二步 log 求导并约分；第三步概率和为 $1$。连续动作替换成积分，结论需要相应正则条件。

这解释了公式 1：固定的状态 baseline 可以提出来，再乘零。**平均为零并不表示每个动作的梯度是零**；不同动作的正负贡献互相抵消。

#### 性质二：乘上待平均的量，就得到分布变化的导数

当 $f(a)$ 不显式依赖参数：

$$\nabla_\theta\mathbb E_{a\sim\pi_\theta}[f(a)]=\mathbb E_{a\sim\pi_\theta}[\nabla_\theta\log\pi_\theta(a)f(a)]$$

这正是 Lecture 5 的 log-trick。若 $f$ 本身含参数，还必须加入对 $f$ 的导数项。这里写 $a$ 是展示一般概率结构，策略实际可继续以状态为条件。

#### 性质三：与 Fisher 信息的联系

在固定状态上，score 的二阶矩形成 Fisher 信息矩阵：

$$\mathbb E_{a\sim\pi_\theta(\cdot\mid s)}\left[\nabla_\theta\log\pi_\theta(a\mid s)\nabla_\theta\log\pi_\theta(a\mid s)^\top\right]$$

因为 score 均值为零，它也是该向量的协方差。这反映分布对参数变化的局部敏感度；**它不是完整“score × 回报”策略梯度估计器的方差**。

#### “单步”不等于“每个时间步独立”

公式 3 的 $\sum_t$ 仍在，经验估计也有 $\sum_i\sum_t$。把一条轨迹展开成多个状态—动作项，并不会让同一轨迹内的时间步独立。

此外，“轨迹 score 等于单步 score 之和”是逐轨迹相等；“总回报换成 reward-to-go，再减 baseline”一般是**期望相等**，不能说单条样本上的数值完全一样。

| 名称 | 指的是什么 |
|---|---|
| 梯度 | 任意可微标量函数对参数的导数向量 |
| score | 对数概率对参数的梯度 |
| 单步 score | $\nabla_\theta\log\pi_\theta(a_t\mid s_t)$ |
| 轨迹 score | $\nabla_\theta\log p_\theta(\tau)$，等于各步完整梯度之和 |

[回到公式 3](#formula-3)，继续看采样分布为什么需要修正。

### 精读 2：为什么重要性权重也要用因果性 {#causality-detail}

**问题：** reward-to-go 去掉过去奖励能理解，为什么权重也可以缩短？

关键是：一条奖励由到它为止的状态、动作和环境随机性决定。未来动作改不了已经发生的奖励。为这个前缀量修正分布，只需前缀的概率比。

#### 先证明一条单步权重的条件平均为 1

在目标动作支持被旧策略覆盖时，固定状态 $s$：

$$\mathbb E_{a\sim\pi_\theta(\cdot\mid s)}\left[\frac{\pi_{\theta'}(a\mid s)}{\pi_\theta(a\mid s)}\right]=\sum_a\pi_\theta(a\mid s)\frac{\pi_{\theta'}(a\mid s)}{\pi_\theta(a\mid s)}=\sum_a\pi_{\theta'}(a\mid s)=1$$

约掉旧策略概率，留下新策略的归一化概率和。每个状态都成立，所以也可以继续对环境产生的状态平均。

#### 再把“未来连乘”逐层平均掉

设 $g(\tau)$ 只依赖前 $k$ 步的状态与动作。完整 IS 为：

$$\mathbb E_{p_{\theta'}}[g(\tau)]=\mathbb E_{p_\theta}\left[\left(\prod_{j=1}^{H}\frac{\pi_{\theta'}(a_j\mid s_j)}{\pi_\theta(a_j\mid s_j)}\right)g(\tau)\right]$$

将连乘在 $k$ 处分开：

$$\mathbb E_{p_\theta}\left[\left(\prod_{j=1}^{k}\frac{\pi_{\theta'}(a_j\mid s_j)}{\pi_\theta(a_j\mid s_j)}\right)g(\tau)\left(\prod_{j=k+1}^{H}\frac{\pi_{\theta'}(a_j\mid s_j)}{\pi_\theta(a_j\mid s_j)}\right)\right]$$

给定前 $k$ 步，前两项固定；先对未来取条件期望：

$$\mathbb E_{p_\theta}\left[\left.\prod_{j=k+1}^{H}\frac{\pi_{\theta'}(a_j\mid s_j)}{\pi_\theta(a_j\mid s_j)}\right|s_{1:k},a_{1:k}\right]=1$$

**为什么连乘也为 1：** 从最后一个动作往前，用上一节的单步恒等式逐层消去，再对环境转移平均。这是全期望公式，**不是假定时间步独立，然后把期望拆成乘积**。

因此得到前缀版 IS：

$$\mathbb E_{p_{\theta'}}[g(\tau)]=\mathbb E_{p_\theta}\left[\left(\prod_{j=1}^{k}\frac{\pi_{\theta'}(a_j\mid s_j)}{\pi_\theta(a_j\mid s_j)}\right)g(\tau)\right]$$

#### 应用于“第 t 步梯度 × 第 t′ 步奖励”

当 $t'\ge t$，这一项只依赖到 $t'$，所以权重可以截到 $t'$：

$$\left(\prod_{k=1}^{t'}\frac{\pi_{\theta'}(a_k\mid s_k)}{\pi_\theta(a_k\mid s_k)}\right)=\left(\prod_{k=1}^{t}\frac{\pi_{\theta'}(a_k\mid s_k)}{\pi_\theta(a_k\mid s_k)}\right)\left(\prod_{k=t+1}^{t'}\frac{\pi_{\theta'}(a_k\mid s_k)}{\pi_\theta(a_k\mid s_k)}\right)$$

两段必须恰好拼接，既不能少一步，也不能在 $t$ 重叠。若 $t'\lt t$，在目标策略分布下，过去奖励对当前动作固定，单步 score 的条件平均为零；于是这些配对可以在期望中消去。

| 改写 | 删去什么 | 严格理由 |
|---|---|---|
| reward-to-go | 当前动作之前的奖励配对 | 单步 score 的条件均值为 $0$ |
| 前缀 IS | 奖励时刻之后的权重因子 | 未来权重的条件均值为 $1$ |
| 再忽略未来回报内部权重 | $t+1,\ldots,t'$ 的因子 | 一般不再是等式；这些因子与奖励有关 |

对单个前缀量，把未来随机性条件平均掉具有 Rao–Blackwell 的降方差性质；对多个相互关联项的总梯度，不能不分析协方差就宣称方差一定严格下降。

#### 两步轨迹：亲眼看第二步权重消失

考虑 $t=1,t'=1$ 的配对：

$$\mathbb E_{p_\theta}\left[\frac{\pi_{\theta'}(a_1\mid s_1)}{\pi_\theta(a_1\mid s_1)}\frac{\pi_{\theta'}(a_2\mid s_2)}{\pi_\theta(a_2\mid s_2)}\nabla_{\theta'}\log\pi_{\theta'}(a_1\mid s_1)r(s_1,a_1)\right]$$

固定 $s_1,a_1,s_2$，只对 $a_2$ 求条件期望。其余项不含 $a_2$，而第二步比值的条件平均为 $1$，于是：

$$\mathbb E_{p_\theta}\left[\frac{\pi_{\theta'}(a_1\mid s_1)}{\pi_\theta(a_1\mid s_1)}\nabla_{\theta'}\log\pi_{\theta'}(a_1\mid s_1)r(s_1,a_1)\right]$$

若改成 $t=1,t'=2$，奖励 $r(s_2,a_2)$ 会随 $a_2$ 变化，不能提出来。第二步比值仍需保留。**权重到哪里结束，由这条被平均的量依赖到哪里决定。**

[回到公式 8](#formula-8)。接下来消除长连乘要经过另外的近似，不能继续把它当成“未来均值等于 1”。

### 精读 3：长连乘怎样接到单步比值，为什么叫一阶近似 {#first-order-detail}

这一步包含三种不同操作：**路径边缘化、改变状态分布、固定旧优势**。将它们拆开，才知道每个等号与近似号的来源。

#### 路径权重不等于状态比值：一个合流例子

假设第一步有三条路线。前两条都会到达同一个状态 $s$，第三条到别处：

| 路线 | 旧概率 | 新概率 | 路径比值 |
|---|---:|---:|---:|
| 路线 1 → $s$ | 0.2 | 0.4 | 2 |
| 路线 2 → $s$ | 0.2 | 0.1 | 0.5 |
| 路线 3 → 别处 | 0.6 | 0.5 | $5/6$ |

到达 $s$ 的状态概率比是：

$$\frac{p_{\theta'}(s)}{p_\theta(s)}=\frac{0.4+0.1}{0.2+0.2}=1.25$$

它既不是路径 1 的 $2$，也不是路径 2 的 $0.5$。在旧策略下，已知到达 $s$，两条路线各占一半，因此：

$$\mathbb E_{p_\theta}[\text{前缀权重}\mid s]=0.5\times2+0.5\times0.5=1.25$$

这就是公式 9 的条件期望桥接。状态比值压缩了到达同一状态的多条路径，不是对某一条路径做代数约分。

#### 从精确的回报差，构造局部 surrogate

有限时域、无折扣下，性能差异恒等式写成：

$$J(\theta')-J(\theta)=\sum_{t=1}^H\mathbb E_{s_t\sim p_{\theta'}}\left[\sum_{a_t}\pi_{\theta'}(a_t\mid s_t)A^{\pi_\theta}(s_t,a_t)\right]$$

**逐处读：** 状态来自新策略；动作来自新策略；优势却用旧策略来衡量。这个组合是精确的性能差异恒等式，不能与“新策略精确梯度使用新优势”的公式混淆。[TRPO 原论文](https://proceedings.mlr.press/v37/schulman15.pdf) 以这类恒等式构造局部目标。

为什么它成立？旧优势可写成单步奖励加旧下一状态价值、减旧当前价值。在新轨迹上逐时刻相加，中间价值项望远镜消去，剩新策略总回报减旧策略起始价值，也就是 $J(\theta')-J(\theta)$。

现在**只把这个式子的状态分布换成旧分布**，得到局部替代量：

$$\sum_{t=1}^H\mathbb E_{s_t\sim p_\theta}\left[\sum_{a_t}\pi_{\theta'}(a_t\mid s_t)A^{\pi_\theta}(s_t,a_t)\right]$$

对内层动作使用 IS，就得到公式 9 的单步动作比值形式。这里没有假装状态分布已被完整校正，而是明确用旧分布作局部替代。

#### 一阶匹配来自哪里：把误差写出来

离散状态下，“精确回报差 − 局部替代量”为：

$$\sum_{t=1}^H\sum_{s_t}\big[p_{\theta'}(s_t)-p_\theta(s_t)\big]\left[\sum_{a_t}\pi_{\theta'}(a_t\mid s_t)A^{\pi_\theta}(s_t,a_t)\right]$$

在 $\theta'=\theta$ 时，第一方括号为零；第二方括号也为零，因为旧策略对自身优势的平均为零：

$$\sum_{a_t}\pi_\theta(a_t\mid s_t)A^{\pi_\theta}(s_t,a_t)=0$$

在光滑、有限时域等局部条件下，参数改变量很小时，这两个因子都从零开始一阶变化，**乘积才是二阶小量**：

$$J(\theta')-J(\theta)-\sum_{t=1}^H\mathbb E_{(s_t,a_t)\sim p_\theta}\left[\frac{\pi_{\theta'}(a_t\mid s_t)}{\pi_\theta(a_t\mid s_t)}A^{\pi_\theta}(s_t,a_t)\right]=O(\|\theta'-\theta\|^2)$$

这说明在旧参数处二者的梯度相同。**不是说状态分布变化本身只有二阶大小**；它一般就有一阶变化，是它乘上的“期望旧优势”在起点也为零，才消去一阶误差。

#### 换成 GAE 后，还多了估计误差

上述论证使用真实的 $A^{\pi_\theta}$。实际 $\hat A_t^{(i)}$ 来自有限数据与 critic/GAE，通常不能要求每个状态下精确满足零均值。因此应分别记住：

- 真实优势下，局部 surrogate 在旧参数处匹配真实梯度。
- 经验 GAE 版本是这个目标的估计，另有采样误差与可能的估计偏差。
- 连续多次更新后会离开旧参数附近，局部近似并不自动有效。

自动驾驶的直觉是：旧数据多在原策略常到的路段；若新策略开始进入以前少见的路段，只修正这些旧路段上的动作概率，无法凭空提供新路段的数据。clip 是控制更新激励的一种实用方式，也可以结合 KL 检查；它不是强制所有状态分布接近的证明。

[回到公式 9](#formula-9)，或继续 [同批更新](#formula-10b)。

### 精读 4：权重离散、ESS，以及 clip 为什么还要 min {#clip-detail}

#### 先看“均值为 1”为什么仍可能不稳定

完整支持条件下：

$$\mathbb E_{\tau\sim p_\theta}[w(\tau)]=\int p_\theta(\tau)\frac{p_{\theta'}(\tau)}{p_\theta(\tau)}\,d\tau=1$$

这说的是总体均值。它允许“大多数权重很小，少数权重很大”，也不要求每一批样本的平均恰好为 $1$。

实际关心的是 $w(\tau)r(\tau)$ 或加权梯度的二阶矩。单看“某个比值离 1 多远”不够；回报、梯度大小以及它们和权重的关系也重要。

#### 五个样本的 ESS 例子

原笔记使用的经验有效样本量指标为：

$$\operatorname{ESS}=\frac{\left(\sum_{i=1}^Nw_i\right)^2}{\sum_{i=1}^Nw_i^2}$$

这里 $w_i$ 就是第 $i$ 个样本的权重。它描述非负权重的集中程度；不是策略梯度准确度的精确换算，也没有计算轨迹内部相关性。

| 五个权重 | 总和 | 平方和 | ESS |
|---|---:|---:|---:|
| $0.9,\ 1,\ 1.1,\ 0.95,\ 1.05$ | 5 | 5.025 | $\approx4.975$ |
| $0.02,\ 0.05,\ 0.03,\ 0.1,\ 8$ | 8.2 | 64.0138 | $\approx1.050$ |

第一组比较均匀，五个样本都在参与；第二组最后一个权重占绝大部分。若所有权重都相同，即使不等于 $1$，ESS 也等于 $N$，可见它衡量的是相对集中程度。

#### clip 变平了，为什么比值还会继续跑

**共享参数。** 一个样本的裁剪分支梯度为零，不表示整张网络梯度为零；别的样本仍会更新相同参数，从而改变它的概率。

**归一化耦合。** 同一状态三个动作原概率为 $0.3,0.3,0.4$。仅把第三个动作的未归一化 softmax 权重翻倍，重新归一化后：

$$\pi_{\theta'}(a_1\mid s)=\frac{0.3}{0.3+0.3+0.8}\approx0.2143,\qquad\frac{\pi_{\theta'}(a_1\mid s)}{\pi_\theta(a_1\mid s)}\approx0.7143$$

即便没有单独降低动作 1 的 logit，它的比值也会低于 $0.9$。概率共享总量，不能把每个动作的变化视为独立。

**有限步长。** 在区间内求得一个非零梯度后，一次更新可能跨过边界；clip 没有在更新结束后执行概率投影。

因此，plain clip 区间外的零梯度会留下两种问题：好动作被其他更新压低，或坏动作被其他更新抬高。这正是 [四格表](#clip-cases) 的后两格。

#### 用导数再读一遍 min

优势固定、避开边界时：

$$\frac{\partial}{\partial w}\min\{w\hat A,w_c\hat A\}=\begin{cases}0,&\hat A\gt0,\ w\gt1+\epsilon\\0,&\hat A\lt0,\ w\lt1-\epsilon\\\hat A,&\text{其余非边界情形}\end{cases}$$

若 $\hat A\gt0$ 而比值太低，导数仍为正，梯度上升会尝试提高比值；若 $\hat A\lt0$ 而比值太高，导数仍为负，梯度上升会尝试降低比值。实际多个样本梯度叠加后，单个比值不保证按此方向移动。

**为什么不是“所有权重都被界住了”：** min 在不利方向会选回未裁剪分支，所以完整 PPO 项并没有在两端统一截断。不能仅凭 clip 的系数有界，就声称 PPO 保证有限方差、策略距离有界或真实回报单调提高。

[回到完整 PPO 公式](#formula-13)。

## 全公式速查 {#formula-index}

| 原编号 | 本讲的任务 | 关键区别 |
|---|---|---|
| [1](#formula-1) | MC 回报减 baseline | 梯度不变，不等于优势估计总是无偏 |
| [2](#formula-2) | on-policy AC + GAE | 当前基础循环每批更新一次 |
| [3](#formula-3) | 定位分布错位 | 新状态、新动作、新优势都与新策略有关 |
| [4](#formula-4) | IS 换分布 | 展开积分 → 插入比值 → 识别期望 |
| [5](#formula-5) | 轨迹权重分解 | 同一环境因子抵消，只剩策略比连乘 |
| [6](#formula-6) | log-trick | 完整梯度，不另造缩写 |
| [7](#formula-7) | 求新参数梯度 | 旧采样分布与分母固定 |
| [8](#formula-8) | 因果性 | 奖励在 $t'$，权重就到 $t'$；拆分从 $t+1$ 接续 |
| [9](#formula-9) | 单步局部替代目标 | 边缘化是等式，替代状态分布是近似 |
| [10b](#formula-10b) | 同批更新 $K$ 次 | 分母与优势固定，分子不断重算 |
| [10](#formula-10) | 估计方差 | 看完整加权量的二阶矩 |
| [11](#formula-11) | plain clip | 系数裁剪，不是概率投影 |
| [12](#formula-12) | min 的四种情况 | 有利方向封顶，不利方向保留纠正斜率 |
| [13](#formula-13) | PPO-Clip | 用裁剪 surrogate 多次更新，再刷新数据 |

## 自测：能否把每一步接回主线 {#self-check}

1. critic 不准时，MC 优势的期望是什么？为什么固定的状态 baseline 仍不改变梯度期望？
2. 重要性采样的支持条件，究竟是谁覆盖谁？
3. 期望变积分之后，怎样一步步认出另一个分布的期望？
4. 求 $\theta'$ 的导数时，哪些项固定？$\theta'=\theta$ 时为什么回到 Lecture 5？
5. 第 $t$ 步梯度配第 $t'$ 步奖励，权重需要到哪里？两段怎样拼接？
6. 路径连乘、状态比值、动作比值，三者是什么关系？
7. 一阶匹配为什么不是“状态分布变化只剩二阶”？
8. $\hat A=-2,w=1.5,\epsilon=0.1$ 时，两支分别多少，min 选哪支？
9. 一个样本的裁剪项梯度为零，为什么它的概率仍可能改变？
10. PPO 内循环固定什么、更新什么？为什么还需要新一批数据？

<details>
<summary>展开参考答案</summary>

1. 是 $Q^\pi-\hat V^\pi_\phi$，只有 critic 精确时才等于真实优势。固定状态 baseline 乘单步 score 的条件期望为零，所以不改变梯度期望；GAE 与拟合同批数据的相关性还要单独分析。
2. 采样分布覆盖目标分布：$p(x)\gt0$ 的地方必须有 $q(x)\gt0$。
3. $\mathbb E_p[f]\to\int pf\to\int q(p/q)f$；认出 $q$ 是密度、$(p/q)f$ 是被平均量，再写成 $\mathbb E_q[(p/q)f]$。
4. 旧分布、分母和固定轨迹奖励不随 $\theta'$ 变化；只有新概率求导。参数相同时比值为 $1$。
5. 到奖励时刻 $t'$。两段是 $1,\ldots,t$ 与 $t+1,\ldots,t'$；内层为空时乘积为 $1$。
6. 状态比值是到达该状态的前缀权重的旧分布条件平均；状态—动作联合比等于状态比乘单步动作比。
7. 状态分布差通常是一阶，但误差还乘上在起点为零的“新动作平均下的旧优势”，乘积才从二阶开始。
8. 未裁剪为 $-3$，裁剪为 $-2.2$，min 取 $-3$，保留压低坏动作概率的梯度。
9. 其他样本的共享参数更新、softmax 归一化和有限步长都能改变它；clip 没有做参数投影。
10. 固定旧 log 概率与优势，更新新参数；多轮之后局部近似与旧数据代表性会下降，因此重新采样。

</details>

## 材料与衔接 {#sources}

本页整理自本地 Lecture 9 的五篇笔记：公式逐行拆解、单步 score 精读、off-policy 因果性精读、slide 10 一阶近似精读、Part 3 方差与 clip/min 精读。网页保留其推导层次、数字例和自测用途，统一新旧参数记号，并补齐期望转换、前缀拆分和局部近似条件。

理论核对使用 [PPO 原论文](https://arxiv.org/abs/1707.06347)、[TRPO 原论文](https://proceedings.mlr.press/v37/schulman15.pdf) 与 [Spinning Up 的 PPO 说明](https://spinningup.openai.com/en/latest/algorithms/ppo.html)。

往前连接：[Lecture 2 的分布漂移](../lecture-02/) 解释“策略影响访问状态”；[Lecture 5 的 log-trick 与 baseline](../lecture-05/) 提供本讲的梯度工具。这里把两条线接起来，讨论如何在数据复用和局部更新之间取得实用折中。
