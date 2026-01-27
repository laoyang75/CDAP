#!/usr/bin/env python3
"""
Web版启动器 - 基于 Flask 的图形化启动器
解决 tkinter 兼容性问题
"""

import os
import sys
import time
import subprocess
import signal
import socket
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# 全局状态
launcher_state = {
    'api_running': False,
    'worker_running': False,
    'port_occupied': False,
    'logs': [],
    'project_dir': Path(__file__).parent,
    'api_port': 8000,
    'launcher_port': 5555,
    'pid_file': Path(__file__).parent / '.launcher.pid'
}


# HTML 模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CDID 数据分析平台启动器</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 900px;
            width: 100%;
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 14px;
            opacity: 0.9;
        }

        .status-section {
            padding: 30px;
            border-bottom: 1px solid #e0e0e0;
        }

        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }

        .status-item {
            padding: 15px;
            background: #f5f5f5;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        .status-indicator.running {
            background: #4caf50;
            box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
        }

        .status-indicator.stopped {
            background: #9e9e9e;
        }

        .status-indicator.occupied {
            background: #ff9800;
            box-shadow: 0 0 10px rgba(255, 152, 0, 0.5);
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .controls-section {
            padding: 30px;
            border-bottom: 1px solid #e0e0e0;
        }

        .button-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }

        .btn {
            padding: 15px 20px;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-danger {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }

        .btn-warning {
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            color: #333;
        }

        .btn-info {
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            color: #333;
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .logs-section {
            padding: 30px;
            background: #f9f9f9;
        }

        .logs-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .logs-container {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 10px;
            height: 300px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.6;
        }

        .log-entry {
            margin-bottom: 5px;
        }

        .log-time {
            color: #858585;
        }

        .log-success {
            color: #4ec9b0;
        }

        .log-error {
            color: #f48771;
        }

        .log-warning {
            color: #dcdcaa;
        }

        .log-info {
            color: #d4d4d4;
        }

        .progress-bar {
            width: 100%;
            height: 4px;
            background: #e0e0e0;
            border-radius: 2px;
            overflow: hidden;
            margin: 15px 0;
        }

        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s;
        }

        .progress-bar.active .progress-bar-fill {
            animation: progress 2s infinite;
        }

        @keyframes progress {
            0% { width: 0%; }
            50% { width: 100%; }
            100% { width: 0%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 CDID 数据分析平台</h1>
            <p>Web 图形化启动器 v2.0</p>
        </div>

        <div class="status-section">
            <h3 style="margin-bottom: 20px;">服务状态</h3>
            <div class="status-grid">
                <div class="status-item">
                    <div class="status-indicator" id="api-status"></div>
                    <div>
                        <div style="font-weight: 600;">API Server</div>
                        <div style="font-size: 12px; color: #666;" id="api-text">未启动</div>
                    </div>
                </div>
                <div class="status-item">
                    <div class="status-indicator" id="worker-status"></div>
                    <div>
                        <div style="font-weight: 600;">Worker</div>
                        <div style="font-size: 12px; color: #666;" id="worker-text">未启动</div>
                    </div>
                </div>
                <div class="status-item">
                    <div class="status-indicator" id="port-status"></div>
                    <div>
                        <div style="font-weight: 600;">端口 8000</div>
                        <div style="font-size: 12px; color: #666;" id="port-text">空闲</div>
                    </div>
                </div>
            </div>
            <div class="progress-bar" id="progress-bar">
                <div class="progress-bar-fill"></div>
            </div>
        </div>

        <div class="controls-section">
            <h3 style="margin-bottom: 20px;">控制面板</h3>
            <div class="button-grid">
                <button class="btn btn-primary" onclick="startServices()">
                    🚀 启动服务
                </button>
                <button class="btn btn-danger" onclick="stopServices()">
                    🛑 停止服务
                </button>
                <button class="btn btn-warning" onclick="restartServices()">
                    🔄 重启服务
                </button>
                <button class="btn btn-info" onclick="openBrowser()">
                    🌐 打开用户端
                </button>
                <button class="btn btn-info" onclick="openAdmin()">
                    🔐 打开管理后台
                </button>
                <button class="btn btn-info" onclick="checkEnv()">
                    🔍 检查环境
                </button>
                <button class="btn btn-danger" onclick="killPort()">
                    💪 清理端口
                </button>
            </div>
        </div>

        <div class="logs-section">
            <div class="logs-header">
                <h3>运行日志</h3>
                <button class="btn btn-info" onclick="clearLogs()" style="padding: 8px 15px; font-size: 12px;">
                    📝 清空日志
                </button>
            </div>
            <div class="logs-container" id="logs"></div>
        </div>
    </div>

    <script>
        function updateStatus() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    // Update API status
                    document.getElementById('api-status').className =
                        'status-indicator ' + (data.api_running ? 'running' : 'stopped');
                    document.getElementById('api-text').textContent =
                        data.api_running ? '运行中' : '未启动';

                    // Update Worker status
                    document.getElementById('worker-status').className =
                        'status-indicator ' + (data.worker_running ? 'running' : 'stopped');
                    document.getElementById('worker-text').textContent =
                        data.worker_running ? '运行中' : '未启动';

                    // Update Port status
                    const portStatus = document.getElementById('port-status');
                    const portText = document.getElementById('port-text');

                    if (data.api_running) {
                        portStatus.className = 'status-indicator running';
                        portText.textContent = '监听中';
                    } else if (data.port_occupied) {
                        portStatus.className = 'status-indicator occupied';
                        portText.textContent = '被其他进程占用';
                    } else {
                        portStatus.className = 'status-indicator stopped';
                        portText.textContent = '空闲';
                    }
                });
        }

        function updateLogs() {
            fetch('/api/logs')
                .then(r => r.json())
                .then(data => {
                    const logsDiv = document.getElementById('logs');
                    logsDiv.innerHTML = data.logs.map(log => {
                        const className = log.level === 'success' ? 'log-success' :
                                        log.level === 'error' ? 'log-error' :
                                        log.level === 'warning' ? 'log-warning' : 'log-info';
                        return `<div class="log-entry">` +
                               `<span class="log-time">[${log.time}]</span> ` +
                               `<span class="${className}">${log.message}</span>` +
                               `</div>`;
                    }).join('');
                    logsDiv.scrollTop = logsDiv.scrollHeight;
                });
        }

        function showProgress() {
            document.getElementById('progress-bar').classList.add('active');
        }

        function hideProgress() {
            document.getElementById('progress-bar').classList.remove('active');
        }

        function startServices() {
            showProgress();
            fetch('/api/start', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    hideProgress();
                    updateStatus();
                    updateLogs();
                });
        }

        function stopServices() {
            showProgress();
            fetch('/api/stop', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    hideProgress();
                    updateStatus();
                    updateLogs();
                });
        }

        function restartServices() {
            showProgress();
            fetch('/api/restart', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    hideProgress();
                    updateStatus();
                    updateLogs();
                });
        }

        function openBrowser() {
            fetch('/api/open-browser', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    updateLogs();
                });
        }

        function openAdmin() {
            fetch('/api/open-admin', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    updateLogs();
                });
        }

        function checkEnv() {
            showProgress();
            fetch('/api/check-env', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    hideProgress();
                    updateLogs();
                });
        }

        function killPort() {
            showProgress();
            fetch('/api/kill-port', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    hideProgress();
                    updateStatus();
                    updateLogs();
                });
        }

        function clearLogs() {
            fetch('/api/clear-logs', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    updateLogs();
                });
        }

        // Auto update every 2 seconds
        setInterval(() => {
            updateStatus();
            updateLogs();
        }, 2000);

        // Initial update
        updateStatus();
        updateLogs();
    </script>
