#!/bin/bash
# 启动 CDID 分析平台 Worker

set -e

# 切换到项目目录
cd "$(dirname "$0")"

echo "正在启动 CDID 分析平台 Worker..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "虚拟环境不存在，正在创建..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 启动 Worker
echo "Worker 启动中..."
python3 -m src.worker.main
