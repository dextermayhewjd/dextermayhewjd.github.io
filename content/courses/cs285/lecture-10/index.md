---
title: "Lecture 10 · 从策略改进界到 PPO-KL 与 TRPO"
description: "解释旧优势与旧状态分布的依据，逐步走过望远镜求和、耦合、TV、Pinsker、KL 惩罚和自然梯度。完整循环集中成框，保留 20 条公式拆解。"
date: 2026-10-07
weight: 100
math: true
ShowToc: false
tags: [CS285, Trust Region, PPO, TRPO, Natural Gradient]
---

## 先看清这一讲在做什么 {#lecture-thread}

**Lecture 9 让一批样本能更新多次；Lecture 10 解释，这种更新为什么要限制策略变化。** 上一讲的代理目标使用旧策略的优势和旧策略访问的状态。本讲分别给它们找依据，再把“别改太多”写成可执行的优化问题。

先把上一讲的完整循环放在一个框里，旁边集中列出全部编号公式。接着沿主线拆开：**新旧回报之差 → 望远镜求和得到旧优势 → 动作重要性采样 → 旧状态代理目标 → 耦合与状态分布界 → 回报差的下界 → KL 约束。**

到 KL 约束处，图分成两条路线：**PPO-KL 用自适应罚项配合多次梯度更新；TRPO 用线性目标、二阶 KL、自然梯度方向和线搜索。** 两条路线的完整算法也各放在一个框里。数学依据逐步拆，算法循环整体看。

{{< lecture-mindmap id="trust-region-flow" cards="argument-cards.json" width="1660" caption="先完整看旧批次复用的循环，再分别解释旧优势与旧状态分布。经过耦合、TV 与回报误差界，用 Pinsker 接到 KL。随后真正分叉：KL 惩罚 → PPO-KL 完整循环；线性目标与 Fisher 几何 → CG 与线搜索 → TRPO 完整循环。完整算法的编号公式集中在一个框旁，其他推导公式尽量单行；点击进入正文。" >}}

### 先用一段话接起来

旧优势不只是拿来冒充新优势。性能差异恒等式直接把“新策略比旧策略好多少”，表示为新轨迹上旧优势的折扣累加。动作期望可用 IS 换成旧动作采样，**此时新状态分布仍然留着**。

把新状态分布换成旧状态分布才产生局部代理目标。新旧策略若在每个状态都接近，可以构造一种动作尽量一致的耦合；轨迹此前至少分歧一次的概率控制状态 TV 距离，再控制期望与回报差。由此得到的是**代理目标减误差项的下界**。

Pinsker 让 KL 控制 TV。实现时从逐状态上限改为旧状态平均，又是一层工程近似。之后既可以用 KL 惩罚调整多次更新的激励，也可以把目标线性化、KL 二阶展开，解出自然梯度方向，再由真实经验目标与 KL 检查候选步长。

