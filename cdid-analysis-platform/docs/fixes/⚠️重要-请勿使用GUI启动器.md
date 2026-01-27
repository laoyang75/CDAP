# ⚠️ 重要警告：请勿使用 GUI 启动器

## 问题说明

您的系统遇到了 **tkinter 兼容性问题**，运行 GUI 启动器会导致程序崩溃：

```
macOS 26 (2602) or later required, have instead 16 (1602) !
Abort trap: 6
```

**崩溃原因**：系统自带的 Python tkinter 库版本过旧，与当前 macOS 不兼容。

---

## ❌ 请勿运行以下命令

这些命令会导致系统崩溃：

```bash
# ❌ 不要运行
python3 launcher_gui.py

# ❌ 不要运行
./run_gui.sh

# ❌ 不要运行
python3 launcher_gui_safe.py  # 虽然名字是 safe，但检测后会退出
```

---

## ✅ 正确的启动方式

### 使用 Web 启动器（强烈推荐）⭐

```bash
./run_web.sh
```

**或者**：

```bash
source venv/bin/activate
python3 launcher_web.py
```

### 特点

- ✅ **无兼容性问题** - 不依赖 tkinter
- ✅ **美观界面** - 现代化渐变色设计
- ✅ **功能完整** - 所有 GUI 功能都有
- ✅ **实时监控** - 自动刷新状态
- ✅ **彩色日志** - 更易读

### 访问地址

启动后浏览器会自动打开：**http://localhost:5555**

---

## 📋 其他启动方式

### 命令行启动器

```bash
python3 launcher.py
```

适合不需要图形界面的场景。

### 直接启动服务

```bash
./dev.sh
```

开发模式，服务直接在前台运行。

---

## 🔍 为什么会崩溃？

从崩溃报告可以看到：

```
4   Tk  0x2448e4730 TkpInit + 452
...
Termination Reason: Namespace SIGNAL, Code 6, Abort trap: 6
Application Specific Information:
abort() called
```

这是 Tk 库在初始化时（`TkpInit`）检测到版本不匹配，主动调用 `abort()` 终止程序。

系统 Tk 版本：**8.5.9** (2010年发布)
需要的版本：**macOS 26 (2602) 或更高**

您的系统 Tk 版本太旧，无法在当前 macOS 上正常工作。

---

## 🛠️ 如何修复？

**不建议修复** tkinter 问题，因为：

1. 需要重新编译 Python + tkinter（复杂且耗时）
2. 可能影响系统稳定性
3. Web 启动器已经提供了完美的替代方案

**推荐方案**：直接使用 Web 启动器。

---

## 📊 功能对比

| 功能 | GUI 启动器 | Web 启动器 |
|------|-----------|-----------|
| 兼容性 | ❌ 崩溃 | ✅ 完美 |
| 界面美观度 | ⚠️ 基础 | ✅ 现代化 |
| 实时刷新 | ✅ | ✅ |
| 彩色日志 | ⚠️ 简单 | ✅ 丰富 |
| 状态监控 | ✅ | ✅ |
| 浏览器访问 | ❌ | ✅ |
| 跨平台 | ❌ | ✅ |

---

## 🚀 立即开始

运行 Web 启动器：

```bash
./run_web.sh
```

然后在浏览器中（http://localhost:5555）：

1. 点击 "🚀 启动服务"
2. 等待 10-15 秒
3. 点击 "🌐 打开浏览器"
4. 开始使用平台

---

## 📞 需要帮助？

查看以下文档：

- **启动器说明.md** - 详细使用指南
- **问题修复总结.md** - 所有问题的解决方案
- **性能优化报告.md** - 性能优化详情

---

**请使用 Web 启动器，避免系统崩溃！** 🎉
