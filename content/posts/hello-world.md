---
title: "Hello, Hugo"
date: 2026-09-27
tags: ["博客"]
summary: "博客上线的第一篇文章，顺便测试一下公式渲染。"
---

博客用 [Hugo](https://gohugo.io/) + [PaperMod](https://github.com/adityatelange/hugo-PaperMod) 搭建，push 到 `main` 后由 GitHub Actions 自动构建发布。

## 公式测试

行内公式：$\nabla_\theta \log p_\theta(x) = \mathbb{E}_{z \sim p_\theta(z|x)}[\nabla_\theta \log p_\theta(x|z)]$

块级公式：

$$
\nabla_\theta \log p_\theta(x) = \frac{\nabla_\theta p_\theta(x)}{p_\theta(x)} = \frac{1}{p_\theta(x)} \int p(z)\, \nabla_\theta p_\theta(x|z)\, dz
$$

## 代码测试

```python
def hello():
    print("hello, hugo")
```

## 如何写新文章

```bash
hugo new content posts/my-new-post.md   # 然后编辑、把 draft 改成 false
git add . && git commit -m "new post" && git push
```
