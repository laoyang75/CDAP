# CDID 数据分析平台

CDID Data Analysis Platform - 完整版（用户端 + 管理端）

---

## ⚠️ 重要提示

**请使用 Web 启动器，不要使用 GUI 启动器（会崩溃）**

```bash
./run_web.sh
```

详见：[⚠️重要-请勿使用GUI启动器.md](./⚠️重要-请勿使用GUI启动器.md)

---

## 功能特性

### 用户端
- 📤 **任务创建**: 上传 CDID 数据文件，创建分析任务
- 📊 **任务列表**: 查看所有任务及其状态
- 🔍 **任务详情**: 实时查看任务进度和详细信息
- 📑 **报告下载**: 下载 HTML 格式的分析报告

### 管理端
- 👥 **用户管理**: 用户 CRUD 操作，角色管理
- ⚙️ **配置管理**: 系统配置参数管理
- 📈 **任务监控**: 实时任务统计和监控
- 🔄 **流程管理**: 自定义分析流程配置
- 📝 **脚本编辑**: Python 分析脚本在线编辑

## 技术栈

- **后端框架**: FastAPI
- **数据库**: SQLite (可升级到 PostgreSQL)
- **数据分析**: Pandas
- **报告生成**: Gemini CLI
- **认证**: JWT + bcrypt
- **前端**: Bootstrap 5 + Vanilla JS

## 🚀 快速开始（推荐）

### 使用 Web 启动器

```bash
./run_web.sh
```

启动后会自动打开浏览器访问 http://localhost:5555，在界面中点击"启动服务"即可。

**详细使用说明**: 查看 `启动器说明.md`

---

## 📋 前置要求

- Python 3.9+（推荐 3.11+）
- Gemini CLI 0.25.2+
- 内网访问权限（访问 http://172.17.129.204:6829）

**注意**：Web 启动器会自动检查和配置环境。

---

## 🛠️ 手动安装（可选）

如果需要手动安装：

1. 创建虚拟环境
\`\`\`bash
python3 -m venv venv
source venv/bin/activate
\`\`\`

2. 安装依赖
\`\`\`bash
pip install -r requirements.txt
\`\`\`

3. 部署 Gemini CLI Skill
\`\`\`bash
mkdir -p ~/.gemini/skills/duofa-panduan
cp skills/duofa-panduan/SKILL.md ~/.gemini/skills/duofa-panduan/
\`\`\`

---

## 🚀 启动方式

### 方式 1: Web 启动器（推荐）⭐

\`\`\`bash
./run_web.sh
\`\`\`

### 方式 2: 命令行启动器

\`\`\`bash
python3 launcher.py
\`\`\`

### 方式 3: 直接启动（开发模式）

\`\`\`bash
./dev.sh
\`\`\`

### 方式 4: Docker 部署

\`\`\`bash
docker-compose up -d
\`\`\`

---

## 🌐 访问应用

- **Web 启动器**: http://localhost:5555 （管理服务）
- **用户端**: http://localhost:8000 （主应用）
- **API 文档**: http://localhost:8000/docs

---

## 🔐 默认管理员账户

- **用户名**: admin
- **密码**: admin123

⚠️ **重要**: 首次登录后请立即修改密码！

---

## 📚 文档

**查看完整文档索引**: [docs/INDEX.md](docs/INDEX.md)

### 快速链接
- [快速启动指南](docs/guides/快速启动指南.md) - 最快速的入门方式
- [启动器说明](docs/guides/启动器说明.md) - 三种启动器详细对比
- [问题修复总结](docs/fixes/问题修复总结.md) - 所有已修复问题

### 开发者
- [HANDOFF_TO_AGENT.md](HANDOFF_TO_AGENT.md) - 🔴 项目移交文档（代码审计）

---

## 🔧 诊断工具

运行性能诊断：

```bash
source venv/bin/activate
python3 diagnose.py
```

---

## 📁 端口说明

- **8000** - 主应用端口（API + 用户界面）
- **5555** - Web 启动器端口（管理界面）

---

## ❓ 常见问题

### Q: tkinter 报错怎么办？

如果遇到：
```
macOS 26 (2602) or later required, have instead 16 (1602) !
Abort trap: 6
```

请使用 **Web 启动器** 代替：
```bash
./run_web.sh
```

### Q: 页面加载慢？

✅ **已解决！** 最新版本已优化，页面加载 < 200ms。

详见：`性能优化报告.md`

### Q: 如何停止服务？

使用 Web 启动器 (http://localhost:5555)，点击"停止服务"按钮。

---

## 许可证

MIT License
