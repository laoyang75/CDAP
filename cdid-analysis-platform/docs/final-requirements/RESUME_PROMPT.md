# 项目恢复 Prompt

**用途**：在 Claude Code 重新启动时，快速恢复项目上下文
**使用方法**：将下方灰色框内的完整 prompt 复制，发送给 Claude

---

```
你是一个资深 Python 后端/全栈工程师。我正在开发一个名为 "CDID 数据分析平台" 的 Web 服务项目。

## 项目背景

**原始需求**：
- 我之前有一套基于 Gemini CLI Skills 的数据分析工具（命令行）
- 包含 3 个 skills：insight（获取数据）、analyzer（分析数据）、report（生成报告）
- 痛点：技术门槛高，普通用户无法使用

**改造目标**：
- 将命令行流程包装成 Web 服务，让任何人都能通过浏览器使用
- 核心流程：用户选择客户 + 上传 CDID 文件 + 选择管线 → Python 后端调用内网 API 获取数据 → 执行管线（Python 分析 + Gemini CLI 生成报告）

## 核心概念

**管线（Pipeline）**：
- 管线 = Python 数据处理脚本 + Gemini Skill（报告生成）
- 一个任务只执行一条管线
- 管线失败后可手动重新运行

**客户配置**：
- 管理客户-包名映射关系
- 用户创建任务时选择客户，系统自动填充包名

## 技术方案（已确认）

**架构**：
```
用户浏览器 → Web UI → FastAPI 后端 → Worker 后台任务
                                     ↓
                          1. 调用内网 API (172.17.129.204:6829)
                          2. 执行管线：Python 脚本分析 + Gemini CLI 生成报告
```

**技术栈**：
- Web 框架：FastAPI + Jinja2
- 前端：Bootstrap 5 + 原生 JS（无构建）
- 数据库：SQLite (MVP) → PostgreSQL
- 数据分析：Pandas + NumPy（Python 标准接口）
- 报告生成：Gemini CLI (subprocess + stdin + `@skill_name` prompt)
- 部署：Docker

**关键决策**：
1. ✅ 管线化设计：Python 脚本 + Gemini Skill 解耦
2. ✅ Python 脚本标准接口：`def analyze(input_file, user_info, start_date, end_date) -> dict`
3. ✅ Gemini CLI Headless Mode：`cat result.json | gemini "@<skill_name> 生成HTML报告"`（或用 `-p`）
4. ✅ Skill 只能导入（不能新建），因为不同 Skill 目录结构不同
5. ✅ 客户配置：客户名称 → 包名自动填充
6. ✅ 数据下载：用户可下载原始数据（Excel）和报告（HTML）

## 当前进度

**已完成**：
1. ✅ 创建项目目录：`cdid-analysis-platform/`
2. ✅ 编写完整方案设计文档：`docs/final-requirements/方案设计-v0.2.0.md`
   - 包含：管线概念、架构图、流程设计、模块设计、API 设计、数据库设计
3. ✅ 完整 UI 原型（8个HTML页面）：`docs/final-requirements/ui-mockups/`
   - 用户界面：创建任务、任务列表、任务详情
   - 后台管理：管线管理、脚本编辑、客户配置、用户管理、任务监控
4. ✅ 待确认问题清单：`docs/final-requirements/待确认问题清单-v0.2.0.md`（25 个问题）
   - 涵盖：Gemini CLI 配置、内网 API、数据分析算法、管线配置、客户配置

**待完成**：
1. ⏸ 等待用户审计文档和 UI 原型
2. ⏸ 等待用户回答"待确认问题清单"
3. ⏸ 根据用户反馈调整方案
4. ⏸ 开始代码实现

## 项目目录结构

当前目录：
```
cdid-analysis-platform/
├── docs/
│   └── final-requirements/         ✅ 最终需求文档（v0.2.0）
│       ├── README.md               ✅ 文档说明
│       ├── 方案设计-v0.2.0.md       ✅ 完整架构设计
│       ├── 待确认问题清单-v0.2.0.md  ✅ 25 个待确认问题
│       ├── RESUME_PROMPT.md        ✅ 本文件
│       └── ui-mockups/             ✅ 8个UI原型（HTML）
│           ├── user-create-task.html
│           ├── user-task-list.html
│           ├── user-task-detail.html
│           ├── admin-pipeline-management.html
│           ├── admin-script-editor.html
│           ├── admin-client-config.html
│           ├── admin-user-management.html
│           └── admin-task-monitoring.html
└── (代码目录待创建)
```

计划目录（开发后）：
```
cdid-analysis-platform/
├── docs/
├── src/
│   ├── api/                  # FastAPI 应用
│   ├── worker/               # 后台任务处理
│   │   ├── insight_client.py # 内网 API 客户端
│   │   ├── pipeline_executor.py # 管线执行器
│   │   └── gemini_reporter.py # Gemini CLI 调用
│   ├── scripts/              # Python 数据分析脚本目录
│   │   ├── duplicate_detection/
│   │   ├── risk_analysis/
│   │   └── impact_time_series/
│   ├── db/                   # 数据库
│   ├── ui/                   # Web UI
│   └── config.py
├── jobs/                     # 运行时目录
└── requirements.txt
```

## 核心模块说明

### 1. 内网 API 客户端（insight_client.py）
**职责**：封装调用 `http://172.17.129.204:6829` 的三个接口
- `create_task()` - 创建任务
- `query_task_status()` - 轮询查询状态
- `download_result()` - 下载结果文件

