#!/bin/bash
# CDID 数据分析平台一键启动脚本

cd "$(dirname "$0")"

echo "🚀 启动 CDID 数据分析平台..."
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未找到，请先安装 Python 3.11+"
    exit 1
fi

# 运行启动器
python3 launcher.py
