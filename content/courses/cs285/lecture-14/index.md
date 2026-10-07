---
title: "Lecture 14 · 从奖励学习到语言模型强化学习"
description: "保留 22 条公式拆解，先展示完整训练循环，再连接 IRL、对抗学习、LLM 策略、GAE/GRPO、参考 KL、偏好与历史状态。"
date: 2026-10-07
weight: 140
math: true
ShowToc: false
tags: [CS285, IRL, RLHF, Language Models, GRPO, POMDP]
---

## 先看清这一讲在做什么 {#lecture-thread}

**Lecture 14 把前几讲的策略梯度工具搬到序列与语言模型，并补上“奖励从哪里来”。** 先把生成回答、打分、冻结采样策略、反复更新的完整循环放在一个框里，旁边列出全部步骤公式，再指出其中三个要填的量：reward、baseline、regularizer。

奖励一条路线来自专家示范：MaxEnt IRL 的最大似然遇到配分函数，推导出两个期望之差，再走向采样与对抗学习。另一条来自偏好或验证器：Bradley–Terry 用奖励差解释偏好，验证器直接提供可检查的任务得分。

接着把语言模型分为整段 completion 的单步视角和 token 的多步视角，分别接上 GAE 或组内相对优势、固定参考模型的 KL，以及 PPO 的旧批次复用。最后用 POMDP 解释为什么要把完整交互历史交给序列模型。

{{< lecture-mindmap id="sequence-rl-flow" cards="argument-cards.json" width="1660" caption="先看完整的回答训练循环，找出 reward、baseline、regularizer 三个插口。奖励来源分为专家示范的 IRL 和偏好/验证器；策略侧按整段与 token 两种视角展开，再接 GAE/GRPO、参考 KL 与 PPO。完整 IRL、LLM 更新、PPO 和 RLHF 循环各集中成一个框，旁边给全部编号公式；其余数学转换逐步拆，点击读正文。" >}}

### 把整讲接成一段话

不知道奖励时，可以先让专家轨迹在奖励诱导分布下有高似然。对 log 配分函数求导后，认出归一化轨迹密度，得到“专家平均梯度 − 当前模型平均梯度”。后一个平均难采，策略优化与重要性采样承担这部分工作；特殊结构下可联系对抗式奖励学习。

语言模型则天然给出条件动作概率：整段回答的概率是 token 概率连乘，log 梯度就是逐 token 相加。沿用策略梯度与旧样本代理目标，再选择优势估计与参考正则，构成完整训练循环。

偏好模型和强化学习是两个相连的训练问题：先拟合“哪个回答更受偏好”的概率，再用该奖励训练策略。奖励模型、采样旧策略和参考模型的角色分别固定在相应阶段，不能混为同一个参照。

