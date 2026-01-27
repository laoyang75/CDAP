#!/usr/bin/env python3
"""
CDID 数据分析平台 GUI 启动器

功能：
- 图形化界面操作
- 实时日志显示
- 一键启动/停止服务
- 状态监控
"""

import os
import sys
import time
import signal
import subprocess
import platform
import webbrowser
import threading
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox


class LauncherGUI:
    """GUI 启动器"""

    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.api_port = 8000
        self.pid_file = self.project_dir / ".launcher.pid"
        self.log_dir = self.project_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)

        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("CDID 数据分析平台启动器")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # 服务状态
        self.is_running = False
        self.api_process = None
        self.worker_process = None

        # 设置样式
        self.setup_styles()

        # 创建界面
        self.create_widgets()

        # 启动状态检查
        self.check_initial_status()

    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        style.theme_use('default')

        # 配置按钮样式
        style.configure('Success.TButton', foreground='green')
        style.configure('Danger.TButton', foreground='red')
        style.configure('Primary.TButton', foreground='blue')

    def create_widgets(self):
        """创建界面组件"""
        # 顶部标题
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        title_label = ttk.Label(
            header_frame,
            text="🚀 CDID 数据分析平台",
            font=('Arial', 18, 'bold')
        )
        title_label.pack()

        subtitle_label = ttk.Label(
            header_frame,
            text="图形化启动器 v1.0",
            font=('Arial', 10)
        )
        subtitle_label.pack()

        # 状态显示区域
        status_frame = ttk.LabelFrame(self.root, text="服务状态", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        # API Server 状态
        api_frame = ttk.Frame(status_frame)
        api_frame.pack(fill=tk.X, pady=2)
        ttk.Label(api_frame, text="API Server:", width=15).pack(side=tk.LEFT)
        self.api_status_label = ttk.Label(api_frame, text="● 未启动", foreground="gray")
        self.api_status_label.pack(side=tk.LEFT)

        # Worker 状态
        worker_frame = ttk.Frame(status_frame)
        worker_frame.pack(fill=tk.X, pady=2)
        ttk.Label(worker_frame, text="Worker:", width=15).pack(side=tk.LEFT)
        self.worker_status_label = ttk.Label(worker_frame, text="● 未启动", foreground="gray")
        self.worker_status_label.pack(side=tk.LEFT)

        # 端口状态
        port_frame = ttk.Frame(status_frame)
        port_frame.pack(fill=tk.X, pady=2)
        ttk.Label(port_frame, text="端口 8000:", width=15).pack(side=tk.LEFT)
        self.port_status_label = ttk.Label(port_frame, text="● 未占用", foreground="gray")
        self.port_status_label.pack(side=tk.LEFT)

        # 控制按钮区域
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        # 第一行按钮
        row1 = ttk.Frame(control_frame)
        row1.pack(fill=tk.X, pady=5)

        self.start_btn = ttk.Button(
            row1,
            text="🚀 启动服务",
            command=self.start_services,
            style='Success.TButton'
        )
        self.start_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.stop_btn = ttk.Button(
            row1,
            text="🛑 停止服务",
            command=self.stop_services,
            style='Danger.TButton',
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.restart_btn = ttk.Button(
            row1,
            text="🔄 重启服务",
            command=self.restart_services,
            state=tk.DISABLED
        )
        self.restart_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # 第二行按钮
        row2 = ttk.Frame(control_frame)
        row2.pack(fill=tk.X, pady=5)

        ttk.Button(
            row2,
            text="🌐 打开浏览器",
            command=self.open_browser
        ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Button(
            row2,
            text="💪 清理端口",
            command=self.force_kill_port
        ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Button(
            row2,
            text="🔍 检查环境",
            command=self.check_environment
        ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # 进度条
        self.progress_frame = ttk.Frame(self.root)
        self.progress_frame.pack(fill=tk.X, padx=10, pady=5)

        self.progress = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate'
        )
        self.progress.pack(fill=tk.X)

        # 日志显示区域
        log_frame = ttk.LabelFrame(self.root, text="运行日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=20,
            wrap=tk.WORD,
            font=('Courier', 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 配置日志颜色
        self.log_text.tag_config('info', foreground='black')
        self.log_text.tag_config('success', foreground='green')
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('warning', foreground='orange')

        # 底部按钮
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            bottom_frame,
            text="📝 清空日志",
            command=self.clear_log
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            bottom_frame,
            text="📚 API 文档",
            command=lambda: webbrowser.open(f"http://localhost:{self.api_port}/docs")
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            bottom_frame,
            text="❌ 退出",
            command=self.on_closing
        ).pack(side=tk.RIGHT, padx=5)

    def log(self, message, level='info'):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}\n"

        self.log_text.insert(tk.END, formatted_msg, level)
        self.log_text.see(tk.END)
        self.root.update()

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)

    def update_status(self):
        """更新状态显示"""
        # 检查进程是否运行
        api_running = self.check_process_running('api')
        worker_running = self.check_process_running('worker')
        port_used = self.check_port(self.api_port)

        # 更新 API Server 状态
        if api_running:
            self.api_status_label.config(text="● 运行中", foreground="green")
        else:
            self.api_status_label.config(text="● 未启动", foreground="gray")

        # 更新 Worker 状态
        if worker_running:
            self.worker_status_label.config(text="● 运行中", foreground="green")
        else:
            self.worker_status_label.config(text="● 未启动", foreground="gray")

        # 更新端口状态
        if port_used:
            self.port_status_label.config(text="● 已占用", foreground="orange")
        else:
            self.port_status_label.config(text="● 未占用", foreground="gray")

        # 更新按钮状态
        if api_running or worker_running:
            self.is_running = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.restart_btn.config(state=tk.NORMAL)
        else:
            self.is_running = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.restart_btn.config(state=tk.DISABLED)

    def check_process_running(self, process_type):
        """检查进程是否运行"""
        # 根据进程类型检查对应的进程
        import subprocess

        try:
            if process_type == 'api':
                # 检查 API Server 进程
                result = subprocess.run(
                    ['pgrep', '-f', 'uvicorn src.api.main:app'],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            elif process_type == 'worker':
                # 检查 Worker 进程
                result = subprocess.run(
                    ['pgrep', '-f', 'src.worker.main'],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            else:
                return False
        except Exception:
            return False

    def check_port(self, port):
        """检查端口是否被占用"""
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0

    def get_venv_python(self):
        """获取虚拟环境的 Python 路径"""
        venv_dir = self.project_dir / "venv"

        if platform.system() == "Windows":
            return venv_dir / "Scripts" / "python.exe"
        else:
            return venv_dir / "bin" / "python"

    def check_initial_status(self):
        """检查初始状态"""
        self.update_status()
        self.log("启动器已就绪", "success")

    def check_environment(self):
        """检查环境"""
        self.log("正在检查环境...", "info")

        # 检查 Python
        version = sys.version.split()[0]
        self.log(f"✓ Python 版本: {version}", "success")

        # 检查虚拟环境
        venv_dir = self.project_dir / "venv"
        if venv_dir.exists():
            self.log("✓ 虚拟环境已存在", "success")
        else:
            self.log("✗ 虚拟环境不存在，需要创建", "warning")

        # 检查 Gemini CLI
        try:
            result = subprocess.run(
                ["gemini", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.log(f"✓ Gemini CLI: {result.stdout.strip()}", "success")
            else:
                self.log("✗ Gemini CLI 未正确安装", "error")
        except FileNotFoundError:
            self.log("✗ Gemini CLI 未找到", "error")

        # 检查端口
        if self.check_port(self.api_port):
            self.log(f"⚠ 端口 {self.api_port} 已被占用", "warning")
        else:
            self.log(f"✓ 端口 {self.api_port} 可用", "success")

        self.log("环境检查完成", "info")

    def force_kill_port(self):
        """强制清理端口"""
        self.log(f"正在清理端口 {self.api_port}...", "info")

        system = platform.system()

        try:
            if system == "Darwin" or system == "Linux":
                cmd = f"lsof -ti:{self.api_port}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        os.kill(int(pid), signal.SIGKILL)
                        self.log(f"✓ 已关闭进程 PID {pid}", "success")
                    time.sleep(1)
                else:
                    self.log(f"端口 {self.api_port} 未被占用", "info")

            self.update_status()
            self.log("端口清理完成", "success")

        except Exception as e:
            self.log(f"清理端口时出错: {e}", "error")

    def start_services_thread(self):
        """启动服务（在后台线程中）"""
        try:
            self.log("=" * 60, "info")
            self.log("开始启动服务...", "info")
            self.progress.start()

            # 检查虚拟环境
            venv_dir = self.project_dir / "venv"
            if not venv_dir.exists():
                self.log("虚拟环境不存在，正在创建...", "warning")
                subprocess.run([sys.executable, "-m", "venv", str(venv_dir)])
                self.log("✓ 虚拟环境创建成功", "success")

                # 安装依赖
                self.log("正在安装依赖...", "info")
                python_exe = self.get_venv_python()
                subprocess.run([
                    str(python_exe), "-m", "pip", "install",
                    "-r", str(self.project_dir / "requirements.txt")
                ])
                self.log("✓ 依赖安装完成", "success")

            python_exe = self.get_venv_python()

            # 清理端口
            self.force_kill_port()

            # 启动 API Server
            self.log("启动 API Server...", "info")
            api_log = self.log_dir / "api.log"
            self.api_process = subprocess.Popen(
                [
                    str(python_exe), "-m", "uvicorn",
                    "src.api.main:app",
                    "--host", "0.0.0.0",
                    "--port", str(self.api_port),
                    "--reload"
                ],
                cwd=str(self.project_dir),
                stdout=open(api_log, 'w'),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )

            # 启动 Worker
            self.log("启动 Worker...", "info")
            worker_log = self.log_dir / "worker.log"
            self.worker_process = subprocess.Popen(
                [str(python_exe), "-m", "src.worker.main"],
                cwd=str(self.project_dir),
                stdout=open(worker_log, 'w'),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )

            # 保存 PID
            with open(self.pid_file, 'w') as f:
                f.write(f"{self.api_process.pid}\n{self.worker_process.pid}\n")

            # 等待服务启动
            self.log("等待服务启动...", "info")
            for attempt in range(30):
                time.sleep(1)
                if self.check_port(self.api_port):
                    self.log(f"✓ 服务启动成功！（用时 {attempt + 1} 秒）", "success")
                    time.sleep(2)  # 再等待 2 秒确保完全启动
                    break
                if attempt % 5 == 0 and attempt > 0:
                    self.log(f"  等待中... ({attempt}/30 秒)", "info")
            else:
                self.log("⚠ 服务启动超时，请检查日志", "warning")
                self.progress.stop()
                return

            self.log("=" * 60, "info")
            self.log("服务启动完成！", "success")
            self.log(f"🌐 用户端: http://localhost:{self.api_port}", "success")
            self.log(f"📚 API 文档: http://localhost:{self.api_port}/docs", "success")
            self.log("=" * 60, "info")

            self.progress.stop()
            self.update_status()

            # 询问是否打开浏览器
            if messagebox.askyesno("启动成功", "服务已启动！是否打开浏览器？"):
                self.open_browser()

        except Exception as e:
            self.log(f"启动失败: {e}", "error")
            self.progress.stop()

    def start_services(self):
        """启动服务"""
        # 在后台线程中启动
        threading.Thread(target=self.start_services_thread, daemon=True).start()

    def stop_services(self):
        """停止服务"""
        self.log("正在停止服务...", "info")

        if self.pid_file.exists():
            with open(self.pid_file, 'r') as f:
                pids = [int(line.strip()) for line in f if line.strip()]

            for pid in pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                    self.log(f"✓ 已停止进程 PID {pid}", "success")
                except ProcessLookupError:
                    self.log(f"进程 PID {pid} 不存在", "warning")
                except Exception as e:
                    self.log(f"停止进程 PID {pid} 失败: {e}", "error")

            self.pid_file.unlink()

        # 强制清理端口
        self.force_kill_port()

        self.update_status()
        self.log("服务已停止", "success")

    def restart_services(self):
        """重启服务"""
        self.log("正在重启服务...", "info")
        self.stop_services()
        time.sleep(2)
        self.start_services()

    def open_browser(self):
        """打开浏览器"""
        url = f"http://localhost:{self.api_port}"
        self.log(f"正在打开浏览器: {url}", "info")
        webbrowser.open(url)

    def on_closing(self):
        """关闭窗口时"""
        if self.is_running:
            if messagebox.askyesno("确认", "服务正在运行，确定要退出吗？\n（服务将继续在后台运行）"):
                self.root.destroy()
        else:
            self.root.destroy()

    def run(self):
        """运行主循环"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()


if __name__ == "__main__":
    app = LauncherGUI()
    app.run()
