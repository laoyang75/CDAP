#!/usr/bin/env python3
"""
CDID 数据分析平台启动器

功能：
- 一键启动/关闭服务
- 自动打开浏览器
- 强制关闭（避免端口锁死）
- 环境检查
"""

import os
import sys
import time
import signal
import subprocess
import platform
import webbrowser
from pathlib import Path


class Launcher:
    """启动器类"""

    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.api_port = 8000
        self.pid_file = self.project_dir / ".launcher.pid"
        self.log_dir = self.project_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)

    def print_banner(self):
        """打印欢迎横幅"""
        banner = """
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║           CDID 数据分析平台 - 启动器 v1.0                     ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
        """
        print(banner)

    def check_port(self, port):
        """检查端口是否被占用"""
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0

    def kill_process_on_port(self, port):
        """强制关闭占用指定端口的进程"""
        print(f"🔍 检查端口 {port} 是否被占用...")

        system = platform.system()

        try:
            if system == "Darwin" or system == "Linux":
                # macOS 和 Linux
                cmd = f"lsof -ti:{port}"
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True
                )

                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        print(f"⚠️  发现进程 PID {pid} 占用端口 {port}，正在关闭...")
                        os.kill(int(pid), signal.SIGKILL)
                    time.sleep(1)
                    print(f"✅ 端口 {port} 已释放")
                else:
                    print(f"✅ 端口 {port} 未被占用")

            elif system == "Windows":
                # Windows
                cmd = f"netstat -ano | findstr :{port}"
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True
                )

                if result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        parts = line.split()
                        if len(parts) > 4:
                            pid = parts[-1]
                            print(f"⚠️  发现进程 PID {pid} 占用端口 {port}，正在关闭...")
                            subprocess.run(f"taskkill /F /PID {pid}", shell=True)
                    time.sleep(1)
                    print(f"✅ 端口 {port} 已释放")
                else:
                    print(f"✅ 端口 {port} 未被占用")

        except Exception as e:
            print(f"⚠️  检查端口时出错: {e}")

    def check_python_version(self):
        """检查 Python 版本"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            print(f"❌ Python 版本过低: {sys.version}")
            print(f"   需要 Python 3.9+")
            return False
        if version.minor < 11:
            print(f"⚠️  Python 版本: {sys.version.split()[0]} (推荐 3.11+)")
        else:
            print(f"✅ Python 版本: {sys.version.split()[0]}")
        return True

    def check_venv(self):
        """检查并创建虚拟环境"""
        venv_dir = self.project_dir / "venv"

        if not venv_dir.exists():
            print("📦 虚拟环境不存在，正在创建...")
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)])
            print("✅ 虚拟环境创建成功")
            return False  # 需要安装依赖
        else:
            print("✅ 虚拟环境已存在")
            return True

    def get_venv_python(self):
        """获取虚拟环境的 Python 路径"""
        venv_dir = self.project_dir / "venv"

        if platform.system() == "Windows":
            return venv_dir / "Scripts" / "python.exe"
        else:
            return venv_dir / "bin" / "python"

    def install_dependencies(self):
        """安装依赖"""
        print("📦 正在安装依赖...")

        python_exe = self.get_venv_python()
        requirements = self.project_dir / "requirements.txt"

        if not requirements.exists():
            print("❌ requirements.txt 不存在")
            return False

        cmd = [str(python_exe), "-m", "pip", "install", "-r", str(requirements)]
        result = subprocess.run(cmd)

        if result.returncode == 0:
            print("✅ 依赖安装成功")
            return True
        else:
            print("❌ 依赖安装失败")
            return False

    def check_gemini_cli(self):
        """检查 Gemini CLI"""
        try:
            result = subprocess.run(
                ["gemini", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✅ Gemini CLI: {version}")
                return True
            else:
                print("❌ Gemini CLI 未正确安装")
                return False

        except FileNotFoundError:
            print("❌ Gemini CLI 未找到")
            print("   请安装: npm install -g @google/generative-ai-cli")
            return False
        except Exception as e:
            print(f"❌ 检查 Gemini CLI 时出错: {e}")
            return False

    def setup_gemini_skill(self):
        """设置 Gemini Skill（使用内置的 report skill）"""
        print("\n📝 配置 Gemini Skill...")

        # 检查 Gemini 自带的 report skill
        try:
            result = subprocess.run(
                ["gemini", "skills", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if "report" in result.stdout:
                print("✅ 找到 Gemini 内置 report skill")

                # 更新配置文件，使用 report skill
                config_file = self.project_dir / "config" / "config.yaml"
                if config_file.exists():
                    import yaml

                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)

                    config['gemini']['skill_name'] = 'report'
                    config['gemini']['skill_path'] = 'built-in'

                    with open(config_file, 'w', encoding='utf-8') as f:
                        yaml.dump(config, f, allow_unicode=True)

                    print("✅ 已更新配置为使用 Gemini 内置 report skill")

                return True
            else:
                print("⚠️  未找到 Gemini 内置 report skill")
                print("   可用的 skills:")
                print(result.stdout)
                return False

        except Exception as e:
            print(f"⚠️  配置 Gemini Skill 时出错: {e}")
            return False

    def initialize_database(self):
        """初始化数据库"""
        print("\n💾 初始化数据库...")

        python_exe = self.get_venv_python()

        # 创建一个简单的数据库初始化脚本
        init_script = """
