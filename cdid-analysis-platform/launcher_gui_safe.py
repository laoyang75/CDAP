#!/usr/bin/env python3
"""
CDID 数据分析平台 GUI 启动器（安全版本）

⚠️ 警告：此启动器依赖 tkinter，在某些系统上可能不兼容
推荐使用 Web 启动器：./run_web.sh
"""

import os
import sys
import platform


def check_tkinter_compatibility():
    """检查 tkinter 兼容性，避免崩溃"""
    print("=" * 70)
    print("GUI 启动器 - 兼容性检查")
    print("=" * 70)

    # 显示系统信息
    macos_version = platform.mac_ver()[0]
    python_version = sys.version.split()[0]

    print(f"\n系统信息：")
    print(f"  macOS 版本: {macos_version}")
    print(f"  Python 版本: {python_version}")

    # 尝试导入 tkinter
    print(f"\n检查 tkinter...")

    try:
        import tkinter as tk
        print("  ✓ tkinter 模块可导入")

        # 尝试获取 Tk 版本
        try:
            root = tk.Tk()
            tk_version = root.tk.call('info', 'patchlevel')
            root.withdraw()
            root.destroy()

            print(f"  ✓ Tk 版本: {tk_version}")
            print(f"\n{'=' * 70}")
            print("✅ 兼容性检查通过，可以使用 GUI 启动器")
            print("=" * 70)
            return True

        except Exception as e:
            print(f"  ✗ Tk 初始化失败: {e}")
            return False

    except ImportError as e:
        print(f"  ✗ tkinter 不可用: {e}")
        return False


def show_alternative():
    """显示替代方案"""
    print("\n" + "=" * 70)
    print("⚠️  GUI 启动器在您的系统上不兼容")
    print("=" * 70)
    print("\n已知问题：")
    print("  某些 macOS 系统的 tkinter 版本过旧，会导致程序崩溃")
    print("\n" + "=" * 70)
    print("推荐解决方案：使用 Web 启动器 ✨")
    print("=" * 70)
    print("\n启动命令：")
    print("  ./run_web.sh")
    print("\n或者：")
    print("  python3 launcher_web.py")
    print("\nWeb 启动器优势：")
    print("  ✓ 无兼容性问题")
    print("  ✓ 更美观的界面")
    print("  ✓ 实时状态监控")
    print("  ✓ 彩色日志显示")
    print("\n启动后会自动打开浏览器访问：http://localhost:5555")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    # 先检查兼容性
    if not check_tkinter_compatibility():
        show_alternative()
        sys.exit(1)

    # 如果兼容，继续加载 GUI
    print("\n正在启动 GUI 启动器...")

    try:
        # 导入原始的 launcher_gui
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "launcher_gui",
            os.path.join(os.path.dirname(__file__), "launcher_gui.py")
        )
        launcher_gui = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(launcher_gui)

        # 启动 GUI
        launcher_gui.main()

    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n尝试使用 Web 启动器代替：")
        print("  ./run_web.sh")
        sys.exit(1)