</body>
</html>
'''


def add_log(message, level='info'):
    """添加日志"""
    timestamp = time.strftime('%H:%M:%S')
    launcher_state['logs'].append({
        'time': timestamp,
        'message': message,
        'level': level
    })
    # 只保留最近 100 条
    if len(launcher_state['logs']) > 100:
        launcher_state['logs'] = launcher_state['logs'][-100:]


def check_port(port):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port)) == 0
    sock.close()
    return result


def check_process_running(process_name):
    """检查进程是否运行"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', process_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False


def update_status():
    """更新服务状态"""
    launcher_state['api_running'] = check_process_running('uvicorn src.api.main:app')
    launcher_state['worker_running'] = check_process_running('src.worker.main')
    launcher_state['port_occupied'] = check_port(launcher_state['api_port'])


def kill_port_process(port):
    """强制关闭占用端口的进程"""
    try:
        # macOS/Linux
        result = subprocess.run(
            f"lsof -ti:{port} | xargs kill -9 2>/dev/null",
            shell=True,
            capture_output=True
        )
        return True
    except:
        return False


def start_service_process(cmd, log_file):
    """启动服务进程"""
    # 激活虚拟环境并运行
    activate = f"source {launcher_state['project_dir']}/venv/bin/activate"
    full_cmd = f"{activate} && {cmd}"

    # 使用追加模式打开日志文件，保留历史日志
    log_handle = open(log_file, 'a')

    # 写入启动分隔符
    import datetime
    log_handle.write(f"\n{'='*60}\n")
    log_handle.write(f"服务启动时间: {datetime.datetime.now()}\n")
    log_handle.write(f"{'='*60}\n")
    log_handle.flush()

    process = subprocess.Popen(
        full_cmd,
        shell=True,
        executable='/bin/bash',
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        cwd=str(launcher_state['project_dir'])
    )
    return process


@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/status')
def api_status():
    """获取状态"""
    update_status()
    return jsonify({
        'api_running': launcher_state['api_running'],
        'worker_running': launcher_state['worker_running'],
        'port_occupied': launcher_state['port_occupied']
    })


@app.route('/api/logs')
def api_logs():
    """获取日志"""
    return jsonify({'logs': launcher_state['logs']})


@app.route('/api/start', methods=['POST'])
def api_start():
    """启动服务"""
    add_log('开始启动服务...', 'info')

    # 检查并清理端口
    if check_port(launcher_state['api_port']):
        add_log('端口已被占用，正在清理...', 'warning')
        kill_port_process(launcher_state['api_port'])
        time.sleep(1)

    # 启动 Worker
    add_log('启动 Worker...', 'info')
    start_service_process(
        f'"{sys.executable}" -m src.worker.main',
        launcher_state['project_dir'] / 'logs' / 'worker.log'
    )
    time.sleep(1)

    # 启动 API Server
    add_log('启动 API Server...', 'info')
    start_service_process(
        f'"{sys.executable}" -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000',
        launcher_state['project_dir'] / 'logs' / 'api.log'
    )

    # 等待启动（增加到 30 秒）
    add_log('等待服务启动...', 'info')
    for i in range(30):
        time.sleep(1)
        if check_port(launcher_state['api_port']):
            add_log(f'✓ 服务启动成功！（用时 {i+1} 秒）', 'success')
            time.sleep(2)  # 额外等待确保完全启动
            break
        if i % 5 == 0 and i > 0:
            add_log(f'  等待中... ({i}秒)', 'info')
    else:
        add_log('⚠️ 服务启动超时（30秒）', 'warning')
        add_log('请查看日志文件: logs/api.log 和 logs/worker.log', 'warning')

        # 尝试读取最后几行日志
        try:
            api_log = launcher_state['project_dir'] / 'logs' / 'api.log'
            if api_log.exists():
                with open(api_log, 'r') as f:
                    lines = f.readlines()
                    last_lines = lines[-5:] if len(lines) > 5 else lines
                    for line in last_lines:
                        add_log(f'  API日志: {line.strip()}', 'error')
        except Exception:
            pass

    update_status()
    return jsonify({'success': True})


@app.route('/api/stop', methods=['POST'])
def api_stop():
    """停止服务"""
    add_log('正在停止服务...', 'info')

    # 停止 API Server
    subprocess.run(['pkill', '-f', 'uvicorn src.api.main:app'])
    # 停止 Worker
    subprocess.run(['pkill', '-f', 'src.worker.main'])

    time.sleep(2)
    add_log('✓ 服务已停止', 'success')
    update_status()
    return jsonify({'success': True})


@app.route('/api/restart', methods=['POST'])
def api_restart():
    """重启服务"""
    add_log('正在重启服务...', 'info')
    api_stop()
    time.sleep(2)
    api_start()
    return jsonify({'success': True})


@app.route('/api/open-browser', methods=['POST'])
def api_open_browser():
    """打开用户端"""
    add_log('正在打开用户端...', 'info')
    subprocess.run(['open', 'http://localhost:8000'])
    add_log('✓ 已打开用户端', 'success')
    return jsonify({'success': True})


@app.route('/api/open-admin', methods=['POST'])
def api_open_admin():
    """打开管理后台"""
    add_log('正在打开管理后台...', 'info')
    subprocess.run(['open', 'http://localhost:8000/admin'])
    add_log('✓ 已打开管理后台', 'success')
    return jsonify({'success': True})


@app.route('/api/check-env', methods=['POST'])
def api_check_env():
    """检查环境"""
    add_log('正在检查环境...', 'info')

    # 检查 Python
    try:
        result = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
        version = result.stdout.strip()
        add_log(f'✓ Python: {version}', 'success')
    except:
        add_log('✗ Python 检查失败', 'error')

    # 检查虚拟环境
    venv_dir = launcher_state['project_dir'] / 'venv'
    if venv_dir.exists():
        add_log('✓ 虚拟环境已存在', 'success')
    else:
        add_log('✗ 虚拟环境不存在', 'error')

    # 检查 Gemini CLI
    try:
        result = subprocess.run(['gemini', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            add_log(f'✓ Gemini CLI: {result.stdout.strip()}', 'success')
        else:
            add_log('✗ Gemini CLI 未安装', 'warning')
    except:
        add_log('✗ Gemini CLI 未安装', 'warning')

    return jsonify({'success': True})


@app.route('/api/kill-port', methods=['POST'])
def api_kill_port():
    """强制清理端口"""
    add_log(f'正在清理端口 {launcher_state["api_port"]}...', 'info')

    if kill_port_process(launcher_state['api_port']):
        add_log('✓ 端口已清理', 'success')
    else:
        add_log('⚠️ 端口清理可能失败', 'warning')

    time.sleep(1)
    update_status()
    return jsonify({'success': True})


@app.route('/api/clear-logs', methods=['POST'])
def api_clear_logs():
    """清空日志"""
    launcher_state['logs'].clear()
    add_log('启动器已就绪', 'info')
    return jsonify({'success': True})


def main():
    """主函数"""
    print("=" * 60)
    print("CDID 数据分析平台 - Web 启动器")
    print("=" * 60)
    print(f"\n启动器地址: http://localhost:{launcher_state['launcher_port']}")
    print(f"API 服务地址: http://localhost:{launcher_state['api_port']}")
    print("\n请在浏览器中打开启动器地址进行管理")
    print("\n按 Ctrl+C 停止启动器")
    print("=" * 60)
    print()

    # 初始化日志
    add_log('启动器已就绪', 'info')

    # 自动打开浏览器
    time.sleep(1)
    subprocess.Popen(['open', f'http://localhost:{launcher_state["launcher_port"]}'])

    # 启动 Flask
    app.run(
        host='0.0.0.0',
        port=launcher_state['launcher_port'],
        debug=False,
        use_reloader=False
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n启动器已退出")
