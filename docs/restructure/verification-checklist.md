# 重构后验证清单（verification-checklist）

## 目录与资产验证
- [x] 核心目录仍存在：`cdid-analysis-platform/`
- [x] 交付目录仍存在：`delivery/cdid-analysis-platform/`
- [x] 历史项目已归档：`archive/legacy/data-insight-service/`
- [x] 历史规格已归档：`archive/legacy/specs_v0_1/`
- [x] 历史需求已归档：`archive/legacy/xuqiu/`
- [x] 代理产物已归档：`artifacts/agent_outputs/`
- [x] 零散笔记已归档：`archive/notes/lsihi.md`

## Git 验证
- [x] 当前分支：`refactor/restructure-docs`
- [x] 远端 `cdap` 已配置：`https://github.com/laoyang75/CDAP.git`
- [x] 原远端 `origin` 保持不变
- [ ] 重构提交已 push 到 `cdap/refactor/restructure-docs`（待执行）

## 运行风险验证
- [x] 未迁移 `cdid-analysis-platform/` 路径，核心启动路径保持不变
- [x] 未改业务逻辑代码（仅目录治理与文档）
- [ ] 全量自动化测试（未执行；建议在你确认后执行）

## 建议补充验证命令
```bash
# 1) 查看本次结构变更
git status --short

# 2) 核心工程基础检查
cd cdid-analysis-platform
python -m pytest -q

# 3) 返回根目录推送分支
cd ..
git push -u cdap refactor/restructure-docs
```
