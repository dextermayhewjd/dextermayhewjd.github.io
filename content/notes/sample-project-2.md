---
date: 2026-09-27
category: "项目"
title: "VAE 小实验：为什么 ELBO 的梯度要这样估计"
source: "vae-playground"
draft: true
summary: "从 $\\nabla_\\theta \\log p_\\theta(x)$ 出发，想清楚为什么需要重参数化。"
build: { render: always, list: local }
---
这是一条**展开成独立页面**的感悟：抽屉里只显示摘要，点击进入全文。

$$
\nabla_\theta \log p_\theta(x) = \mathbb{E}_{z \sim p_\theta(z|x)}\left[\nabla_\theta \log p_\theta(x|z)\right]
$$

后验 $p_\theta(z|x)$ 采不到，所以换成 $q_\phi(z|x)$ 并用重参数化把随机性挪出去……
