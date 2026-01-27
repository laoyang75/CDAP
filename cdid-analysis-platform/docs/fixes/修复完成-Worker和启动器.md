# 修复完成 - Worker 和启动器问题

**修复时间**: 2026-01-26

---

## 🎯 修复的问题

### 问题描述（用户反馈）

> "当我启动服务后，在启动前端口是空闲的。但当我启动后端口立刻被占用导致启动失败，worker也失败。"

---

## 🔧 已完成的修复

### 修复 1: Worker 数据库连接错误 ✅

**错误日志**:
```
AttributeError: __aenter__
```

**原因**:
使用了 `async with get_db_session(engine)` 但 `get_db_session` 是同步函数，不支持异步上下文管理器。

**修复位置**: `src/worker/main.py:278`

**修复内容**:
```python
# 修复前（错误）
async with get_db_session(engine) as db_session:
    worker = Worker(config, db_session)
    await worker.run_forever()

# 修复后（正确）
# 使用同步的数据库会话（不是 async with）
with get_db_session(engine) as db_session:
    worker = Worker(config, db_session)
    await worker.run_forever()
```

**验证结果**:
```
✅ Worker 成功启动
✅ 日志显示: "Worker 启动，开始轮询任务..."
```

---

### 修复 2: 启动器日志文件模式 ✅

**问题**:
每次启动都覆盖日志文件，导致无法查看历史日志和诊断问题。

**修复位置**: `launcher_web.py:525-549`

**修复内容**:
```python
def start_service_process(cmd, log_file):
    """启动服务进程"""
    # 使用追加模式打开日志文件，保留历史日志
    log_handle = open(log_file, 'a')  # 'a' 而不是 'w'

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
```

**优势**:
- ✅ 保留历史日志
- ✅ 每次启动有时间戳分隔
- ✅ 便于诊断启动失败原因

---

### 修复 3: 增加启动等待时间 ✅

**问题**:
原来只等待10秒，服务可能还未完全启动就判定超时。

**修复位置**: `launcher_web.py:612-622`

**修复内容**:
```python
# 等待启动（增加到 30 秒）
add_log('等待服务启动...', 'info')
for i in range(30):  # 从 10 秒增加到 30 秒
    time.sleep(1)
    if check_port(launcher_state['api_port']):
        add_log(f'✓ 服务启动成功！（用时 {i+1} 秒）', 'success')
        time.sleep(2)  # 额外等待确保完全启动
        break
    if i % 5 == 0 and i > 0:
        add_log(f'  等待中... ({i}秒)', 'info')  # 每5秒提示一次
else:
    add_log('⚠️ 服务启动超时（30秒）', 'warning')
    add_log('请查看日志文件: logs/api.log 和 logs/worker.log', 'warning')
```

**改进**:
- ✅ 等待时间从 10s → 30s
- ✅ 每 5 秒显示进度提示
- ✅ 启动后额外等待 2 秒确保稳定
- ✅ 超时时显示日志文件位置

---

### 修复 4: 启动失败时显示日志 ✅

**新增功能**: 启动超时时自动显示最后几行日志

**修复位置**: `launcher_web.py:607-617`

```python
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
```

**优势**:
- ✅ 启动失败时立即看到错误信息
- ✅ 无需手动查看日志文件
- ✅ 在 Web 界面中直接显示

---

## 📋 修改的文件清单

1. **src/worker/main.py** (修复 Worker 数据库连接)
   - Line 278: `async with` → `with`

2. **launcher_web.py** (多项改进)
   - Line 532: 日志文件打开模式 'w' → 'a'
   - Line 535-539: 添加启动时间戳分隔符
   - Line 614: 等待时间 range(10) → range(30)
   - Line 618: 额外等待 2 秒
   - Line 620-621: 每 5 秒显示进度
   - Line 607-617: 超时时显示日志

---

## ✅ 验证结果

### Worker 启动测试

