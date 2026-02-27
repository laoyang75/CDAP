# cdid-analysis-platform 目录边界评估

## 评估结论
- 建议继续采用“根目录做治理，`cdid-analysis-platform/` 做产品代码”的双层结构。
- 根目录不再放第二套可运行代码，`delivery/` 已删除后，代码来源已单轨化。
- 当前主要问题不是代码分叉，而是“项目文档与治理文档分散在两层”，需要边界约定。

## 现状观察
- 核心可运行代码集中在 `cdid-analysis-platform/`。
- 根目录集中放置重构、提示词、历史归档、产物文档：`docs/`、`archive/`、`artifacts/`。
- 历史线下交付目录 `delivery/` 已删除，避免双份维护。
- `delivery` 与核心目录对比结果：仅 `docs/QUICKSTART.md` 为交付目录独有文件，已归档到 `docs/delivery/OFFLINE_QUICKSTART.md`。

## 目录职责建议
- 根目录：仓库治理与跨阶段文档
- `cdid-analysis-platform/`：应用代码、配置、测试、运行脚本、产品内文档
- `archive/`：历史项目与历史资料
- `artifacts/`：补丁和中间产物，不作为源码输入
- `docs/delivery/`：历史线下交付说明归档

## 边界风险
- 若继续在根目录新增业务代码，会再次出现“上下层混写”问题。
- 若产品文档长期分散在 `docs/` 与 `cdid-analysis-platform/docs/`，维护成本会上升。

## 后续治理建议
1. 代码和配置变更统一在 `cdid-analysis-platform/` 下完成。
2. 根目录 `docs/` 仅保留治理类文档（重构、审查、交付策略、流程）。
3. 产品使用文档优先维护在 `cdid-analysis-platform/docs/`。
4. 若需要线下交付，改为从主目录自动打包到 `artifacts/releases/`，不再复制目录。

## 可执行检查规则（建议）
- PR 检查：禁止新增 `delivery/**` 路径。
- PR 检查：根目录禁止新增业务代码文件（只允许 `docs/`、`archive/`、`artifacts/`、`cdid-analysis-platform/` 下变更）。
- 发版检查：发布包仅由 `cdid-analysis-platform/` 生成。
