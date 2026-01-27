# 🚀 CDID 数据分析平台 - 开发启动 Prompt

**创建日期**: 2026-01-24
**用途**: 在具备开发环境后，使用此 prompt 启动项目实施

---

## 📌 项目概述

### 项目名称
CDID 数据分析平台（CDID Analysis Platform）

### 项目目标
将现有的 Gemini CLI 命令行工作流（数据获取 → Python 分析 → Gemini 报告生成）包装成 Web 服务，降低使用门槛，实现全自动化的数据分析流程。

### 核心价值
- ✅ **零门槛**: 浏览器操作，无需命令行技能
- ✅ **全自动**: 后端自动调用内网 API、执行分析、生成报告
- ✅ **可追溯**: 所有任务记录在数据库，支持历史查询
- ✅ **可扩展**: 管线化设计，方便添加新的分析逻辑
- ✅ **纯 Python**: 无需 Go 二进制，部署简单

---

## 📁 项目文档结构

```
D:\AI\Cursor\gupiao\data_fenxi\cdid-analysis-platform\
├── docs/
│   ├── final-requirements/                      # ⭐ 需求文档（必读）
│   │   ├── README.md                            # 文档导航
│   │   ├── 方案设计-v0.2.0.md                    # 完整系统设计
│   │   ├── 待确认问题清单-v0.2.0.md               # 技术细节问题
│   │   ├── _generated/
│   │   │   └── 最终方案-v0.2.0.md                # 收敛后的最终方案
│   │   └── ui-mockups/                          # ⭐ UI 原型（已完成，中文界面）
│   │       ├── user-create-task.html            # 创建任务页
│   │       ├── user-task-list.html              # 任务列表页
│   │       ├── user-task-detail.html            # 任务详情页
│   │       ├── admin-pipeline-management.html   # 管线管理
│   │       ├── admin-script-editor.html         # 脚本编辑
│   │       ├── admin-client-config.html         # 客户配置
│   │       ├── admin-user-management.html       # 用户管理
│   │       └── admin-task-monitoring.html       # 任务监控
│   └── plans/                                   # ⭐ 实施计划（已完成）
│       ├── 2026-01-24-cdid-analysis-platform-mvp.md         # 英文详细计划（含完整代码）
│       └── 2026-01-24-实施计划-中文概述.md                    # 中文方案概述
└── (项目代码将在这里生成)
```

---

## 🎯 核心功能（基于需求文档）

### 1. 管线（Pipeline）概念
- **定义**: Pipeline = Python 数据分析脚本 + Gemini Skill 报告生成
- **流程**: 用户创建任务 → 内网 API 获取数据 → Python 脚本分析 → Gemini 生成报告
- **状态**: `queued → fetching → analyzing → reporting → done/failed`

### 2. 用户功能（3 个页面）
1. **创建任务页** (`user-create-task.html`)
   - 客户名称检索（自动填充包名）
   - 管线选择下拉框
   - 时间范围选择（start/end 必填）
   - 数据类型选择（dna/daa 可选）
   - CDID 文件拖拽上传

2. **任务列表页** (`user-task-list.html`)
   - 筛选（状态、管线、搜索）
   - 实时进度条显示
   - 操作：查看详情、删除、重新运行

3. **任务详情页** (`user-task-detail.html`)
   - 基本信息展示
   - 执行流程时间轴
   - 报告展示（iframe 嵌入）
   - 下载按钮：原始数据（Excel）、HTML 报告

### 3. 管理功能（5 个页面）
1. **管线管理** - 配置 Python 脚本和 Gemini Skill
2. **脚本编辑** - 编辑分析脚本（不支持新建 Skill，只引用）
3. **客户配置** - 客户-包名映射管理（支持批量导入）
4. **用户管理** - 用户增删（权限对接现有接口）
5. **任务监控** - 查看所有任务、失败任务列表、错误日志

---

## 🏗️ 技术架构

