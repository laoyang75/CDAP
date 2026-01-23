# CDID 数据分析平台

**版本**: v0.1.0
**状态**: 方案设计阶段 - 等待技术细节确认

---

## 📋 项目概述

将基于 Gemini CLI Skills 的命令行数据分析工具，包装成 **Web 服务**，降低使用门槛。

**核心流程**：
```
用户上传 CDID 文件 → Python 后端 → 调用内网 API → 数据分析 → Gemini CLI 生成报告
```

---

## 📁 当前文档

| 文档 | 说明 | 状态 |
|------|------|------|
| [方案设计.md](docs/方案设计.md) | 完整架构设计（8000字） | ✅ 已完成 |
| [待确认问题清单.md](docs/待确认问题清单.md) | 20 个待确认问题 | ⏸ 等待填写 |
| [RESUME_PROMPT.md](docs/RESUME_PROMPT.md) | 恢复上下文的 Prompt | ✅ 已完成 |

---

## 🎯 下一步行动

### 1. 填写问题清单（优先）

请打开 `docs/待确认问题清单.md`，填写以下优先级最高的问题：

**Gemini CLI 配置**（Q1-Q3）：
- Q1: Gemini CLI 是否已安装？版本？
- Q2: 是否需要 API Key？
- Q3: 管道输入方式是否可行？

**内网 API 配置**（Q4-Q7）：
- Q4: 是否需要认证？
- Q5: 是否有调用频率限制？
- Q7: `start/end` 参数是否必填？

**数据分析算法**（Q8-Q10）：
- Q8: "多发检测"的具体定义？
- Q9: "碰撞检测"的具体定义？
- Q10: "风险检测"的具体定义？

### 2. 方案确认

填写完成后，审核 `docs/方案设计.md`，确认架构是否符合需求。

### 3. 开始开发

技术细节确认后，按以下顺序开发：
1. 内网 API 客户端（`src/worker/insight_client.py`）
2. Python 数据分析（`src/worker/analyzer.py`）
3. Gemini CLI 调用（`src/worker/gemini_reporter.py`）
4. FastAPI + 数据库
5. Worker 主循环
6. Web UI
7. 集成测试
8. Docker 部署

---

## 🔄 重新启动项目（恢复上下文）

如果 Claude Code 重新启动，使用以下步骤快速恢复：

1. 打开 `docs/RESUME_PROMPT.md`
2. 复制灰色框内的完整 prompt
3. 在新对话中发送给 Claude
4. Claude 会自动恢复项目上下文

---

## 📊 技术栈

- **Web 框架**: FastAPI
- **模板引擎**: Jinja2
- **前端**: Bootstrap 5 + 原生 JS
- **数据库**: SQLite (MVP) → PostgreSQL
- **数据分析**: Pandas + NumPy
- **报告生成**: Gemini CLI (subprocess + 管道)
- **部署**: Docker

---

## 📞 联系方式

如有问题，请在对话中提出，或填写"待确认问题清单"后反馈。

---

**当前状态**: 等待用户填写问题清单 → 开始开发
