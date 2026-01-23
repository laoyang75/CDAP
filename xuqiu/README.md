# 数据洞察分析工具使用指南

本工具包提供三个 skill，配合使用完成数据分析全流程：

1. **insight** - 上传 CDID 文件，调用远程服务获取 DNA/DAA 详情数据
2. **analyzer** - 分析 insight 返回的详情数据，进行多发/碰撞/风险检测
3. **report** - 根据 analyzer 输出结果，生成专业的 HTML 格式分析报告

**典型流程：** 上传 CDID 列表 → insight 获取详情 → 下载结果 → analyzer 本地分析 → report 生成报告

---

## 目录结构

```
.
├── README.md                    # 本文档
├── CLAUDE.md                    # Claude Code 项目配置
├── skills/
│   ├── claude/                  # Claude Code Skills
│   │   ├── analyzer/
│   │   │   └── SKILL.md        # 本地分析工具 skill
│   │   ├── insight/
│   │   │   └── SKILL.md        # 远程服务 skill
│   │   └── report/
│   │       └── SKILL.md        # 报告生成 skill
│   └── gemini/                  # Gemini CLI Skills
│       ├── analyzer/
│       │   └── SKILL.md
│       ├── insight/
│       │   └── SKILL.md
│       └── report/
│           └── SKILL.md
├── bin/
│   ├── darwin_amd64/
│   │   └── data_insight_analyzer    # macOS Intel 版本
│   ├── darwin_arm64/
│   │   └── data_insight_analyzer    # macOS Apple Silicon 版本
│   ├── linux_amd64/
│   │   └── data_insight_analyzer    # Linux 版本
│   └── windows_amd64/
│       └── data_insight_analyzer.exe # Windows 版本
└── script/
    └── install.sh               # 自动化安装脚本
```

---

## 一、环境要求

### 必需条件

- **AI CLI 工具**（二选一）：
  - **Claude Code**：任意版本
  - **Gemini CLI**：版本 >= v0.24.5 ⚠️
- **网络**：使用 insight skill 需要能访问 `172.17.129.204:6829`
- **操作系统**：macOS (Intel/Apple Silicon)、Linux 或 Windows

### ⚠️ Gemini CLI 重要配置

**如果你使用 Gemini CLI，必须完成以下配置，否则 skills 无法使用：**

1. **检查版本**（必须 >= v0.24.5）：
   ```bash
   gemini --version
   ```

2. **启用 Skills 功能**（必须执行）：
   - 在 Gemini CLI 对话中输入 `/setting`
   - 搜索 `agent`
   - 找到 `skills` 选项并启用（设为 `enabled`）

**没有完成上述配置，skills 将不会被加载！**

---

## 二、安装步骤

### 🚀 快速安装（推荐）

**⚠️ Gemini CLI 用户请先完成上述"环境要求"中的配置，再执行安装！**

使用自动化安装脚本一键安装所有组件：

```bash
# macOS / Linux
cd /path/to/data-analysis-skill
bash script/install.sh
```

脚本会自动：
- 检测操作系统和 AI CLI 工具
- 安装对应平台的 skills（analyzer、insight、report）
- 安装本地分析工具二进制文件
- 验证安装结果

**Gemini CLI 用户注意：** 安装完成后，如果 skills 未生效，请检查是否已在 `/setting` 中启用 skills 功能。

### 📋 手动安装

如果需要手动安装，请按以下步骤操作：

#### 2.1 安装 Skills

根据你使用的 AI CLI 工具选择对应目录：

**Claude Code 用户：**

```bash
# macOS / Linux
mkdir -p ~/.claude/skills
cp -r skills/claude/analyzer ~/.claude/skills/
cp -r skills/claude/insight ~/.claude/skills/
cp -r skills/claude/report ~/.claude/skills/
```

```powershell
# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills"
Copy-Item -Recurse skills\claude\analyzer "$env:USERPROFILE\.claude\skills\"
Copy-Item -Recurse skills\claude\insight "$env:USERPROFILE\.claude\skills\"
Copy-Item -Recurse skills\claude\report "$env:USERPROFILE\.claude\skills\"
```

**Gemini CLI 用户：**

⚠️ **重要提醒：**
1. 确保 Gemini CLI 版本 >= v0.24.5
2. 必须先在 `/setting` 中启用 skills 功能（详见"环境要求"）

```bash
# macOS / Linux
# 1. 检查版本
gemini --version  # 必须 >= v0.24.5

# 2. 安装 skills
mkdir -p ~/.gemini/skills
cp -r skills/gemini/analyzer ~/.gemini/skills/
cp -r skills/gemini/insight ~/.gemini/skills/
cp -r skills/gemini/report ~/.gemini/skills/

# 3. 重启 Gemini CLI 后，在对话中执行：
#    /setting → 搜索 agent → 启用 skills
```

