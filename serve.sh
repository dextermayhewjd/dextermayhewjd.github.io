#!/usr/bin/env bash
# 启动本地 Hugo 预览，额外参数直接传给 hugo server。
set -euo pipefail
cd "$(dirname "$0")"
HUGO="${HUGO:-hugo}"
command -v "$HUGO" >/dev/null || { echo "找不到 hugo，请先安装 Hugo Extended 0.166.0 或设置 HUGO=/path/to/hugo" >&2; exit 1; }

if [[ ! -f themes/PaperMod/theme.toml ]]; then
  echo "缺少 PaperMod 主题，请先运行：git submodule update --init --recursive" >&2
  exit 1
fi

exec "$HUGO" server -D --bind 127.0.0.1 --port 1313 --noHTTPCache --disableFastRender "$@"
