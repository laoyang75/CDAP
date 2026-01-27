#!/bin/bash
# 启动图形化启动器
# 自动选择兼容的版本

cd "$(dirname "$0")"

echo "🎨 启动图形化启动器..."
echo ""
echo "⚠️  注意：由于 tkinter 兼容性问题，推荐使用 Web 启动器"
echo "按 Ctrl+C 取消，或等待 3 秒自动启动 Web 启动器..."
echo ""

# 等待 3 秒，给用户取消的机会
for i in 3 2 1; do
  echo "  $i..."
  sleep 1
done

echo ""
echo "启动 Web 启动器（http://localhost:5555）..."
./run_web.sh
