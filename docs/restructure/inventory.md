# 阶段一盘点清单（inventory）

## 当前状态判断
- 仓库核心运行目录为 `cdid-analysis-platform/`，本次未迁移该目录，避免影响当前可运行能力。
- 对外交付副本 `delivery/cdid-analysis-platform/` 已删除，避免双份代码并行。
- 根目录混有历史项目与规格文档（`data-insight-service/`、`specs_v0_1/`、`xuqiu/`），已执行归档迁移。
- 根目录存在代理输出与补丁文件，已迁移到 `artifacts/agent_outputs/`。
- 现有工作区包含你之前的业务代码修改（`cdid-analysis-platform/` 下多文件改动），本次未覆盖这些改动。
- 远程仓库已新增 `cdap -> https://github.com/laoyang75/CDAP.git`，`origin` 保持原状。

## 路径分类表

| 路径 | 类型 | 建议动作 | 状态 | 理由 |
|---|---|---|---|---|
| `cdid-analysis-platform/` | 核心业务代码 | 保留原位 | 已保留 | 当前可运行核心，避免路径重构带来运行风险 |
| `delivery/cdid-analysis-platform/` | 对外交付副本 | 删除 | 已删除 | 已切换 Git 单轨开发，不再维护双份代码 |
| `data-insight-service/` | 历史项目 | 迁移至 `archive/legacy/` | 已迁移 | 非当前核心，按生命周期归档 |
| `specs_v0_1/` | 历史规格文档 | 迁移至 `archive/legacy/` | 已迁移 | 需求/规格归档，减少根目录噪音 |
| `xuqiu/` | 历史需求/演示材料 | 迁移至 `archive/legacy/` | 已迁移 | 非当前核心运行路径 |
| `_agent_outputs/` | 代理执行产物 | 迁移至 `artifacts/agent_outputs/` | 已迁移 | 归并构建与中间产物 |
| `lsihi.md` | 零散笔记 | 迁移至 `archive/notes/` | 已迁移 | 与核心工程解耦 |
| `docs/prompt/` | Prompt 文档 | 保留并继续维护 | 已保留 | 属于流程资产 |
| `.DS_Store` | 本地系统文件 | 候选删除并加入忽略 | 待确认 | 不属于项目资产 |
| `delivery.zip` | 历史压缩包 | 删除 | 已删除 | 已切换 Git 交付，不再保留线下压缩包 |

## 已执行迁移摘要
- `data-insight-service -> archive/legacy/data-insight-service`
- `specs_v0_1 -> archive/legacy/specs_v0_1`
- `xuqiu -> archive/legacy/xuqiu`
- `_agent_outputs -> artifacts/agent_outputs`
- `lsihi.md -> archive/notes/lsihi.md`
- `delivery/` 已删除
- `delivery.zip` 已删除
