#!/bin/bash
# 开发环境快速启动脚本（同时启动 Server 和 Worker）

set -e

cd "$(dirname "$0")"

echo "正在启动开发环境..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "虚拟环境不存在，正在创建..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 创建必要的目录
mkdir -p jobs/uploads jobs/outputs logs

# 启动 Worker（后台）
echo "启动 Worker（后台）..."
python3 -m src.worker.main &
WORKER_PID=$!

# 启动 Server（前台）
echo "启动 API Server（前台）..."
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload &
SERVER_PID=$!

echo ""
echo "========================================="
echo "CDID 数据分析平台已启动"
echo "========================================="
echo "API Server: http://localhost:8000"
echo "Worker PID: $WORKER_PID"
echo "Server PID: $SERVER_PID"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "========================================="

# 等待中断信号
trap "echo '正在停止服务...'; kill $WORKER_PID $SERVER_PID 2>/dev/null; exit 0" INT TERM

wait