| 当前卡点 | 阅读位置 |
|---|---|
| 循环里究竟还缺什么 | [公式 14 的完整循环](#formula-14) |
| 配分函数怎样变成期望 | [公式 2–3](#formula-2) |
| 没有软最优样本，权重怎样补 | [公式 5–6](#formula-5) |
| IRL、GAN、GAIL、AIRL 什么关系 | [公式 7–10](#formula-7) |
| 整段概率怎样拆成 token 梯度 | [公式 11–13](#formula-11) |
| GAE 和组内 baseline 有何区别 | [公式 15–16](#formula-15) |
| 旧策略与参考模型为何是两个对象 | [公式 17](#formula-17) → [KL 精读](#reference-detail) |
| 偏好如何变成可学的奖励 | [公式 19–20](#formula-19) |
| 为什么历史还需要包含动作 | [公式 21–22](#formula-21) |

<details>
<summary>展开全页目录与公式索引</summary>

{{< chapter-outline id="lecture14-outline" title="Lecture 14 阅读位置" >}}

</details>

## 符号与阅读范围 {#notation}

保留本地《Lecture14 公式逐行拆解》的 22 个公式编号与 Slide 定位。原笔记的参数与概率记号继续使用：$\theta$ 训练策略，$\psi$ 训练奖励/判别器，$\phi$ 训练 critic；$\bar\pi$ 是本批采样旧策略，$\pi_{\mathrm{ref}}$ 是长期冻结的参考策略。

| 符号 | 本讲的含义 |
|---|---|
| $\pi_\theta(a\mid s)$ | 状态/前缀下的动作或 completion 分布 |
| $p_\theta(\tau)$ | 策略与环境共同产生的轨迹概率 |
| $p(\tau)$ | IRL 中固定的动力学因子/轨迹基测度；不是缺动作概率的随机策略分布 |
| $\pi^\star(\tau)$ | 原笔记用来表示专家轨迹的分布 |
| $r_\psi(\tau)$ | 整条轨迹的奖励和 |
| $\mathcal O_t=1$ | 用于推断模型的最优性事件；指数奖励先作为似然因子 |
| $Z$ | 对所有轨迹累积未归一化质量的配分函数，依赖 $\psi$ |
| $D_\psi$ | 判别为专家/真实数据的概率；约定专家一侧是 1 |
| $\bar\pi$ | 收集本批回答的旧策略，在 actor 内循环固定 |
| $\pi_{\mathrm{ref}}$ | 参考模型，在多个批次间通常也保持固定 |
| $\hat V_\phi,\delta_t,\hat A$ | critic、TD 残差、用于 actor 的固定优势估计 |
| $N,M,K,H$ | 专家/训练样本数、策略样本数、组大小或内层次数、生成长度 |
| $\sigma(z)$ | sigmoid，$1/(1+e^{-z})$；此处不是高斯标准差 |

采用有限生成轨迹，真实终止后价值为零，时间截断另作 bootstrap。重要性采样要求支持覆盖。IRL 轨迹密度按同一固定动作基测度比较；若使用非均匀动作先验，它也要留在概率模型和比值里。

在 LLM 章节中始终用 $\pi_\theta/\bar\pi$ 比较当前策略与采样策略，不另外引入梯度缩写。原笔记的 $K$ 在组内优势段表示同题回答数，在算法段表示更新次数，按各自段落读取。

本页 LLM 的终端任务奖励采用无折扣目标；GAE 保留 $\gamma$ 的泛式，作单步/多步等价推导时取 $\gamma=1$。若另改折扣或长度权重，需同时修改目标与估计约定。


## Part 1：奖励未知，怎样从专家行为学习


### 公式 1 · Slide 4：最优性变量 + 轨迹后验 {#formula-1}

> **这条公式的任务：** 先建立轨迹概率模型，说明奖励怎样进入似然。

**最优性似然因子：**

$$p(\mathcal O_t=1\mid s_t,a_t,\psi)\propto\exp(r_\psi(s_t,a_t))$$

奖励越高，对最优性事件的似然越大。这里先使用正的指数因子；任意正奖励的指数可能大于 1，不能不加条件就当成已归一化的 Bernoulli 概率。可在适当奖励范围/尺度下定义概率，或在能量模型中直接使用该势因子。

单步因子沿轨迹相乘，得到：

$$p(\tau\mid\mathcal O_{1:H}=1,\psi)\propto p(\tau)\exp\left(\sum_{t=1}^H r_\psi(s_t,a_t)\right)$$

其中 $p(\tau)$ 包含固定初始分布和环境转移，动作基测度也固定。指数连乘变成奖励累加后取指数。对 $\psi$ 求导时，动力学因子不变；但归一化需要遍历整个轨迹空间。

**这一步是一个行为概率模型的假设，不是证明所有专家必然按这个分布行动。** 奖励学习随后让示范在该模型下更可能。


### 公式 2 · Slide 4–5：IRL 的最大似然目标 + 配分函数 $Z$ {#formula-2}

> **这条公式的任务：** 区分示范上可算的奖励项与全空间的归一化。

**最大似然学习**
$$\arg\max_\psi\ \frac1N\sum_{i=1}^N\log p(\tau_i\mid\mathcal O,\psi)=\arg\max_\psi\left[\frac1N\sum_{i=1}^N r_\psi(\tau_i)-\log Z\right]$$

**配分函数**
$$Z=\int p(\tau)\exp\big(r_\psi(\tau)\big)\,d\tau$$

**怎么读**："调 $\psi$，让 N 条专家轨迹的对数似然平均最大；展开后 = '专家轨迹的平均奖励' 减去 '$\log Z$'。"

**为什么 $=$ 成立（逐步看）**
1. 代入公式 1：$\log p(\tau_i\mid\mathcal{O},\psi)=\underbrace{\log p(\tau_i)}_{\text{与}\psi\text{无关，扔}}+\,r_\psi(\tau_i)-\log Z$。
2. $r_\psi(\tau_i)=\sum_t r_\psi(\mathbf{s}_t^{(i)},\mathbf{a}_t^{(i)})$ —— 第 $i$ 条专家轨迹的总奖励。
3. $\log Z$ 来自公式 1 那个 $\propto$ 缺的归一化：$p(\tau\mid\mathcal O)=\frac1Z p(\tau)\exp(r_\psi(\tau))$，取 log 就甩出 $-\log Z$。

**逐符号拆 $Z$**
- $\int\cdots d\tau$ —— 对**所有可能的轨迹**积分（轨迹空间巨大无比）。
- $p(\tau)\exp(r_\psi(\tau))$ —— 公式 1 后验的"分子"。$Z$ 就是把这个分子在全空间加起来，好让它变成合法概率。

> ⚠️ **$Z$ 才是 IRL 的全部难点（slide 标"the hard part"）**：第一项 $\frac1N\sum r_\psi(\tau_i)$ 只用**专家样本**就能算，简单。但 $Z$ 要对**整个轨迹空间**积分 —— 这就是为什么"逆 RL 难"。**Part 1 剩下的每一页，都在和这个 $Z$ 搏斗。**

> 💡 一句话：**IRL = 最大化"专家轨迹奖励" − "所有轨迹的 log 配分"。** 第一项把专家往上抬，$\log Z$ 这个减项把"其它所有轨迹"往下压，否则只要把奖励无脑调大就能作弊。


这是去掉 $\log p(\tau_i)$ 常数后的同一个优化问题；两个目标的数值一般仍相差该常数。固定长度下，给所有奖励加常数会同时平移奖励和 log 配分，并不改变归一化行为分布，因此奖励未必唯一可辨识。



### 公式 3 · Slide 5：目标的梯度 → 两个期望之差 {#formula-3}

> **这条公式的任务：** 每一步都认清积分如何变成一个新分布的期望。

先对示范似然的奖励项直接求导，再处理 $\log Z$：

$$\nabla_\psi\mathcal L=\frac1N\sum_{i=1}^N\nabla_\psi r_\psi(\tau_i)-\nabla_\psi\log Z$$

**第 1 步：log 的链式法则。**

$$\nabla_\psi\log Z=\frac1Z\nabla_\psi Z$$

**第 2 步：对配分积分求导，指数再用一次链式法则。**

$$\frac1Z\nabla_\psi Z=\frac1Z\int p(\tau)\exp(r_\psi(\tau))\nabla_\psi r_\psi(\tau)\,d\tau$$

**第 3 步：认出真正的概率密度。**

$$\int\underbrace{\frac{p(\tau)\exp(r_\psi(\tau))}{Z}}_{p(\tau\mid\mathcal O,\psi)}\underbrace{\nabla_\psi r_\psi(\tau)}_{\text{被平均的量}}\,d\tau$$

只有这个归一化因子与第二部分对应好了，才可以写回期望：

$$\nabla_\psi\log Z=\mathbb E_{\tau\sim p(\tau\mid\mathcal O,\psi)}[\nabla_\psi r_\psi(\tau)]$$

所以总体目标的梯度为：

$$\nabla_\psi\mathcal L=\mathbb E_{\tau\sim\pi^\star}[\nabla_\psi r_\psi(\tau)]-\mathbb E_{\tau\sim p(\tau\mid\mathcal O,\psi)}[\nabla_\psi r_\psi(\tau)]$$

| 项 | 样本来源 | 作用 |
|---|---|---|
| 正项 | 专家示范 | 提高专家轨迹在奖励模型中的相对似然 |
| 负项 | 当前奖励诱导的归一化轨迹分布 | 防止只把所有轨迹都无条件抬高 |

若这两个期望相等，参数梯度为零，说明相应奖励梯度/特征期望匹配；有限表达能力下，不等于已经匹配整个行为分布，更不保证找到唯一真实奖励。难点是第二个期望的采样。


### 公式 4 · Slide 6：内层用 max-ent RL + 采样估计梯度 {#formula-4}

> **这条公式的任务：** 为奖励诱导分布构造策略采样，并检查可实现性。

**思路**：第二项的分布 $p(\mathbf{a}_t\mid\mathbf{s}_t,\mathcal O_{1:T},\psi)$（软最优策略）可以用**任意 max-ent RL 算法**学出来，目标是
$$J(\theta)=\sum_t\left(\mathbb E_{p_\theta(s_t),\pi_\theta}[r_\psi(s_t,a_t)]+\mathbb E_{p_\theta(s_t)}[\mathcal H(\pi_\theta(\cdot\mid s_t))]\right)$$

**怎么读**："训练一个策略 $\pi_\theta$，让它在当前奖励 $r_\psi$ 下既**拿高奖励**（第一项）又**保持高熵/随机**（第二项熵 $\mathcal H$）。"

**逐符号拆**
- 第一项 $\mathbb E[r_\psi]$ —— 普通 RL 目标（最大化期望奖励）。
- 第二项 $\mathbb E[\mathcal H(\pi)]$ —— **熵奖励**。加它是因为公式 1 的后验天生是"软"的（不是非黑即白的最优，而是"越优越可能"）。在相应可实现条件下，带熵目标与最优性推断相联系： $p(\mathbf{a}_t\mid\mathbf{s}_t,\mathcal O,\psi)$。

**学到策略后，跑它采样 $\{\tau_j\}$，把两个期望都换成有限和**：
$$\nabla_\psi\mathcal L\ \approx\ \frac1N\sum_{i=1}^N\nabla_\psi r_\psi(\tau_i)\ -\ \frac1M\sum_{j=1}^M\nabla_\psi r_\psi(\tau_j)$$

**逐符号拆**
- $\frac1N\sum_{i=1}^N$（左）—— "sum over **expert samples**"，$N$ 条专家轨迹。
- $\frac1M\sum_{j=1}^M$（右）—— "sum over **policy samples**"，$M$ 条当前策略 $\pi_\theta$ 跑出来的轨迹。
- 两个减项**结构一模一样**（都是 $\nabla_\psi r_\psi$ 的平均），只是**采样来源不同**：专家 vs 自己。

> 💡 一句话：**梯度 = "把专家走过的地方的奖励往上推" − "把自己走过的地方的奖励往下推"。** 这就是公式 3 的可计算版。

> ⚠️ **这一版很贵**：每更新一次奖励 $\psi$，第二项都要求一个**完整收敛的 max-ent RL 策略**再采样。下一页给省钱方案。


**条件要分开。** 确定性动力学下这种最大熵目标可与精确推断对应；随机动力学下，任意轨迹后验可能改变环境结果的条件分布，因果策略不能控制这些结果。此时固定环境转移下的最大熵策略优化通常是变分/受限近似，不能一概说采出的分布精确等于完整后验。[control-as-inference 综述](https://arxiv.org/abs/1805.00909)



### 公式 5 · Slide 7：未充分优化的策略与自归一化重要性采样 {#formula-5}

> **这条公式的任务：** 用提议策略样本近似目标平均，同时说明有限样本偏差。

**省钱思路（slide 把 "learn" 划掉改成 "improve (a little)"）**：别每次都把策略训到收敛，**只改进一点点**，然后就拿它采样。

> ⚠️ **但这会引入 bias（slide 红字 "estimator is now biased! wrong distribution!"）**：公式 4 第二项要求样本来自**当前奖励的软最优分布**；但"只改进一点点"的策略 $\pi$ 还没到那儿，分布**不对**，直接拿来平均就是错的。

**solution 1：重要性采样（importance sampling）**修正这个分布错配：
$$\nabla_\psi\mathcal L\ \approx\ \frac1N\sum_{i=1}^N\nabla_\psi r_\psi(\tau_i)\ -\ \frac{1}{\sum_j w_j}\sum_{j=1}^M w_j\,\nabla_\psi r_\psi(\tau_j),\qquad w_j=\frac{p(\tau_j)\exp\big(r_\psi(\tau_j)\big)}{p_\theta(\tau_j)}$$

**逐符号拆**
- $w_j$ —— 第 $j$ 条样本的**重要性权重** = $\dfrac{\text{它在目标分布（软最优）下的"未归一化概率"}}{\text{它在实际采样分布 }\pi\text{ 下的概率}}$。
- 分子 $p(\tau_j)\exp(r_\psi(\tau_j))$ —— 公式 1 后验的分子（目标分布想要的）。
- 分母 $p_\theta(\tau_j)$ —— 你**实际**用来采样的那个"还没练好"的策略。
- $\frac{1}{\sum_j w_j}$ —— 用**权重和**做归一化（self-normalized importance sampling），因为我们只知道目标分布到一个常数 $Z$。

> 🔑 **和 [Lecture10 公式逐行拆解](../lecture-10/) 同一招**：那里用重要性采样把"新策略目标"用"旧策略样本"算（公式 4）；这里用它把"软最优分布的期望"用"当前偷懒策略的样本"算。**同一个数学工具，换了个战场。**

策略改善有望让提议分布更接近目标、权重更均匀；并非任意优化器的每一步都保证分布距离下降。


**自归一化并不使有限样本严格无偏。** $\sum_jw_j\nabla r/\sum_jw_j$ 是两个样本和之比，通常存在有限样本偏差；在支持覆盖、适当可积等条件下随样本增长一致。它避免直接知道 $Z$，但仍可能受到极端权重和覆盖不足影响。



### 公式 6 · Slide 8：重要性权重的化简（转移全消掉） {#formula-6}

> **这条公式的任务：** 明确在哪个共同测度下环境概率可以约掉。

把 $w_j$ 里的轨迹概率按定义展开，会发现**绝大部分都能约掉**：
$$w_j=\frac{p(\tau)\exp(r_\psi(\tau))}{p_\theta(\tau)}=\frac{\cancel{p(\mathbf{s}_1)}\,\cancel{\prod_t p(\mathbf{s}_{t+1}\mid\mathbf{s}_t,\mathbf{a}_t)}\,\exp\big(\sum_t r_\psi(\mathbf{s}_t,\mathbf{a}_t)\big)}{\cancel{p(\mathbf{s}_1)}\,\cancel{\prod_t p(\mathbf{s}_{t+1}\mid\mathbf{s}_t,\mathbf{a}_t)}\,\prod_t\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)}=\frac{\exp\big(\sum_t r_\psi(\mathbf{s}_t,\mathbf{a}_t)\big)}{\prod_t\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)}$$

**怎么读**："分子分母里的**初始状态 $p(\mathbf{s}_1)$ 和环境转移 $\prod p(\mathbf{s}_{t+1}\mid\mathbf{s}_t,\mathbf{a}_t)$ 完全相同，约掉**；只剩'奖励的 exp'除以'策略各步动作概率之乘积'。"

**逐符号拆为什么能约**
- $p(\tau)=p(\mathbf{s}_1)\prod_t p(\mathbf{s}_{t+1}\mid\mathbf{s}_t,\mathbf{a}_t)$ —— 纯动力学，不含策略。
- $p_\theta(\tau)=p(\mathbf{s}_1)\prod_t p(\mathbf{s}_{t+1}\mid\mathbf{s}_t,\mathbf{a}_t)\,\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)$ —— 动力学**乘上**策略。
- 两者只差一个 $\prod_t\pi_\theta(\mathbf{a}_t\mid\mathbf{s}_t)$ —— 所以**未知的环境模型整片消失**，只留下你**能算的东西**（奖励 + 自己的策略概率）。

> 🔑 **和 [Lecture2 公式逐行拆解](../lecture-02/) / [Lecture10 公式逐行拆解](../lecture-10/) 的"转移消去"是同一个魔法**：只要两条轨迹概率**在同一动作基测度下共享同一套动力学**，比值里的环境模型必然约光 —— 这就是 model-free 方法能绕开"不知道环境"的根本原因。

> 💡 一句话：**重要性权重不需要知道环境怎么转移，只需要知道"奖励"和"自己每步动作的概率"。** 这让公式 5 真正可算。



### 公式 7 · Slide 9：奖励与策略交替优化：对抗结构 {#formula-7}

> **这条公式的任务：** 把两套参数的交替优化装入完整循环。

把两个梯度并排放，IRL 突然显出**两个玩家在对抗**的样子：

**奖励 / 判别器一方（最大化区分专家与自己）**
$$\nabla_\psi\mathcal L\ \approx\ \frac1N\sum_{i=1}^N\nabla_\psi r_\psi(\tau_i)\ -\ \frac{1}{\sum_j w_j}\sum_{j=1}^M w_j\nabla_\psi r_\psi(\tau_j)\qquad(\text{demos 更可能，samples 更不可能})$$

**策略 / 生成器一方（让自己更难被区分）**
$$\nabla_\theta\mathcal L\ \approx\ \frac1M\sum_{j=1}^M\sum_{t=1}^H\nabla_\theta\log\pi_\theta(a_t^{(j)}\mid s_t^{(j)})\,r_\psi(\tau_j)$$

**怎么读**
- 上式（奖励 $\psi$）："**抬高专家轨迹的奖励、压低自己样本的奖励**" —— 让奖励函数学会"挑刺"，把专家和模仿者分开。
- 下式（策略 $\theta$）：就是一条**策略梯度**（[Lecture9 公式逐行拆解](../lecture-09/) 的 $\nabla\log\pi\cdot r$ 形式），用当前奖励 $r_\psi$ 当回报，**把策略往"高奖励"方向推** —— slide 注："policy changed to make it **harder** to distinguish from demos"。

**逐符号拆下式**
- $\sum_{t=1}^H\nabla_\theta\log\pi_\theta(a_t^{(j)}\mid s_t^{(j)})$ —— 策略梯度的老朋友（"提高这条轨迹概率的方向"）。
- $r_\psi(\tau_j)$ —— 当前奖励给这条轨迹打的分，**当成 REINFORCE 里的回报**。
- 合起来：**奖励高的轨迹，就提高它的概率** —— 标准策略梯度。

> 🔑 **两个玩家的对抗（slide 标题 "It looks a bit like a game…"）**：
> - **奖励 $r_\psi$（判别器）**：努力把"专家"和"机器人"分开（专家奖励↑、机器人奖励↓）。
> - **策略 $\pi_\theta$（生成器）**：努力让自己的轨迹**骗过奖励**，看起来像专家。
> 这形成了与 GAN 类似的对抗结构。下一页把它和真正的 GAN 对上号。


#### 奖励与策略交替更新，整组看 {#irl-loop}

$$\begin{aligned}
&1.\ \text{专家数据：}\quad\tau_i\sim\pi^\star(\tau),\quad i=1,\ldots,N\\
&2.\ \text{策略改善：}\quad\max_\theta\mathbb E_{p_\theta}\left[r_\psi(\tau)+\sum_t\mathcal H(\pi_\theta(\cdot\mid s_t))\right]\quad(\psi\text{ 固定，可不充分优化})\\
&3.\ \text{采样与权重：}\quad\tau_j\sim p_\theta,\quad w_j=\frac{p(\tau_j)e^{r_\psi(\tau_j)}}{p_\theta(\tau_j)}\\
&4.\ \text{奖励更新：}\quad\psi\leftarrow\psi+\alpha\left[\frac1N\sum_i\nabla_\psi r_\psi(\tau_i)-\frac{\sum_jw_j\nabla_\psi r_\psi(\tau_j)}{\sum_jw_j}\right]\\
&5.\ \text{刷新奖励后回到 2，继续改善策略与采样}
\end{aligned}$$

策略与奖励两套参数交替固定；这一版使用自归一化估计，不宣称有限样本或每个内层更新都有精确总体保证。



### 公式 8 · Slide 10：生成对抗网络（GAN） {#formula-8}

> **这条公式的任务：** 读出 GAN 的两个目标及生成器变体。

GAN 训练两个网络对打（Goodfellow et al. '14）：

**判别器 $D_\psi$（学着分辨真假）**
$$\psi=\arg\max_\psi\ \frac1N\sum_{\mathbf{x}\sim p^\star}\log D_\psi(\mathbf{x})\ +\ \frac1M\sum_{\mathbf{x}\sim p_\theta}\log\big(1-D_\psi(\mathbf{x})\big)$$

**生成器 $p_\theta$（学着骗过判别器）**
$$\theta=\arg\max_\theta\ \mathbb E_{\mathbf{x}\sim p_\theta}\big[\log D_\psi(\mathbf{x})\big]$$

**逐符号拆**
- $D_\psi(\mathbf{x})=p_\psi(\text{real}\mid\mathbf{x})$ —— 判别器认为"$\mathbf{x}$ 是**真**数据"的概率（0~1）。
- $p^\star$ —— 真实数据分布（"demonstrations"）；$p_\theta(\mathbf{x}\mid\mathbf{z})$ —— 生成器从噪声 $\mathbf{z}$ 造出的假样本。
- 判别器目标：对真样本 $\log D$ 越大越好（认成真），对假样本 $\log(1-D)$ 越大越好（认成假）。
- 生成器目标：让 $\log D_\psi(\mathbf{x})$ 大 —— 即**让判别器把自己造的假样本误判成真**。

> 🔑 **一一对应（这就是 Part 1 的题眼）**：
> | GAN | IRL |
> |---|---|
> | 真实数据 $p^\star$ | 专家示范 $\pi^\star$ |
> | 生成器 $p_\theta$ | 策略 $\pi_\theta$ |
> | 判别器 $D_\psi$ | 奖励 $r_\psi$ |
> | "骗过判别器" | "拿高奖励/像专家" |
>
> **本讲的对抗式 IRL 与特定 GAN 结构相联系** —— 这是本课 Part 1 想让你记住的核心同构。


这里生成器最大化 $\log D$ 是常用的 non-saturating 目标；它和原始 GAN 的 minimax 生成器目标不同，不能只因为判别器相同就把全部优化目标视为逐项相等。



### 公式 9 · Slide 11：能不能直接用普通判别器？（GAIL） {#formula-9}

> **这条公式的任务：** 解释直接对抗模仿得到什么、仍欠什么。

用普通二分类器判断一个状态—动作样本是否来自专家，约定 $D_\psi=1$ 表示专家：

$$\max_\psi\ \mathbb E_{\text{专家占用分布}}[\log D_\psi(s,a)]+\mathbb E_{\text{策略占用分布}}[\log(1-D_\psi(s,a))]$$

策略将判别器给出的模仿信号用作奖励，例如采用 $\log D_\psi(s,a)$ 的非饱和目标，并通过完整策略梯度更新：

$$\nabla_\theta J(\theta)\approx\frac1M\sum_{j,t}\nabla_\theta\log\pi_\theta(a_t^{(j)}\mid s_t^{(j)})\hat Q_t^{(j)}$$

这里 $\hat Q_t$ 由所选择的判别器奖励计算。普通 GAIL 常在状态—动作占用分布上做分类；原笔记的轨迹级 $D(\tau)$ 是展示对抗结构的另一种概括，不是必须输入完整轨迹。

**买到的东西：** 直接获得模仿策略，避免每一步显式解奖励模型的配分积分。**仍欠的东西：** 判别边界与当前策略及环境有关，不能保证就是一份跨环境可复用的真实任务奖励。分布匹配处的最优平衡判别器可趋于 $1/2$，这也不等于任何有限模型“完全没有知识”。[GAIL 原论文](https://arxiv.org/abs/1606.03476)


### 公式 10 · Slide 12：结构化密度比判别器与 IRL 的联系 {#formula-10}

> **这条公式的任务：** 给出包含奖励的密度比判别器，避免错误约分和泛化承诺。

假设专家侧轨迹模型为 $p(\tau)e^{r_\psi(\tau)}/Z$，策略侧为 $p_\theta(\tau)$，且两类先验各为一半。对应的密度比判别器为：

$$D_\psi(\tau)=\frac{p(\tau)e^{r_\psi(\tau)}/Z}{p(\tau)e^{r_\psi(\tau)}/Z+p_\theta(\tau)}$$

在固定动作基测度下，$p_\theta(\tau)=p(\tau)\prod_t\pi_\theta(a_t\mid s_t)$，消去公共动力学：

$$D_\psi(\tau)=\frac{e^{r_\psi(\tau)}/Z}{e^{r_\psi(\tau)}/Z+\prod_t\pi_\theta(a_t\mid s_t)}$$

**不能只删除专家侧的动力学，却把策略侧仍写成含动力学的完整轨迹概率。** 两边必须在同一测度上比较，再同时消去公共因子。

还可看出判别 logit：

$$\log\frac{D_\psi(\tau)}{1-D_\psi(\tau)}=r_\psi(\tau)-\log Z-\sum_t\log\pi_\theta(a_t\mid s_t)$$

奖励显式进入判别器，这说明奖励学习与对抗分类的结构联系。实际 AIRL 使用转移级结构与奖励/势函数分解，并在相应假设下讨论奖励迁移；仅写一个含指数奖励的判别器，并不能保证恢复唯一、任意环境可迁移的奖励。[AIRL 原论文](https://arxiv.org/abs/1710.11248)

因此，本讲应记住“特定结构的奖励学习可以连接对抗优化”，而不是把所有 IRL 方法、GAN 目标和 GAIL 逐项划成同一个公式。


## Part 2：语言模型的概率与策略梯度


### 公式 11 · Slide 20：把 LLM 看成"一步 RL" {#formula-11}

> **这条公式的任务：** 把整段回答当作一个随机动作。

**策略 = 在 prompt 下生成 completion**
$$\pi_\theta(\mathbf{a}\mid\mathbf{s}),\qquad p(\mathbf{a}\mid\mathbf{s})=p(x_5\mid x_{1:4})\,p(x_6\mid x_{1:4},x_5)$$

**目标 = 一步 RL 的期望奖励**
$$\mathbb E_{\pi_\theta(\mathbf{a}\mid\mathbf{s})}\big[r(\mathbf{s},\mathbf{a})\big]$$

**逐符号拆（看 slide 那张图）**
- $\mathbf{s}$ = **context / prompt / prefix**（上文，如 "what is capital of France?"）。
- $\mathbf{a}$ = **completion**（补全，如 "Paris EOS"）。
- $p(\mathbf{a}\mid\mathbf{s})=\prod p(x_t\mid x_{<t})$ —— 整个 completion 的概率 = 各 token 条件概率连乘（这就是 transformer 的 autoregressive 输出）。
- $r(\mathbf{s},\mathbf{a})$ —— 给"整段回答"打一个分（如"对不对""人喜不喜欢"）。

> 🟨 **slide 黄框 "Basic one step RL problem"**：把**整段回答**当作**一个动作 $\mathbf a$**，于是"prompt→回答→打分"就是一个**单步**（one-step / bandit）RL 问题。最简单的视角：发一个动作，拿一个奖励，结束。

> 🔑 **和 [Lecture2 公式逐行拆解](../lecture-02/) 公式 1–2 的呼应**：监督学习的 $p_\theta(y\mid\mathbf x)$、模仿学习的 $\pi_\theta(\mathbf a_t\mid\mathbf o_t)$、这里 LLM 的 $\pi_\theta(\mathbf a\mid\mathbf s)$ —— **同一个条件概率骨架**，只是把 $\mathbf x/\mathbf o\to$ prompt、$y/\mathbf a\to$ completion。所以语言模型"天生就是个策略"。


prompt 也可来自一个固定任务分布，目标再对 prompt 平均。将 completion 整体视为动作，要求整段回答的概率包括 EOS/终止规则并与实际采样分布一致。



### 公式 12 · Slide 21：等价的"多步"视角 {#formula-12}

> **这条公式的任务：** 将同一生成过程按 token 分解。

把同一个回答**逐 token 拆成多步**：
$$\pi_\theta(\mathbf{a}_1\mid\mathbf{s}_1),\ \pi_\theta(\mathbf{a}_2\mid\mathbf{s}_2),\ \dots\qquad\Longrightarrow\qquad \mathbb E_{\pi_\theta(\tau)}\big[r(\tau)\big]$$

**怎么读**："不再把整段回答当一个动作，而是**每生成一个 token = 一步**（动作 $\mathbf a_t$ = 第 $t$ 个 token，状态 $\mathbf s_t$ = 已生成的前缀）；目标变成对**整条轨迹** $\tau$ 求期望回报。"

**逐符号拆**
- $\mathbf{s}_1,\mathbf{s}_2,\dots$ —— 状态随着生成不断变长（$\mathbf s_2$ = prompt + 第一个生成 token …）。
- $\mathbf{a}_1,\mathbf{a}_2,\dots$ —— 一个个 token。
- $\tau$ —— 整条 "prompt + 逐 token 生成" 的轨迹。

**和公式 11 啥关系？** 数学上**完全等价**（一步 vs 多步只是把同一个 $p(\mathbf a\mid\mathbf s)$ 拆不拆开）。

> 🟨 **slide 黄框：为什么要这个多步视角**："this perspective makes more sense when we use **intermediate rewards and value function baselines**" —— 一旦你想给"中间 token"打分、或用**价值函数当 baseline 降方差**（Part 3），就必须把它看成**多步**问题。**一步视角好理解，多步视角好优化。**


“等价”指保留相同采样规则与总奖励时，两种分解给出相同目标；若另外增加中间奖励、不同折扣或长度权重，就已经改变了目标，而不只是换记号。



### 公式 13 · Slide 22：LLM 的策略梯度（REINFORCE 与 PPO 两版） {#formula-13}

> **这条公式的任务：** 完整保留 log 概率梯度，分开精确 IS 与代理更新。

**先把 $\nabla\log\pi$ 摊到 token 级**
$$\nabla_\theta\log\pi_\theta(\mathbf{a}\mid\mathbf{s})=\nabla_\theta\log p(x_5\mid x_{1:4})+\nabla_\theta\log p(x_6\mid x_{1:4},x_5)$$
（log 把连乘变连加 → 整段的 log 概率梯度 = 各 token log 概率梯度之和。）

**策略梯度恒等式**
$$\nabla_\theta\,\mathbb E_{\pi_\theta(\mathbf{a}\mid\mathbf{s})}\big[r(\mathbf{s},\mathbf{a})\big]=\mathbb E_{\pi_\theta(\mathbf{a}\mid\mathbf{s})}\big[\nabla_\theta\log\pi_\theta(\mathbf{a}\mid\mathbf{s})\,r(\mathbf{s},\mathbf{a})\big]$$

**两种估计器**

① **REINFORCE 版**（直接用自己的样本）：
$$\nabla_\theta\,\mathbb E[r]\ \approx\ \frac1N\sum_i\nabla_\theta\log\pi_\theta(\mathbf{a}_i\mid\mathbf{s}_i)\,r(\mathbf{s}_i,\mathbf{a}_i)\qquad(\mathbf{a}_i\sim\pi_\theta)$$

② **重要性加权版（PPO 类）**（用旧策略 $\bar\pi$ 的样本）：
$$\nabla_\theta\,\mathbb E[r]\ \approx\ \frac1N\sum_i\frac{\pi_\theta(\mathbf{a}_i\mid\mathbf{s}_i)}{\bar\pi(\mathbf{a}_i\mid\mathbf{s}_i)}\,\nabla_\theta\log\pi_\theta(\mathbf{a}_i\mid\mathbf{s}_i)\,r(\mathbf{s}_i,\mathbf{a}_i)\qquad(\mathbf{a}_i\sim\bar\pi)$$

**逐符号拆**
- $\frac{\pi_\theta(\mathbf a_i\mid\mathbf s_i)}{\bar\pi(\mathbf a_i\mid\mathbf s_i)}$ —— **重要性比值**：样本来自旧策略 $\bar\pi$，但我们想要新策略 $\pi_\theta$ 的梯度，比值把分布"换算"过来（同 [Lecture10 公式逐行拆解](../lecture-10/) 公式 4）。
- "samples from $\pi_\theta$"（①）vs "samples from $\bar\pi$"（②）—— 这是两者唯一的本质区别。

> ❓ **"Why might we prefer this?"（slide 提问，下一页答）**：因为 ② 允许**采一批样本（用 $\bar\pi$）后，反复更新 $\theta$ 很多步**而不用每步重采 —— 对 LLM 这种**采样极贵**（要跑一整段生成）的场景，省钱是刚需。① 每更新一次就得重新采样，太奢侈。

> 🔑 **这页 = lec9/lec10 的策略梯度，原封不动搬到 LLM**：$\nabla\log\pi\cdot r$ 的 REINFORCE、重要性采样换分布、PPO —— 你已经全学过，这里只是把 $\mathbf a$ 解释成"一段文字"。


**整段与单 token 比值要区分：**

$$\frac{\pi_\theta(a\mid s)}{\bar\pi(a\mid s)}=\prod_t\frac{\pi_\theta(a_t\mid s_t)}{\bar\pi(a_t\mid s_t)}$$

固定 prompt 分布下，完整 completion 比值可以精确换动作分布；PPO 常使用单 token 比值配固定优势，是旧前缀分布上的局部代理。后者沿用 Lecture 9–10 的近似条件，不等于把整个连乘严格约成一项。



### 公式 14 · Slide 23：PPO-on-LLM 的训练循环 {#formula-14}

> **这条公式的任务：** 先整体看训练机器，再填三个插口。

先展示只含采样、奖励与旧样本复用的完整框架；baseline 和参考 KL 暂留到后面填：

$$\begin{aligned}
&1.\ \text{冻结采样策略：}\quad\bar\pi\leftarrow\pi_\theta\\
&2.\ \text{生成回答：}\quad a_i\sim\bar\pi(\cdot\mid s_i),\quad i=1,\ldots,N\\
&3.\ \text{打分：}\quad r(s_i,a_i)\\
&4.\ \text{取同批小批数据，旧概率与样本固定}\\
&5.\ \text{更新：}\quad\theta\leftarrow\theta+\frac{\alpha}{N}\sum_i\frac{\pi_\theta(a_i\mid s_i)}{\bar\pi(a_i\mid s_i)}\nabla_\theta\log\pi_\theta(a_i\mid s_i)r(s_i,a_i)\quad(\text{重复 }K\text{ 次})\\
&6.\ \text{刷新采样策略，回到 1 生成新一批}
\end{aligned}$$

这组先以整段回答为动作展示 IS 更新。固定 prompt、支持覆盖、奖励不显式依赖当前参数等条件下，它估计完整 completion 分布的梯度；仍可能有很大方差，尚未加入 PPO-Clip。

**三个待填插口：** baseline 减少估计噪声；regularizer 约束偏离固定参考；reward 来自验证器、奖励模型或其他可评估任务目标。后面每一组公式都回到这台训练机器里的一个位置。



## Part 3：优势、参考正则与 PPO 的完整装配


### 公式 15 · Slide 27：价值函数 baseline & GAE {#formula-15}

> **这条公式的任务：** 把 critic、TD 与 GAE 放到生成位置上。

**回顾**：策略梯度里把 $r$ 换成 **advantage** $\hat A$ 通常用于降低方差（baseline 思想）。LLM 常用 **GAE（Generalized Advantage Estimation）**。

**单步 TD 误差**
$$\delta_{t'}=r(\mathbf{s}_{t'},\mathbf{a}_{t'})+\gamma\hat V_\phi^\pi(\mathbf{s}_{t'+1})-\hat V_\phi^\pi(\mathbf{s}_{t'})$$

**GAE 优势 = TD 误差的几何加权和**
$$\hat A_{\mathrm{GAE}}^\pi(\mathbf{s}_t,\mathbf{a}_t)=\sum_{t'=t}^H(\gamma\lambda)^{t'-t}\,\delta_{t'}$$

**逐符号拆**
- $\delta_{t'}$ —— "**实际看到的一步回报** $r+\gamma\hat V(\mathbf s_{t'+1})$" 减去 "**预测值** $\hat V(\mathbf s_{t'})$"；正数=比预期好，负数=比预期差。
- $\hat V_\phi^\pi$ —— 价值函数（另一个网络/网络的另一个头，参数 $\phi$）。
- 折扣为 γ；GAE 的 λ 控制真实 rollout 与 critic 尾部的混合。λ = 0 为单步 TD；λ = 1 在真实终止、末端价值为零时为 MC 回报减 baseline。偏差与方差不保证对任意模型单调变化。
- $(\gamma\lambda)^{t'-t}$ —— 越远的 TD 误差权重指数衰减。

**价值函数的训练（回归到 GAE 目标）**
$$\mathcal L(\phi)=\frac12\sum_{i=1}^N\big\lVert\hat V_\phi^\pi(\mathbf{s}_i)-y_i\big\rVert^2,\qquad y_i=\hat A_{\mathrm{GAE}}^\pi(\mathbf{s}_i,\mathbf{a}_i)+\hat V_{\mathrm{old}}(\mathbf{s}_i)$$

**逐符号拆**
- 这是个**最小二乘回归**：让 $\hat V_\phi$ 去拟合目标 $y_i$。
- 目标 $y_i=\hat A_{\mathrm{GAE}}+\hat V_{\mathrm{old}}$ —— 因为 $A=Q-V$，所以 $Q\approx A+V_{\mathrm{old}}$，用它当价值回归目标（TD($\lambda$) 风格）。

> 🔧 **两个工程细节（slide 橙框）**：
> - **价值头**："either add a new head or make a copy of the entire network" —— 价值函数要么和策略**共享 transformer 加一个输出头**，要么**整份拷贝**。
> - **只训 suffix**："don't train the value function on the **prompt**, only the **suffix**" —— prompt 是给定的，没必要对它估值，只对**生成出来的部分**算 value。

> 🔗 GAE 是 actor-critic 那一课的延伸，这里把它接到 LLM 的 token 级 advantage 上。


拟合价值时把 $y_i$ 与旧价值固定，不对构造目标的旧网络反向传播。真实终止后后续价值取零；只是截断则保留合适的 bootstrap。完整 GAE 来历见 [Lecture 6](../lecture-06/)。



### 公式 16 · Slide 28：不要价值函数也能 baseline → GRPO {#formula-16}

> **这条公式的任务：** 解释组内相对权重与其统计条件。

对同一个 prompt $s_i$，从采样策略生成 $K$ 个回答 $a_{i,1},\ldots,a_{i,K}$。先保留原笔记的简化组内中心化：

$$\hat A_{i,j}=r(s_i,a_{i,j})-\frac1K\sum_{k=1}^K r(s_i,a_{i,k})$$

**怎么读：** 一个回答比同题其他回答的平均水平好多少。所有样本得分一致时，组内差为零；$K=1$ 时也没有相对信号。

对这版简化的整段目标，可以用：

$$\frac1{NK}\sum_{i,j}\frac{\pi_\theta(a_{i,j}\mid s_i)}{\bar\pi(a_{i,j}\mid s_i)}\nabla_\theta\log\pi_\theta(a_{i,j}\mid s_i)\hat A_{i,j}$$

这是组内权重配动作比值的经验更新。标准 GRPO 还常将组内差除以组标准差，并在 token 级裁剪目标里使用相应权重：

$$\hat A_{i,j}=\frac{r(s_i,a_{i,j})-\frac1K\sum_k r(s_i,a_{i,k})}{\operatorname{std}_{k=1,\ldots,K}[r(s_i,a_{i,k})]}$$

标准差为零需要实现约定，通常设置正的分母下限；此时中心化分子也为零。真实目标还明确回答长度的归一化和参考 KL，不能把“减均值”一条公式当成完整 GRPO。[DeepSeekMath 的 GRPO 定义](https://arxiv.org/abs/2402.03300)

**批均值包含自己，严格无偏性需另看。** 在固定 prompt、独立同分布回答、on-policy、仅减均值不除随机标准差的理想条件下：

$$\mathbb E\left[\frac1K\sum_j\nabla_\theta\log\pi_\theta(a_{i,j}\mid s_i)\left(r(s_i,a_{i,j})-\frac1K\sum_k r(s_i,a_{i,k})\right)\right]=\left(1-\frac1K\right)\nabla_\theta\mathbb E[r\mid s_i]$$

自项与自身动作相关，不能直接以“baseline 只看 prompt”推出零贡献。留一均值可去掉这一自项偏差；随机标准差、裁剪、多次更新又有各自的影响。这里的目的主要是降低 critic 成本与提供相对学习信号。

| 方法 | 参照 | 主要代价 |
|---|---|---|
| GAE | 每个 prefix 的 critic 估值 | 要拟合价值头，有自举误差 |
| 组内相对优势 | 同 prompt 的多个回答 | 要采多个回答，统计量依赖整组与具体归一化 |



### 公式 17 · Slide 29：参考模型正则（KL） {#formula-17}

> **这条公式的任务：** 分开本批采样旧策略和长期参考模型。

长期参考模型 $\pi_{\mathrm{ref}}$ 与每批变化的采样旧策略 $\bar\pi$ 是不同对象。参考 KL 比较的是两个完整分布，不能把单个动作的两个概率值直接放进散度：

$$D_{\mathrm{KL}}(\pi_\theta(\cdot\mid s)\Vert\pi_{\mathrm{ref}}(\cdot\mid s))=\mathbb E_{a\sim\pi_\theta}\left[\log\frac{\pi_\theta(a\mid s)}{\pi_{\mathrm{ref}}(a\mid s)}\right]$$

整段动作视角下，任务奖励加参考正则：

$$\mathbb E_{a\sim\pi_\theta}[r(s,a)]-\beta D_{\mathrm{KL}}(\pi_\theta(\cdot\mid s)\Vert\pi_{\mathrm{ref}}(\cdot\mid s))$$

自回归分解与 KL 链式法则给出：

$$D_{\mathrm{KL}}(\pi_\theta(\text{completion}\mid s)\Vert\pi_{\mathrm{ref}}(\text{completion}\mid s))=\mathbb E_{\tau\sim\pi_\theta}\left[\sum_t\log\frac{\pi_\theta(a_t\mid s_t)}{\pi_{\mathrm{ref}}(a_t\mid s_t)}\right]$$

**采样时的 token 奖励写法：**

$$\bar r(s_t,a_t)=r(s_t,a_t)-\beta\log\frac{\pi_\theta(a_t\mid s_t)}{\pi_{\mathrm{ref}}(a_t\mid s_t)}$$

单个 log 比可以为负；在对应分布下平均才是 KL。一轮 PPO 实现可用采样策略计算并固定这些奖励与优势；内层是代理优化，不能说每个新参数处仍精确优化同一个固定 shaped reward。

参考正则鼓励保留原模型行为，能限制偏离，但不能保证没有 reward hacking 或无效语言。[InstructGPT 的奖励与参考 KL](https://arxiv.org/abs/2203.02155)

| 对比对象 | 用途 | 何时变化 |
|---|---|---|
| 当前 $\pi_\theta$ 与采样 $\bar\pi$ | IS/局部 PPO 数据复用 | 每批刷新 $\bar\pi$ |
| 当前 $\pi_\theta$ 与参考 $\pi_{\mathrm{ref}}$ | 长期行为正则 | 参考通常长期冻结 |



### 公式 18 · Slide 30：全部拼起来 → PPO-for-LLMs {#formula-18}

> **这条公式的任务：** 完整装配生成、打分、优势、价值拟合与 clip。

统一沿用 $\pi_\theta$ 为当前优化策略、$\bar\pi$ 为固定采样策略，不再在同一页来回改变参数角色。完整 token 裁剪目标为：

$$\mathcal L_{\mathrm{CLIP}}(\theta)=\frac1N\sum_{i,t}\min\left\{\frac{\pi_\theta(a_t^{(i)}\mid s_t^{(i)})}{\bar\pi(a_t^{(i)}\mid s_t^{(i)})}\hat A_t^{(i)},\ \operatorname{clip}\left(\frac{\pi_\theta(a_t^{(i)}\mid s_t^{(i)})}{\bar\pi(a_t^{(i)}\mid s_t^{(i)})},1-\epsilon,1+\epsilon\right)\hat A_t^{(i)}\right\}$$

这一归一化按轨迹平均；实际按有效 token 或按回答长度平均时，学习目标的权重也需说清。min 的正负优势分支见 [Lecture 9 的四格表](../lecture-09/#clip-cases)。

#### 完整 PPO-for-LLM 循环 {#llm-ppo-loop}

$$\begin{aligned}
&1.\ \text{固定本批采样策略：}\quad\bar\pi\leftarrow\pi_\theta,\quad\pi_{\mathrm{ref}}\text{ 长期冻结}\\
&2.\ \text{生成：}\quad a_t^{(i)}\sim\bar\pi(\cdot\mid s_t^{(i)})\\
&3.\ \text{打分并加参考惩罚：}\quad\bar r_t^{(i)}=r_t^{(i)}-\beta\log\frac{\bar\pi(a_t^{(i)}\mid s_t^{(i)})}{\pi_{\mathrm{ref}}(a_t^{(i)}\mid s_t^{(i)})}\\
&4.\ \text{算 GAE：}\quad\delta_t^{(i)}=\bar r_t^{(i)}+\gamma\hat V_{\mathrm{old}}(s_{t+1}^{(i)})-\hat V_{\mathrm{old}}(s_t^{(i)}),\quad\hat A_t^{(i)}=\sum_{t'=t}^H(\gamma\lambda)^{t'-t}\delta_{t'}^{(i)}\\
&5.\ \text{拟合价值：}\quad y_t^{(i)}=\hat A_t^{(i)}+\hat V_{\mathrm{old}}(s_t^{(i)}),\quad\min_\phi\sum_{i,t}(\hat V_\phi(s_t^{(i)})-y_t^{(i)})^2\\
&6.\ \text{取同批 minibatch，固定旧概率、奖励与优势}\\
&7.\ \text{优化：}\quad\theta\leftarrow\theta+\alpha\nabla_\theta\mathcal L_{\mathrm{CLIP}}(\theta)\quad(6\text{–}7\text{ 重复 }K\text{ 次})\\
&8.\ \text{刷新 }\bar\pi\text{，回到 1 生成新一批}
\end{aligned}$$

这组集中呈现 GAE、参考惩罚、critic 回归与 clip/min。使用组内相对优势时，优势构造与价值训练步骤按相应算法替换；不是同时再训练一份已省去的 critic。

clip 改的是目标激励，真实比值仍可出区间；min 逐点低于未裁剪代理项，不是实际总奖励的通用下界。参考惩罚已进入当前优势时，应明确是否还另外加 KL loss，避免不知不觉重复计入同一罚项。



## Part 4：偏好与验证器提供奖励


### 公式 19 · Slide 33：Bradley-Terry 偏好模型 {#formula-19}

> **这条公式的任务：** 把二元偏好转成可训练的奖励差概率。

**问题**："How do we train $r_\psi$? need probabilistic model!" —— 人只会说"A 比 B 好"，怎么把它变成能训奖励的概率模型？

**Bradley-Terry：偏好概率 = 奖励的 softmax**
$$p(\tau_i\succ\tau_j)=\frac{\exp\big(\sum_t r_\psi(\mathbf s_t^{(i)},\mathbf a_t^{(i)})\big)}{\exp\big(\sum_t r_\psi(\mathbf s_t^{(i)},\mathbf a_t^{(i)})\big)+\exp\big(\sum_t r_\psi(\mathbf s_t^{(j)},\mathbf a_t^{(j)})\big)}$$

**怎么读**："轨迹 $i$ 被选中（优于 $j$）的概率 = $i$ 的奖励 exp，除以 $i$、$j$ 两者奖励 exp 之和。"（$\succ$ 读"优于 / preferred over"。）

**用 sigmoid 写成更简洁的对数似然**
$$\log p(\tau_i\succ\tau_j)=\log\sigma\big(r_\psi(\tau_i)-r_\psi(\tau_j)\big)$$

**训练目标**
$$\psi\leftarrow\arg\max_\psi\sum_{i,j}\log\sigma\big(r_\psi(\tau_i)-r_\psi(\tau_j)\big)$$

**逐符号拆**
- $r_\psi(\tau)=\sum_t r_\psi(\mathbf s_t,\mathbf a_t)$ —— 整条轨迹奖励。
- 两个 exp 相除 = softmax，正好把"两奖励的差"压成"被偏好的概率"。
- $\sigma(r_\psi(\tau_i)-r_\psi(\tau_j))$ —— 化简：分子分母同除 $\exp(r_\psi(\tau_i))$ 即得 $\frac{1}{1+\exp(-(r_i-r_j))}=\sigma(r_i-r_j)$。**只取决于两者奖励之差**。

> 💬 **slide 两句话直觉**：
> - "**better trajectories are exponentially more likely to be chosen based on their reward**" —— 奖励高一点，被选中的概率指数级提高。
> - "the same method as **Elo scores in chess**" —— 和国际象棋 Elo 等级分一个模型（用对局胜负反推每个人的"实力分"）。

> 🔑 **slide 红字 "this looks a lot like logistic regression"**：是的 —— 把"$i$ 赢 $j$"当二分类标签，特征是 $r_\psi(\tau_i)-r_\psi(\tau_j)$，目标是 $\log\sigma(\cdot)$ → **这是二元 logistic 似然的形式**。这也是 RLHF 奖励模型训练的标准损失，和后来的 **DPO** 同根同源。



### 公式 20 · Slide 34, 36–37：完整 RLHF 算法 {#formula-20}

> **这条公式的任务：** 把奖励拟合的外循环和 PPO 的内循环接起来。

偏好奖励学习和策略训练的外循环集中看：

$$\begin{aligned}
&1.\ \text{同题多个回答：}\quad a_{i,j}\sim\pi_\theta(\cdot\mid s_i)\\
&2.\ \text{获取偏好：}\quad\tau_i\succ\tau_j\quad(\text{比较相同 prompt 的回答})\\
&3.\ \text{奖励拟合：}\quad\psi\leftarrow\arg\max_\psi\sum_{i\succ j}\log\sigma(r_\psi(\tau_i)-r_\psi(\tau_j))\\
&4.\ \text{策略训练：}\quad\max_\theta\mathbb E_{\pi_\theta}[r_\psi]-\beta D_{\mathrm{KL}}(\pi_\theta\Vert\pi_{\mathrm{ref}})\quad(\text{用 PPO 等算法近似执行})
\end{aligned}$$

第 4 步内部又是一整组 PPO 更新；偏好收集/奖励拟合的外循环与每批 token 更新的内循环分别看。原笔记把末尾偏好分数作为终端奖励，参考 KL 仍可按 token 提供稠密信号。

外循环可以迭代重新收集偏好，也可先离线拟合固定奖励模型再进行多轮策略训练。不能因为内层更新多次，就认为每一批都必须让人重新标注；也不能因此忽略奖励模型在新行为上的泛化误差。

**验证器与过程奖励。** 可验证数学答案、程序测试等任务能直接给任务奖励，不必先拟合偏好模型；过程奖励给中间步骤额外信号。奖励来源不同，目标和归一化仍须明确，不是自动获得同一评价标准。

#### 部分可观测的接口

语言生成通常将完整 prefix 当状态；一般交互环境只给观测 $o_t$，隐藏真实状态 $s_t$。此时同一观测可能来自不同历史、具有不同后续价值。信息收集动作可能有未来价值；随机无记忆策略也可能优于确定性无记忆策略。但这不意味着一般 POMDP 的最优历史策略必然随机。

纯轨迹策略梯度不需要把单个观测假设为 Markov 状态，也不保证非凸优化找到策略类的全局最优。观测条件价值可以定义，困难在于仅以观测作状态的一步 Bellman/bootstrap 通常不再正确。下面两种方法补的是充分状态表示。



## Part 5：部分可观测与序列状态


### 公式 21 · Slide 48：学一个 Markov 的状态空间（state space model） {#formula-21}

> **这条公式的任务：** 说明学习隐状态所需的信息与假设。

用序列编码器读取交互历史，得到隐状态：

$$q_\phi(z_t\mid o_{1:t},a_{1:t-1}),\qquad p(z_{t+1}\mid z_t,a_t)$$

编码器希望保留预测或决策所需的信息，隐空间转移希望具备 Markov 结构。完整历史通常包括过去动作；若动作信息可从其他输入恢复，可用相应简化。

原笔记的 $\prod_tq_\phi(z_t\mid o_{1:t})$ 是一种因子化近似/建模选择，不能把过滤边缘概率的乘积自动当成一般联合后验。学到一个固定长度向量，也不自动证明它保留了所有决策信息。

**代价：** 预测环境可能很难，预测得准也未必保证任务决策最好；若隐表示丢失关键历史，价值递归仍会出错。


### 公式 22 · Slide 49：直接用历史当状态（history states） {#formula-22}

> **这条公式的任务：** 用完整交互历史恢复价值递归的状态接口。

最直接的充分状态是完整交互历史，沿用原笔记的 $s_t$ 来打包：

$$s_t=(o_1,a_1,o_2,a_2,\ldots,a_{t-1},o_t)$$

在标准受控过程里，给定这份历史与当前动作，下一观测的条件分布不再需要更早的遗漏信息。过去历史是当前历史的前缀。

仅写 $(o_1,\ldots,o_t)$ 一般不够：过去动作会影响隐藏状态，又未必能从观测恢复。保留动作历史或等价充分信息，才可在这个状态上构造价值递归。

**经验 Bellman 目标：**

$$y_t=r_t+\gamma\max_{a'}Q(o_1,a_1,\ldots,o_t,a_t,o_{t+1},a')$$

这是一个样本目标，真 Bellman 关系仍对下一观测取条件期望。on-policy 评估则用当前策略对下一动作平均，不使用 max。

**序列模型的作用：** RNN/Transformer 读取变长历史，策略与 critic 据此输出动作/价值。有限窗口或压缩隐藏向量只是近似表示；若任务需要更久以前的信息，窗口与模型容量要足够。

这把本讲接成闭环：自回归语言模型读 prefix，交互策略读观测—动作历史，二者都用序列概率结构表达决策，但不能说任意序列模型天然解决所有 POMDP。


## 三个值得单独复原的步骤

### log Z 为什么变成期望 {#partition-detail}

合上公式 3，写出：log 求导 → 配分积分求导 → 指数链式法则 → 认出 $p(\tau)e^{r_\psi}/Z$ 是归一化密度 → 按定义写成期望。若跳过识别密度，就只是在背最后的两个期望。

### 固定参考 KL 与旧批次 PPO 怎样同时存在 {#reference-detail}

参考项比较整个动作分布；PPO 比值比较同一个已采动作的新旧概率。$\bar\pi$ 每批刷新，$\pi_{\mathrm{ref}}$ 长期不动。对整段目标，log 比链式求和的平均是 completion KL；对固定旧批次的内层，则由代理目标近似执行。

还要看奖励对参数的依赖：$r-\beta\log(\pi_\theta/\pi_{\mathrm{ref}})$ 含 $\theta$。在正规 on-policy 整段期望下，直接微分 log 比产生的额外 score 均值项为零，可以得到相应的加权 score 表达式；固定旧 shaped reward 后的多步 PPO 是另一层局部近似。不能把“停止梯度”当成任意分布下的自动无偏证明。

### 组内均值自项怎么产生缩放 {#group-detail}

用 $K$ 个独立回答展开双重求和。交叉项的 score 与别的回答奖励独立，平均为零；对角项包含自己，不为零，因此：

$$\frac1K\sum_j\mathbb E[\nabla_\theta\log\pi_\theta(a_j\mid s)r(s,a_j)]-\frac1{K^2}\sum_j\mathbb E[\nabla_\theta\log\pi_\theta(a_j\mid s)r(s,a_j)]=\left(1-\frac1K\right)\nabla_\theta\mathbb E[r\mid s]$$

这个理想推导针对中心化、不含随机标准差、不含 clip 的情况。加入这些操作后，应分析对应的实际代理目标。GAE 与批均值基线的详细证明接 [Lecture 6](../lecture-06/)。

## 全公式速查 {#formula-index}

| 编号 | 本讲的任务 |
|---|---|
| [1](#formula-1) | 指数奖励与最优性轨迹模型 |
| [2](#formula-2) | 示范最大似然与配分函数 |
| [3](#formula-3) | log Z 求导、识别密度、两个期望之差 |
| [4](#formula-4) | 最大熵策略与采样，说明可实现条件 |
| [5](#formula-5) | 未充分优化策略的自归一化 IS |
| [6](#formula-6) | 同一测度下消去环境因子 |
| [7](#formula-7) | 奖励—策略交替的完整 IRL 循环 |
| [8](#formula-8) | GAN 的判别与生成目标 |
| [9](#formula-9) | GAIL 的占用分布模仿 |
| [10](#formula-10) | 结构化密度比判别器与 AIRL 的联系 |
| [11](#formula-11) | completion 单步动作视角 |
| [12](#formula-12) | token 多步视角 |
| [13](#formula-13) | log 连乘梯度与完整动作 IS |
| [14](#formula-14) | 待填三个插口的完整 LLM 更新循环 |
| [15](#formula-15) | 价值 baseline、GAE 与回归目标 |
| [16](#formula-16) | 组内相对优势、标准化与自项偏差 |
| [17](#formula-17) | 固定参考分布 KL 与采样 log 比 |
| [18](#formula-18) | 完整 token PPO、固定本批优势 |
| [19](#formula-19) | Bradley–Terry 偏好概率与奖励差 |
| [20](#formula-20) | 偏好奖励学习与策略训练的外循环 |
| [21](#formula-21) | 学习隐状态，保留充分历史的条件 |
| [22](#formula-22) | 观测—动作完整历史与价值递归 |

## 自测：能否说清对象与改写条件 {#self-check}

1. $p(\tau)$ 与 $p_\theta(\tau)$ 在 IRL 部分分别含什么？
2. log Z 求导后，积分里哪一部分是密度？
3. 自归一化权重为什么一般有有限样本偏差？
4. 显式奖励判别器为什么仍不保证唯一、任意环境可迁移的奖励？
5. completion 比值与 token 比值有什么关系？什么时候是严格换分布？
6. 固定旧概率、固定参考概率、固定奖励模型，分别固定什么？
7. λ = 1 的 GAE 在什么末端条件下退化成 MC？
8. 组均值包含自身会出现哪个缩放？标准差归一后还能直接套用吗？
9. KL 应比较概率分布还是两个标量概率？采样 log 比为何可能为负？
10. 为什么 POMDP 的完整状态要包含过去动作？

<details>
<summary>展开参考答案</summary>

1. $p(\tau)$ 是固定动力学/基测度因子，$p_\theta(\tau)$ 还包含策略各步动作概率；必须在同一动作测度下比较。
2. $p(\tau)e^{r_\psi(\tau)}/Z$ 是归一化轨迹密度，乘上 $\nabla_\psi r_\psi$ 才是该分布下的期望。
3. 它是随机分子与随机分母的比值；并非已知 Z 下的普通 IS 平均。
4. 行为可能由许多等价奖励解释；结构化恢复与迁移依赖模型与环境假设。
5. 完整比值是 token 比值连乘；固定 prompt 与支持条件下可精确换 completion 分布，单 token PPO 是局部代理。
6. 旧概率是本批采样参照；参考概率是长期行为正则；奖励模型在当前策略训练阶段负责固定评价，外循环可再拟合。
7. 真实终止、末端价值为零；截断时一般仍有尾部 bootstrap。
8. 理想独立 on-policy 中心化为 $1-1/K$。随机标准差与 clip 改变估计，不能原样套。
9. KL 比较分布；单个动作 log 比可为负，完整分布平均才非负。
10. 动作影响隐藏状态，又未必从观测可恢复；只存观测会遗漏后续条件分布所需信息。

</details>

## 材料与衔接 {#sources}

主材料为本地《Lecture14 公式逐行拆解》，保留 22 条公式的讲次结构、主要拆解与例子。补齐配分积分转期望、动力学约分的测度、整段与 token IS 的区别，以及组内均值、参考 KL、完整交互历史的条件。

理论核对：[control-as-inference](https://arxiv.org/abs/1805.00909)、[GAIL](https://arxiv.org/abs/1606.03476)、[AIRL](https://arxiv.org/abs/1710.11248)、[InstructGPT](https://arxiv.org/abs/2203.02155)、[DeepSeekMath/GRPO](https://arxiv.org/abs/2402.03300)。

往前连接：[Lecture 5 策略梯度](../lecture-05/)、[Lecture 6 价值与 GAE](../lecture-06/)、[Lecture 9 PPO-Clip](../lecture-09/)、[Lecture 10 KL 与信赖域](../lecture-10/)。这一讲说明同一批工具如何服务于奖励学习和序列决策。
