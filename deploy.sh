#!/usr/bin/env bash
# 本地构建并发布到 gh-pages 分支（GitHub Pages 从该分支提供网站）
set -euo pipefail
cd "$(dirname "$0")"
HUGO="${HUGO:-hugo}"
command -v "$HUGO" >/dev/null || { echo "找不到 hugo，请先安装或设置 HUGO=/path/to/hugo"; exit 1; }

git submodule update --init --recursive
rm -rf public
"$HUGO" --gc --minify
touch public/.nojekyll

src=$(git rev-parse --short HEAD)
remote=$(git remote get-url origin)
cd public
git init -q -b gh-pages
git add -A
git commit -qm "deploy: $src"
git push -qf "$remote" gh-pages
echo "已发布 $src → https://dextermayhewjd.github.io/ （约 1 分钟后生效）"
