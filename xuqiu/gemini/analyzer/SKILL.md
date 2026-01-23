---
name: analyzer
description: 分析 insight 获取的详情数据，进行多发/碰撞/风险检测。当用户需要检测设备数据异常时使用。
user_invokable: true
version: v1.1.2
---

# 数据洞察分析工具 - 本地检测

对 insight 服务返回的详情数据进行多发/碰撞/风险检测。

## 安装位置

跨平台统一安装到用户目录：`~/.insight/bin/`

| 系统 | 可执行文件路径 |
|------|---------------|
| macOS | ~/.insight/bin/data_insight_analyzer |
| Linux | ~/.insight/bin/data_insight_analyzer |
| Windows | %USERPROFILE%\.insight\bin\data_insight_analyzer.exe |

## 输入文件格式

使用 insight 下载的结果文件，或包含以下列的 Excel 文件：

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

## 使用方法

### macOS / Linux
```bash
~/.insight/bin/data_insight_analyzer -i input.xlsx -o result.xlsx
```

### Windows (PowerShell)
```powershell
& "$env:USERPROFILE\.insight\bin\data_insight_analyzer.exe" -i input.xlsx -o result.xlsx
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| -i | 输入文件路径（必填） | - |
| -o | 输出文件路径 | 输入文件名_result.xlsx |
| -t | 检测类型: all/duplicate/impact/risk | all |
| -v | 显示版本号 | - |
| -h | 显示帮助 | - |

## 检测类型

| 类型 | 说明 |
|------|------|
| duplicate | 多发检测 - 检测重复的设备指纹 |
| impact | 碰撞检测 - 检测同一 ID 关联多个设备 |
| risk | 风险检测 - 检测命中风控规则的记录 |
| all | 全部检测（默认） |

## 输出结果

生成的 Excel 文件包含以下 Sheet：

| Sheet 名称 | 说明 |
|------------|------|
| 结论 | 汇总每个 CDID 的检测结果 |
| 多发检测 | 多发记录详情，相同背景色表示同一组 |
| 碰撞检测 | 碰撞记录详情，相同背景色表示同一 ID |
| 风险检测 | 命中风控规则的记录 |

## 调用说明

根据用户操作系统选择正确的命令格式：

**判断操作系统：**
- macOS: `uname` 返回 "Darwin"
- Linux: `uname` 返回 "Linux"
- Windows: 存在 `USERPROFILE` 环境变量，使用 PowerShell

**执行命令：**
- macOS/Linux: `~/.insight/bin/data_insight_analyzer -i <input> -o <output>`
- Windows: `& "$env:USERPROFILE\.insight\bin\data_insight_analyzer.exe" -i <input> -o <output>`

确认输入文件存在后再执行，分析完成后告知用户输出文件位置。
