#!/usr/bin/env bash
# 重建 Lambda Layer（layer_build/python 已預先打包，通常不需重跑）
# 需要重建時（例如升級 anthropic 版本）執行：
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf layer_build/python
mkdir -p layer_build/python
pip install anthropic --target layer_build/python \
  --platform manylinux2014_x86_64 --python-version 3.12 \
  --only-binary=:all: --implementation cp
# feedparser 依賴 sgmllib3k（無 wheel），純 Python 直接裝
pip install feedparser --target layer_build/python --no-deps
pip install sgmllib3k --target layer_build/python --no-deps
find layer_build/python -name "__pycache__" -type d -exec rm -rf {} +
echo "layer_build/python 完成："
du -sh layer_build/python
