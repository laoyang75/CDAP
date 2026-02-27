# 迁移计划与实施（migration-plan）

## Step 1：建立重构分支
- 命令：`git checkout -b refactor/restructure-docs`
- 结果：已执行成功。
- 风险：在脏工作区切分支，可能混入历史改动。
- 回滚：`git checkout main`。

## Step 2：创建归档与产物目录骨架
- 命令：`mkdir -p archive/legacy archive/notes artifacts`
- 结果：已执行成功。
- 风险：低（仅新增目录）。
- 回滚：删除新增空目录。

## Step 3：迁移历史项目到归档区
- 命令：
  - `git mv data-insight-service archive/legacy/data-insight-service`
  - `git mv specs_v0_1 archive/legacy/specs_v0_1`
  - `git mv xuqiu archive/legacy/xuqiu`
- 结果：已执行成功（保留 Git 历史）。
- 风险：引用路径可能失效（若存在外部脚本依赖旧路径）。
- 回滚：反向 `git mv` 回原路径。

## Step 4：迁移代理产物与零散笔记
- 命令：
  - `git mv _agent_outputs artifacts/agent_outputs`
  - `mv lsihi.md archive/notes/lsihi.md`
- 结果：已执行成功。
- 风险：若有本地脚本引用旧路径需同步调整。
- 回滚：将目录与文件移动回原位置。

## Step 5：补齐治理文档
- 命令：在 `docs/restructure/` 写入盘点、目标结构、迁移与验证文档。
- 结果：已执行。
- 风险：低。
- 回滚：删除新增文档。

## Step 6：Git 远端治理与推送准备
- 已执行：新增远端 `cdap` 指向 `https://github.com/laoyang75/CDAP.git`。
- 保留：`origin` 不变，避免影响原工作流。
- 推送命令：`git push -u cdap refactor/restructure-docs`

## 不在本阶段执行的动作
- 不做核心业务逻辑改写。
- 不删除不确定文件，仅归档。
- 不处理既有业务代码改动内容（仅做结构治理范围内动作）。
