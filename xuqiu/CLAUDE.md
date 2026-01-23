# 数据洞察分析工具 - Claude Code 项目配置

本文件为 Claude Code 提供项目特定的上下文和指引。

---

## 项目概述

**项目名称：** 数据洞察分析工具
**用途：** 通过三个协同工作的 skills，完成设备指纹数据的获取、分析和报告生成
**技术栈：** Go (分析工具)、Bash (安装脚本)、Markdown (Skills 定义)
**支持平台：** Claude Code (任意版本) / Gemini CLI (>= v0.24.5)

---

## 环境要求

### Claude Code
- 版本：任意版本
- 配置：无需额外配置，安装 skills 后自动生效

### Gemini CLI ⚠️
- **版本：>= v0.24.5**（必需）
- **配置：必须启用 skills 功能**（关键步骤）

**Gemini CLI 配置步骤：**
1. 检查版本：`gemini --version`
2. 在对话中输入：`/setting`
3. 搜索：`agent`
4. 启用：`skills`（设为 enabled）
5. 重启 Gemini CLI

**⚠️ 如果不完成上述配置，Gemini CLI 中的 skills 将不会被加载！**

---

## 项目结构

```
data-analysis-skill/
├── skills/              # Skills 定义
│   ├── claude/         # Claude Code Skills
│   │   ├── analyzer/   # 本地数据分析
│   │   ├── insight/    # 远程数据获取
│   │   └── report/     # 报告生成
│   └── gemini/         # Gemini CLI Skills (相同功能)
├── bin/                # 编译好的分析工具二进制
│   ├── darwin_amd64/
│   ├── darwin_arm64/
│   ├── linux_amd64/
│   └── windows_amd64/
└── script/             # 安装和部署脚本
    └── install.sh
```

---

## Skills 工作流程

### 1. insight Skill
**功能：** 上传 CDID 列表文件到远程服务，获取设备指纹详情数据

**关键信息：**
- API 服务地址：`http://172.17.129.204:6829`
- 需要内网访问权限
- 支持 DNA 和 DAA 两种数据类型
- 异步任务处理模式

**典型对话：**
```
用户：创建分析任务，文件是 cdid_list.xlsx，包名 com.example.app，获取 dna 和 daa 数据
Claude: [调用 insight skill，上传文件到远程服务]

用户：查询任务 1234567890 的状态
Claude: [调用 insight skill，查询任务状态]

用户：获取任务 1234567890 的下载地址
Claude: [调用 insight skill，返回下载链接]
```

### 2. analyzer Skill
**功能：** 使用本地 Go 工具分析设备指纹数据

**关键信息：**
- 本地工具路径：`~/.insight/bin/data_insight_analyzer`
- 支持三种检测：多发、碰撞、风险
- 输入：insight 下载的 Excel 文件
- 输出：包含多个 Sheet 的分析结果 Excel

**典型对话：**
```
用户：分析 /path/to/data.xlsx 这个文件
Claude: [调用 analyzer skill，执行本地分析工具]

用户：只对 data.xlsx 做多发检测
Claude: [调用 analyzer skill，指定 -t duplicate]
```

### 3. report Skill
**功能：** 基于 analyzer 的分析结果生成专业的 HTML 报告

**关键信息：**
- 输入：analyzer 的分析输出（在对话上下文中）
- 输出：HTML 格式的可视化报告
- 特性：支持图表、颜色标记、结构化展示

**典型对话：**
```
用户：根据上面的分析结果生成一份报告
Claude: [调用 report skill，生成 HTML 格式报告]
```

---

## 完整工作流示例

```
1. 用户：创建分析任务，文件是 cdid_list.xlsx，包名 com.example.app，获取 dna 数据
   → Claude 调用 insight skill 上传文件

2. 用户：查询任务 1234567890 的状态
   → Claude 调用 insight skill 查询状态
   → 返回：任务已完成

3. 用户：获取任务 1234567890 的下载地址
   → Claude 调用 insight skill 获取下载链接
   → 用户下载结果文件到本地

4. 用户：分析 /path/to/downloaded_result.xlsx
   → Claude 调用 analyzer skill 执行本地分析
   → 返回：多发 15 条，碰撞 8 条，风险 3 条

5. 用户：生成报告
   → Claude 调用 report skill 生成 HTML 报告
   → 返回：专业的可视化分析报告
```

---

## 开发和维护指南

### 添加新 Skill

1. 在 `skills/claude/` 和 `skills/gemini/` 下创建同名目录
2. 编写 `SKILL.md` 文件，包含：
   - YAML frontmatter (name, description, user_invokable, version)
   - Skill 功能说明和使用示例
3. 更新 `script/install.sh`，添加新 skill 的安装逻辑
4. 更新 `README.md`，添加新 skill 的文档

### 更新分析工具

1. 编译新版本的 Go 二进制文件
2. 放置到 `bin/` 对应平台目录
3. 更新版本号和文档

### 修改 Skills

1. 编辑 `skills/claude/xxx/SKILL.md` 和 `skills/gemini/xxx/SKILL.md`
2. 增加 version 号
3. 测试 skill 是否正常工作
4. 更新相关文档

