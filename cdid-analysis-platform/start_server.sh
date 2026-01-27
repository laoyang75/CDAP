#!/bin/bash
# 启动 CDID 分析平台 API Server

set -e

# 切换到项目目录
cd "$(dirname "$0")"

echo "正在启动 CDID 分析平台 API Server..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "虚拟环境不存在，正在创建..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 启动服务器
echo "服务器启动中..."
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