| 当前卡点 | 阅读位置 |
|---|---|
| 上一讲完整算法究竟在哪两处近似 | [起始循环](#starting-loop) → [公式 1](#formula-1) |
| 新轨迹上为什么可以用旧优势 | [公式 3](#formula-3) |
| 动作换分布后，还欠哪个分布 | [公式 4](#formula-4) → [公式 5](#formula-5) |
| 分布接近怎样变成回报误差界 | [公式 6–8](#formula-6) → [耦合精读](#coupling-detail) |
| TV 与 KL 怎样接起来 | [公式 10](#formula-10) → [Pinsker 完整证明](#pinsker-detail) |
| KL 怎样变成可以训练的罚项 | [公式 11–14](#formula-11) |
| Fisher 为什么出现、步长如何算 | [公式 18–19](#formula-18) → [自然梯度精读](#natural-detail) |
| 公式怎样变成能跑的 TRPO | [公式 20](#formula-20) → [工程精读](#trpo-detail) |

<details>
<summary>展开全页目录与公式索引</summary>

{{< chapter-outline id="lecture10-outline" title="Lecture 10 阅读位置" >}}

</details>

## 符号与分析范围 {#notation}

本页保留本地《Lecture10 公式逐行拆解》的 **20 个公式编号**，并整合耦合、TV/KL、Jensen、Pinsker 与自然梯度/TRPO 的配套精读。Slide 编号沿用原笔记，不推断课件年份。

| 符号 | 含义 |
|---|---|
| $\theta,\theta'$ | 采集本批数据的旧参数、正在优化的新参数 |
| $\pi_\theta(a\mid s)$ | 给定状态后的动作分布 |
| $p_\theta(s_t)$ | 旧策略在第 $t$ 步的状态分布 |
| $p_\theta(s)$ | 实现路线中，将各时刻旧状态按折扣权重混合后的训练分布 |
| $J(\theta)$ | 从同一初始分布出发的期望折扣总回报 |
| $V^{\pi_\theta},A^{\pi_\theta}$ | 旧策略真实的价值、优势；$\hat V_\phi,\hat A_t^{(i)}$ 是估计 |
| $\bar A(\theta')$ | 本讲已有的代理改进量：旧状态分布、新动作分布、旧优势 |
| $H,N,K$ | 时域长度、轨迹条数、同批数据的内层更新次数 |
| $\gamma,\lambda,\delta_t$ | 折扣、GAE 参数、TD 残差 |
| $\epsilon$ | 当前段落中的距离预算；TV 半径与 KL 半径的单位和数值关系要分别读 |
| $C$ | 优势绝对值的统一上界；公式 8 明确给出 |
| $\beta,\mathcal L_{\mathrm{KL}}$ | 非负 KL 惩罚系数、KL 惩罚目标 |
| $\mathbf F$ | 固定旧状态训练分布下，策略的 Fisher 信息矩阵 |
| $\Delta=\theta'-\theta$ | 参数位移；沿用配套精读的写法 |
| $x,v$ | CG 要解出的搜索方向、Hessian-vector product 的输入向量 |

**时间与折扣统一。** 采用 $t=0,\ldots,H-1$、终端 $V^{\pi_\theta}(s_H)=0$。有限时域的时刻包含在状态里。保留外层 $\gamma^t$，因此无折扣特例直接取 $\gamma=1$，不用猜某一步是否把折扣“吸收”了。无限时域版本需要 $0\lt\gamma\lt1$、有界价值等条件，使尾项消失。

**概率与求导条件。** 新旧策略共享初始分布、环境转移与奖励；IS 需要旧动作分布覆盖新动作分布。默认满足交换求导与积分、概率归一化求导等正则条件。

**KL 方向统一。** 本页使用旧策略在前的 $D_{\mathrm{KL}}(\pi_\theta\Vert\pi_{\theta'})$。TV 对称，但 KL 不对称；两个方向在相等处具有相同的局部二阶 Fisher 形式，不代表离开该点后相等。

## 起点：上一讲完整的样本复用循环 {#starting-loop}

这一组集中看，细节可回到 [Lecture 9 的公式 10b](../lecture-09/#formula-10b)：

$$\begin{aligned}
&1.\ \text{采样：}\quad\tau^{(i)}\sim p_\theta(\tau),\quad\text{保存旧动作概率}\\
&2.\ \text{目标：}\quad y_t^{(i)}=r(s_t^{(i)},a_t^{(i)})+\gamma\hat V_\phi(s_{t+1}^{(i)})\\
&3.\ \text{拟合：}\quad\min_\phi\frac1N\sum_{i,t}\left(\hat V_\phi(s_t^{(i)})-y_t^{(i)}\right)^2\\
&4.\ \text{优势：}\quad\delta_t^{(i)}=r(s_t^{(i)},a_t^{(i)})+\gamma\hat V_\phi(s_{t+1}^{(i)})-\hat V_\phi(s_t^{(i)}),\quad\hat A_t^{(i)}=\sum_{t'=t}^{H-1}(\gamma\lambda)^{t'-t}\delta_{t'}^{(i)}\\
&5.\ \text{初始化：}\quad\theta'\leftarrow\theta\\
&6.\ \text{目标：}\quad\frac1N\sum_{i,t}\gamma^t\frac{\pi_{\theta'}(a_t^{(i)}\mid s_t^{(i)})}{\pi_\theta(a_t^{(i)}\mid s_t^{(i)})}\hat A_t^{(i)}\\
&7.\ \text{更新：}\quad\theta'\leftarrow\theta'+\alpha\nabla_{\theta'}\left[\frac1N\sum_{i,t}\gamma^t\frac{\pi_{\theta'}(a_t^{(i)}\mid s_t^{(i)})}{\pi_\theta(a_t^{(i)}\mid s_t^{(i)})}\hat A_t^{(i)}\right]\quad(6\text{–}7\text{ 重复 }K\text{ 次})\\
&8.\ \text{刷新：}\quad\theta\leftarrow\theta'\quad\Longrightarrow\quad\text{回到 1}
\end{aligned}$$

内层固定样本、旧动作概率与优势，只重算新策略概率。**本讲盯住第 6 步：旧状态和旧优势组成的目标，在什么条件下能代表真实改进量？** critic 目标停止梯度；真实终止后价值为零，rollout 截断仍按任务语义处理 bootstrap。

## Part 1：辨认两个近似，与策略迭代接起来

### 公式 1 · Slide 3：旧状态与旧优势，究竟替换了什么 {#formula-1}

> **任务：** 分开“新策略的精确梯度”和“用旧数据构造的改进目标”。

精确的折扣策略梯度，可在新策略状态—动作分布下写为：

$$\nabla_{\theta'}J(\theta')=\sum_{t=0}^{H-1}\gamma^t\mathbb E_{(s_t,a_t)\sim p_{\theta'}}[\nabla_{\theta'}\log\pi_{\theta'}(a_t\mid s_t)A^{\pi_{\theta'}}(s_t,a_t)]$$

换成旧状态—动作采样，要有两个比值：

$$\nabla_{\theta'}J(\theta')=\sum_{t=0}^{H-1}\gamma^t\mathbb E_{(s_t,a_t)\sim p_\theta}\left[\frac{p_{\theta'}(s_t)}{p_\theta(s_t)}\frac{\pi_{\theta'}(a_t\mid s_t)}{\pi_\theta(a_t\mid s_t)}\nabla_{\theta'}\log\pi_{\theta'}(a_t\mid s_t)A^{\pi_{\theta'}}(s_t,a_t)\right]$$

状态比值写 $p(s_t)$；动作概率写 $\pi(a_t\mid s_t)$。与 Lecture 9 一样，轨迹前缀连乘要经过条件平均，才接到状态边缘比值。

| 实际目标采用什么 | 精确梯度里原本是什么 | 本讲怎样解释 |
|---|---|---|
| 旧优势 $A^{\pi_\theta}$ | 新优势 $A^{\pi_{\theta'}}$ | 改用性能差异恒等式，直接表达回报改变量 |
| 旧状态 $p_\theta(s_t)$ | 新状态 $p_{\theta'}(s_t)$ | 用耦合控制状态偏移，并为替代误差给界 |

不能直接声称“旧优势等于新优势”。本讲会先换一个数学问题：研究 $J(\theta')-J(\theta)$，而不是在任意新参数处把旧优势塞进精确梯度。

### 公式 2 · Slide 6：策略梯度与策略迭代的共同骨架 {#formula-2}

> **任务：** 把“评估当前策略，再改进策略”的结构认出来。

$$\nabla_\theta J(\theta)\approx\frac1N\sum_{i=1}^N\sum_{t=0}^{H-1}\gamma^t\nabla_\theta\log\pi_\theta(a_t^{(i)}\mid s_t^{(i)})\hat A_t^{(i)}$$

策略梯度先估计当前策略的优势，再用优势加权梯度更新参数。经典策略迭代先评估价值/优势，再在每个状态选改善的动作；精确贪心改进可写为：

$$\pi'(s)\in\arg\max_a A^\pi(s,a)$$

两者共享评估—改进的结构，但有限步的参数更新、近似 critic 和函数类约束会带来差别。下面的恒等式把这个联系写成明确的回报差。

## Part 2：旧优势从哪里合法地出现

### 公式 3 · Slide 7：性能差异恒等式，逐行望远镜求和 {#formula-3}

> **任务：** 把新旧回报之差变成新轨迹上的旧优势和。

$$J(\theta')-J(\theta)=\mathbb E_{\tau\sim p_{\theta'}}\left[\sum_{t=0}^{H-1}\gamma^t A^{\pi_\theta}(s_t,a_t)\right]$$

**第 1 步：旧回报写成初始状态价值。**

$$J(\theta)=\mathbb E_{s_0\sim p(s_0)}[V^{\pi_\theta}(s_0)]$$

**第 2 步：统一到新轨迹分布。** 初始状态分布与策略无关，所以：

$$J(\theta')-J(\theta)=J(\theta')-\mathbb E_{\tau\sim p_{\theta'}}[V^{\pi_\theta}(s_0)]$$

这一步只把一个依赖 $s_0$ 的量放进整条轨迹期望，没把旧策略价值换成新策略价值。

**第 3 步：插入可以望远镜抵消的差。** 在单条轨迹上：

$$\sum_{t=0}^{H-1}\gamma^t\big(\gamma V^{\pi_\theta}(s_{t+1})-V^{\pi_\theta}(s_t)\big)=-V^{\pi_\theta}(s_0)+\gamma^H V^{\pi_\theta}(s_H)$$

最后一项为零。展开前三项就能看见相消：

$$\gamma V(s_1)-V(s_0)+\gamma^2V(s_2)-\gamma V(s_1)+\gamma^3V(s_3)-\gamma^2V(s_2)+\cdots$$

**第 4 步：把新回报也放到同一新轨迹期望里，合并。**

$$J(\theta')-J(\theta)=\mathbb E_{\tau\sim p_{\theta'}}\left[\sum_{t=0}^{H-1}\gamma^t\big(r(s_t,a_t)+\gamma V^{\pi_\theta}(s_{t+1})-V^{\pi_\theta}(s_t)\big)\right]$$

**第 5 步：先对下一状态条件平均，才认出优势。**

$$A^{\pi_\theta}(s_t,a_t)=r(s_t,a_t)+\gamma\mathbb E_{s_{t+1}\sim p(\cdot\mid s_t,a_t)}[V^{\pi_\theta}(s_{t+1})]-V^{\pi_\theta}(s_t)$$

这是 Bellman 关系 $A=Q-V$。单条样本里的 $r+\gamma V(s_{t+1})-V(s_t)$ 是 TD 型量；它的条件期望才等于真实优势。用全期望公式代回，得到开头的性能差异恒等式。

**看清搭配：** 轨迹来自新策略，优势评价来自旧策略。旧优势的出现由恒等式保证；并不要求旧优势和新优势相等。[TRPO 原论文](https://proceedings.mlr.press/v37/schulman15.pdf) 以这个性能差异关系构造局部目标。

### 公式 4 · Slide 8：只对内层动作期望换分布 {#formula-4}

> **任务：** 把新动作平均换成旧动作采样，同时保留新状态分布。

先按时刻分开，再使用条件期望：

$$J(\theta')-J(\theta)=\sum_{t=0}^{H-1}\gamma^t\mathbb E_{s_t\sim p_{\theta'}}\left[\mathbb E_{a_t\sim\pi_{\theta'}(\cdot\mid s_t)}[A^{\pi_\theta}(s_t,a_t)]\right]$$

固定 $s_t$，将动作期望按定义展开成积分：

$$\mathbb E_{a_t\sim\pi_{\theta'}}[A^{\pi_\theta}(s_t,a_t)]=\int\pi_{\theta'}(a_t\mid s_t)A^{\pi_\theta}(s_t,a_t)\,da_t$$

插入旧动作密度与比值：

$$\int\pi_{\theta'}(a_t\mid s_t)A^{\pi_\theta}(s_t,a_t)\,da_t=\int\pi_\theta(a_t\mid s_t)\frac{\pi_{\theta'}(a_t\mid s_t)}{\pi_\theta(a_t\mid s_t)}A^{\pi_\theta}(s_t,a_t)\,da_t$$

**先识别结构，再写回期望：**

$$\int\underbrace{\pi_\theta(a_t\mid s_t)}_{\text{旧动作密度}}\underbrace{\left[\frac{\pi_{\theta'}(a_t\mid s_t)}{\pi_\theta(a_t\mid s_t)}A^{\pi_\theta}(s_t,a_t)\right]}_{\text{被平均的量}}\,da_t$$

因此：

$$J(\theta')-J(\theta)=\sum_{t=0}^{H-1}\gamma^t\mathbb E_{s_t\sim p_{\theta'}}\left[\mathbb E_{a_t\sim\pi_\theta}\left[\frac{\pi_{\theta'}(a_t\mid s_t)}{\pi_\theta(a_t\mid s_t)}A^{\pi_\theta}(s_t,a_t)\right]\right]$$

离散动作把积分换成求和。支持条件是新策略可能选择的动作，旧策略也能采到。**现在动作与优势都能由旧批次提供，状态仍来自新策略**，所以尚不能直接把整个外层期望换成旧样本平均。

## Part 3：状态替换带来多少误差

### 公式 5 · Slide 10：明确把近似定义成代理改进量 {#formula-5}

> **任务：** 把替换状态分布的那一步单独标出来。

$$\bar A(\theta')=\sum_{t=0}^{H-1}\gamma^t\mathbb E_{s_t\sim p_\theta}\left[\mathbb E_{a_t\sim\pi_\theta}\left[\frac{\pi_{\theta'}(a_t\mid s_t)}{\pi_\theta(a_t\mid s_t)}A^{\pi_\theta}(s_t,a_t)\right]\right]$$

和公式 4 对照：只把外层 $p_{\theta'}(s_t)$ 改成 $p_\theta(s_t)$。新动作概率仍保留在分子中，优化变量仍是 $\theta'$。

$$J(\theta')-J(\theta)\approx\bar A(\theta')$$

在 $\theta'=\theta$ 处，旧策略对自身优势的平均为零，因此 $\bar A(\theta)=0$；使用真实优势时，其梯度也与真实回报梯度匹配。**起点的一阶匹配不能推出离开起点后仍相等。**

下一步要定量回答这个近似会差多少。原笔记中“只要策略接近，状态也接近”的结论，需要逐状态的控制与时间累积。

### 公式 6 · Slide 11：确定性旧策略，先看分歧事件 {#formula-6}

> **任务：** 把状态差转成“此前是否至少分歧一次”。

旧策略确定性时，假设每个状态都有：

$$\pi_{\theta'}(a_t\ne\pi_\theta(s_t)\mid s_t)\le\epsilon$$

让两条轨迹共用初始状态，在相同状态、相同动作时共用环境随机性。到状态 $s_t$ 之前，发生过 $t$ 次动作决策。

$$\Pr(\text{此前一次都未分歧})\ge(1-\epsilon)^t,\qquad\Pr(\text{此前至少分歧一次})\le1-(1-\epsilon)^t\le t\epsilon$$

最后一项可由 Bernoulli 不等式或逐步 union bound 得到；不需要假定独立，每步使用的是尚未分歧条件下的概率上界。

**这里不能直接写原笔记的固定混合等式。** 单步误差依赖状态时，“没有分歧”会对访问路径进行筛选；其条件状态分布不必恰好等于完整旧分布。因此不能一般地断言：

$$p_{\theta'}(s_t)=(1-\epsilon)^t p_\theta(s_t)+\big(1-(1-\epsilon)^t\big)p_{\mathrm{mistake}}(s_t)$$

上式只在额外结构条件下成立。本页实际使用共同轨迹构造：未分歧时状态相同，从而控制两个状态边缘的 TV。下一条把这个构造推广到随机策略。

### 公式 7 · Slide 12：随机策略用最大耦合接上同一证明 {#formula-7}

> **任务：** 将“两张动作概率表差多少”变成可控制的分歧概率。

假设对每个状态：

$$D_{\mathrm{TV}}(\pi_\theta(\cdot\mid s),\pi_{\theta'}(\cdot\mid s))=\frac12\sum_a|\pi_\theta(a\mid s)-\pi_{\theta'}(a\mid s)|\le\epsilon$$

**最大耦合引理：** 可为 $X\sim p,Y\sim q$ 构造一种联合抽样，保持各自边缘分布，并满足：

$$\Pr(X\ne Y)=D_{\mathrm{TV}}(p,q),\qquad\Pr(X=Y)=1-D_{\mathrm{TV}}(p,q)$$

这说的是存在一种最佳配对方式，不是独立抽样就能做到。具体构造见 [耦合精读](#coupling-detail)。

在两条轨迹还位于同一状态时，对动作使用最大耦合；动作相同，则共用同一环境转移随机源。两条轨迹各自仍精确服从自身策略分布。于是：

$$D_{\mathrm{TV}}(p_{\theta'}(s_t),p_\theta(s_t))\le\Pr(s_t'\ne s_t)\le\Pr(\text{此前至少分歧一次})\le1-(1-\epsilon)^t\le t\epsilon$$

**每个不等号分别做什么：** 任意耦合的失配概率上界 TV → 状态不同必须此前有过分歧 → 每步最多分歧 $\epsilon$ → 再放松到线性时间界。到 $s_0$ 之前没有动作，所以 $t=0$ 时距离上界为零。

### 公式 8 · Slide 13：从状态 TV 到期望，再到回报差 {#formula-8}

> **任务：** 完整写出原笔记最容易卡住的“差价”推导。

先对一个有界、可正可负的函数 $f(s_t)$：

$$\mathbb E_{p_{\theta'}}[f]-\mathbb E_{p_\theta}[f]=\sum_{s_t}\big(p_{\theta'}(s_t)-p_\theta(s_t)\big)f(s_t)$$

取绝对值，用三角不等式：

$$\left|\mathbb E_{p_{\theta'}}[f]-\mathbb E_{p_\theta}[f]\right|\le\sum_{s_t}|p_{\theta'}(s_t)-p_\theta(s_t)|\,|f(s_t)|$$

把函数绝对值的最大值提出来：

$$\left|\mathbb E_{p_{\theta'}}[f]-\mathbb E_{p_\theta}[f]\right|\le2D_{\mathrm{TV}}(p_{\theta'}(s_t),p_\theta(s_t))\max_{s_t}|f(s_t)|$$

这里必须是 **max |f|**；仅写 max f，在函数有负值时不够。代入公式 7：

$$\mathbb E_{p_{\theta'}}[f]\ge\mathbb E_{p_\theta}[f]-2t\epsilon\max_{s_t}|f(s_t)|$$

现在才指定要比较的函数：

$$f(s_t)=\mathbb E_{a_t\sim\pi_{\theta'}}[A^{\pi_\theta}(s_t,a_t)]=\mathbb E_{a_t\sim\pi_\theta}\left[\frac{\pi_{\theta'}(a_t\mid s_t)}{\pi_\theta(a_t\mid s_t)}A^{\pi_\theta}(s_t,a_t)\right]$$

取一个不随候选新策略变化的统一上界：

$$C=\max_{s,a}|A^{\pi_\theta}(s,a)|,\qquad|f(s_t)|\le C$$

最后乘 $\gamma^t$ 并对时间相加：

$$J(\theta')-J(\theta)\ge\bar A(\theta')-2C\epsilon\sum_{t=0}^{H-1}t\gamma^t$$

**无折扣时可以算到底：**

$$\sum_{t=0}^{H-1}t=\frac{H(H-1)}2,\qquad J(\theta')-J(\theta)\ge\bar A(\theta')-C\epsilon H(H-1)$$

无限折扣时：

$$\sum_{t=0}^\infty t\gamma^t=\frac{\gamma}{(1-\gamma)^2}$$

**真正的下界是代理量减误差项，不是裸的 $\bar A$。** 如果候选策略的代理提升大于这个差价，才能从这个界推出真实改进为正。只提高代理目标一点点，并不自动满足这个条件。

使用旧优势均值为零还可得到二阶策略距离界，见 [更紧的误差界](#sharper-bound)。主图先保留本讲逐时刻分布证明的基本版本。

### 公式 9 · Slide 14：把“别改太多”写成约束 {#formula-9}

> **任务：** 将定量条件接回优化问题。

$$\max_{\theta'}\bar A(\theta')\qquad\text{s.t.}\quad D_{\mathrm{TV}}(\pi_\theta(\cdot\mid s),\pi_{\theta'}(\cdot\mid s))\le\epsilon\quad\forall s$$

**逐符号拆：** 最大化旧数据可估的代理改进量；同时在所有相关状态限制动作分布变化；小预算让状态替换的误差项受控。

理论界使用所有状态的控制。只在有限旧样本上检查平均距离，并不自动覆盖旧策略极少访问的新状态。后面落地会明确标出这个变化。

## Part 4：把约束变成 KL 罚项，形成 PPO-KL

### 公式 10 · Slide 17：Pinsker 把 TV 约束接到 KL {#formula-10}

> **任务：** 给好解释的 TV 找一个便于梯度优化的充分条件。

自然对数约定下：

$$D_{\mathrm{TV}}(p,q)\le\sqrt{\frac12D_{\mathrm{KL}}(p\Vert q)}$$

所以要保证 TV 半径为 $\epsilon$，一个充分条件是：

$$D_{\mathrm{KL}}(p\Vert q)\le2\epsilon^2\quad\Longrightarrow\quad D_{\mathrm{TV}}(p,q)\le\epsilon$$

**两者不能用同一个数值直接互换。** 从下面 KL 优化段落起，$\epsilon$ 表示 KL 预算；此前的 TV 预算要按平方关系转换。

对所有状态控制 KL，可推出：

$$D_{\mathrm{KL}}(\pi_\theta(\cdot\mid s)\Vert\pi_{\theta'}(\cdot\mid s))\le\epsilon\quad\forall s\quad\Longrightarrow\quad D_{\mathrm{TV}}(p_{\theta'}(s_t),p_\theta(s_t))\le t\sqrt{\epsilon/2}$$

TV 在相等处分段不可微，KL 在正概率与常规参数化条件下更便于求导与二阶展开。TV 也可用次梯度等方法处理，不是数学上绝对不可优化。

**二选一数字例。** 旧策略 $(0.5,0.5)$、新策略 $(0.6,0.4)$：

$$D_{\mathrm{TV}}=0.1,\qquad D_{\mathrm{KL}}=0.5\log(0.5/0.6)+0.5\log(0.5/0.4)\approx0.020411$$

$$\sqrt{D_{\mathrm{KL}}/2}\approx0.101023\ge0.1$$

这个接近五五开的例子很紧，但不能推出所有相近分布的 Pinsker 都几乎取等；偏斜分布的局部常数也可能松。完整推导见 [Pinsker 精读](#pinsker-detail)。

#### 从理论逐状态上限到实践旧状态平均 {#average-kl}

理论条件是每个状态的上限；训练通常使用旧状态分布上的平均：

$$\mathbb E_{s\sim p_\theta(s)}[D_{\mathrm{KL}}(\pi_\theta(\cdot\mid s)\Vert\pi_{\theta'}(\cdot\mid s))]\le\epsilon$$

其中旧状态训练分布按折扣混合：

$$p_\theta(s)=\frac{\sum_{t=0}^{H-1}\gamma^t p_\theta(s_t=s)}{\sum_{t=0}^{H-1}\gamma^t}$$

**这是工程近似。** 平均小允许少量状态的 KL 大，不能直接代回前面的逐状态耦合保证。[TRPO 原论文](https://proceedings.mlr.press/v37/schulman15.pdf) 也将最大 KL 改为平均 KL，明确区分理论方案与实际算法。

### 公式 11 · Slide 18：KL 的样本形式与最大似然 {#formula-11}

> **任务：** 展开 KL，找出哪些项随新参数变化。

固定状态时：

$$D_{\mathrm{KL}}(\pi_\theta\Vert\pi_{\theta'})=\mathbb E_{a\sim\pi_\theta(\cdot\mid s)}[\log\pi_\theta(a\mid s)-\log\pi_{\theta'}(a\mid s)]$$

旧参数与样本固定，第一项不含 $\theta'$。因此对新参数而言，最小化 KL 等价于最大化旧分布下的新策略 log 似然：

$$\arg\min_{\theta'}D_{\mathrm{KL}}(\pi_\theta\Vert\pi_{\theta'})=\arg\max_{\theta'}\mathbb E_{a\sim\pi_\theta}[\log\pi_{\theta'}(a\mid s)]$$

对多个旧状态平均后，同样成立。旧批次的折扣加权平均 KL 估计为：

$$\mathbb E_{s\sim p_\theta}[D_{\mathrm{KL}}(\pi_\theta\Vert\pi_{\theta'})]\approx\frac{\sum_{i=1}^N\sum_{t=0}^{H-1}\gamma^t[\log\pi_\theta(a_t^{(i)}\mid s_t^{(i)})-\log\pi_{\theta'}(a_t^{(i)}\mid s_t^{(i)})]}{N\sum_{t=0}^{H-1}\gamma^t}$$

**三件事分别读：** 从 KL 定义到期望是等式；期望到有限样本平均是估计；去掉旧 log 概率常数是对固定 $\beta$、固定数据的 actor 优化化简。有限样本的 log 比平均可能为负，尽管总体 KL 非负。

旧 $(0.5,0.3,0.2)$、新 $(0.4,0.4,0.2)$ 的单状态例子：

$$D_{\mathrm{KL}}\approx0.025267,\qquad\mathbb E_{\pi_\theta}[\log\pi_\theta]\approx-1.029653,\qquad\mathbb E_{\pi_\theta}[\log\pi_{\theta'}]\approx-1.054920$$

两项之差正好是 KL。优化梯度时可以省掉旧项；**更新 $\beta$ 和检查距离时仍要计算 KL**，不能说整个算法都不需要知道它。

### 公式 12 · Slide 20：拉格朗日与非负乘子更新 {#formula-12}

> **任务：** 把平均 KL 预算变成一个可以交替优化的目标。

$$\mathcal L(\theta',\beta)=\bar A(\theta')-\beta\left(\mathbb E_{s\sim p_\theta}[D_{\mathrm{KL}}(\pi_\theta\Vert\pi_{\theta'})]-\epsilon\right),\qquad\beta\ge0$$

固定 $\beta$，对 $\theta'$ 做梯度上升；对乘子做投影对偶下降：

$$\theta'\leftarrow\theta'+\alpha\nabla_{\theta'}\mathcal L(\theta',\beta)$$

$$\beta\leftarrow\max\left\{0,\ \beta+\alpha\left(\mathbb E_{s\sim p_\theta}[D_{\mathrm{KL}}(\pi_\theta\Vert\pi_{\theta'})]-\epsilon\right)\right\}$$

**为什么符号是加号：** $\partial\mathcal L/\partial\beta=-(\mathrm{KL}-\epsilon)$，对 $\beta$ 下降就加上约束超标量。KL 超标，罚重一点；KL 低于目标，罚轻一点。外面的 max 保证乘子不变成负数，否则会奖励距离变大。

这里沿用原笔记的 $\alpha$ 表示更新步长；实现可为 actor 与乘子分别选步长。神经网络问题非凸、样本有误差、内层未必充分优化，这个更新并不保证每轮精确满足 KL 约束。

### 公式 13 · Slide 21：样本目标的两块，保留归一化 {#formula-13}

> **任务：** 分别写出代理提升与平均 KL 惩罚，避免把平均与时间总和混用。

忽略固定 $\beta$ 下对 $\theta'$ 无关的加性常数，可写：

$$\mathcal L(\theta',\beta)\approx\frac1N\sum_{i,t}\gamma^t\frac{\pi_{\theta'}(a_t^{(i)}\mid s_t^{(i)})}{\pi_\theta(a_t^{(i)}\mid s_t^{(i)})}\hat A_t^{(i)}+\frac{\beta}{N\sum_{t=0}^{H-1}\gamma^t}\sum_{i,t}\gamma^t\log\pi_{\theta'}(a_t^{(i)}\mid s_t^{(i)})+\text{const}$$

第一块提高有正优势动作的概率；第二块鼓励保留旧策略曾选择动作的概率。因为本页 $\bar A$ 是总回报改变量，KL 是状态平均，两个部分的归一化分别保留；若把二者都改成时间步平均，应同时调整系数，不能只删某一个除数。

**const 的范围：** $\beta\epsilon$ 和旧 log 概率项对 actor 是常数，但对 $\beta$ 并非常数。乘子更新使用公式 12 的完整约束量。

### 公式 14 · Slide 22：PPO-KL 的完整循环 {#formula-14}

> **任务：** 把上面的目标与乘子更新装入一组算法，整组对照起始循环。

定义当前批次的 KL 惩罚目标：

$$\mathcal L_{\mathrm{KL}}(\theta',\beta)=\frac1N\sum_{i,t}\gamma^t\frac{\pi_{\theta'}(a_t^{(i)}\mid s_t^{(i)})}{\pi_\theta(a_t^{(i)}\mid s_t^{(i)})}\hat A_t^{(i)}-\beta\,\mathbb E_{s\sim p_\theta}[D_{\mathrm{KL}}(\pi_\theta\Vert\pi_{\theta'})]$$

完整步骤在图中同一框旁展示；正文集中写成：

$$\begin{aligned}
&1.\ \text{采样：}\quad\tau^{(i)}\sim p_\theta,\quad\text{保存旧动作概率}\\
&2.\ \text{目标：}\quad y_t^{(i)}=r(s_t^{(i)},a_t^{(i)})+\gamma\hat V_\phi(s_{t+1}^{(i)})\\
&3.\ \text{拟合：}\quad\min_\phi\frac1N\sum_{i,t}(\hat V_\phi(s_t^{(i)})-y_t^{(i)})^2\\
&4.\ \text{优势：}\quad\delta_t^{(i)}=r(s_t^{(i)},a_t^{(i)})+\gamma\hat V_\phi(s_{t+1}^{(i)})-\hat V_\phi(s_t^{(i)}),\quad\hat A_t^{(i)}=\sum_{t'=t}^{H-1}(\gamma\lambda)^{t'-t}\delta_{t'}^{(i)}\\
&5.\ \text{初始化：}\quad\theta'\leftarrow\theta,\quad\beta\ge0\\
&6.\ \text{策略更新：}\quad\theta'\leftarrow\theta'+\alpha\nabla_{\theta'}\mathcal L_{\mathrm{KL}}(\theta',\beta)\quad(\text{同批更新 }K\text{ 次})\\
&7.\ \text{乘子更新：}\quad\beta\leftarrow\max\{0,\beta+\alpha(\mathbb E_{s\sim p_\theta}[D_{\mathrm{KL}}(\pi_\theta\Vert\pi_{\theta'})]-\epsilon)\}\\
&8.\ \text{刷新：}\quad\theta\leftarrow\theta'\quad\Longrightarrow\quad\text{回到 1}
\end{aligned}$$

第 1–4 步准备数据，第 6 步复用数据，第 7 步调距离惩罚。内层旧分母与优势固定，下一批才更新采样参照。

本讲用投影对偶更新说明惩罚系数的方向。[PPO 原论文](https://arxiv.org/abs/1707.06347) 的 adaptive-KL 变体使用另一种启发式：平均 KL 太低时将 $\beta$ 除以二，太高时乘以二。两种规则都在自适应调罚项，不应当成同一条更新公式。

与 Lecture 9 的 PPO-Clip 相比，这里显式惩罚平均 KL；clip/min 修改的是样本目标的激励，不能被解释为硬限制全部概率比值。二者是相关的实现路线，不是严格相等的目标。

## Part 5：另一条路线——自然梯度与 TRPO

### 公式 15 · Slide 24：目标在旧参数处一阶线性化 {#formula-15}

> **任务：** 把难优化的代理目标变为局部线性函数。

$$\bar A(\theta')=\bar A(\theta)+\left(\left.\nabla_{\theta'}\bar A(\theta')\right|_{\theta'=\theta}\right)^\top(\theta'-\theta)+O(\|\theta'-\theta\|^2)$$

真实旧优势使 $\bar A(\theta)=0$。因此局部问题保留线性项：

$$\max_{\theta'}\left(\left.\nabla_{\theta'}\bar A(\theta')\right|_{\theta'=\theta}\right)^\top(\theta'-\theta)\quad\text{s.t.}\quad\mathbb E_{s\sim p_\theta}[D_{\mathrm{KL}}(\pi_\theta\Vert\pi_{\theta'})]\le\epsilon$$

这个写法明确只对新参数求导，求完再令新旧相等；旧分布与旧优势固定，避免将 $\nabla_\theta\bar A(\theta)$ 误读成同时微分所有旧参数位置。

**从一元回忆：** $f(x)=x^2$ 在 $x=3$，到 $3.1$ 的线性近似为 $9+6(0.1)=9.6$，真实值为 $9.61$。移动扩大到 $1$ 时误差为 $1$，到 $7$ 时误差为 $49$。

多元的一阶项是点积。$f(\theta_1,\theta_2)=\theta_1^2+\theta_2^2$ 在 $(3,4)$，移动 $(0.1,0.2)$，预测改变量为 $6(0.1)+8(0.2)=2.2$，真实改变量为 $2.25$。

若梯度非零而不加范围约束，线性目标沿梯度放大可以无限增长。信赖域使我们只在局部范围内使用近似。

### 公式 16 · Slide 25：这个线性系数就是旧策略梯度 {#formula-16}

> **任务：** 一步步求导，再在旧参数处使比值变成 1。

首先只有分子含 $\theta'$：

$$\nabla_{\theta'}\bar A(\theta')=\sum_t\gamma^t\mathbb E_{p_\theta(s_t),\pi_\theta}\left[\frac{\nabla_{\theta'}\pi_{\theta'}(a_t\mid s_t)}{\pi_\theta(a_t\mid s_t)}A^{\pi_\theta}(s_t,a_t)\right]$$

代入 $\nabla\pi=\pi\nabla\log\pi$：

$$\nabla_{\theta'}\bar A(\theta')=\sum_t\gamma^t\mathbb E_{p_\theta(s_t),\pi_\theta}\left[\frac{\pi_{\theta'}(a_t\mid s_t)}{\pi_\theta(a_t\mid s_t)}\nabla_{\theta'}\log\pi_{\theta'}(a_t\mid s_t)A^{\pi_\theta}(s_t,a_t)\right]$$

然后才代入 $\theta'=\theta$：

$$\left.\nabla_{\theta'}\bar A(\theta')\right|_{\theta'=\theta}=\sum_t\gamma^t\mathbb E_{p_\theta(s_t),\pi_\theta}[\nabla_\theta\log\pi_\theta(a_t\mid s_t)A^{\pi_\theta}(s_t,a_t)]=\nabla_\theta J(\theta)$$

**只在旧点相等。** 使用真实优势是总体等式；实际 GAE 与有限批次还会有估计误差。这一步确定线性目标的系数，后面仍要决定如何按 KL 几何选择方向与长度。

### 公式 17 · Slide 26：欧氏球和 KL 区域不是同一把尺子 {#formula-17}

> **任务：** 解释普通梯度方向为何未必最适合 KL 预算。

令 $\Delta=\theta'-\theta$。欧氏球中的线性最大化问题为：

$$\max_\Delta\nabla_\theta J(\theta)^\top\Delta\quad\text{s.t.}\quad\|\Delta\|^2\le\epsilon$$

非零梯度下，柯西–施瓦茨给出：

$$\nabla_\theta J(\theta)^\top\Delta\le\|\nabla_\theta J(\theta)\|\|\Delta\|\le\|\nabla_\theta J(\theta)\|\sqrt\epsilon$$

两次取等号需要方向平行、长度到边界，因此：

$$\Delta^\star=\sqrt{\frac{\epsilon}{\|\nabla_\theta J(\theta)\|^2}}\nabla_\theta J(\theta)$$

普通固定学习率更新也沿该方向，但长度是 $\alpha\|\nabla J\|$，不是固定半径 $\sqrt\epsilon$。这个对应讨论的是方向和欧氏度量，不能说固定学习率始终解同一个固定半径问题。

**高斯例子看出差别：**

$$D_{\mathrm{KL}}(\mathcal N(\mu,\sigma^2)\Vert\mathcal N(\mu+0.1,\sigma^2))=\frac{0.1^2}{2\sigma^2}$$

| 标准差 | 均值移动 | 欧氏距离 | KL |
|---|---:|---:|---:|
| $\sigma=1$ | 0.1 | 0.1 | 0.005 |
| $\sigma=0.01$ | 0.1 | 0.1 | 50 |

同样的参数移动，策略变化相差一万倍。KL 的局部区域通常是椭球，敏感方向窄、迟钝方向宽；欧氏球无法表达这种差别。

### 公式 18 · Slide 27：KL 的零阶、一阶项为零，二阶项是 Fisher {#formula-18}

> **任务：** 说明为什么目标用一阶，约束却要二阶。

旧状态训练分布固定。在 $\theta'=\theta$：

$$\mathbb E_{s\sim p_\theta}[D_{\mathrm{KL}}(\pi_\theta\Vert\pi_\theta)]=0,\qquad\left.\nabla_{\theta'}\mathbb E_{s\sim p_\theta}[D_{\mathrm{KL}}(\pi_\theta\Vert\pi_{\theta'})]\right|_{\theta'=\theta}=0$$

零阶为零是同一分布的 KL；一阶为零因为它是可微的最小点，也可由 score 均值为零直接计算。

若只保留一阶，约束近似成 $0\le\epsilon$，不给移动任何信息。必须继续到二阶：

$$\mathbb E_{s\sim p_\theta}[D_{\mathrm{KL}}(\pi_\theta\Vert\pi_{\theta'})]\approx\frac12(\theta'-\theta)^\top\mathbf F(\theta'-\theta)$$

$$\mathbf F=\mathbb E_{s\sim p_\theta,\ a\sim\pi_\theta(\cdot\mid s)}[\nabla_\theta\log\pi_\theta(a\mid s)\nabla_\theta\log\pi_\theta(a\mid s)^\top]$$

**逐符号拆：** 每个完整 log 概率梯度是列向量；与自身转置相乘成矩阵；对旧状态和旧动作平均，得到 KL 的局部曲率。状态平均不能省略定义。

任意向量 $v$ 都满足：

$$v^\top\mathbf Fv=\mathbb E[(v^\top\nabla_\theta\log\pi_\theta(a\mid s))^2]\ge0$$

所以 Fisher 对称半正定；不自动严格正定。零特征方向可能让逆不存在，数值求解需处理。KL Hessian 与外积期望为什么相等，完整两次归一化求导见 [Fisher 精读](#fisher-detail)。

### 公式 19 · Slide 28：自然梯度方向与正确的步长 {#formula-19}

> **任务：** 解出线性目标与二次约束，而不只背一个逆矩阵。

先在 $\mathbf F$ 正定、梯度非零的条件下：

$$\max_\Delta\nabla_\theta J(\theta)^\top\Delta\quad\text{s.t.}\quad\frac12\Delta^\top\mathbf F\Delta\le\epsilon$$

解为：

$$\theta'=\theta+\alpha\mathbf F^{-1}\nabla_\theta J(\theta),\qquad\alpha=\sqrt{\frac{2\epsilon}{\nabla_\theta J(\theta)^\top\mathbf F^{-1}\nabla_\theta J(\theta)}}$$

**分母含 $\mathbf F^{-1}$。** 原主笔记的 $\mathbf F$ 已由配套 Slide 28 精读指出错误，本页采用其推导后的正确版本。

为什么它出现？将位移 $\alpha\mathbf F^{-1}\nabla J$ 代回约束：

$$\frac12\alpha^2(\mathbf F^{-1}\nabla J)^\top\mathbf F(\mathbf F^{-1}\nabla J)=\frac12\alpha^2\nabla J^\top\mathbf F^{-1}\nabla J=\epsilon$$

中间那一对 $\mathbf F$ 与逆矩阵约掉，才得到步长。若 $\mathbf F$ 奇异，应使用适当的阻尼/受限空间方法；这个普通逆的闭式公式不能原样照搬。

**沿用配套精读的数字：**

$$\nabla_\theta J=(6,8)^\top,\qquad\mathbf F=\operatorname{diag}(1,100),\qquad\epsilon=0.01$$

$$\mathbf F^{-1}\nabla J=(6,0.08)^\top,\qquad\nabla J^\top\mathbf F^{-1}\nabla J=36.64$$

$$\alpha\approx0.0233635,\qquad\Delta\approx(0.140181,0.00186908)^\top,\qquad\frac12\Delta^\top\mathbf F\Delta=0.01$$

第二个方向对策略更敏感，所以移动被缩小。自然梯度在局部 KL 预算下重新分配各方向的移动。完整拉格朗日推导见 [自然梯度精读](#natural-detail)。

**Slide 29 的高斯控制例子。** 若同时训练 $k$ 和 $\sigma$，不能把 $-\log\sigma$ 扔进“常数”：

$$\log\pi_{(k,\sigma)}(a\mid s)=-\frac{(a-ks)^2}{2\sigma^2}-\log\sigma-\frac12\log(2\pi)$$

在固定旧状态分布下，相关 Fisher 为：

$$\mathbf F=\operatorname{diag}\left(\frac{\mathbb E[s^2]}{\sigma^2},\frac{2}{\sigma^2}\right)$$

若参数是均值 $\mu$，第一项才是 $1/\sigma^2$。该例说明小方差策略对参数变化更敏感，不保证自然梯度在任意任务上消除探索不足。

### 公式 20 · Slide 30：TRPO 的完整循环与线搜索 {#formula-20}

> **任务：** 补齐原主笔记的空算法块：解方向、选步长、检查候选，再采下一批。

#### 整组算法放在一起 {#implementation-loop}

下面 $x$ 沿用配套精读中线性系统的搜索方向记号；经验代理目标采用本批固定优势。

$$\begin{aligned}
&1.\ \text{采样：}\quad\tau^{(i)}\sim p_\theta,\quad\text{保存旧动作概率}\\
&2.\ \text{估优势：}\quad\delta_t^{(i)}=r_t^{(i)}+\gamma\hat V_\phi(s_{t+1}^{(i)})-\hat V_\phi(s_t^{(i)}),\quad\hat A_t^{(i)}=\sum_{t'=t}^{H-1}(\gamma\lambda)^{t'-t}\delta_{t'}^{(i)}\\
&3.\ \text{估梯度：}\quad\nabla_\theta J(\theta)\approx\frac1N\sum_{i,t}\gamma^t\nabla_\theta\log\pi_\theta(a_t^{(i)}\mid s_t^{(i)})\hat A_t^{(i)}\\
&4.\ \text{解方向：}\quad\mathbf Fx=\nabla_\theta J(\theta)\quad(\mathrm{CG},\ \text{实际通常加正的对角阻尼})\\
&5.\ \text{步长：}\quad\alpha=\sqrt{2\epsilon/(x^\top\mathbf Fx)}\\
&6.\ \text{线搜索：}\quad\theta'=\theta+0.5^j\alpha x,\quad j=0,1,\ldots,\quad\text{检查平均 KL 与经验代理改进}\\
&7.\ \text{刷新：}\quad\theta\leftarrow\theta'_{\mathrm{accepted}}\quad\Longrightarrow\quad\text{回到 1}
\end{aligned}$$

第 4–5 步先按理想二次模型写原理式；阻尼实现应按实际求解矩阵一致计算候选尺度，并在第 6 步检查真实经验 KL。如果所有候选都未通过，则保留旧参数。下标 accepted 只是说明选中的候选，并非新增网络。

**为什么不用逆：**

$$x=\mathbf F^{-1}\nabla_\theta J(\theta)\quad\Longleftrightarrow\quad\mathbf Fx=\nabla_\theta J(\theta)$$

CG 只需要矩阵—向量乘积。Fisher 又是旧点 KL 的 Hessian，因此可以用自动微分计算：

$$\mathbf Fv=\left.\nabla_{\theta'}\left[\left(\nabla_{\theta'}\mathbb E_{s\sim p_\theta}[D_{\mathrm{KL}}(\pi_\theta\Vert\pi_{\theta'})]\right)^\top v\right]\right|_{\theta'=\theta}$$

不用存一个参数量平方大小的矩阵。实际代价取决于网络、批次、乘积计算和 CG 轮数，不是保证总求解都只用 $O(n)$ 时间。标准 CG 要正定条件；半正定不够，数值阻尼很常见。

**线搜索为什么保留：** 目标已线性化，KL 已二阶近似，还有样本和 CG 误差。二次模型预算合法，不代表真实经验 KL 一定合法。接受候选时至少检查：

$$\mathbb E_{s\sim p_\theta}[D_{\mathrm{KL}}(\pi_\theta\Vert\pi_{\theta'})]\le\epsilon,\qquad\bar A_{\mathrm{empirical}}(\theta')\gt\bar A_{\mathrm{empirical}}(\theta)$$

这里 empirical 指本批次固定优势构造的代理量。实际实现还可要求足够的预测改进比例。验证的是经验 KL 和代理目标，不是完整真实回报的逐步保证。[Spinning Up 的 TRPO 实现说明](https://spinningup.openai.com/en/latest/algorithms/trpo.html)

## PPO-KL 与 TRPO，放在同一张对照表 {#algorithm-comparison}

| | PPO-KL | TRPO |
|---|---|---|
| 共同起点 | 旧数据代理目标、平均 KL 预算 | 同左 |
| 策略目标 | KL 罚项下的非线性经验目标 | 先以局部线性/二次模型计算候选 |
| 控制距离 | 自适应 $\beta$ 改变更新激励 | 线搜索检查经验 KL |
| 核心计算 | 多次一阶梯度更新 | CG、Hessian-vector product、候选验收 |
| 一批的用法 | 更新多次，再刷新 | 用本批算候选、线搜索、接受一次策略更新 |
| 主要近似 | 状态平均、优势估计、未充分优化 | 状态平均、优势估计、局部模型、截断 CG |

两条路线都在控制局部数据与策略变化的关系。实际优化中的平均约束、有限数据和函数近似，应与前面逐状态的理论证明分开读。

## 数学卡点精读：从耦合到自然梯度

### 精读 1：最大耦合怎样构造，为什么能用于轨迹 {#coupling-detail}

耦合是一个联合分布：同时抽出 $X,Y$，要求单看两边仍分别服从 $p,q$。可以设计相关性，不能改变任一边的概率表。

**先找公共质量。** 沿用原精读的 $m(x)=\min\{p(x),q(x)\}$：

$$|p(x)-q(x)|=p(x)+q(x)-2m(x)$$

求和并除以二：

$$D_{\mathrm{TV}}(p,q)=1-\sum_xm(x)$$

令这里两分布的 TV 恰为 $\epsilon$，则重叠质量为 $1-\epsilon$。当 $0\lt\epsilon\lt1$ 时构造：

- 以 $1-\epsilon$ 的概率，从 $m/(1-\epsilon)$ 抽一个值，令 $X=Y$。
- 以 $\epsilon$ 的概率，分别从 $(p-m)/\epsilon$ 与 $(q-m)/\epsilon$ 抽样。

验证边缘：

$$\Pr(X=x)=(1-\epsilon)\frac{m(x)}{1-\epsilon}+\epsilon\frac{p(x)-m(x)}{\epsilon}=p(x)$$

第二分支的残余支持不相交：$p\gt q$ 处 $q-m=0$；$p\lt q$ 处 $p-m=0$。因此恰好：

$$\Pr(X=Y)=1-\epsilon,\qquad\Pr(X\ne Y)=\epsilon$$

$\epsilon=0$ 时两边完全共用抽样；$\epsilon=1$ 时没有公共分支，不执行含零分母的表达式。

**原数字例。** $p=(0.5,0.3,0.2)$、$q=(0.4,0.4,0.2)$ 的 TV 为 $0.1$。最大耦合一致率为 $0.9$；独立抽样的一致率仅为：

$$0.5(0.4)+0.3(0.4)+0.2(0.2)=0.36$$

所以“存在一种抽法”不能省。对任何耦合，任意事件 $B$ 的概率差不超过失配概率：

$$|p(B)-q(B)|\le\Pr(X\ne Y)$$

取事件的上确界，再加上构造可达性：

$$D_{\mathrm{TV}}(p,q)=\min_{\text{所有耦合}}\Pr(X\ne Y)$$

用于轨迹时，动作耦合只在两边尚未分歧且位于同一状态时采用；初始状态与相同状态—动作后的环境转移也共用随机性。单看每个策略的轨迹分布完全不变。证明因此只控制分歧事件，不要求“没分歧条件下的状态分布等于旧分布”。

[回到公式 7](#formula-7)。

### 精读 2：TV、KL、期望差，分别是哪一种量 {#tv-kl-detail}

| 量 | 定义/读法 | 本讲使用 |
|---|---|---|
| TV | $\frac12\sum_x\lvert p(x)-q(x)\rvert$，需要搬动的质量 | 把概率表差换成可构造的分歧概率 |
| KL | $\sum_xp(x)\log[p(x)/q(x)]$ | 可估计的罚项与局部曲率 |
| 期望差 | $\sum_x(p-q)f$ | 将状态分布偏移转成目标偏差 |

TV 对称、有上界、满足三角不等式；KL 一般不对称，可为无穷，不是 metric。本文 log 为自然对数，单位是 nats；若用二进制对数，信息量单位和 Pinsker 常数相应改变。

**KL 小给 TV 小，反过来不行。** 例如 $p=(\delta,1-\delta)$、$q=(0,1)$，TV 为 $\delta$，但只要 $\delta\gt0$，$D_{\mathrm{KL}}(p\Vert q)=+\infty$。

要保证 TV 上限 $\epsilon$，KL 上限 $2\epsilon^2$ 是充分条件，可能排除部分 TV 已合格的候选。这说的是可行域更保守；将真实 TV 用更大的 Pinsker 上界替代，则误差保证更松。两个视角要分开。

**平均与最大也要分开。** 少量旧状态的 KL 巨大，可能仍被其他状态的低 KL 稀释。平均约束适合训练，不等价于对所有状态的统一上限。

### 精读 3：Jensen、KL 非负与 log-sum {#jensen-detail}

对凸函数 $\varphi$，完整的两点定义是：

$$\varphi(\lambda x+(1-\lambda)y)\le\lambda\varphi(x)+(1-\lambda)\varphi(y),\qquad0\le\lambda\le1$$

曲线在割线下方。只验证中点版本，还需相应连续性等条件才能得到一般凸性；这里直接使用完整权重定义。

Jensen 将有限加权和扩展为期望：

$$\varphi(\mathbb E[X])\le\mathbb E[\varphi(X)]$$

$x^2,e^x,x\log x$ 在其相应定义域上凸；$\log x$ 在正数上凹，所以：

$$\mathbb E[\log X]\le\log\mathbb E[X]$$

若 $X$ 以相同概率取 $1,9$，则平方例中 $25\le41$；对数例中 $\frac12\log9\approx1.099\le\log5\approx1.609$。

对 $q/p$、以 $p$ 加权，可证 KL 非负：

$$-D_{\mathrm{KL}}(p\Vert q)=\mathbb E_p[\log(q/p)]\le\log\mathbb E_p[q/p]\le\log1=0$$

最后一个不等号考虑了 $p=0$ 区域可能仍有 $q$ 质量；若支持匹配，可写等号。遇到 $p\gt0,q=0$ 时 KL 无穷，非负结论仍成立。

**log-sum 的直接推导。** 对正数列 $a_i,b_i$，用权重 $b_i/\sum_jb_j$ 对凸函数 $x\log x$ 使用 Jensen，整理得到：

$$\sum_i a_i\log\frac{a_i}{b_i}\ge\left(\sum_i a_i\right)\log\frac{\sum_i a_i}{\sum_i b_i}$$

零值按极限与 KL 约定处理。这允许把许多概率项合并成一格后降低 KL，是下一节压到二点分布的代数依据。

### 精读 4：Pinsker 完整证明，先归约再一元求导 {#pinsker-detail}

要证：

$$D_{\mathrm{KL}}(P\Vert Q)\ge2D_{\mathrm{TV}}(P,Q)^2$$

沿用本地精读的记号：$p(x),q(x)$ 是单点概率，$a,b$ 是一整块的概率总和，$d(a\Vert b)$ 是二元 KL。它们仅在这份局部证明中使用。

**第 1 步：选能保留 TV 的事件。**

$$A=\{x:p(x)\ge q(x)\},\qquad a=\sum_{x\in A}p(x),\qquad b=\sum_{x\in A}q(x)$$

因为 $\sum_x(p-q)=0$，正差总量等于负差总量：

$$D_{\mathrm{TV}}(P,Q)=\sum_{x\in A}(p(x)-q(x))=a-b$$

**第 2 步：把世界压成“在 A 内/外”两格。** 对这两块各用 log-sum：

$$\sum_{x\in A}p(x)\log\frac{p(x)}{q(x)}\ge a\log\frac ab$$

$$\sum_{x\notin A}p(x)\log\frac{p(x)}{q(x)}\ge(1-a)\log\frac{1-a}{1-b}$$

相加得到：

$$D_{\mathrm{KL}}(P\Vert Q)\ge d(a\Vert b),\qquad d(a\Vert b)=a\log\frac ab+(1-a)\log\frac{1-a}{1-b}$$

**归约方向为什么合法：** TV 不变，KL 变小。若更小的二元 KL 都压得住 $2(a-b)^2$，原来的 KL 当然压得住。仅证明某个两点例子不足以证明一般情形；关键是这条对任意 $P,Q$ 都成立的归约。

**第 3 步：固定 a，构造需要非负的函数。**

$$g(b)=d(a\Vert b)-2(a-b)^2,\qquad g(a)=0$$

在 $0\lt b\lt1$ 上逐项求导：

$$\frac{d}{db}d(a\Vert b)=-\frac ab+\frac{1-a}{1-b}=\frac{b-a}{b(1-b)}$$

$$\frac{d}{db}[-2(a-b)^2]=-4(b-a)$$

因此：

$$g'(b)=(b-a)\left[\frac1{b(1-b)}-4\right]$$

**第 4 步：看导数符号。** 因为：

$$b(1-b)=\frac14-\left(b-\frac12\right)^2\le\frac14$$

方括号非负；$b\lt a$ 时 $g'\le0$，$b\gt a$ 时 $g'\ge0$。所以 $b=a$ 是最小点，$g(b)\ge g(a)=0$。边界以极限处理。

**第 5 步：把链拼回一般分布。**

$$D_{\mathrm{KL}}(P\Vert Q)\ge d(a\Vert b)\ge2(a-b)^2=2D_{\mathrm{TV}}(P,Q)^2$$

开根号即得 Pinsker。两个机关是“选 $A=\{p\ge q\}$ 保留 TV”和“$b(1-b)\le1/4$ 控制导数”。

**关于取等与近似。** $P=Q$ 时精确取等。二元五五开、小扰动时可渐近达到最佳常数；对非零扰动，不能把二阶近似当作精确等号。

### 精读 5：从状态误差得到更紧的二阶策略界 {#sharper-bound}

公式 8 使用 $|f|\le C$ 得到一次策略距离界。旧优势有额外结构：

$$\mathbb E_{a\sim\pi_\theta}[A^{\pi_\theta}(s,a)]=0$$

因此新动作下的旧优势平均可写成差：

$$f(s)=\sum_a[\pi_{\theta'}(a\mid s)-\pi_\theta(a\mid s)]A^{\pi_\theta}(s,a)$$

若逐状态动作 TV 不超过 $\epsilon$，则：

$$|f(s)|\le2C\epsilon$$

状态 TV 已有 $t\epsilon$ 上界，再代入期望差：

$$|J(\theta')-J(\theta)-\bar A(\theta')|\le4C\epsilon^2\sum_{t=0}^{H-1}t\gamma^t$$

一个 $\epsilon$ 来自访问状态差，另一个来自旧优势零均值。这也接回 Lecture 9 的“起点两个因子都为零，所以目标误差是二阶”。

### 精读 6：Fisher 外积与 KL Hessian 为什么相等 {#fisher-detail}

固定一个旧状态，对概率归一化求导：

$$\int\pi_\theta(a\mid s)\,da=1\quad\Longrightarrow\quad\int\nabla_\theta\pi_\theta(a\mid s)\,da=0$$

用 $\nabla\pi=\pi\nabla\log\pi$：

$$\mathbb E_{a\sim\pi_\theta}[\nabla_\theta\log\pi_\theta(a\mid s)]=0$$

再对这条零均值式求导，必须同时微分概率和 log 梯度：

$$\mathbb E_{a\sim\pi_\theta}[\nabla_\theta\log\pi_\theta(a\mid s)\nabla_\theta\log\pi_\theta(a\mid s)^\top]+\mathbb E_{a\sim\pi_\theta}[\nabla_\theta^2\log\pi_\theta(a\mid s)]=0$$

而旧在前的 KL 对新参数的 Hessian，在旧点正是负的第二项。因此再对旧状态平均得到：

$$\mathbf F=-\mathbb E_{s\sim p_\theta,a\sim\pi_\theta}[\nabla_\theta^2\log\pi_\theta(a\mid s)]$$

这与外积期望是**总体恒等式**。有限样本中，直接对采到的 log 比求 Hessian，和样本 score 外积未必数值相等；前者还可能不保持半正定。TRPO 常对旧样本状态上的解析动作 KL 求 Hessian-vector product。

正定条件也要核对：若某个参数方向完全不改变概率，那个方向的曲率为零，Fisher 只是半正定。不能由 $v^\top Fv\ge0$ 直接推出标准 CG 所需的严格正定。

### 精读 7：自然梯度的拉格朗日推导 {#natural-detail}

仅在本节，用 $\beta$ 表示二次约束的拉格朗日乘子；这是本地解析求解，不是 PPO 的在线惩罚调度。假设 $\mathbf F$ 正定、梯度非零：

$$\mathcal L(\Delta,\beta)=\nabla_\theta J(\theta)^\top\Delta-\beta\left(\frac12\Delta^\top\mathbf F\Delta-\epsilon\right)$$

对位移求导：

$$\nabla_\Delta\mathcal L=\nabla_\theta J(\theta)-\beta\mathbf F\Delta=0$$

所以：

$$\Delta=\frac1\beta\mathbf F^{-1}\nabla_\theta J(\theta)$$

代回边界约束：

$$\frac1{2\beta^2}\nabla_\theta J(\theta)^\top\mathbf F^{-1}\nabla_\theta J(\theta)=\epsilon$$

解出 $1/\beta$，即公式 19 的 $\alpha$。方向与长度分别来自驻点条件和预算边界。

同一 $(6,8)$、$\operatorname{diag}(1,100)$ 的例子，在**相同二次 KL 预算 $0.01$** 下比较：

| 方向 | 放到同一预算边界后的位移 | 线性改进 |
|---|---|---:|
| 沿普通梯度 | $\sqrt{0.02/6436}(6,8)$ | $\approx0.1763$ |
| 沿自然梯度 | $\sqrt{0.02/36.64}(6,0.08)$ | $\approx0.8560$ |

不能拿两个不同约束半径比较效率。这里方向和最终长度都已按同一预算计算。

### 精读 8：TRPO 为什么还要 CG、阻尼与线搜索 {#trpo-detail}

一百万参数的稠密 Fisher 有 $10^{12}$ 个元素；32 位存储约需 4 TB。我们需要的是一个方向向量，不是整个逆矩阵。

Hessian-vector product 先求 KL 梯度，再与固定 $v$ 点积，最后求该标量的梯度。CG 通过重复这类乘积求解，代价与每次网络计算和迭代次数相关。误差受条件数影响，不应把“近似只跑少量轮”说成普遍的固定复杂度保证。

**阻尼做什么：** 加正的对角项可处理奇异与病态方向，但也改变求解模型。候选步长要与所用模型一致，最终仍以实际经验 KL 检查。

**线搜索检查什么：** 经验平均 KL 小于预算，固定批次的代理目标有足够改进。查的是原经验目标和 KL，不是刚才的线性/二次近似；也不等于证明总体真实回报每步都增长。

若没有候选通过，保持旧策略。接受一个候选之后刷新数据，重新估计优势与局部几何。

## 复原练习与公式速查

### Pinsker 的七步复原 {#pinsker-recall}

先盖住 [完整证明](#pinsker-detail)，按“选事件 → 命名块概率 → TV 保留 → KL 合并 → 二元辅助函数 → 导数符号 → 拼链”写出推导。

| 应写的接缝 | 检查点 |
|---|---|
| 为什么选 $\{p\ge q\}$ | 必须说明正差总量正好等于 TV |
| 为什么可降到二元 | 必须说明 TV 不变、KL 只减 |
| 为什么最小值是零 | 必须写出导数与 $b(1-b)\le1/4$ |
| 为什么一般情形也成立 | 必须拼完整的三段不等式 |

### 全公式索引 {#formula-index}

| 编号 | 任务 |
|---|---|
| [1](#formula-1) | 分开旧优势与旧状态两个替代 |
| [2](#formula-2) | 评估—改进与策略迭代的共同骨架 |
| [3](#formula-3) | 望远镜求和得到性能差异恒等式 |
| [4](#formula-4) | 动作期望展开、插比值、认结构、写回期望 |
| [5](#formula-5) | 定义旧状态代理改进量 |
| [6](#formula-6) | 一次未分歧/至少分歧一次 |
| [7](#formula-7) | 最大耦合与状态 TV 界 |
| [8](#formula-8) | 期望差 → 逐时刻误差 → 回报下界 |
| [9](#formula-9) | 逐状态 TV 约束 |
| [10](#formula-10) | Pinsker 与 KL；标清平均替代 |
| [11](#formula-11) | KL 样本形式与旧样本似然 |
| [12](#formula-12) | 拉格朗日与非负乘子 |
| [13](#formula-13) | 代理提升与 KL 罚项的归一化 |
| [14](#formula-14) | 完整 PPO-KL 循环 |
| [15](#formula-15) | 一阶目标与局部信赖域 |
| [16](#formula-16) | 旧点代理梯度匹配真实梯度 |
| [17](#formula-17) | 欧氏球与概率空间的敏感度 |
| [18](#formula-18) | KL 二阶项与 Fisher |
| [19](#formula-19) | 自然梯度方向与逆矩阵步长分母 |
| [20](#formula-20) | 完整 TRPO、CG、线搜索 |

### 串起主线的自测 {#self-check}

1. 旧优势为何不必等于新优势，也能出现在精确性能差异式里？
2. 单条 TD 型量怎样经过条件期望变成优势？
3. 动作 IS 换完以后，哪个分布仍是新策略的？
4. 耦合为什么不需要让两条真实运行轨迹同时执行？
5. “一次没分歧条件下仍是旧分布”的混合等式为什么一般不成立？
6. 期望误差界为何要 max |f|，因子 2 从哪里来？
7. 裸代理量、代理量减误差、真实改变量，谁与谁有界？
8. 逐状态 KL 与样本平均 KL 有什么区别？
9. 为什么 $\beta$ 不能变成负数？
10. KL 为什么必须展开到二阶，Fisher 为何只保证半正定？
11. 自然梯度的步长为什么含 $\nabla J^\top F^{-1}\nabla J$？
12. 线搜索验收为什么还不能等同真实回报保证？

<details>
<summary>展开参考答案</summary>

1. 用旧价值做望远镜求和，精确把新旧回报差写成新轨迹上的旧优势和；没有使用两种优势相等。
2. 固定当前状态动作，对相同环境下的下一状态平均，才将奖励加旧后续价值变成旧 Q。
3. 外层新状态分布仍没有换；旧状态替代是另一步近似。
4. 只设计联合抽样的相关性，边缘仍保持每个策略的真实分布，所以用于证明即可。
5. 分歧概率可依赖状态路径，未分歧事件会筛选路径，其条件分布会变。
6. 优势可有负值，需绝对上界；TV 定义带一半，L1 和等于两倍 TV。
7. 真实改变量至少是代理量减误差项；裸代理量本身不是通用下界。
8. 平均允许少量状态距离很大，无法保证所有状态都满足原统一上限。
9. 非负才是距离罚项；负值会鼓励约束违反，投影保持合法。
10. 同策略处零阶、一阶都为零。外积只保证任意方向二次型非负，冗余方向可为零。
11. 把自然梯度位移代回二次约束，矩阵与逆抵消后只留一个逆。
12. 它检查有限样本的代理目标与平均 KL，而理论条件与总体回报还受采样及函数近似影响。

</details>

## 材料与前后衔接 {#sources}

主材料为本地《Lecture10 公式逐行拆解》。精读整合自耦合引理、TV/KL、Pinsker 推导与周边地图、凸函数/Jensen、归约方法、Pinsker 主动复原，以及 Slide 17–18、24–30 的配套逐页说明。核心推导、数字例与自测用途保留，统一时间、折扣、KL 方向和归一化，并按配套精读修正自然梯度步长、补齐 TRPO 算法。

理论与实现核对：[TRPO 原论文](https://proceedings.mlr.press/v37/schulman15.pdf)、[PPO 原论文](https://arxiv.org/abs/1707.06347)、[Spinning Up 的 TRPO 说明](https://spinningup.openai.com/en/latest/algorithms/trpo.html)。

往前连接：[Lecture 2 的状态分布变化](../lecture-02/)、[Lecture 5 的策略梯度](../lecture-05/)、[Lecture 9 的旧样本复用与 PPO-Clip](../lecture-09/)。本讲解释这些工具之间的条件与误差；后续用它们训练序列策略和语言模型。
