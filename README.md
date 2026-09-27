# dextermayhewjd.github.io

Hugo + PaperMod 个人博客：https://dextermayhewjd.github.io/

网站由本地构建后推送到 `gh-pages` 分支发布（`main` 只放源码）。

```bash
git clone --recurse-submodules https://github.com/dextermayhewjd/dextermayhewjd.github.io.git
hugo server -D                     # 本地预览 http://localhost:1313
hugo new content posts/xxx.md      # 新文章，写完把 draft 改为 false
git add -A && git commit -m "..." && git push   # 保存源码
./deploy.sh                        # 构建并发布网站
```

`.github/workflows/hugo.yml` 是 Actions 自动部署方案，目前已停用；如需启用，把 Pages 来源改为 GitHub Actions 并 `gh workflow enable hugo.yml`。