```powershell
# Windows (PowerShell)
# 1. 检查版本
gemini --version  # 必须 >= v0.24.5

# 2. 安装 skills
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.gemini\skills"
Copy-Item -Recurse skills\gemini\analyzer "$env:USERPROFILE\.gemini\skills\"
Copy-Item -Recurse skills\gemini\insight "$env:USERPROFILE\.gemini\skills\"
Copy-Item -Recurse skills\gemini\report "$env:USERPROFILE\.gemini\skills\"

# 3. 重启 Gemini CLI 后，在对话中执行：
#    /setting → 搜索 agent → 启用 skills
```

### 2.2 安装本地分析工具（使用 analyzer skill 必需）

根据你的操作系统，选择对应的二进制文件进行安装：

#### macOS (Intel)

```bash
mkdir -p ~/.insight/bin
cp bin/darwin_amd64/data_insight_analyzer ~/.insight/bin/
chmod +x ~/.insight/bin/data_insight_analyzer
```

#### macOS (Apple Silicon M1/M2/M3)

```bash
mkdir -p ~/.insight/bin
cp bin/darwin_arm64/data_insight_analyzer ~/.insight/bin/
chmod +x ~/.insight/bin/data_insight_analyzer
```

#### Linux

```bash
mkdir -p ~/.insight/bin
cp bin/linux_amd64/data_insight_analyzer ~/.insight/bin/
chmod +x ~/.insight/bin/data_insight_analyzer
```

#### Windows (PowerShell)

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.insight\bin"
Copy-Item bin\windows_amd64\data_insight_analyzer.exe "$env:USERPROFILE\.insight\bin\"
```

### 2.3 验证安装

#### 验证 analyzer 安装

```bash
# macOS / Linux
~/.insight/bin/data_insight_analyzer -v

# Windows (PowerShell)
& "$env:USERPROFILE\.insight\bin\data_insight_analyzer.exe" -v
```

#### 验证 skills 安装

重新启动 AI CLI 工具，对话中提到分析相关需求时会自动调用对应的 skill。

**Claude Code：**
```bash
# 重启后在对话中输入
/skills
# 应该能看到 analyzer, insight, report 三个 skills
```

**Gemini CLI：**
```bash
# 1. 检查版本（必须 >= v0.24.5）
gemini --version

# 2. 启用 skills 功能（必须执行）
# 在对话中输入：/setting
# 搜索：agent
# 启用：skills（设为 enabled）

# 3. 验证 skills 已加载
# 在对话中输入：skills list
# 应该能看到 analyzer, insight, report 三个 skills

