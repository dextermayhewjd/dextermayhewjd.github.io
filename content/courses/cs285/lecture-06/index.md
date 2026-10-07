---
title: "Lecture 6 · 从回报估计到 Actor-Critic 与 GAE"
description: "保留 21 条公式拆解，先看完整循环，再拆 Q/V/A、价值回归、自举、n-step、GAE、replay 与重参数化。算法集中成框，数学依据逐步展开。"
date: 2026-10-07
weight: 60
math: true
ShowToc: false
tags: [CS285, Actor-Critic, GAE, Reparameterization]
---

## 先看清这一讲在做什么 {#lecture-thread}

**Lecture 5 已给出策略梯度，但乘上的 reward-to-go 只是一次随机 rollout。Lecture 6 接着问：能否更好地估计这个乘子？** 先整体看 REINFORCE 的采样—回报—梯度—更新循环，再定位噪声来自哪。

主线是 **单样本回报 → 条件期望 Q → 状态参照 V → 优势 A → Bellman 拆解 → 学 V 的回归 → bootstrap → 完整 actor-critic → n-step → GAE。** 到这里得到 PPO 使用的优势估计；后面再讨论 replay 旧数据需要动作条件的 Q，以及可微动作上的重参数化。

图里完整算法各占一个框，右侧集中给出全部步骤公式：基础 REINFORCE、batch actor-critic、GAE 版更新、replay 的 Q 版更新、重参数化版更新。估计器与变形依据仍逐步拆，公式尽量单行，点击读正文。

{{< lecture-mindmap id="actor-critic-flow" cards="argument-cards.json" width="1660" caption="先看 REINFORCE 全循环，定位随机回报；再沿 Q、V、A、Bellman、回归与自举组成 actor-critic。n-step 与 GAE 是优势的进一步改造。另一条路用 replay 与 Q 构造固定 critic 的策略代理，再分别用 score 和 pathwise 梯度。完整循环集中在一个框旁，内部公式编号集中展示；数学依据才拆成小节点。" >}}

### 把主线接成一段话

Q 把后续动作与环境随机性条件平均，V 再把当前动作平均，A 就是具体动作相对当前状态平均的差。Bellman 把 Q 写成当前奖励加下一状态 V，所以只学 V 也能构造一个单步优势估计。

学 V 时，MC 回报可以当监督标签；bootstrap 用预测的尾部价值替换长 rollout。**单次采样不自动产生偏差，误差来自替换的 critic 与其他估计依赖。** n-step 决定真实奖励看多远，GAE 将各个合法 n-step 估计加权平均，再望远镜化成 TD 残差和。

replay 里动作来自旧策略，直接训练状态 V 的目标会混入旧动作平均。Q 显式保留动作，允许下一动作由当前策略重新采。actor 仍使用 replay 状态，因此优化的是相应固定 critic 代理；连续可微动作下，重参数化给这个代理梯度另一种估计路径。