import sys
sys.path.insert(0, '.')
from src.config import get_config
from src.db import get_engine

config = get_config()
engine = get_engine(config)
print("✅ 数据库初始化成功")
"""

        result = subprocess.run(
            [str(python_exe), "-c", init_script],
            cwd=str(self.project_dir),
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(result.stdout.strip())
            return True
        else:
            print(f"❌ 数据库初始化失败: {result.stderr}")
            return False

    def start_services(self):
        """启动服务"""
        print("\n🚀 启动服务...\n")

        python_exe = self.get_venv_python()

        # 启动 API Server（后台）
        print("📡 启动 API Server...")
        api_log = self.log_dir / "api.log"
        api_proc = subprocess.Popen(
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

        # 启动 Worker（后台）
        print("⚙️  启动 Worker...")
        worker_log = self.log_dir / "worker.log"
        worker_proc = subprocess.Popen(
            [str(python_exe), "-m", "src.worker.main"],
            cwd=str(self.project_dir),
            stdout=open(worker_log, 'w'),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )

        # 保存 PID
        with open(self.pid_file, 'w') as f:
            f.write(f"{api_proc.pid}\n{worker_proc.pid}\n")

        # 等待服务启动
        print("\n⏳ 等待服务启动...")
        for attempt in range(30):  # 增加等待时间到 30 秒
            time.sleep(1)
            if self.check_port(self.api_port):
                print(f"✅ 服务启动成功！（用时 {attempt + 1} 秒）\n")
                # 再等待 2 秒确保完全启动
                time.sleep(2)
                break
            if attempt % 5 == 0:
                print(f"   等待中... ({attempt + 1}/30 秒)")
        else:
            print("⚠️  服务启动超时，请检查日志")
            print("   提示：可以尝试选择菜单项 7 查看日志")
            return False

        # 打印信息
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║  服务已启动                                                    ║")
        print("╠════════════════════════════════════════════════════════════════╣")
        print(f"║  🌐 用户端:     http://localhost:{self.api_port}                    ║")
        print(f"║  📚 API 文档:   http://localhost:{self.api_port}/docs              ║")
        print(f"║  📊 API Server: PID {api_proc.pid}                                  ║")
        print(f"║  ⚙️  Worker:     PID {worker_proc.pid}                                  ║")
        print("╠════════════════════════════════════════════════════════════════╣")
        print(f"║  📝 API 日志:   {api_log}                  ║")
        print(f"║  📝 Worker 日志: {worker_log}               ║")
        print("╚════════════════════════════════════════════════════════════════╝")

        return True

    def open_browser(self):
        """打开浏览器"""
        print("\n🌐 正在打开浏览器...")
        time.sleep(2)
        webbrowser.open(f"http://localhost:{self.api_port}")

    def stop_services(self):
        """停止服务"""
        print("\n🛑 停止服务...\n")

        if self.pid_file.exists():
            with open(self.pid_file, 'r') as f:
                pids = [int(line.strip()) for line in f if line.strip()]

            for pid in pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                    print(f"✅ 已停止进程 PID {pid}")
                except ProcessLookupError:
                    print(f"⚠️  进程 PID {pid} 不存在")
                except Exception as e:
                    print(f"❌ 停止进程 PID {pid} 失败: {e}")

            self.pid_file.unlink()

        # 强制清理端口
        self.kill_process_on_port(self.api_port)

        print("\n✅ 服务已停止")

    def show_status(self):
        """显示状态"""
        print("\n📊 服务状态:\n")

        if self.pid_file.exists():
            with open(self.pid_file, 'r') as f:
                pids = [int(line.strip()) for line in f if line.strip()]

            for pid in pids:
                try:
                    os.kill(pid, 0)  # 检查进程是否存在
                    print(f"✅ 进程 PID {pid} 正在运行")
                except ProcessLookupError:
                    print(f"❌ 进程 PID {pid} 已停止")
        else:
            print("ℹ️  服务未运行")

        if self.check_port(self.api_port):
            print(f"✅ 端口 {self.api_port} 已占用（服务运行中）")
        else:
            print(f"ℹ️  端口 {self.api_port} 未占用")

    def show_menu(self):
        """显示菜单"""
        menu = """