# ⚠️ 如果看不到 skills，说明步骤 2 未正确完成
```

---

## 三、完整使用流程

### 步骤 1：使用 insight 获取详情数据

准备一个包含 CDID 列表的 Excel 文件，通过 insight 上传获取 DNA/DAA 详情。

**对话示例：**
```
帮我创建一个分析任务：
- 任务名称：12月数据分析
- 包名：com.example.app
- 文件：/path/to/cdid_list.xlsx
- 数据类型：dna 和 daa
```

### 步骤 2：等待任务完成

**对话示例：**
```
查询任务 1234567890 的状态
```

### 步骤 3：下载结果文件

任务完成后，获取下载地址并下载详情数据文件。

**对话示例：**
```
获取任务 1234567890 的下载地址
```

### 步骤 4：使用 analyzer 分析详情数据

对下载的详情数据进行多发/碰撞/风险检测。

**对话示例：**
```
分析 /path/to/downloaded_result.xlsx 这个文件
```

### 步骤 5：使用 report 生成专业报告

基于 analyzer 的分析结果，生成可读性强的 HTML 格式报告。

**对话示例：**
```
根据上面的分析结果生成一份报告
```

---

## 四、insight Skill 详细说明

通过调用远程 API 服务，上传 CDID 列表获取对应的 DNA/DAA 详情数据。

### 4.1 输入文件格式

上传的 Excel 文件需包含 CDID 列表：

| 列名 | 必填 | 说明 |
|------|------|------|
| cdid | 是 | 客户设备 ID |

**示例：**

| cdid |
|------|
| abc123 |
| def456 |
| ghi789 |

> 文件可以包含其他列，但必须有 cdid 列。

### 4.2 功能说明

| 功能 | 说明 |
|------|------|
| 创建任务 | 上传 CDID 文件，获取 DNA/DAA 详情 |
| 查询列表 | 分页查询任务列表 |
| 查询详情 | 获取任务详情和结果下载地址 |

### 4.3 使用示例

**创建任务：**
```
创建分析任务，文件是 cdid_list.xlsx，包名 com.example.app，获取 dna 和 daa 数据
```

**查询任务列表：**
```
查询最近的分析任务
```

```
查询包名包含 example 的失败任务
```

**查询任务详情：**
```
查询任务 1234567890 的详情，获取下载地址
```

### 4.4 任务状态

| 状态 | 说明 |
|------|------|
| pending | 待处理 |
| running | 处理中 |
| success | 已完成，可下载结果 |
| failed | 失败 |

### 4.5 输出结果

任务完成后，返回包含 DNA/DAA 详情的 Excel 文件，包含以下字段：

| 字段 | 说明 |
|------|------|
| cdid | 客户设备 ID |
| did | 设备 ID |
| oaid | OAID |
| idfa | IDFA |
| imei | IMEI |
| android_id | Android ID |
| rc_rules | 风控规则版本 |
| rc_scenes | 风控场景标识 |
| ... | 其他设备指纹字段 |

---

## 五、analyzer Skill 详细说明

使用本地安装的分析工具，对 insight 返回的详情数据进行多发/碰撞/风险检测。

### 5.1 输入文件格式

使用 insight 下载的结果文件，或符合以下格式的 Excel 文件：

| 列名 | 必填 | 说明 |
|------|------|------|
| cdid | 是 | 客户设备 ID |
| did | 否 | 设备 ID |
| oaid | 否 | OAID |
| idfa | 否 | IDFA |
| imei | 否 | IMEI |
| android_id | 否 | Android ID |
| rc_rules | 否 | 风控规则版本（风险检测需要） |
| rc_scenes | 否 | 风控场景标识（风险检测需要） |

### 5.2 检测类型

| 检测类型 | 说明 |
|----------|------|
| duplicate | 多发检测 - 检测重复的设备指纹 |
| impact | 碰撞检测 - 检测同一 ID 关联多个设备 |
| risk | 风险检测 - 检测命中风控规则的记录 |
| all | 全部检测（默认） |

### 5.3 使用示例

**完整分析：**
```
分析 /Users/test/data.xlsx 这个文件
```

**指定输出文件：**
```
分析 data.xlsx，结果保存到 result.xlsx
```

**指定检测类型：**
```
只对 data.xlsx 做多发检测
```

```
分析 data.xlsx，只需要碰撞检测
```

### 5.4 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| -i | 输入文件路径（必填） | -i data.xlsx |
| -o | 输出文件路径 | -o result.xlsx |
| -t | 检测类型 | -t duplicate |
| -v | 显示版本 | -v |
| -h | 显示帮助 | -h |

### 5.5 输出结果

生成的 Excel 文件包含以下 Sheet：

| Sheet 名称 | 说明 |
|------------|------|
| 结论 | 汇总每个 CDID 的检测结果 |
| 多发检测 | 多发记录详情，相同背景色表示同一组 |
| 碰撞检测 | 碰撞记录详情，相同背景色表示同一 ID |
| 风险检测 | 命中风控规则的记录 |

---

## 六、report Skill 详细说明

根据 analyzer 的分析结果，生成专业、可读性强的 HTML 格式数据分析报告。

### 6.1 功能特点

| 特性 | 说明 |
|------|------|
| 专业格式 | HTML 格式，支持图表和样式 |
| 可读性强 | 结构化展示，重点突出 |
| 颜色标记 | 不同颜色强调不同级别的问题 |
| 图表支持 | 可视化展示分析结论 |

### 6.2 使用示例

**基于 analyzer 结果生成报告：**
```
根据上面的分析结果生成一份报告
```

**直接请求生成报告：**
```
生成数据分析报告
```

### 6.3 报告内容

生成的 HTML 报告通常包含：

| 章节 | 内容 |
|------|------|
| 执行摘要 | 核心发现和关键指标汇总 |
| 多发检测 | 重复设备指纹的详细分析 |
| 碰撞检测 | ID 碰撞情况的可视化展示 |
| 风险检测 | 风控规则命中情况统计 |
| 结论建议 | 基于分析的行动建议 |

### 6.4 报告输出

报告以 HTML 格式输出，可以：
- 直接在浏览器中打开查看
- 保存为文件进行分享
- 打印成 PDF 文档
- 嵌入到其他文档系统

---

## 七、常见问题

### Q1: 提示 "command not found" 或找不到可执行文件

确认二进制文件已正确安装到 `~/.insight/bin/` 目录，并且有执行权限：

```bash
# 检查文件是否存在
ls -la ~/.insight/bin/