| 当前卡点 | 阅读位置 |
|---|---|
| 完整循环里哪个量噪声大 | [起始循环](#starting-loop) → [公式 1–2](#formula-1) |
| Q、V、A 到底各平均掉什么 | [公式 2–5](#formula-2) → [Bellman 精读](#bellman-detail) |
| 为什么 MC 可以作为回归标签 | [公式 6–8](#formula-6) → [回归精读](#regression-detail) |
| 为什么 baseline 与 bootstrap 的偏差不同 | [公式 13](#formula-13) → [偏差/方差精读](#bias-detail) |
| GAE 是否把同一奖励反复算了 | [公式 14–15](#formula-14) → [GAE 展开](#gae-detail) |
| 批均值是否严格无偏 | [公式 16](#formula-16) → [自项证明](#centering-detail) |
| replay 为什么需要显式动作的 Q | [公式 17–19](#formula-17) |
| 重参数化从哪条推导岔出来 | [公式 20–21](#formula-20) → [严格性审查](#reparameterization-detail) |

<details>
<summary>展开全页目录与公式索引</summary>

{{< chapter-outline id="lecture6-outline" title="Lecture 6 阅读位置" >}}

</details>

## 符号与推导范围 {#notation}

按本地《Lecture6 公式逐行拆解》的 21 个公式组织，并整合 Q 的条件平均、Bellman、价值回归、bias/variance、GAE、中心化、replay 与重参数化的配套精读。

| 符号 | 含义 |
|---|---|
| $\theta,\phi$ | actor 与 critic 的参数 |
| $N,H,B$ | 轨迹条数、时域长度、replay 小批转移数 |
| $\hat Q_t^{(i)}$ | 单条轨迹的 reward-to-go；与学习的 $\hat Q_\phi(s,a)$ 区分 |
| $Q^\pi,V^\pi,A^\pi$ | 当前策略的真实状态—动作价值、状态价值、优势 |
| $\hat V_\phi^\pi,\hat Q_\phi^\pi$ | critic 的函数近似 |
| $y_t^{(i)},\mathcal L(\phi)$ | 固定的价值训练目标、回归损失 |
| $\gamma,\lambda,\delta_t$ | 折扣、GAE 的混合参数、TD 残差 |
| $\hat A_n,\hat A_{\mathrm{GAE}}$ | n-step 优势与 GAE 优势估计 |
| $\mu,\sigma,\bar A$ | 批优势的均值、标准差、中心化后的权重 |
| $\bar\pi,\mathcal R$ | 旧行为策略、replay buffer |
| $\mu_\theta(s),\sigma_\theta(s),\epsilon$ | 连续策略的均值、标准差、与参数无关的标准高斯噪声 |

开头回顾 Lecture 5 的有限时域无折扣版本；公式 9 起显式讨论折扣。时间为 $t=1,\ldots,H$，终端价值 $V(s_{H+1})=0$。有限时域将剩余时刻包含在状态里；否则价值不能一概写成时间不变函数。

严格从起点计算的折扣目标采用 $\sum_t\gamma^{t-1}r_t$，相应策略梯度配外层 $\gamma^{t-1}$。图里的集中 episodic 算法保留这个权重；实际展平 transition 的等权更新，要明确是按折扣占用分布采样，还是采用相应训练代理。

默认策略/critic 可微，满足交换求导与积分所需条件。baseline 无偏性论证将它作为固定状态函数；拟合同批数据的相关性、batch 标准化、bootstrap 等要各自分析。目标和优势在对应网络更新里停止梯度，不等于统计上自动独立。

## 起点：完整 REINFORCE 循环 {#starting-loop}

先整体看算法，便于定位本讲改动的地方：

$$\begin{aligned}
&1.\ \text{采样：}\quad\tau^{(i)}\sim p_\theta(\tau),\quad i=1,\ldots,N\\
&2.\ \text{实际回报：}\quad\hat Q_t^{(i)}=\sum_{t'=t}^H r(s_{t'}^{(i)},a_{t'}^{(i)})\\
&3.\ \text{估计与更新：}\quad\theta\leftarrow\theta+\frac{\alpha}{N}\sum_{i,t}\nabla_\theta\log\pi_\theta(a_t^{(i)}\mid s_t^{(i)})\hat Q_t^{(i)}\quad\Longrightarrow\quad\text{回到 1}
\end{aligned}$$

第 2 步每个乘子只来自一次实际轨迹，运气会进入第 3 步。本讲主要改造优势/回报估计，再接回完整循环；不是先更换策略梯度恒等式。


## Part 1：把单次回报变成价值与优势


### 公式 1 · Slide 3：回顾——reward-to-go 版策略梯度 {#formula-1}

> **这条公式的任务：** 定位随机回报在策略更新中的位置。

$$\nabla_\theta J(\theta)\approx\frac1N\sum_{i=1}^{N}\sum_{t=1}^{H}\nabla_\theta\log\pi_\theta(\mathbf{a}_t^{(i)}\mid\mathbf{s}_t^{(i)})\,\hat Q_t^{(i)},\qquad \hat Q_t^{(i)}=\sum_{t'=t}^{H}r(\mathbf{s}_{t'}^{(i)},\mathbf{a}_{t'}^{(i)})$$

**怎么读**："策略梯度 ≈ 每条轨迹每一步的 $\nabla\log\pi$，各自乘上『它之后的奖励之和 $\hat Q_t^{(i)}$』，再平均。"

**逐符号拆**
- $\hat Q_t^{(i)}$ —— lec5 公式 13 的 **reward-to-go**：第 $i$ 条轨迹从第 $t$ 步累加到底的奖励。帽子 ^ 提醒你这是**一条轨迹跑出来的单样本估计**。
- $\sum_{t'=t}^H$ —— 从当前步 $t$ 开始（causality，lec5 已切过）。

> 🔑 **本讲的出发点就藏在 $\hat Q_t^{(i)}$ 这个"帽子"里**：它只是**一次** rollout 的结果，运气成分极大（lec5 的国际象棋例子）。本讲全部努力 = **把这个单样本 $\hat Q$ 换成更准的估计**，从而压低方差。



### 公式 2 · Slide 4：真正想要的是"期望"reward-to-go {#formula-2}

> **这条公式的任务：** 固定起点动作，对未来随机性取条件平均。

单样本 $\hat Q_t^{(i)}$ 其实是在估计一个期望——把"未来所有可能的走法"都平均掉：

$$\hat Q_t^{(i)}\ \approx\ \sum_{t'=t}^{H}\mathbb{E}_{\pi_\theta}\big[r(\mathbf{s}_{t'},\mathbf{a}_{t'})\mid \mathbf{s}_t^{(i)},\mathbf{a}_t^{(i)}\big]$$

把这个期望命名为**真·Q 函数**：

$$\boxed{\;Q^\pi(\mathbf{s}_t,\mathbf{a}_t)=\sum_{t'=t}^{H}\mathbb{E}_{\pi_\theta}\big[r(\mathbf{s}_{t'},\mathbf{a}_{t'})\mid\mathbf{s}_t,\mathbf{a}_t\big]\;}\quad\text{（true expected reward-to-go）}$$

代回梯度：
$$\nabla_\theta J(\theta)\approx\frac1N\sum_{i=1}^{N}\sum_{t=1}^{H}\nabla_\theta\log\pi_\theta(\mathbf{a}_t^{(i)}\mid\mathbf{s}_t^{(i)})\,Q^\pi(\mathbf{s}_t^{(i)},\mathbf{a}_t^{(i)})$$

**怎么读**："把乘子从『单样本剩余奖励 $\hat Q_t^{(i)}$』换成『期望剩余奖励 $Q^\pi(\mathbf{s}_t,\mathbf{a}_t)$』。"

**逐符号拆**
- $Q^\pi(\mathbf{s}_t,\mathbf{a}_t)$ —— 没有帽子：它是**真值/期望**，不是某一次跑出来的。下标 $\pi$ 提醒它是"在策略 $\pi$ 下"的期望。
- $\mathbb{E}_{\pi_\theta}[\cdots\mid\mathbf{s}_t,\mathbf{a}_t]$ —— 固定起点 $(\mathbf{s}_t,\mathbf{a}_t)$，对**之后所有随机性**（后续动作、环境转移）取平均。

> 💡 **为什么换成期望能降方差**：$\hat Q_t^{(i)}$ 是一根羽毛飘出来的一条路；$Q^\pi$ 是把"从这点出发的所有可能路"提前算好的平均分。**用平均分当乘子，单次估计的抖动当然小得多。** 这就是 slide 那句 "can we get a better estimate?" 的答案。


条件平均的严格陈述是 $\mathbb E[\hat Q_t\mid s_t,a_t]=Q^\pi(s_t,a_t)$；某个单样本不必数值接近真值。理想已知 Q 可对单个梯度项作 Rao–Blackwell 条件平均；学习出来的 critic 和跨时间项的协方差，则不能仅凭“更像期望”就保证整个梯度方差降低。



### 公式 3 · Slide 5：把 baseline 升级成状态价值 $V$ {#formula-3}

> **这条公式的任务：** 把当前动作平均与动作相对好坏分开。

lec5 我们减过一个常数 baseline $b$（一批轨迹的平均奖励）。现在用一个**跟状态走的** baseline：

$$\nabla_\theta J(\theta)\approx\frac1N\sum_{i=1}^{N}\sum_{t=1}^{H}\nabla_\theta\log\pi_\theta(\mathbf{a}_t^{(i)}\mid\mathbf{s}_t^{(i)})\Big(Q^\pi(\mathbf{s}_t^{(i)},\mathbf{a}_t^{(i)})-V^\pi(\mathbf{s}_t^{(i)})\Big)$$

其中
$$V^\pi(\mathbf{s}_t)=\mathbb{E}_{\mathbf{a}_t\sim\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)}\big[Q^\pi(\mathbf{s}_t,\mathbf{a}_t)\big],\qquad A^\pi(\mathbf{s}_t,\mathbf{a}_t)=Q^\pi(\mathbf{s}_t,\mathbf{a}_t)-V^\pi(\mathbf{s}_t)$$

**怎么读**："乘子 = $Q$ 减 $V$。$V$ 是『把这个状态下所有动作的 $Q$，按策略概率平均』。"

**逐符号拆**
- $V^\pi(\mathbf{s}_t)$ —— **状态价值**：站在 $\mathbf{s}_t$，**还没挑动作**时的期望回报。它就是"该状态的平均水平"。
- $Q^\pi-V^\pi$ —— **优势 $A^\pi$**：这个具体动作 $\mathbf{a}_t$ 比"平均动作"好多少。
- 对照 lec5：那里 $b=\frac1N\sum r(\tau)$ 是**一个常数**；这里 $V^\pi(\mathbf{s}_t)$ **每个状态一个值**，更贴合的参照，通常用于降方差。

> 🔑 **$V$ 是"按动作平均的 $Q$"**：竖线右边给定 $\mathbf{s}_t$，对 $\mathbf{a}_t\sim\pi$ 取期望，把动作这一维平均掉，就从 $Q(\mathbf{s},\mathbf{a})$ 降成 $V(\mathbf{s})$。所以 $A=Q-V$ 天然以 0 为中心：比平均好的动作 $A>0$，差的 $A<0$。
> 🔗 **直通 GRPO**：lec5 我们说 GRPO 的"组内平均奖励当 baseline"对应常数 $b$；本页把 baseline 升级成 $V^\pi(\mathbf{s})$，正是从"组级 baseline"走向"状态级 baseline"的一步。



### 公式 4 · Slide 6：三个价值函数的正式定义 + 优势版梯度 {#formula-4}

> **这条公式的任务：** 统一三种价值并接回策略梯度。

$$\begin{aligned}
Q^\pi(\mathbf{s}_t,\mathbf{a}_t)&=\sum_{t'=t}^{H}\mathbb{E}_{\pi_\theta}\big[r(\mathbf{s}_{t'},\mathbf{a}_{t'})\mid\mathbf{s}_t,\mathbf{a}_t\big]&&\text{从 }\mathbf{s}_t\text{ 做 }\mathbf{a}_t\text{ 起的总回报}\\[4pt]
V^\pi(\mathbf{s}_t)&=\mathbb{E}_{\mathbf{a}_t\sim\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)}\big[Q^\pi(\mathbf{s}_t,\mathbf{a}_t)\big]&&\text{从 }\mathbf{s}_t\text{ 起的总回报}\\[4pt]
A^\pi(\mathbf{s}_t,\mathbf{a}_t)&=Q^\pi(\mathbf{s}_t,\mathbf{a}_t)-V^\pi(\mathbf{s}_t)&&\mathbf{a}_t\text{ 比平均好多少}
\end{aligned}$$

$$\nabla_\theta J(\theta)\approx\frac1N\sum_{i=1}^{N}\sum_{t=1}^{H}\nabla_\theta\log\pi_\theta(\mathbf{a}_t^{(i)}\mid\mathbf{s}_t^{(i)})\,A^\pi(\mathbf{s}_t^{(i)},\mathbf{a}_t^{(i)})$$

**三句话记牢区别**
- $Q^\pi$：吃两个输入 $(\mathbf{s},\mathbf{a})$ —— "**这个状态 + 这个动作**值多少分"。
- $V^\pi$：吃一个输入 $\mathbf{s}$ —— "**这个状态**值多少分（动作还没定）"。
- $A^\pi$：差值 —— "**这个动作相对该状态平均，好/坏多少**"。

> 🟨 **slide 黄字（本讲的中心思想）**：*the better this estimate, the lower the variance.* —— 精确条件平均可去掉相应未来采样噪声；学习优势还需分别考虑误差与方差。整条 actor-critic 路线就是在**把 $A^\pi$ 估得更准**。
> ⭐ **难点辨析**：别把 $V^\pi(\mathbf{s}_t)$（状态价值，一个数）和 $\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)$（策略，一个分布）搞混。$V$ 回答"这地方好不好"，$\pi$ 回答"在这地方该怎么走"。
> ❓ **卡在第一行数学上？**（"$\sum_{t'}\mathbb{E}[\cdot]$ 里，下一状态随机、下一动作按 π 随机选，这些写在哪了？"）→ 见 [Lecture6 最常卡的一步（Q 的 ΣE 定义式为什么对·摊平式与递归式是同一回事 精读）](#bellman-detail)，把这行拆成"换记号 3 步 + 真推导 1 步"，并用数字验证它与 $Q=r+\mathbb{E}[V(\mathbf{s}')]$ 完全等价。



## Part 2：用 Bellman 与回归学习 critic


### 公式 5 · Slide 8：fit 谁？把 $Q,A$ 都化简成只需要 $V$ {#formula-5}

> **这条公式的任务：** 拆出奖励与下一状态价值，区分随机性和预测误差。

把未来奖励按当前一步与之后全部拆开：

$$Q^\pi(s_t,a_t)=r(s_t,a_t)+\mathbb E_{s_{t+1}\sim p(\cdot\mid s_t,a_t)}[V^\pi(s_{t+1})]$$

这是当前无折扣版本。下一状态由环境产生，在那里未来动作再按当前策略平均，所以尾部正好是 V，而不是某个固定下一动作的 Q。

采到一个下一状态时：

$$r(s_t,a_t)+V^\pi(s_{t+1})$$

是 Q 的一个随机估计；**若 V 为真值，其条件期望就是 Q，单样本带来方差而不是自动带来偏差。**

减去当前状态的 V，得到：

$$\hat A_t=r(s_t,a_t)+V^\pi(s_{t+1})-V^\pi(s_t),\qquad\mathbb E[\hat A_t\mid s_t,a_t]=A^\pi(s_t,a_t)$$

实际用 $\hat V_\phi$ 替换真 V 后，可能因 critic 误差产生偏差。这一步使 critic 只需拟合状态价值，即可用奖励与相邻价值构造单步优势。折扣版本在下一状态 V 前加 $\gamma$。



### 公式 6 · Slide 9：策略评估 = 蒙特卡洛 {#formula-6}

> **这条公式的任务：** 从状态起点评估当前策略。

$$V^\pi(\mathbf{s}_t)=\sum_{t'=t}^{H}\mathbb{E}_{\pi_\theta}\big[r(\mathbf{s}_{t'},\mathbf{a}_{t'})\mid\mathbf{s}_t\big],\qquad J(\theta)=\mathbb{E}_{\mathbf{s}_1\sim p(\mathbf{s}_1)}\big[V^\pi(\mathbf{s}_1)\big]$$

**蒙特卡洛策略评估**（这正是 lec5 策略梯度在偷偷做的事）：
$$V^\pi(\mathbf{s}_t)\approx\sum_{t'=t}^{H}r(\mathbf{s}_{t'},\mathbf{a}_{t'})\qquad\text{（单条 rollout）}$$
$$V^\pi(\mathbf{s}_t)\approx\frac1N\sum_{i=1}^{N}\sum_{t'=t}^{H}r(\mathbf{s}_{t'}^{(i)},\mathbf{a}_{t'}^{(i)})\qquad\text{（多条，需要能 reset 模拟器）}$$

**逐符号拆**
- $J(\theta)=\mathbb{E}_{\mathbf{s}_1}[V^\pi(\mathbf{s}_1)]$ —— RL 目标 = 初始状态价值的期望。"策略好不好"= "从起点出发能值多少分"。
- 第一行单 rollout 估计 = lec5 的 $\hat Q$ 同款思路（只是这里估的是 $V$，不带动作条件）。
- "需要 reset 模拟器" —— 想从**同一个 $\mathbf{s}_t$** 多跑几条来平均，得能把模拟器拨回那个状态；真实世界做不到，所以下页改用函数逼近。

> 💡 单条 rollout 的 $V$ 估计**没有把 reset 的多条平均掉**，方差大；但好处是**不需要 reset**。下页用神经网络把"不同状态的样本"互相共享信息，部分弥补这一点。



### 公式 7 · Slide 10：蒙特卡洛 + 函数逼近 = 监督回归 {#formula-7}

> **这条公式的任务：** 把 noisy return 当成有条件均值的监督标签。

把"状态 → 它的 reward-to-go"当成 $(x,y)$ 训练数据，拿神经网络回归：

$$\text{训练数据：}\Big\{\Big(\mathbf{s}_t^{(i)},\ \underbrace{\textstyle\sum_{t'=t}^{H}r(\mathbf{s}_{t'}^{(i)},\mathbf{a}_{t'}^{(i)})}_{y_t^{(i)}}\Big)\Big\}$$
$$\mathcal{L}(\phi)=\frac12\sum_{i=1}^{N}\sum_{t=1}^{H}\big\lVert \hat V_\phi^\pi(\mathbf{s}_t^{(i)})-y_t^{(i)}\big\rVert^2$$

**怎么读**："输入状态 $\mathbf{s}_t^{(i)}$、标签 $y_t^{(i)}$=它的剩余奖励，最小化预测与标签的平方误差。"

**逐符号拆**
- $y_t^{(i)}$ —— **回归目标**：第 $i$ 条轨迹第 $t$ 步的实际剩余奖励（蒙特卡洛标签）。
- $\hat V_\phi^\pi(\mathbf{s}_t^{(i)})$ —— critic 网络对该状态的价值预测。
- $\frac12\lVert\cdot\rVert^2$ —— 平方误差（lec2 公式 8 老朋友：高斯 + $\Sigma=I$ 的最大似然就是最小二乘）。

> 🔑 **函数逼近带来的样本共享**：两个相似的状态会被网络映到相近的 $\hat V$。所以哪怕每个状态只跑了一条 rollout（标签很糙），**网络在状态间做平滑**，相当于"软性地"实现了多条平均的效果。slide 图里画两个绿点落在同一个 $\hat V$ 上，就是这个意思（"the same function should fit multiple samples"）。
>
> 📎 **"为什么蒙特卡洛突然变成了监督回归、单样本标签为什么还能用"单独开了一篇逐字精读，配数字例子**：[Lecture6 最常卡的一步（蒙特卡洛怎么突然变成监督回归精读）](#regression-detail)。卡在"怎么跳过去的"就去那篇。


网络有机会在状态之间共享信息；是否有用取决于表达能力、拟合与泛化，不能把平滑本身当成必定准确的平均。回归标签有噪声不妨碍其条件平均提供学习目标。



### 公式 8 · Slide 11：能更好吗——bootstrap（自举） {#formula-8}

> **这条公式的任务：** 固定旧尾部预测，构造可训练的 TD 目标。

不再等待整个 rollout，把尾部交给旧 critic：

$$y_t^{(i)}=r(s_t^{(i)},a_t^{(i)})+\hat V_{\mathrm{old}}^\pi(s_{t+1}^{(i)})$$

$$\mathcal L(\phi)=\frac1{2N}\sum_{i,t}\left(\hat V_\phi^\pi(s_t^{(i)})-y_t^{(i)}\right)^2$$

**逐步读：** 用当前版本/旧目标网络计算标签 → 固定标签 → 对新的预测误差更新 $\phi$。不是把预测与目标里的同一网络一起任意求导；标准 TD 拟合用半梯度/停止目标梯度的形式。

bootstrap 通常减少需要实际采出的未来长度，可能降低估计噪声；若尾部 critic 有误差，就可能引入偏差。不能对任意 reward 相关性与任意 critic 直接宣布方差一定降低。



### 公式 9 · Slide 12：折扣因子 $\gamma$ {#formula-9}

> **这条公式的任务：** 说明折扣改变的目标与相应时间权重。

给未来奖励乘折扣，定义：

$$J(\theta)=\mathbb E_{\tau\sim p_\theta}\left[\sum_{t=1}^H\gamma^{t-1}r(s_t,a_t)\right]$$

相应价值递归和目标为：

$$Q^\pi(s_t,a_t)=r(s_t,a_t)+\gamma\mathbb E[V^\pi(s_{t+1})\mid s_t,a_t]$$

$$y_t^{(i)}=r(s_t^{(i)},a_t^{(i)})+\gamma\hat V_{\mathrm{old}}^\pi(s_{t+1}^{(i)})$$

$\gamma\lt1$ 配合有界奖励，使无限时域回报有限；$\gamma=1$ 则需有限/终止等额外条件。

**死亡状态解释。** 在每步奖励之后，以 $1-\gamma$ 概率进入零后续奖励的终止状态；存活后的普通转移质量乘 $\gamma$。这样第 t 步存活概率为 $\gamma^{t-1}$，得到同样的期望目标。



### 公式 10 · Slide 13：time-invariant——把 transition 当独立样本 {#formula-10}

> **这条公式的任务：** 分开改记号与独立采样假设。

把时间与轨迹下标展开成 transition 编号：

$$\{(s_i,a_i,s_i')\},\qquad y_i=r(s_i,a_i)+\gamma\hat V_{\mathrm{old}}^\pi(s_i')$$

$$\mathcal L(\phi)=\frac12\sum_i(\hat V_\phi^\pi(s_i)-y_i)^2$$

这是记号与数据组织上的改变。**把转移展平、打乱，并不会使同一轨迹内的数据自动独立。** 若是有限时域，状态还应包含时刻/剩余时间，或明确使用时间条件的价值函数。

能否把旧转移放进 replay，取决于后面如何处理行为策略与目标策略差异；不能只因为改成单下标 i，就宣称已消除分布错配。



## Part 3：完整 actor-critic 与两种更新节奏


### 公式 11 · Slide 16：batch actor-critic 算法 {#formula-11}

> **这条公式的任务：** 将 critic 与 actor 两种更新装入完整循环。

$$\begin{aligned}
&1.\ \text{采样：}\quad\tau^{(i)}\sim p_\theta,\quad i=1,\ldots,N\\
&2.\ \text{目标：}\quad y_t^{(i)}=r(s_t^{(i)},a_t^{(i)})+\gamma\hat V_{\mathrm{old}}^\pi(s_{t+1}^{(i)})\\
&3.\ \text{critic 更新：}\quad\phi\leftarrow\phi-\alpha\nabla_\phi\frac1{2N}\sum_{i,t}(\hat V_\phi^\pi(s_t^{(i)})-y_t^{(i)})^2\\
&4.\ \text{优势：}\quad\hat A_t^{(i)}=r(s_t^{(i)},a_t^{(i)})+\gamma\hat V_\phi^\pi(s_{t+1}^{(i)})-\hat V_\phi^\pi(s_t^{(i)})\\
&5.\ \text{actor 梯度：}\quad\nabla_\theta J(\theta)\approx\frac1N\sum_{i,t}\gamma^{t-1}\nabla_\theta\log\pi_\theta(a_t^{(i)}\mid s_t^{(i)})\hat A_t^{(i)}\\
&6.\ \text{actor 更新：}\quad\theta\leftarrow\theta+\alpha\nabla_\theta J(\theta)\quad\Longrightarrow\quad\text{回到 1}
\end{aligned}$$

**怎么读**：跑数据 → 配标签 → 训 critic（步 2-3）→ 用 critic 算优势 → 训 actor（步 4-6）。两个网络交替更新。

### 🔍 步 3「refit critic」到底在干嘛（最容易卡的一步）

很多人卡在 "refit" 上。先把**步 2 和步 3 当一对看**——它俩合起来才是"训练 critic"一件完整的事，被拆成了两半：

| | 在干嘛 | 类比 |
|---|---|---|
| **步 2** $y_i=r+\gamma\hat V_\phi(\mathbf{s}_i')$ | **出题**：给每个状态 $\mathbf{s}_i$ 算一个"目标分"$y_i$（标签）。**只是算标签，还没碰网络参数** | 老师出一套题的标准答案 |
| **步 3** refit | **做题**：真正训练 critic 网络，让预测 $\hat V_\phi(\mathbf{s}_i)$ 去**靠近**这些标签 $y_i$ | 学生照标准答案练、调整自己 |

**步 3 字面在干嘛 = 把 [公式 7](#formula-7) 那个最小二乘真正跑一遍梯度下降**：

$$\mathcal L(\phi)=\frac12\sum_i\big\lVert\underbrace{\hat V_\phi(\mathbf{s}_i)}_{\text{网络的预测}}-\underbrace{y_i}_{\text{步2算的标签}}\big\rVert^2,\qquad \phi\leftarrow\phi-\alpha\nabla_\phi\mathcal L(\phi)$$

- 输入 = 状态 $\mathbf{s}_i$，标签 = 步 2 的 $y_i$；调的是 **critic 的 $\phi$**（不是 actor 的 $\theta$）。
- **就是一次普通的"喂 (输入, 标签) 训练神经网络"**，没有新东西——只是 Part 2 学的那个回归，现在塞进循环里跑。

> 🔑 **为什么叫 "RE-fit"（重新拟合）而不是 fit**：因为这是个**循环**（步 6 回到步 1）。每转一圈——
> $$\underbrace{\text{步6 更新 }\theta}_{\text{策略 }\pi_\theta\text{ 变了}}\ \Rightarrow\ \underbrace{V^\pi\text{ 也变了}}_{V^\pi\text{ 是"评估当前策略"的价值，策略一变它就变}}\ \Rightarrow\ \underbrace{\text{下一圈把 critic 重训一遍}}_{\text{refit}}$$
> $V^\pi$ 永远是"**当前这个策略**有多好"。actor 一进步、策略就换了，旧 critic 立刻过时 → **每圈都拿新数据把 critic 重新拟合，追上新策略**。不是训一次就完，是**追着不断变化的策略反复重训**——这就是 "re"。

> 💡 **两条训练线交替**：critic 用**监督回归**训（步 2-3，调 $\phi$）当"打分器"；actor 用**策略梯度**训（步 4-6，调 $\theta$）。类比：critic = 教练学打分，actor = 球员照打分改进；球员变强 → 教练得重学怎么给新打法打分（refit）。**advantage 是 critic 算的、actor 用的**——critic 负责"打分/算优势"，actor 负责"拿这张成绩单改进策略"。

> 🔑 **这就是 lec4 那张"橙→绿→蓝"循环图的完整体**：绿（fit a model to estimate return）= 步 2-3 训 critic；蓝（improve the policy）= 步 4-6 训 actor；橙（generate samples）= 步 1。
> 🔗 LLM 对照：actor = 被训的语言模型；critic = value model（PPO 里那个 value head）。**PPO 的 value function 就是这里的 $\hat V_\phi$。**


图中这六步作为一整个算法节点。critic 用负号下降回归损失，actor 用正号上升目标；两种优化器可分别设学习率。停止目标与优势梯度是计算图要求，严格无偏性还取决于估计与采样条件。



### 公式 12 · Slide 17-18：在线 actor-critic 与 A3C 的联系 {#formula-12}

> **这条公式的任务：** 说明在线单转移原型与并行算法的联系。

不攒一批，**走一步就更新一次**：

$$\begin{aligned}
&1.\ \text{走一步：}\mathbf{a}\sim\pi_\theta(\mathbf{a}\mid\mathbf{s})\text{，拿到一个转移 }(\mathbf{s}_i,\mathbf{a}_i,\mathbf{s}_i')\\
&2.\ y_i=r(\mathbf{s}_i,\mathbf{a}_i)+\gamma\hat V_\phi^\pi(\mathbf{s}_i')\\
&3.\ \text{用 }\nabla_\phi\mathcal{L}_i(\phi)\text{ 更新 critic }\phi\\
&4.\ \hat A^\pi(\mathbf{s}_i,\mathbf{a}_i)=r(\mathbf{s}_i,\mathbf{a}_i)+\gamma\hat V_\phi^\pi(\mathbf{s}_i')-\hat V_\phi^\pi(\mathbf{s}_i)\\
&5.\ \nabla_\theta J(\theta)\approx\nabla_\theta\log\pi_\theta(\mathbf{a}_i\mid\mathbf{s}_i)\hat A^\pi(\mathbf{s}_i,\mathbf{a}_i)\\
&6.\ \theta\leftarrow\theta+\alpha\nabla_\theta J(\theta)
\end{aligned}$$

配套的 critic 单样本损失与更新：
$$\mathcal{L}_i(\phi)=\big\lVert\hat V_\phi^\pi(\mathbf{s}_i)-y_i\big\rVert^2,\qquad \phi\leftarrow\phi-\alpha\nabla_\phi\mathcal{L}_i(\phi)$$

**逐符号拆**
- 步 5 没有 $\frac1N\sum$ —— 因为只有**一个**样本，单样本估梯度。
- critic 更新用 **−**（最小化损失），actor 更新用 **+**（最大化回报）——别写反。

> ⚠️ **单样本 online 很不稳**：一步一个梯度，方差极大、还相关（连续状态高度相似）。slide 黄字：*Getting this to work in practice typically requires multiple parallel workers.*
> 💡 **A3C** = Asynchronous Advantage Actor-Critic：开**多个并行 worker** 各跑各的，凑出近似 i.i.d. 的一批转移来降方差。这就是 online actor-critic 的经典落地。


这组描述的是单转移在线 actor-critic 原型；A3C 还包含异步 workers 和短 rollout/n-step 等设计。并行改善数据多样性，不保证数据精确 i.i.d.，异步还会带来参数滞后。这里的单步 actor 方向按对应状态采样约定使用，不冒充任意折扣起点 J 的精确等权估计。



## Part 4：n-step、GAE 与优势中心化


### 公式 13 · Slide 22：critic 作 baseline 与 bootstrap：分别判偏差与方差 {#formula-13}

> **这条公式的任务：** 用期望判偏差，用完整加权梯度判方差。

先并排看三种乘子，而不把“低方差/无偏”当作无条件标签：

| 估计 | 完整乘子 | 误差来自哪里 |
|---|---|---|
| 单步 actor-critic | $r_t+\gamma\hat V_\phi(s_{t+1})-\hat V_\phi(s_t)$ | 用预测尾部替换真实未来 |
| MC + 固定常数 baseline | $\sum_{t'=t}^H\gamma^{t'-t}r_{t'}-b$ | 长 rollout 的随机性 |
| MC + 状态 critic baseline | $\sum_{t'=t}^H\gamma^{t'-t}r_{t'}-\hat V_\phi(s_t)$ | 仍用真实未来，改变参考值 |

**baseline 为什么可消掉：**

$$\mathbb E_{a_t\sim\pi_\theta}[\nabla_\theta\log\pi_\theta(a_t\mid s_t)\hat V_\phi(s_t)]=\hat V_\phi(s_t)\nabla_\theta\int\pi_\theta(a_t\mid s_t)\,da_t=0$$

critic 必须作为固定、只依赖当前状态的 baseline；若用同批动作回报拟合再评估，还需检查数据依赖。停止自动微分并不能替代这个统计条件。

**自举误差为什么不同：** 减当前状态误差可经 score 平均消去，下一状态误差却受当前动作影响。相应额外梯度项为：

$$\gamma\mathbb E\left[\nabla_\theta\log\pi_\theta(a_t\mid s_t)\mathbb E[\hat V_\phi(s_{t+1})-V^\pi(s_{t+1})\mid s_t,a_t]\right]$$

它一般不为零，因此可能有偏；但不是“critic 一有误差就必然有偏”。例如未来误差对当前动作的条件平均完全相同，这项仍可能消去。

**MC 减 critic 不等于优势估计总是无偏。**

$$\mathbb E[\hat A_{\mathrm{MC}}\mid s_t,a_t]=Q^\pi(s_t,a_t)-\hat V_\phi(s_t)$$

这一般不等于真实 A，但在固定 baseline 条件下不改变梯度期望。

**方差还要乘上 score 看。** 只比较乘子方差，忽略它与动作梯度的关系，不足以证明梯度方差的排序；多时间步之和还含协方差。状态 V 常是好参照，却不必是所有策略参数化下方差最优的 baseline。证明与反例见 [偏差精读](#bias-detail)。



### 公式 14 · Slide 23：n-step 优势——在偏差和方差之间滑动 {#formula-14}

> **这条公式的任务：** 确保 n 步只含 n 个奖励。

正确 n-step 估计只使用 n 个奖励，随后在第 n 步末尾接 critic：

$$\hat A_n^\pi(s_t,a_t)=\sum_{k=0}^{n-1}\gamma^k r(s_{t+k},a_{t+k})+\gamma^n\hat V_\phi^\pi(s_{t+n})-\hat V_\phi^\pi(s_t)$$

**上限必须是 n−1。** 原主笔记的 t 到 t+n 含 n+1 个奖励，会与 n=1 单步 TD 对不上；此处补齐后两者一致。

$$n=1:\quad\hat A_1=r_t+\gamma\hat V_\phi(s_{t+1})-\hat V_\phi(s_t)$$

若一路展开到真实终止、末端价值为零：

$$\hat A_{\mathrm{MC}}=\sum_{t'=t}^H\gamma^{t'-t}r_{t'}-\hat V_\phi(s_t)$$

n 越短，更多未来依赖 critic；n 越长，更多未来依赖实际 rollout。这是有用的 bias/variance 调节思路，不是对任意环境和预测误差都成立的单调定理。截断未终止时还保留尾部价值。



### 公式 15 · Slide 24：Generalized Advantage Estimation（GAE） {#formula-15}

> **这条公式的任务：** 先把混合权重归一，再化成 TD 残差和。

先在无限/适当收敛情形且 $0\le\lambda\lt1$，把权重真正归一化：

$$w_n=(1-\lambda)\lambda^{n-1},\qquad\sum_{n=1}^{\infty}w_n=1$$

$$\hat A_{\mathrm{GAE}}=\sum_{n=1}^{\infty}(1-\lambda)\lambda^{n-1}\hat A_n$$

**第 1 步：每个 n-step 优势本身就是加权 TD 残差和。**

$$\delta_t=r_t+\gamma\hat V_\phi(s_{t+1})-\hat V_\phi(s_t),\qquad\hat A_n=\sum_{k=0}^{n-1}\gamma^k\delta_{t+k}$$

中间价值正负相消，只留下首端 baseline 与末端 bootstrap。

**第 2 步：某个 δ 到底出现在哪些 n 里？** $\delta_{t+k}$ 只出现在 $n\ge k+1$ 的估计中，其总权重为：

$$\sum_{n=k+1}^\infty(1-\lambda)\lambda^{n-1}=\lambda^k$$

**第 3 步：交换求和后，一行收口。**

$$\hat A_{\mathrm{GAE}}(s_t,a_t)=\sum_{k=0}^{\infty}(\gamma\lambda)^k\delta_{t+k}$$

有限 rollout 则累到末尾，并按终止/截断设置末端价值。$\lambda=0$ 留下当前 TD，$\lambda=1$ 在完整终止轨迹上得到 MC 减 baseline；不能在 $\lambda=1$ 时直接把所有 $(1-\lambda)\lambda^{n-1}$ 当成零再求无穷和。

**两种“1”要分开：** n-step 混合权重的和为 1；$\gamma,\lambda$ 是每步的衰减参数，不是单个奖励必须按满额累计一次的要求。[GAE 原论文](https://arxiv.org/abs/1506.02438)

有限长度的权重折叠与数值例见 [GAE 精读](#gae-detail)。



### 公式 16 · Slide 25：policy gradient with GAE + 优势中心化 {#formula-16}

> **这条公式的任务：** 集中看 GAE 版循环，并单独分析随机中心化。

用 GAE 替代单步优势，完整循环集中在一个框中：

$$\begin{aligned}
&1.\ \text{采样：}\quad\tau^{(i)}\sim p_\theta,\quad i=1,\ldots,N\\
&2.\ \text{价值目标：}\quad y_t^{(i)}=r_t^{(i)}+\gamma\hat V_{\mathrm{old}}(s_{t+1}^{(i)})\quad(\text{也可用固定的 }\lambda\text{-return})\\
&3.\ \text{critic 更新：}\quad\phi\leftarrow\phi-\alpha\nabla_\phi\frac1{2N}\sum_{i,t}(\hat V_\phi(s_t^{(i)})-y_t^{(i)})^2\\
&4.\ \text{GAE：}\quad\delta_t^{(i)}=r_t^{(i)}+\gamma\hat V_\phi(s_{t+1}^{(i)})-\hat V_\phi(s_t^{(i)}),\quad\hat A_t^{(i)}=\sum_{t'=t}^H(\gamma\lambda)^{t'-t}\delta_{t'}^{(i)}\\
&5.\ \text{actor 梯度：}\quad\nabla_\theta J(\theta)\approx\frac1N\sum_{i,t}\gamma^{t-1}\nabla_\theta\log\pi_\theta(a_t^{(i)}\mid s_t^{(i)})\hat A_t^{(i)}\\
&6.\ \text{actor 更新：}\quad\theta\leftarrow\theta+\alpha\nabla_\theta J(\theta)\quad\Longrightarrow\quad\text{回到 1}
\end{aligned}$$

价值目标有不同实现选择，但生成目标的旧估值与 actor 优势在相应更新阶段固定。如果采用 $\lambda$-return 回归，可先用旧网络算 GAE，再用 $y_t=\hat A_t+\hat V_{\mathrm{old}}(s_t)$ 作为固定标签。

**可选的优势标准化：**

$$\mu=\frac1{NH}\sum_{i,t}\hat A_t^{(i)},\qquad\sigma=\sqrt{\frac1{NH}\sum_{i,t}(\hat A_t^{(i)}-\mu)^2},\qquad\bar A_t^{(i)}=\frac{\hat A_t^{(i)}-\mu}{\sigma}$$

如果有效长度不同，应按有效样本数计算；标准差为零时要设置实现约定。减均值改变权重中心，除标准差改变更新尺度。

**不能将随机批均值直接当成独立状态 baseline。** 它包含自身动作与奖励，理想独立样本中会有 $1-1/N$ 的缩放；同轨迹相关样本和随机标准差归一的情况更复杂。标准化是训练代理的处理，不是无偏性的自动证明。见 [中心化精读](#centering-detail)。

本讲给出 PPO 的优势估计部分；[Lecture 9](../lecture-09/) 再改造旧样本复用与 actor 目标，[Lecture 14](../lecture-14/) 将这套工具用于 token/回答策略。



## Part 5：replay、Q 与两条 actor 梯度路线


### 公式 17 · Slide 27-28：直接套 replay buffer 会坏——改估 Q {#formula-17}

> **这条公式的任务：** 在旧转移上保留动作条件，换成当前下一动作。

直接用 replay 的旧动作来拟合 V，会使用错误的动作平均。想要的当前策略 Bellman 评估是：

$$V^\pi(s)=\mathbb E_{a\sim\pi_\theta,s'\mid s,a}[r(s,a)+\gamma V^\pi(s')]$$

旧动作来自 $\bar\pi$ 时，未经修正会变成行为策略算子作用在当前预测上。不能仍将这个平均宣称为同一个 $V^\pi$。

**Q 保留了当前动作条件：**

$$y_i=r(s_i,a_i)+\gamma\mathbb E_{a'\sim\pi_\theta(\cdot\mid s_i')}[\hat Q_{\mathrm{old}}^\pi(s_i',a')]$$

$$\mathcal L(\phi)=\frac1{2B}\sum_{i=1}^B(\hat Q_\phi^\pi(s_i,a_i)-y_i)^2$$

buffer 里的 $(s_i,a_i,s_i')$ 仍可提供给定状态—动作后的真实环境转移；下一动作则从当前策略重新取平均。这是条件 Bellman 目标的关键。

**并非“V 永远不能 off-policy”。** 重要性采样等校正也可支持 V 的 off-policy 评估；这里选择 Q 是让当前动作条件显式保留的一种路线。函数近似、覆盖不足和 replay 状态加权问题仍未自动消失。



### 公式 18 · Slide 29：actor 更新也用"现采动作"的同款 trick {#formula-18}

> **这条公式的任务：** 看清固定 replay 状态下的策略代理。

actor 在 replay 状态 $s_i$ 上，不沿用旧动作，而从当前策略采样：

$$a_i^\pi\sim\pi_\theta(\cdot\mid s_i)$$

固定 critic 参数 $\phi$，优化当前动作的预测 Q 平均：

$$\nabla_\theta\mathbb E_{a\sim\pi_\theta(\cdot\mid s_i)}[\hat Q_\phi(s_i,a)]=\mathbb E_{a\sim\pi_\theta}[\nabla_\theta\log\pi_\theta(a\mid s_i)\hat Q_\phi(s_i,a)]$$

状态已经有了，再采动作并查询 critic 不需要重新和环境交互。但 replay 状态分布与当前策略的真实访问分布仍可能不同。因此这条等式是固定状态、固定 critic 的代理梯度，不直接标成真实回报 J 的无偏梯度。



### 公式 19 · Slide 30-31：off-policy AC 算法 + "这在估什么梯度" {#formula-19}

> **这条公式的任务：** 逐步恢复密度与期望，写出 score 版完整循环。

整组 replay actor-critic 集中看，先抽出训练批次再计算它们的目标：

$$\begin{aligned}
&1.\ \text{采环境并抽 replay：}\quad(s,a,r,s')\text{ 存入 }\mathcal R,\quad\{(s_i,a_i,r_i,s_i')\}_{i=1}^B\sim\mathcal R\\
&2.\ \text{Q 目标：}\quad y_i=r_i+\gamma\mathbb E_{a'\sim\pi_\theta(\cdot\mid s_i')}[\hat Q_{\mathrm{old}}(s_i',a')]\\
&3.\ \text{critic 更新：}\quad\phi\leftarrow\phi-\alpha\nabla_\phi\frac1{2B}\sum_i(\hat Q_\phi(s_i,a_i)-y_i)^2\\
&4.\ \text{当前动作梯度：}\quad\frac1B\sum_i\mathbb E_{a\sim\pi_\theta}[\nabla_\theta\log\pi_\theta(a\mid s_i)\hat Q_\phi(s_i,a)]\\
&5.\ \text{actor 更新：}\quad\theta\leftarrow\theta+\frac{\alpha}{B}\sum_i\mathbb E_{a\sim\pi_\theta}[\nabla_\theta\log\pi_\theta(a\mid s_i)\hat Q_\phi(s_i,a)]\quad\Longrightarrow\quad\text{回到 1}
\end{aligned}$$

第 4 步的来历需要四个转换，而不是把 ∇ log π 当成凭空冒出的新量：

$$\nabla_\theta\mathbb E_{a\sim\pi_\theta}[\hat Q_\phi(s_i,a)]=\nabla_\theta\int\pi_\theta(a\mid s_i)\hat Q_\phi(s_i,a)\,da$$

$$=\int\nabla_\theta\pi_\theta(a\mid s_i)\hat Q_\phi(s_i,a)\,da$$

$$=\int\pi_\theta(a\mid s_i)\nabla_\theta\log\pi_\theta(a\mid s_i)\hat Q_\phi(s_i,a)\,da$$

$$=\mathbb E_{a\sim\pi_\theta}[\nabla_\theta\log\pi_\theta(a\mid s_i)\hat Q_\phi(s_i,a)]$$

梯度只作用在 actor 的动作分布；critic 作为固定函数。代入 log-trick 后恢复“密度 × 被平均量”，才重新写成期望。

**还剩的误差：** replay 状态不是当前访问分布；Q 是估计；有限数据还有噪声。加大 batch 不会自动消除前两者。接受这条路线是构造近似策略改进，不是把真实策略梯度定理无条件搬来。



### 公式 20 · Slide 32：重参数化：换分布表示，再对动作路径求导 {#formula-20}

> **这条公式的任务：** 将参数从密度挪到可导动作函数，并检查导数交换条件。

固定 replay 状态与 critic，我们要的是同一个代理：

$$\nabla_\theta\mathbb E_{a\sim\pi_\theta(\cdot\mid s)}[\hat Q_\phi(s,a)]$$

score 路线对动作概率求导；另一条路线利用 critic 对动作可导。先以一维高斯为例，标准差明确是 $\sigma_\theta$：

$$\epsilon\sim\mathcal N(0,1),\qquad a=\mu_\theta(s)+\sigma_\theta(s)\epsilon,\qquad a\sim\mathcal N(\mu_\theta(s),\sigma_\theta(s)^2)$$

**第 1 步：变的是表示方式，分布不变。**

$$\mathbb E_{a\sim\pi_\theta}[\hat Q_\phi(s,a)]=\mathbb E_{\epsilon\sim\mathcal N(0,1)}[\hat Q_\phi(s,\mu_\theta(s)+\sigma_\theta(s)\epsilon)]$$

这由随机变量变换得到，不是单样本近似。接下来需要新的合法条件：可微组合、可积的局部导数控制等。

**第 2 步：条件满足时交换梯度与期望。**

$$\nabla_\theta\mathbb E_{\epsilon}[\hat Q_\phi(s,\mu_\theta+\sigma_\theta\epsilon)]=\mathbb E_\epsilon[\nabla_\theta\hat Q_\phi(s,\mu_\theta+\sigma_\theta\epsilon)]$$

**第 3 步：完整展开链式法则。**

$$\nabla_\theta\hat Q_\phi(s,\mu_\theta+\sigma_\theta\epsilon)=\left.\frac{\partial\hat Q_\phi(s,a)}{\partial a}\right|_{a=\mu_\theta+\sigma_\theta\epsilon}\big(\nabla_\theta\mu_\theta(s)+\epsilon\nabla_\theta\sigma_\theta(s)\big)$$

**第 4 步：抽一个 ε，估计这个期望。**

$$\mathbb E_\epsilon[\nabla_\theta\hat Q_\phi(\cdots)]\approx\nabla_\theta\hat Q_\phi(s,\mu_\theta(s)+\sigma_\theta(s)\epsilon)$$

随机性仍存在，只是分布不再带参数；固定这次噪声后，动作随参数沿确定可导的路径变化。与 score 一样，这是在估固定 critic 代理的梯度；可交换条件下单样本平均无偏，但不自动等于真实 J 梯度。

**原数值例。** $\hat Q(a)=-(a-3)^2$、$a\sim\mathcal N(\theta,1)$，在 $\theta=3$：

$$\text{score 估计}=-\epsilon^3,\quad\operatorname{Var}=15;\qquad\text{pathwise 估计}=-2\epsilon,\quad\operatorname{Var}=4$$

这个例子利用可导地形降低方差，不是一般的固定方差排序定理。普通离散 token 不能直接使用这种光滑动作路径；连续松弛或其他离散梯度方法需额外分析。

“高斯”“连续动作”“可重参数化”是不同概念：高斯只是位置—尺度例子，可重参数化分布不限于单峰高斯。推导合法性与不能求导的反例见 [严格性精读](#reparameterization-detail)。



### 公式 21 · Slide 33：完整重参数化 actor-critic 与 SAC 骨架 {#formula-21}

> **这条公式的任务：** 以 pathwise 替换 actor 更新，区分 SAC 骨架与完整算法。

只将 replay 算法中的 actor 梯度换成 pathwise，完整循环为：

$$\begin{aligned}
&1.\ \text{采环境并抽 replay：}\quad(s,a,r,s')\text{ 存入 }\mathcal R,\quad\{(s_i,a_i,r_i,s_i')\}_{i=1}^B\sim\mathcal R\\
&2.\ \text{Q 目标：}\quad y_i=r_i+\gamma\mathbb E_{a'\sim\pi_\theta(\cdot\mid s_i')}[\hat Q_{\mathrm{old}}(s_i',a')]\\
&3.\ \text{critic 更新：}\quad\phi\leftarrow\phi-\alpha\nabla_\phi\frac1{2B}\sum_i(\hat Q_\phi(s_i,a_i)-y_i)^2\\
&4.\ \text{当前动作：}\quad\epsilon_i\sim\mathcal N(0,1),\quad a_i^\pi=\mu_\theta(s_i)+\sigma_\theta(s_i)\epsilon_i\\
&5.\ \text{actor 更新：}\quad\theta\leftarrow\theta+\frac{\alpha}{B}\sum_i\nabla_\theta\hat Q_\phi(s_i,\mu_\theta(s_i)+\sigma_\theta(s_i)\epsilon_i)\quad\Longrightarrow\quad\text{回到 1}
\end{aligned}$$

更新 actor 时冻结 critic 参数，但保留 critic 对动作的导数；每个样本独立抽噪声。critic 的目标整体固定，构造那个目标时是否需要 reparameterized sample 是另一件事。

**这是 SAC 的骨架之一，不是完整 SAC。** SAC 还使用最大熵目标与相应 soft 价值目标、稳定的 critic/目标网络等设计；不能因为使用 replay 和可导动作就将算法完全等同 SAC。[SAC 原论文](https://arxiv.org/abs/1801.01290)

对真实策略改进仍要考虑 replay 状态、Q 近似与其动作梯度误差。函数值接近不保证导数也接近，所以不能用“小 value loss”替代全部 actor 误差检查。



## 配套卡点精读

### Q 的累加定义与 Bellman 递归是同一件事 {#bellman-detail}

在同一折扣约定下：

$$Q^\pi(s_t,a_t)=\mathbb E\left[\left.\sum_{k=0}^{H-t}\gamma^k r(s_{t+k},a_{t+k})\right|s_t,a_t\right]$$

先拆当前奖励，再对下一状态条件平均：

$$Q^\pi(s_t,a_t)=r(s_t,a_t)+\gamma\mathbb E_{s_{t+1}\mid s_t,a_t}\left[\mathbb E\left[\left.\sum_{k=0}^{H-t-1}\gamma^k r(s_{t+1+k},a_{t+1+k})\right|s_{t+1}\right]\right]$$

内层是从下一状态出发、动作还按当前策略采的剩余回报，因此：

$$Q^\pi(s_t,a_t)=r(s_t,a_t)+\gamma\mathbb E[V^\pi(s_{t+1})\mid s_t,a_t]$$

**单点 Q 与 V 的区别：** 当前动作固定，所以 Q 吃 $(s,a)$；从下一状态开始，动作尚未固定，按策略平均，所以用 V。将这一步再按当前动作平均，就得到 V 的 Bellman 评估式。

这里是 policy evaluation，固定当前策略对动作平均；没有 $\max_a$，所以不是最优价值迭代。

### 为什么噪声回报标签能做监督回归 {#regression-detail}

将 MC 标签写为 $y=\sum_{t'=t}^H\gamma^{t'-t}r_{t'}$。当前策略固定时：

$$\mathbb E[y\mid s_t]=V^\pi(s_t)$$

条件平方损失分解为：

$$\mathbb E[(\hat V_\phi(s_t)-y)^2\mid s_t]=(\hat V_\phi(s_t)-\mathbb E[y\mid s_t])^2+\operatorname{Var}(y\mid s_t)$$

第二项不由预测值改变。可自由表示时，最优平方回归函数是条件平均，即 V。网络表达能力、数据覆盖和训练误差决定实际近似质量；单条标签不需要等于 V，也不保证每个训练值都接近它。

bootstrap 标签则使用预测尾部，条件平均一般是某个 Bellman 算子作用在旧预测上，不能把它当成相同的无误差 MC 标签。

### bias 与 variance 的判定，不能只靠“帽子” {#bias-detail}

判偏差看**实际估计器的期望**；单样本带来随机性，不自动产生 bias。MC 回报的条件平均是 Q，固定状态 baseline 经 score 零均值消去。自举则在未来插入预测值，其误差能通过动作影响未来状态，因而一般有额外梯度项。

对于理想已知 Q，某个梯度坐标 $j$ 的单项使用全方差公式：

$$\operatorname{Var}\!\left(\frac{\partial\log\pi_\theta(a_t\mid s_t)}{\partial\theta_j}\hat Q_t\right)=\mathbb E\left[\operatorname{Var}\!\left(\left.\frac{\partial\log\pi_\theta}{\partial\theta_j}\hat Q_t\right|s_t,a_t\right)\right]+\operatorname{Var}\!\left(\frac{\partial\log\pi_\theta(a_t\mid s_t)}{\partial\theta_j}Q^\pi(s_t,a_t)\right)$$

第一项非负，所以替换成真实条件平均可降低这个单项的方差。**不是只比 $\operatorname{Var}(\hat Q)$ 与 $\operatorname{Var}(Q)$**；动作梯度也在随机变量里。

预测 baseline 也不一定越接近 V 就越接近方差最优。在固定状态上，最小化梯度向量二阶矩的理想 baseline 为：

$$b(s)=\frac{\mathbb E_{a\sim\pi_\theta}[\|\nabla_\theta\log\pi_\theta(a\mid s)\|^2Q^\pi(s,a)]}{\mathbb E_{a\sim\pi_\theta}[\|\nabla_\theta\log\pi_\theta(a\mid s)\|^2]}$$

动作梯度长度不等时，它不必等于 $V^\pi(s)=\mathbb E[Q\mid s]$。实践中学 V 仍方便、有价值，但不能把“状态 V 更贴近回报”当成对任何模型的严格方差排序。

### GAE 会不会把 reward 反复加了：有限轨迹完整核对 {#gae-detail}

到真实终止还剩 $H-t+1$ 个奖励。有限 n-step 混合应把超出终止后的尾部权重归到最长估计：

$$w_n=(1-\lambda)\lambda^{n-1}\quad(1\le n\lt H-t+1),\qquad w_{H-t+1}=\lambda^{H-t}$$

它们加起来等于 1。长估计同样包含前面的奖励，所以看起来有重复，但**各候选估计先乘了权重**。不能把不同 n 的整段回报直接无权相加。

取三步奖励 $(1,2,3)$、$\gamma=1$、critic 为零、$\lambda=0.5$：

| n-step | 回报估计 | 混合权重 | 加权贡献 |
|---|---:|---:|---:|
| 1 | 1 | 0.5 | 0.5 |
| 2 | 3 | 0.25 | 0.75 |
| 3 | 6 | 0.25 | 1.5 |

总和 $2.75$。直接 TD 和也给出：

$$1+0.5(2)+0.25(3)=2.75$$

每个 $\delta_{t+k}$ 在所有包含它的候选里权重总和为 $\lambda^k$，再乘 $\gamma^k$，所以恰好是 $(\gamma\lambda)^k$。

**递归与首端 baseline：**

$$\hat A_t=\delta_t+\gamma\lambda\hat A_{t+1}$$

$$\hat A_t=-\hat V_\phi(s_t)+r_t+\gamma\left[(1-\lambda)\hat V_\phi(s_{t+1})+\lambda(r_{t+1}+\gamma((1-\lambda)\hat V_\phi(s_{t+2})+\cdots))\right]$$

原主笔记的嵌套式漏掉了 $-\hat V_\phi(s_t)$，不能不补就称为优势。$\lambda=1$ 时，中间价值抵消；若末端只是截断，则留下尾部 bootstrap，而不自动变成纯 MC。

### 中心化为什么等于加 baseline，却可能有自项偏差 {#centering-detail}

对固定独立 baseline，减均值型参考值可由 score 零均值证明不改梯度期望。但一批里的均值包含自己，相关性改变了这个证明。

以 N 条独立完整轨迹、各自总回报为例：

$$\mathbb E\left[\frac1N\sum_i\nabla_\theta\log p_\theta(\tau_i)\left(r(\tau_i)-\frac1N\sum_jr(\tau_j)\right)\right]=\left(1-\frac1N\right)\nabla_\theta J(\theta)$$

展开双重和：$i\ne j$ 的交叉项因独立与 score 零均值消去；$i=j$ 的自项留下 $1/N$ 份原梯度。N=1 时，减自己回报后更新完全为零。

若用其他轨迹的留一均值，独立条件下没有这份自项；同一轨迹内展平的多个时间步彼此相关，不能机械套 N 条独立轨迹的公式。再除随机批标准差，则又改变估计器与梯度尺度。

### 重参数化的四道关卡，哪里真正需要条件 {#reparameterization-detail}

| 关卡 | 检查的东西 | 性质 |
|---|---|---|
| 分布对应 | $a=\mu_\theta+\sigma_\theta\epsilon$ 产生指定高斯 | 随机变量变换 |
| 期望对应 | 按 a 平均等于按噪声加工后平均 | 对可积函数的分布恒等式 |
| 导数穿过期望 | 路径可微、导数有可积局部控制 | 条件性定理，不是自动允许 |
| 单样本估计 | 用独立噪声估导数期望 | 满足条件时无偏，但有方差 |

一维密度换元可以亲眼看见 $\sigma$ 消掉：$a=\mu+\sigma\epsilon$、$da=\sigma\,d\epsilon$，高斯密度的 $1/\sigma$ 与微元里的 $\sigma$ 抵消，留下标准噪声密度与改变后的被积函数。

**不满足光滑条件的反例：**

$$Q(a)=\mathbf1\{a\gt0\},\qquad a\sim\mathcal N(\mu,1)$$

真实期望为高斯累积分布，$\mu=0$ 时导数：

$$\frac{d}{d\mu}\mathbb E[\mathbf1\{a\gt0\}]\bigg|_{\mu=0}=\frac1{\sqrt{2\pi}}\approx0.398942$$

然而逐样本对 $\mathbf1\{\mu+\epsilon\gt0\}$ 求路径导数，几乎处处是零。先求导再积分与先积分再求导不相等。score 估计在常规高斯条件下仍能正确给出这个边界贡献。

**value 误差小不等于动作导数误差小：**

$$Q(a)=0,\qquad\hat Q(a)=0.001\sin(10^6a)$$

函数误差至多 $0.001$，导数却为 $1000\cos(10^6a)$。这说明 actor 使用的动作地形不能仅凭回归误差大小判断。

**计算图对应。** 普通不可导采样与可重参数化采样要区分；冻结 $\phi$ 只是停止更新 critic 参数，仍应保留 Q 对动作的导数。把 Q 输出整体停止梯度，会把 actor 经动作这条路径也切断。

### 单峰、连续、重参数化，分别问不同问题 {#distribution-detail}

单个高斯密度在非退化一维情形为单峰；离散动作概率表可以有多个大概率动作；连续策略也可以用混合分布/可导变换表达复杂形状。是否存在方便的无参噪声变换，以及组合目标能否求合法路径导数，才是重参数化的问题。

高斯只是本讲例子，不是重参数化的定义。反之，能写出一个随机变量变换也不保证通过非连续目标的 pathwise 求导一定合法。

## 全公式索引 {#formula-index}

| 编号 | 本讲的任务 |
|---|---|
| [1](#formula-1) | 回顾 reward-to-go 单样本乘子 |
| [2](#formula-2) | 用条件期望定义 Q |
| [3](#formula-3) | V 平均动作，A 比较相对好坏 |
| [4](#formula-4) | 三种价值与优势版梯度 |
| [5](#formula-5) | Bellman 拆到奖励与下一 V |
| [6](#formula-6) | MC 状态价值评估 |
| [7](#formula-7) | MC 标签变成监督回归 |
| [8](#formula-8) | 固定旧预测的 bootstrap |
| [9](#formula-9) | 折扣、起点权重与死亡状态解释 |
| [10](#formula-10) | 展平 transition 不会自动独立 |
| [11](#formula-11) | 完整 batch actor-critic |
| [12](#formula-12) | 在线原型与异步 actor-critic |
| [13](#formula-13) | baseline、自举与偏差/方差 |
| [14](#formula-14) | 正确 n-step 上限 |
| [15](#formula-15) | 归一化混合变成 TD 残差和 |
| [16](#formula-16) | 完整 GAE 循环与中心化 |
| [17](#formula-17) | replay 条件下的 Q Bellman 目标 |
| [18](#formula-18) | 在旧状态上重新采当前动作 |
| [19](#formula-19) | 完整 score 版 replay 循环与期望变形 |
| [20](#formula-20) | 分布换元、导数交换与路径梯度 |
| [21](#formula-21) | 完整 pathwise 循环与 SAC 的联系 |

## 自测：能否把每一步放回循环 {#self-check}

1. Q 的定义中，哪些随机性已平均掉？V 又平均掉什么？
2. 单个下一状态代替其期望，会产生随机性还是必然偏差？
3. MC 标签有噪声，为什么最小平方损失仍指向条件平均？
4. baseline 与下一状态 bootstrap，哪个能直接通过 score 平均消掉？
5. n=1 时 n-step 为什么必须恰好退化成 TD？
6. 三步例子用 n-step 混合和 TD 和各算出多少？
7. λ=1 时为什么还需要检查终端/截断价值？
8. 展平样本为何不等于独立？批均值含自己时会怎样？
9. Q 如何允许旧动作条件与当前下一动作共存？
10. score 与 pathwise 分别在哪个位置对 θ 求导？
11. indicator 反例中真实导数和 pathwise 导数各多少？
12. replay/pathwise 还欠真实 J 哪些误差？为什么这不是完整 SAC？

<details>
<summary>展开参考答案</summary>

1. Q 固定当前状态动作，平均未来动作与环境；V 还对当前动作按策略平均。
2. 真 V 下是条件无偏的单样本估计，增加的是方差；预测 V 的替代可能另有偏差。
3. 条件平方损失分解为预测与条件均值的误差，加不可由预测改变的标签方差。
4. 当前固定状态 baseline 可消；下一状态由动作影响，其预测误差一般不能消。
5. n 个奖励的上限为 $t+n-1$，再在 $t+n$ 接 $\gamma^n V$；$n=1$ 只留下 $r_t$。
6. 两条路都为 2.75；候选回报不是无权相加，混合权重归一。
7. 截断未终止仍有 γ 的尾部 bootstrap；真实终止后的价值才为零。
8. 同一轨迹仍相关；独立 N 条完整轨迹的自身批均值会产生 $1-1/N$ 缩放。
9. Q 显式固定本次动作，用旧样本提供条件转移；下一动作由当前策略重新平均。
10. score 微分动作密度；pathwise 把参数放进动作加工函数，通过 Q 的动作导数求导。
11. μ=0 时真实导数约 0.398942，普通路径导数几乎处处零，因为交换条件失效。
12. 状态分布、Q 拟合与动作导数误差仍存在；完整 SAC 还包含最大熵等相应目标和稳定设计。

</details>

## 材料与衔接 {#sources}

主材料为本地《Lecture6 公式逐行拆解》。数学精读整合了 Q 的累加/递归、Bellman、MC 回归、三种估计的 bias/variance、GAE 权重与重复奖励、中心化与自项、replay、重参数化的积分/计算图/严格性以及连续分布形状的配套笔记。

保留 21 条公式的教学层次与主要例子，补齐 n-step 端点、GAE 权重、首端 baseline、采样与自举偏差区别、固定 critic 代理与真实梯度区别。理论核对：[GAE 原论文](https://arxiv.org/abs/1506.02438)、[SAC 原论文](https://arxiv.org/abs/1801.01290)。

往前接 [Lecture 5](../lecture-05/) 的策略梯度；往后接 [Lecture 9](../lecture-09/) 的旧样本复用、[Lecture 10](../lecture-10/) 的局部改进约束、[Lecture 14](../lecture-14/) 的序列与语言模型训练。
