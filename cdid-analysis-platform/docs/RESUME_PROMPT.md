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
- 核心流程：用户上传 CDID 文件 → Python 后端调用内网 API 获取数据 → Python 数据分析 → Gemini CLI 生成 HTML 报告

## 技术方案（已确认）

**架构**：
```
用户浏览器 → Web UI → FastAPI 后端 → Worker 后台任务
                                     ↓
                          1. 调用内网 API (172.17.129.204:6829)
                          2. Python Pandas 数据分析（重新实现 analyzer）
                          3. Gemini CLI Headless Mode（管道输入生成报告）
```

**技术栈**：
- Web 框架：FastAPI + Jinja2
- 前端：Bootstrap 5 + 原生 JS（无构建）
- 数据库：SQLite (MVP) → PostgreSQL
- 数据分析：Pandas + NumPy
- 报告生成：Gemini CLI (subprocess + 管道)
- 部署：Docker

**关键决策**：
1. ✅ 不需要 analyzer 二进制，用 Python 重新实现分析逻辑
2. ✅ 用 Gemini CLI Headless Mode（管道输入：`cat result.json | gemini -p "..."`）
3. ✅ 第一期重点：利用 Gemini CLI 智能生成个性化报告
4. ✅ 可扩展设计：方便添加新的 Python 分析模块、新的 Gemini skills

## 当前进度

**已完成**：
1. ✅ 创建新项目目录：`cdid-analysis-platform/`
2. ✅ 编写完整方案设计文档：`docs/方案设计.md`（约 8000 字）
   - 包含：架构图、流程设计、模块设计、API 设计、数据库设计、部署方案
3. ✅ 整理待确认问题清单：`docs/待确认问题清单.md`（20 个问题）
   - 涵盖：Gemini CLI 配置、内网 API、数据分析算法、报告格式、性能规模

**待完成**：
1. ⏸ 等待用户填写"待确认问题清单"，明确技术细节
2. ⏸ 根据用户反馈调整方案
3. ⏸ 开始代码实现

## 项目目录结构

当前目录：
```
cdid-analysis-platform/
├── docs/
│   ├── 方案设计.md           ✅ 完整架构设计
│   ├── 待确认问题清单.md      ✅ 20 个待确认问题
│   └── RESUME_PROMPT.md       ✅ 本文件
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
│   │   ├── analyzer.py       # Python 数据分析
│   │   └── gemini_reporter.py # Gemini CLI 调用
│   ├── db/                   # 数据库
│   ├── ui/                   # Web UI
│   └── config.py
├── jobs/                     # 运行时目录
├── requirements.txt
└── README.md
```

## 核心模块说明

### 1. 内网 API 客户端（insight_client.py）
**职责**：封装调用 `http://172.17.129.204:6829` 的三个接口
- `create_task()` - 创建任务
- `query_task_status()` - 轮询查询状态
- `download_result()` - 下载结果文件

### 2. Python 数据分析（analyzer.py）
**职责**：重新实现原 Go analyzer 的逻辑
- `_detect_duplicate()` - 多发检测
- `_detect_impact()` - 碰撞检测
- `_detect_risk()` - 风险检测
- 输出：`analysis_result.json`（结构化分析结果）

### 3. Gemini CLI 调用（gemini_reporter.py）
**职责**：使用 Gemini CLI Headless Mode 生成 HTML 报告
- 通过管道输入分析结果
- 命令：`cat analysis_result.json | gemini -p "根据以下数据生成专业HTML报告..."`
- 输出：`report.html`

### 4. Worker（worker.py）
**职责**：后台任务处理（FIFO 单线程）
- 状态机：queued → fetching → analyzing → reporting → done
- 每阶段更新数据库状态

## 关键待确认事项（优先级最高）

**Gemini CLI 配置**：
- Q1: 是否已安装？版本？
- Q2: 是否需要 API Key？如何配置？
- Q3: 管道输入方式是否可行？

**内网 API**：
- Q4: 是否需要认证？
- Q5: 是否有调用频率限制？
- Q7: `start/end` 参数是否必填？

**数据分析算法**：
- Q8-Q10: 多发/碰撞/风险检测的具体定义是什么？

## 原始材料位置

**重要文档**：
- 原始需求：`xuqiu/README.md`
- Gemini Skills 定义：`xuqiu/gemini/{insight,analyzer,report}/SKILL.md`
- 项目调研报告：`_agent_outputs/01_项目情况.md`（如存在）

**错误实现**（可忽略/删除）：
- `data-insight-service/`（之前基于错误理解的实现，已废弃）

## 下一步行动

请帮我：
1. 检查用户是否已填写"待确认问题清单"
2. 如果已填写，根据答案调整方案设计
3. 如果未填写，提醒用户优先回答 Q1-Q10（Gemini CLI + API + 算法）
4. 准备好后，开始代码实现（从内网 API 客户端开始）

## 注意事项

1. ⚠️ 本项目的目标是"将命令行包装成 Web 服务"，不是从零设计数据分析平台
2. ⚠️ 核心价值在于"利用 Gemini CLI 智能生成报告"，不需要固定模板
3. ⚠️ 数据分析算法需要重新实现（原 Go 二进制不保留）
4. ⚠️ MVP 阶段优先简单可用，后续迭代优化

---

**当前状态**：方案设计完成，等待用户确认技术细节后开始开发。
```

---

## 使用方法

**下次启动 Claude Code 时**：
1. 打开新对话
2. 复制上方灰色框内的完整 prompt
3. 发送给 Claude
4. Claude 会自动恢复项目上下文，继续开发

**如果用户已填写问题清单**：
- 将填写好的"待确认问题清单.md"一起发送
- 或直接在对话中回复关键问题的答案

**如果需要调整方案**：
- 说明需要修改的部分
- Claude 会更新"方案设计.md"并同步修改本 prompt

---

**文件维护**：
- 每次方案有重大变更时，更新本文件
- 版本号：v0.1.0 (2026-01-23)
