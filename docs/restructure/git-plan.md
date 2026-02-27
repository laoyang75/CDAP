# Git 方案（git-plan）

## 远程与分支策略
- `origin`: `https://github.com/laoyang75/data_fenxi.git`（保留原远端）
- `cdap`: `https://github.com/laoyang75/CDAP.git`（新增目标远端）
- 本次工作分支：`refactor/restructure-docs`
- 建议长期分支模型：`main` / `dev` / `refactor/*` / `feature/*`

## 建议提交序列
1. `refactor: archive legacy directories and agent outputs`
- 内容：历史目录和产物迁移（`git mv` 为主）。
2. `docs: add stage1 restructure inventory and migration docs`
- 内容：`docs/restructure/` 文档与 `docs/prompt/` 更新。
3. `refactor: remove legacy delivery duplicate tree`
- 内容：删除 `delivery/` 与 `delivery.zip`，彻底切换到 Git 单轨开发。

## 实际提交策略（避免混入既有改动）
- 仅暂存本次结构治理相关路径：
  - `archive/`
  - `artifacts/`
  - `docs/prompt/`
  - `docs/restructure/`
- 不暂存你已有业务改动路径：
  - `cdid-analysis-platform/`（已有改动）
  - `.DS_Store`

## 推送命令
```bash
git push -u cdap refactor/restructure-docs
```

## 若 push 失败（认证或网络）
- 检查认证：`gh auth status` 或 GitHub Token/SSH。
- 重试命令：`git push -u cdap refactor/restructure-docs`
