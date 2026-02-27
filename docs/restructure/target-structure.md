# 目标目录结构（target-structure）

## 设计原则
- 核心运行路径稳定：`cdid-analysis-platform/` 不做高风险位移。
- 生命周期分层：`core`、`delivery`、`archive`、`artifacts` 分离。
- 历史优先归档：不确定可删除项先迁移到 `archive/`。
- 产物集中管理：补丁、临时输出统一放入 `artifacts/`。
- 文档可追踪：重构方案与执行记录集中在 `docs/restructure/`。

## 当前执行后结构（简化 tree）

```text
.
├── cdid-analysis-platform/            # 核心可运行代码（保留原位）
├── delivery/
│   └── cdid-analysis-platform/        # 对外交付副本（保留原位）
├── archive/
│   ├── legacy/
│   │   ├── data-insight-service/
│   │   ├── specs_v0_1/
│   │   └── xuqiu/
│   └── notes/
│       └── lsihi.md
├── artifacts/
│   └── agent_outputs/
│       ├── *.patch
│       └── *.md
└── docs/
    ├── prompt/
    └── restructure/
```

## 后续可选结构（不在本阶段执行）
- 若交付副本长期存在，建议后续拆分为独立仓库，避免核心仓库中出现双份代码。
- 若 `delivery.zip` 仍是交付资产，建议固定为 `artifacts/releases/` 并增加生成脚本。
