#!/bin/bash
# 启动 Web 版本的启动器

cd "$(dirname "$0")"

echo "🌐 启动 Web 图形化启动器..."
source venv/bin/activate
python3 launcher_web.py