### 技术栈
- **后端**: FastAPI + SQLAlchemy + httpx (async)
- **前端**: Jinja2 + Bootstrap 5 + Vanilla JavaScript（⚠️ **中文界面**）
- **数据库**: SQLite (MVP) → PostgreSQL (生产)
- **数据分析**: Pandas + Python 3.11+
- **报告生成**: Gemini CLI (subprocess + stdin pipe)
- **部署**: Docker + docker-compose

### 系统架构
```
用户浏览器
    ↓ HTTP
FastAPI Server (API + Web UI)
    ↓
Worker (后台任务处理)
    ↓
内网 API (172.17.129.204:6829) + Gemini CLI
```

### 数据库表
1. **jobs** - 任务表（状态、进度、文件路径）
2. **pipelines** - 管线配置（脚本目录、脚本文件、Skill 名称）
3. **clients** - 客户配置（客户名-包名映射）
4. **users** - 用户表（基本信息）

---

## 📋 实施计划（9 个任务）

### 任务清单（按顺序执行）
1. ✅ **数据库和配置** - 建立 SQLAlchemy 模型、连接管理、配置模块
2. ✅ **内网 API 客户端** - 封装 172.17.129.204:6829 的三个接口
3. ✅ **分析脚本模板** - 实现标准化的 `analyze()` 接口和动态加载
4. ✅ **Gemini 报告生成器** - subprocess 调用 CLI，stdin 传 JSON
5. ✅ **Worker 主循环** - 4 阶段处理（fetch → analyze → report → done）
6. ✅ **FastAPI 核心 API** - 任务 CRUD、报告下载、数据下载
7. ✅ **管线客户管理 API** - 配置管理、CSV 批量导入
8. ⭐ **Web UI 实现** - **基于 `docs/final-requirements/ui-mockups/` 的中文界面**
9. ✅ **Docker 部署配置** - Dockerfile + docker-compose

### 详细计划文档
- **英文版（含完整代码）**: `docs/plans/2026-01-24-cdid-analysis-platform-mvp.md`
- **中文版（方案概述）**: `docs/plans/2026-01-24-实施计划-中文概述.md`

---

## ⚠️ 重要说明

### 1. UI 界面语言
- **所有 UI 必须是中文**
- **参考文件**: `docs/final-requirements/ui-mockups/*.html`
- **不要使用英文界面**，包括：
  - 页面标题
  - 表单标签
  - 按钮文字
  - 提示信息
  - 错误消息
  - 导航菜单

### 2. UI 原型已完成
- **8 个 HTML 原型页面已经设计完成**
- **必须严格参考这些原型实现**：
  - 布局结构
  - 样式设计
  - 交互逻辑
  - 字段命名
  - 功能完整性

### 3. 内网 API 调用规范
- **Base URL**: `http://172.17.129.204:6829`
- **创建任务**: POST `/api/statistical-analysis/v1/task/create`
  - 必填：`start`, `end` (YYYY-MM-DD)
  - 可选：`message` (dna/daa，通过 multipart 重复字段传递)
- **查询状态**: GET `/api/statistical-analysis/v1/task/detail?task_id=xxx`
- **轮询间隔**: 建议 60 秒
- **超时时间**: 建议 ≥ 60 分钟

### 4. Gemini CLI 调用方式
```bash
cat analysis_result.json | gemini "@<skill_name> 根据以上JSON生成完整HTML报告，只输出HTML"
```
- **Skill/扩展管理边界**: 平台只引用 `@skill_name`，不负责安装/新建
- **输入格式**: JSON via stdin
- **输出格式**: HTML via stdout

### 5. Python 分析脚本标准接口
```python
def analyze(input_file: str, user_info: dict, start_date: str, end_date: str) -> dict:
    """
    参数：
        input_file: 原始数据文件路径（Excel）
        user_info: {'user_id': '...', 'task_id': '...'}
        start_date: YYYY-MM-DD
        end_date: YYYY-MM-DD
    返回：
        dict: 必须可 JSON 序列化
    """
```

