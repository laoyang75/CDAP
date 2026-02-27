# data_fenxi 仓库说明

本仓库已切换为 **Git 持续协作模式**，不再以线下交付副本作为主开发方式。

## 当前开发主目录
- 主代码目录：`cdid-analysis-platform/`
- 该目录是唯一的功能开发、修复、测试与评审来源。

## 目录分工
- `cdid-analysis-platform/`：核心可运行项目（主开发目录）
- `docs/`：统一文档目录（含 prompt、重构文档、交付归档文档）
- `archive/`：历史项目与历史资料归档
- `artifacts/`：执行产物、补丁等中间文件
- `delivery/`：历史线下交付目录（已彻底移除）

## 关于 delivery 的结论
`delivery/` 在过去用于线下交付。当前转为 Git 协作后，不再需要维护双份代码。

为避免分叉维护风险，现执行以下规则：
1. 所有代码改动只在 `cdid-analysis-platform/` 进行。
2. 交付相关历史文档统一放在 `docs/delivery/`。
3. `delivery/` 代码目录已删除，不再作为任何开发/交付入口。

更多说明见：
- `docs/delivery/STATUS.md`
- `docs/delivery/README.md`

## 历史交付文档（已收敛）
- `docs/delivery/OFFLINE_DELIVERY_README.md`
- `docs/delivery/OFFLINE_QUICKSTART.md`
- `docs/delivery/OFFLINE_HANDOFF.md`
- `docs/delivery/OFFLINE_DELIVERY_CHECKLIST.md`

## 开发与运行（核心项目）
在 `cdid-analysis-platform/` 下执行：

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python launcher_web.py
```

启动后访问：`http://localhost:5555`

## Git 远端
- `origin`: `https://github.com/laoyang75/data_fenxi.git`
- `cdap`: `https://github.com/laoyang75/CDAP.git`

日常建议：在功能分支提交后，通过 PR 合并。