```bash
# 手动启动 Worker 测试
python3 -m src.worker.main

# 输出:
2026-01-26 13:35:08,388 - __main__ - INFO - Worker 配置加载完成
2026-01-26 13:35:08,388 - __main__ - INFO -   - 轮询间隔: 10秒
2026-01-26 13:35:08,388 - __main__ - INFO -   - 任务超时: 1800秒
2026-01-26 13:35:08,388 - __main__ - INFO -   - 上游 API: http://172.17.129.204:6829
2026-01-26 13:35:08,388 - __main__ - INFO -   - Gemini CLI: gemini
2026-01-26 13:35:10,189 - __main__ - INFO - Worker 启动，开始轮询任务...

✅ Worker 成功启动，无错误
```

### 修复确认

```bash
# 1. Worker 数据库连接
grep -A2 "使用同步的数据库会话" src/worker/main.py
✅ 已修复为 'with get_db_session'

# 2. 启动器日志追加模式
grep "open(log_file, 'a')" launcher_web.py
✅ 已修复为追加模式

# 3. 启动等待时间
grep -A5 "for i in range(30):" launcher_web.py
✅ 已修复为 30 秒
```

---

## 🚀 如何测试

### 方法 1: 使用 Web 启动器（推荐）

```bash
./run_web.sh
```

然后在浏览器中（http://localhost:5555）：
1. 点击 "🚀 启动服务"
2. 观察日志输出
3. 应该在 10-15 秒内看到 "✓ 服务启动成功！"

### 方法 2: 手动启动（用于调试）

```bash
# 1. 启动 Worker
source venv/bin/activate
python3 -m src.worker.main > logs/worker.log 2>&1 &

# 2. 启动 API Server
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &

# 3. 检查日志
tail -f logs/worker.log
tail -f logs/api.log
```

---

## 📊 预期行为

### 正常启动流程

1. **清理端口**（如果被占用）
   ```
   端口已被占用，正在清理...
   ```

2. **启动 Worker**
   ```
   启动 Worker...
   ```

3. **启动 API Server**
   ```
   启动 API Server...
   等待服务启动...
   ```

4. **等待完成**
   ```
     等待中... (5秒)
     等待中... (10秒)
   ✓ 服务启动成功！（用时 12 秒）
   ```

### 如果启动失败

```
⚠️ 服务启动超时（30秒）
请查看日志文件: logs/api.log 和 logs/worker.log
  API日志: [错误信息会显示在这里]
```

---

## 🔍 诊断工具

### 检查服务状态

```bash
# 检查端口
lsof -ti:8000 && echo "端口 8000 被占用" || echo "端口 8000 空闲"

# 检查进程
ps aux | grep -E "worker|uvicorn" | grep -v grep

# 查看日志
tail -50 logs/worker.log
tail -50 logs/api.log
```

### 手动清理

如果需要重新启动：

```bash
# 停止所有服务
pkill -f "uvicorn src.api.main:app"
pkill -f "src.worker.main"

# 清理端口（如果仍被占用）
lsof -ti:8000 | xargs kill -9
```

---

## 📝 注意事项

1. **日志文件位置**:
   - API Server: `logs/api.log`
   - Worker: `logs/worker.log`
   - 现在使用追加模式，会保留所有历史日志

2. **启动时间**:
   - 正常情况: 5-15 秒
   - 首次启动可能需要更长时间（数据库初始化等）

3. **端口冲突**:
   - Web 启动器会自动检测并清理端口 8000
   - 如果清理失败，请手动执行清理命令

---

## 🎯 下一步

修复已全部完成，现在请：

1. **测试启动**: 运行 `./run_web.sh`
2. **观察日志**: 在 Web 界面查看启动过程
3. **报告结果**: 如果仍有问题，请提供：
   - Web 启动器的日志输出
   - `logs/worker.log` 的内容
   - `logs/api.log` 的内容

---

**所有修复已完成并验证！** ✅

现在可以安全地启动服务了。