---

## 常见开发任务

### 如何测试 Skills？

**Claude Code：**
1. 将修改后的 skill 复制到 `~/.claude/skills/`
2. 重启 Claude Code
3. 在对话中测试对应功能
4. 使用 `/skills` 命令查看已加载的 skills

**Gemini CLI：**
1. 确认版本 >= v0.24.5：`gemini --version`
2. 确认已启用 skills：`/setting` → 搜索 `agent` → 确认 `skills` 为 `enabled`
3. 将修改后的 skill 复制到 `~/.gemini/skills/`
4. 重启 Gemini CLI
5. 使用 `skills list` 命令查看已加载的 skills
6. 在对话中测试对应功能

### 如何调试分析工具？

```bash
# 直接运行二进制文件测试
~/.insight/bin/data_insight_analyzer -i test_data.xlsx -o result.xlsx -t all

# 查看版本
~/.insight/bin/data_insight_analyzer -v

# 查看帮助
~/.insight/bin/data_insight_analyzer -h
```

### 如何更新安装脚本？

修改 `script/install.sh`，关注以下部分：
- `install_skills()`: Skills 安装逻辑
- `install_analyzer()`: 二进制文件安装逻辑
- `verify_installation()`: 验证逻辑
- `print_usage()`: 使用说明

---

## 关键文件说明

| 文件 | 用途 | 修改频率 |
|------|------|----------|
| `skills/*/SKILL.md` | Skill 定义和文档 | 中 |
| `script/install.sh` | 自动化安装脚本 | 低 |
| `bin/*/data_insight_analyzer` | 分析工具二进制 | 中 |
| `README.md` | 用户文档 | 中 |
| `CLAUDE.md` | 项目配置（本文件） | 低 |

---

## 注意事项

1. **Skills 同步**：修改 skill 时，确保 `skills/claude/` 和 `skills/gemini/` 保持一致
2. **版本管理**：每次修改 skill 或二进制文件，记得更新版本号
3. **跨平台兼容**：确保脚本和文档适用于 macOS、Linux、Windows
4. **网络依赖**：insight skill 依赖内网服务，测试时需要内网环境
5. **路径一致性**：所有工具使用统一路径 `~/.insight/bin/`
6. **⚠️ Gemini CLI 特殊要求**：
   - 版本必须 >= v0.24.5
   - 必须在 `/setting` 中启用 skills 功能
   - 安装脚本无法自动完成 Gemini 配置，需手动操作

---

## 故障排查

### Skill 未加载

**Claude Code：**
```bash
# 检查 skill 文件位置
ls -la ~/.claude/skills/

# 检查 skill 文件内容
cat ~/.claude/skills/analyzer/SKILL.md

# 重启 Claude Code
```

**Gemini CLI（⚠️ 最常见问题）：**
```bash
# 1. 检查版本（必须 >= v0.24.5）
gemini --version

# 2. 确认 skills 功能已启用（最常见原因）
# 在对话中：/setting → 搜索 agent → 确认 skills 为 enabled

# 3. 检查 skill 文件位置
ls -la ~/.gemini/skills/

# 4. 检查 skill 文件内容
cat ~/.gemini/skills/analyzer/SKILL.md

# 5. 重启 Gemini CLI

# 6. 验证 skills 已加载
# 在对话中：skills list
```

**Gemini CLI skills 未加载，99% 是因为未在 /setting 中启用 skills 功能！**

### 分析工具执行失败

```bash
# 检查文件是否存在
ls -la ~/.insight/bin/data_insight_analyzer

# 检查执行权限
chmod +x ~/.insight/bin/data_insight_analyzer

# 手动测试
~/.insight/bin/data_insight_analyzer -v
```

### insight 服务连接失败

```bash
# 测试网络连通性
curl http://172.17.129.204:6829/api/statistical-analysis/v1/task/list \
  -d '{"page":1,"limit":1}'

# 检查 VPN 连接
# 检查防火墙设置
```

---

## 贡献指南

1. **提交前检查：**
   - 所有 skills 已在 Claude Code 和 Gemini CLI 中测试
   - Gemini CLI 测试需确认版本 >= v0.24.5 且已启用 skills
   - 文档已更新（README.md 和 CLAUDE.md）
   - 安装脚本已验证

2. **版本号规则：**
   - 主版本：重大功能变更
   - 次版本：新增 skill 或重要功能
   - 修订版本：Bug 修复和小改进

3. **文档规范：**
   - 保持 README.md 和 CLAUDE.md 同步
   - 所有新功能必须有使用示例
   - Gemini CLI 相关内容必须标注版本和配置要求
   - 更新版本日志

4. **Gemini CLI 测试清单：**
   - [ ] 版本检查：`gemini --version` >= v0.24.5
   - [ ] Skills 启用：`/setting` → `agent` → `skills` enabled
   - [ ] Skills 安装：复制到 `~/.gemini/skills/`
   - [ ] 重启验证：`skills list` 显示所有 skills
   - [ ] 功能测试：每个 skill 正常工作

---

## 联系信息

**维护人员：** [维护人员信息]
**问题反馈：** [反馈渠道]
**内部文档：** [内部文档链接]
