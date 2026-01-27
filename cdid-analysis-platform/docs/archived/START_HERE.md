# 🚀 开发启动 Prompt

**使用时机**: 当您准备好开发环境（可以访问内网 API）后，复制下面的 prompt 给 Claude Code

---

## 📋 启动 Prompt（直接复制使用）

```
你好！我需要实施 CDID 数据分析平台项目。

项目位置：D:\AI\Cursor\gupiao\data_fenxi\cdid-analysis-platform

请按以下步骤操作：

1. 阅读完整需求：
   - docs/final-requirements/README.md
   - docs/final-requirements/方案设计-v0.2.0.md
   - docs/final-requirements/_generated/最终方案-v0.2.0.md
   - docs/final-requirements/ui-mockups/ （所有 HTML 原型）

2. 阅读实施计划：
   - docs/plans/2026-01-24-实施计划-中文概述.md
   - docs/plans/2026-01-24-cdid-analysis-platform-mvp.md
   - docs/plans/UI实现说明.md

3. 执行开发：
   使用 superpowers:subagent-driven-development 技能，按照实施计划逐个任务执行。

⚠️ 重要提醒：
- Web UI 必须是中文界面
- 严格参考 docs/final-requirements/ui-mockups/ 中的 8 个 HTML 原型
- 所有页面标题、按钮、提示信息都使用中文
- 保持原型的视觉风格和交互逻辑

现在开始实施，创建完整的 CDID 数据分析平台 MVP。
```

---

## 📁 关键文档快速链接

1. **恢复开发完整说明**: `docs/RESUME_DEVELOPMENT.md`
2. **实施计划（中文）**: `docs/plans/2026-01-24-实施计划-中文概述.md`
3. **实施计划（英文，含代码）**: `docs/plans/2026-01-24-cdid-analysis-platform-mvp.md`
4. **UI 实现说明**: `docs/plans/UI实现说明.md`
5. **UI 原型**: `docs/final-requirements/ui-mockups/`
6. **需求文档**: `docs/final-requirements/`

---

## ⚡ 快速检查清单

开发前请确认：
- [ ] 可以访问内网 API (172.17.129.204:6829)
- [ ] 已安装 Python 3.11+
- [ ] 已安装 Node.js（用于 Gemini CLI）
- [ ] 已安装 Docker（可选，用于容器化部署）
- [ ] 已阅读 UI 原型文件

---

**祝开发顺利！** 🎉
