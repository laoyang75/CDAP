# 历史线下交付清单（归档）

> 来源：`delivery/cdid-analysis-platform/docs/DELIVERY_CHECKLIST.md`

# 交付清单（建议随代码一起发给接手人）

## 必需
- [ ] `launcher_web.py` 可启动（启动器页能显示 API/Worker 状态）
- [ ] `config/config.yaml` 已配置正确：
  - [ ] `gemini.cli_path` 可执行（`gemini --version`）
  - [ ] `gemini.model` 可用（例如 `gemini-3-flash-preview` 或你当前环境可用的模型）
  - [ ] `gemini.timeout` 已放大（当前为 3600 秒）
  - [ ] `upstream.base_url` 内网可达（标准模式才需要）
- [ ] 默认管理员可登录后台（启动时会自动初始化）
- [ ] 调试模式可跑通：上传 `raw_data.xlsx` → 出 `analysis.json`、`report_input.json` 与 `report.html`

## 推荐
- [ ] 清空交付包内的运行数据：不携带 `jobs/`、`logs/`、`*.db`
- [ ] 交付包只保留一个启动入口：`launcher_web.py`
- [ ] 把真实样例 `raw_data.xlsx`（可脱敏）单独提供给接手人做回归测试