### 6. MVP 范围限制
- ✅ 单线程 Worker（FIFO 队列）
- ✅ 本地文件存储
- ✅ SQLite 数据库
- ❌ 暂不集成现有权限系统（弱化登录鉴权）
- ❌ 暂不支持并发队列
- ❌ 暂不支持在 Web UI 中新建 Skill

---

## 🚀 开发启动命令

### 步骤 1: 阅读需求文档
```
请阅读以下文档以了解完整需求：
1. docs/final-requirements/README.md
2. docs/final-requirements/方案设计-v0.2.0.md
3. docs/final-requirements/_generated/最终方案-v0.2.0.md
4. docs/final-requirements/ui-mockups/ （所有 HTML 文件）
```

### 步骤 2: 审查实施计划
```
请阅读实施计划：
1. docs/plans/2026-01-24-实施计划-中文概述.md （方案总览）
2. docs/plans/2026-01-24-cdid-analysis-platform-mvp.md （详细步骤）
```

### 步骤 3: 执行实施计划
```
请按照以下方式执行实施计划：

⚠️ 重要提醒：
1. Web UI 必须是中文界面（参考 docs/final-requirements/ui-mockups/）
2. 严格按照 UI 原型的设计和布局实现
3. 所有提示信息、错误消息、按钮文字都使用中文

执行方式（二选一）：

【方式 A - 当前会话逐任务执行】（推荐）
使用 superpowers:subagent-driven-development 技能：
- 逐个任务调度专门的子代理
- 每个任务完成后进行代码审查
- 快速迭代，即时反馈
- 在当前工作目录执行

【方式 B - 新会话批量执行】
使用 superpowers:executing-plans 技能：
- 在新会话中批量执行
- 设置检查点进行审查
- 适合无打扰的持续执行

请开始执行实施计划，实现完整的 CDID 数据分析平台 MVP。
```

---

## 📝 待确认事项（不阻塞开发）

以下信息在开发过程中可以逐步补充：

1. **内网 API 细节**
   - QPS/并发限制
   - 典型任务耗时

2. **数据分析规则**
   - 风险表/异常口径的规则清单
   - raw_data.xlsx 的实际字段名清单

3. **客户数据**
   - 客户-包名映射数据文件（CSV/Excel）
   - 已知规模约 500 条

4. **Gemini Skill**
   - 可用的 Skill 列表
   - Skill 的输入输出格式要求

---

## 🎯 预期产出

执行完成后，将得到：

### 代码结构
```
cdid-analysis-platform/
├── src/
│   ├── api/                  # FastAPI 应用
│   │   ├── main.py
│   │   └── routes/
│   ├── worker/               # 后台 Worker
│   │   ├── main.py
│   │   ├── insight_client.py
│   │   ├── pipeline_executor.py
│   │   └── gemini_reporter.py
│   ├── scripts/              # 分析脚本
│   │   └── duplicate_detection/
│   ├── db/                   # 数据库
│   │   ├── models.py
│   │   └── connection.py
│   ├── ui/                   # Web UI（中文界面）
│   │   ├── templates/
│   │   └── static/
│   └── config.py
├── tests/                    # 测试文件
├── jobs/                     # 运行时目录
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### 功能验收
- [ ] 用户可通过浏览器创建任务（中文界面）
- [ ] 系统自动调用内网 API 获取数据
- [ ] Python 脚本自动分析数据
- [ ] Gemini CLI 自动生成 HTML 报告
- [ ] 用户可查看任务列表和详情
- [ ] 用户可下载原始数据和报告
- [ ] 管理员可配置管线和客户
- [ ] Docker 一键部署成功

### 部署方式
```bash
# 启动服务
docker-compose up -d

# 访问 Web UI（中文界面）
http://localhost:8000/ui

# 访问 API 文档
http://localhost:8000/docs
```

---

## 📞 联系与支持

如有问题，请检查：
1. 需求文档是否理解正确
2. UI 原型是否严格遵循（中文界面）
3. 实施计划是否按步骤执行
4. 测试用例是否全部通过

**开发愉快！** 🚀

---

**版本**: v1.0
**创建时间**: 2026-01-24
**最后更新**: 2026-01-24