# 添加执行权限（macOS/Linux）
chmod +x ~/.insight/bin/data_insight_analyzer
```

### Q2: Skill 没有生效

**Claude Code 用户：**
1. 确认 SKILL.md 文件已复制到 `~/.claude/skills/{analyzer,insight,report}/SKILL.md`
2. 重新启动 Claude Code
3. 使用 `/skills` 命令查看已加载的 skills

**Gemini CLI 用户（⚠️ 常见问题）：**
1. **检查版本**：`gemini --version` 必须 >= v0.24.5
2. **确认 skills 功能已启用**（最常见原因）：
   - 在对话中输入 `/setting`
   - 搜索 `agent`
   - 确认 `skills` 选项是 `enabled`（不是 `disabled`）
3. 确认 SKILL.md 文件已复制到 `~/.gemini/skills/{analyzer,insight,report}/SKILL.md`
4. 重新启动 Gemini CLI
5. 使用 `skills list` 命令验证

**如果 Gemini CLI 的 skills 仍未生效，99% 是因为未在 /setting 中启用 skills 功能！**

### Q3: insight 服务连接失败

1. 确认网络可以访问 `172.17.129.204:6829`
2. 检查 VPN 或防火墙设置
3. 尝试手动测试：`curl http://172.17.129.204:6829/api/statistical-analysis/v1/task/list -d '{"page":1,"limit":1}'`

### Q4: 分析结果文件在哪里？

- 如果指定了 `-o` 参数，结果保存在指定路径
- 如果未指定，结果保存在输入文件同目录，文件名为 `原文件名_result.xlsx`

### Q5: Windows 下 PowerShell 执行报错

确保使用 `&` 操作符调用带路径的可执行文件：

```powershell
& "$env:USERPROFILE\.insight\bin\data_insight_analyzer.exe" -i data.xlsx
```

### Q6: 如何使用自动安装脚本？

运行 `script/install.sh`，脚本会自动：
1. 检测你的操作系统（macOS Intel/ARM、Linux）
2. 检测已安装的 AI CLI 工具（Claude Code/Gemini CLI）
3. 安装对应的 skills 和二进制文件
4. 验证安装结果

**注意事项：**
- 如果两个 AI CLI 工具都未安装，默认安装 Claude Code 的 skills
- **Gemini CLI 用户必须手动完成配置**（检查版本、启用 skills），脚本无法自动完成

### Q7: Gemini CLI 显示版本过低怎么办？

如果 `gemini --version` 显示版本 < v0.24.5：

```bash
# 升级 Gemini CLI
npm update -g @google/generative-ai-cli
# 或
npm install -g @google/generative-ai-cli@latest

# 验证新版本
gemini --version
```

### Q8: Gemini CLI 中找不到 skills 设置选项？

如果在 `/setting` 中搜索 `agent` 后找不到 `skills` 选项：
1. 检查版本是否 >= v0.24.5（旧版本没有此功能）
2. 尝试完整重启 Gemini CLI
3. 检查是否有配置文件权限问题

如果确认版本正确但仍无法找到，说明你的 Gemini CLI 版本可能不支持 skills 功能。

---

## 八、快速参考卡片

### insight skill 常用命令

| 需求 | 说法示例 |
|------|----------|
| 创建任务 | "创建分析任务，文件是 cdid.xlsx，包名 com.xxx，获取 dna 数据" |
| 查询列表 | "查询分析任务列表" |
| 按状态查询 | "查询失败的任务" |
| 查询详情 | "查询任务 xxx 的详情" |
| 获取下载地址 | "获取任务 xxx 的下载地址" |

### analyzer skill 常用命令

| 需求 | 说法示例 |
|------|----------|
| 完整分析 | "分析 data.xlsx" |
| 多发检测 | "对 data.xlsx 做多发检测" |
| 碰撞检测 | "检测 data.xlsx 的碰撞情况" |
| 风险检测 | "分析 data.xlsx 的风险记录" |
| 指定输出 | "分析 data.xlsx，保存到 result.xlsx" |

### report skill 常用命令

| 需求 | 说法示例 |
|------|----------|
| 生成报告 | "根据上面的分析结果生成报告" |
| 直接生成 | "生成数据分析报告" |
| HTML 格式 | "用 HTML 格式输出分析报告" |

---

## 九、版本信息

**当前版本：** v1.0

**更新日志：**
- v1.0 (2025-01-20)
  - 新增 report skill，支持生成 HTML 格式分析报告
  - 添加 Gemini CLI 支持
  - 新增自动化安装脚本 (install.sh)
  - 支持 macOS (Intel/ARM)、Linux、Windows 平台

---

## 十、联系支持

如有问题，请联系工具维护人员。