╔════════════════════════════════════════════════════════════════╗
║  请选择操作：                                                  ║
╠════════════════════════════════════════════════════════════════╣
║  1. 🚀 启动服务                                                ║
║  2. 🛑 停止服务                                                ║
║  3. 🔄 重启服务                                                ║
║  4. 🌐 打开浏览器                                              ║
║  5. 📊 查看状态                                                ║
║  6. 💪 强制清理端口                                            ║
║  7. 📝 查看日志                                                ║
║  0. 🚪 退出                                                    ║
╚════════════════════════════════════════════════════════════════╝
        """
        print(menu)

    def view_logs(self):
        """查看日志"""
        print("\n📝 最近的日志:\n")

        api_log = self.log_dir / "api.log"
        worker_log = self.log_dir / "worker.log"

        if api_log.exists():
            print("=== API Server 日志 (最后 20 行) ===")
            with open(api_log, 'r') as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    print(line.rstrip())

        print("\n")

        if worker_log.exists():
            print("=== Worker 日志 (最后 20 行) ===")
            with open(worker_log, 'r') as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    print(line.rstrip())

    def run(self):
        """主运行函数"""
        self.print_banner()

        # 环境检查
        print("🔍 环境检查...\n")

        if not self.check_python_version():
            return

        venv_exists = self.check_venv()

        if not venv_exists or not (self.project_dir / "venv" / "lib").exists():
            if not self.install_dependencies():
                return

        if not self.check_gemini_cli():
            print("\n⚠️  请先安装 Gemini CLI:")
            print("   npm install -g @google/generative-ai-cli")
            return

        # 配置 Gemini Skill
        self.setup_gemini_skill()

        # 初始化数据库
        self.initialize_database()

        # 交互式菜单
        while True:
            self.show_menu()
            choice = input("\n请输入选项 (0-7): ").strip()

            if choice == '1':
                self.kill_process_on_port(self.api_port)
                if self.start_services():
                    self.open_browser()
            elif choice == '2':
                self.stop_services()
            elif choice == '3':
                self.stop_services()
                time.sleep(2)
                self.kill_process_on_port(self.api_port)
                if self.start_services():
                    self.open_browser()
            elif choice == '4':
                self.open_browser()
            elif choice == '5':
                self.show_status()
            elif choice == '6':
                self.kill_process_on_port(self.api_port)
            elif choice == '7':
                self.view_logs()
            elif choice == '0':
                print("\n👋 再见！")
                break
            else:
                print("\n❌ 无效选项，请重新选择")

            input("\n按回车键继续...")


if __name__ == "__main__":
    launcher = Launcher()
    try:
        launcher.run()
    except KeyboardInterrupt:
        print("\n\n🛑 检测到中断信号...")
        launcher.stop_services()
        print("👋 再见！")