### 2. 管线执行器（pipeline_executor.py）
**职责**：执行管线（Python 脚本 + Gemini Skill）
- 动态加载 Python 脚本模块
- 调用标准接口：`analyze(input_file, user_info, start_date, end_date)`
- 保存分析结果为 JSON

### 3. Gemini CLI 调用（gemini_reporter.py）
**职责**：使用 Gemini CLI Headless Mode 生成 HTML 报告
- 通过管道输入分析结果
- 命令：`cat analysis_result.json | gemini "@<skill_name> 根据以上JSON生成完整HTML报告，只输出HTML"`
- 输出：`report.html`

### 4. Worker（worker.py）
**职责**：后台任务处理（FIFO 单线程）
- 状态机：queued → fetching → analyzing → reporting → done
- 每阶段更新数据库状态

## 数据库设计

**核心表**：
1. `jobs` - 任务
2. `pipelines` - 管线配置（脚本目录、脚本文件名、Skill 名称）
3. `clients` - 客户配置（客户名称、包名）
4. `users` - 用户（权限由现有接口控制）

## Web UI 设计要点

**用户界面**：
- 创建任务页：客户名称检索 + 自动填充包名 + 管线选择 + 文件拖拽上传
- 任务列表页：筛选、实时进度条、删除/重新运行
- 任务详情页：执行流程时间轴、报告展示、下载原始数据/报告

**后台管理**：
- 管线管理：卡片式展示，配置脚本目录、文件名、Skill
- 脚本编辑：编辑 Python 脚本、配置/引用 Gemini Skill（不支持新建；导入走人工）
- 客户配置：添加/编辑/删除客户、批量导入
- 用户管理：添加/删除用户、权限展示
- 任务监控：查看所有用户任务、失败日志

## 关键待确认事项（优先级最高）

**Gemini CLI 配置**：
- Q1: 是否已安装？版本？
- Q2: 是否需要 API Key？如何配置？
- Q3: 管道输入 + `@skill_name` prompt 方式是否可行？

**内网 API**：
- Q4: 是否需要认证？
- Q5: 是否有调用频率限制？
- Q6: `start/end` 参数是否必填？
- Q7: 平均处理时长？

**管线配置**：
- Q12: Python 脚本命名规范？
- Q13: 标准接口是否可行？
- Q14: Skill 目录结构？
- Q15: 导入 Skill 后是否需要重启 Gemini CLI？

**数据分析算法**：
- Q8-Q10: 多发/碰撞/风险检测的具体定义？

## 原始材料位置

**重要文档**：
- 最终需求：`docs/final-requirements/`
- UI 原型：`docs/final-requirements/ui-mockups/`
- 方案设计：`docs/final-requirements/方案设计-v0.2.0.md`
- 问题清单：`docs/final-requirements/待确认问题清单-v0.2.0.md`

## 下一步行动

请帮我：
1. 如果用户已审计文档，询问是否有需要调整的地方
2. 如果用户已回答问题清单，根据答案调整方案设计
3. 如果用户尚未完成审计，提醒用户优先查看 UI 原型和方案设计
4. 准备好后，开始代码实现（从项目框架开始）

## 注意事项

1. ⚠️ 管线 = Python 脚本 + Gemini Skill（解耦设计）
2. ⚠️ 一个任务只执行一条管线
3. ⚠️ Skill 只能导入，不能新建（目录结构复杂）
4. ⚠️ Python 脚本必须实现标准接口
5. ⚠️ 客户配置是独立功能，用于简化任务创建
6. ⚠️ 数据下载包括原始数据（Excel）和报告（HTML）

---

**当前状态**：UI 设计完成，方案设计完成（v0.2.0），等待用户审计和回答问题。
```

---

## 使用方法

**下次启动 Claude Code 时**：
1. 打开新对话
2. 复制上方灰色框内的完整 prompt
3. 发送给 Claude
4. Claude 会自动恢复项目上下文，继续开发

**如果用户已审计文档**：
- 说明需要调整的部分
- Claude 会更新相应文档

**如果用户已回答问题清单**：
- 将答案一起发送
- 或直接在对话中回复关键问题
- Claude 会根据答案优化方案设计

---

## 版本历史

### v0.2.0（2026-01-23）

**重大更新**：
- ✅ 引入管线（Pipeline）概念
- ✅ 增加客户配置功能
- ✅ 完成 8 个 UI 原型
- ✅ 明确 Python 脚本标准接口
- ✅ 明确 Skill/扩展管理边界（平台只引用 `@skill_name`，不负责导入/新建）
- ✅ 增加数据下载功能

### v0.1.0（2026-01-23）

- 初始版本
- 基于原始需求的方案设计

---

**文件维护**：
- 每次方案有重大变更时，更新本文件
- 与"方案设计.md"保持同步
