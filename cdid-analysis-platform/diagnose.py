#!/usr/bin/env python3
"""
诊断工具 - 检查系统性能和问题

用于诊断：
- 启动速度慢
- 页面加载慢
- 服务响应慢
"""

import time
import subprocess
import sys
from pathlib import Path
import requests


def measure_time(func):
    """测量函数执行时间"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        return result, elapsed
    return wrapper


@measure_time
def test_python_import():
    """测试 Python 模块导入速度"""
    print("测试 Python 模块导入...")
    sys.path.insert(0, '.')

    # 测试主要模块
    import src.config
    import src.db
    import src.api.main

    return True


@measure_time
def test_database_init():
    """测试数据库初始化速度"""
    print("测试数据库初始化...")
    sys.path.insert(0, '.')

    from src.config import get_config
    from src.db import get_engine

    config = get_config()
    engine = get_engine(config)

    return True


@measure_time
def test_api_response(url):
    """测试 API 响应速度"""
    print(f"测试 API 响应: {url}")

    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"  错误: {e}")
        return False


@measure_time
def test_static_file(url):
    """测试静态文件加载"""
    print(f"测试静态文件: {url}")

    try:
        response = requests.get(url, timeout=5)
        return response.status_code in [200, 404]  # 404 也算正常（文件可能不存在）
    except Exception as e:
        print(f"  错误: {e}")
        return False


def main():
    """主诊断流程"""
    print("=" * 60)
    print("CDID 数据分析平台 - 系统诊断工具")
    print("=" * 60)
    print()

    results = []

    # 1. 测试 Python 模块导入
    print("1️⃣  测试 Python 模块导入速度")
    result, elapsed = test_python_import()
    results.append(("模块导入", elapsed, result))
    print(f"   ✓ 完成，用时: {elapsed:.2f} 秒")
    if elapsed > 2:
        print(f"   ⚠️  导入速度较慢（> 2秒）")
    print()

    # 2. 测试数据库初始化
    print("2️⃣  测试数据库初始化速度")
    result, elapsed = test_database_init()
    results.append(("数据库初始化", elapsed, result))
    print(f"   ✓ 完成，用时: {elapsed:.2f} 秒")
    if elapsed > 1:
        print(f"   ⚠️  数据库初始化较慢（> 1秒）")
    print()

    # 3. 检查服务是否运行
    print("3️⃣  检查服务是否运行")
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port_open = sock.connect_ex(('127.0.0.1', 8000)) == 0
    sock.close()

    if not port_open:
        print("   ⚠️  服务未运行（端口 8000 未开放）")
        print("   提示: 请先启动服务")
        print()
        print("=" * 60)
        print("诊断完成")
        print("=" * 60)
        return
    else:
        print("   ✓ 服务正在运行")
        print()

    # 4. 测试 API 响应速度
    print("4️⃣  测试 API 端点响应速度")

    endpoints = [
        "http://localhost:8000/health",
        "http://localhost:8000/",
        "http://localhost:8000/api/jobs",
    ]

    for url in endpoints:
        result, elapsed = test_api_response(url)
        results.append((f"API {url}", elapsed, result))
        status = "✓" if result else "✗"
        print(f"   {status} {url}: {elapsed:.2f} 秒")
        if elapsed > 1:
            print(f"      ⚠️  响应较慢（> 1秒）")
    print()

    # 5. 测试静态文件加载
    print("5️⃣  测试静态文件加载速度")

    static_files = [
        "http://localhost:8000/static/css/bootstrap.min.css",
        "http://localhost:8000/static/css/bootstrap-icons.min.css",
        "http://localhost:8000/static/js/bootstrap.bundle.min.js",
        "http://localhost:8000/static/css/style.css",
        "http://localhost:8000/static/js/app.js",
    ]

    for url in static_files:
        result, elapsed = test_static_file(url)
        results.append((f"静态文件 {url}", elapsed, result))
        status = "✓" if result else "✗"
        filename = url.split("/")[-1]
        print(f"   {status} {filename}: {elapsed:.2f} 秒")
    print()

    # 汇总报告
    print("=" * 60)
    print("诊断汇总")
    print("=" * 60)

    slow_items = [(name, elapsed) for name, elapsed, _ in results if elapsed > 1]

    if slow_items:
        print("\n⚠️  发现性能问题：\n")
        for name, elapsed in slow_items:
            print(f"   - {name}: {elapsed:.2f} 秒")
        print("\n建议：")
        print("   1. 检查网络连接")
        print("   2. 检查系统资源（CPU、内存）")
        print("   3. 查看日志文件: logs/api.log")
        print("   4. 尝试重启服务")
    else:
        print("\n✓ 所有测试项响应速度正常")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
