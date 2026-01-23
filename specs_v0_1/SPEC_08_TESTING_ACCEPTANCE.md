# SPEC_08_TESTING_ACCEPTANCE — 测试与验收

- Spec Version: 0.1.0
- Last Updated: 2026-01-23

## 1. 单元测试（MUST）
- API：请求校验、错误模型、状态码
- Preprocess：schema.json/meta.json/data_quality.json 生成正确；hash 稳定
- Skills：每个 skill 必须有最小 fixture（10-100 行脱敏数据）
  - result.json 必须通过 JSON Schema 校验（result-v1）
  - 核心 metrics 有可预测值（golden）

## 2. 集成测试（MUST）
- 使用 fixture upstream.xlsx（或 mock fetch）跑完整流程：
  - 产出 report.html
  - 产出 bundle.zip
  - GET /jobs/{id} 状态最终为 done

## 3. 契约测试（SHOULD）
- schema 演进时：
  - 旧 skill 遇到新字段不得崩溃（降级 warnings）
  - 缺失关键列时必须输出明确 warnings 或失败（按 critical）

## 4. 验收标准（MVP MUST）
A1. `POST /jobs` → 最终得到可下载的 `report.html` 与 `bundle.zip`  
A2. `GET /jobs/{id}` 可实时查看状态、阶段、进度与错误  
A3. 至少 1 个 skill（basic_stats）可运行并出现在报告中  
A4. 失败可定位：每阶段日志齐全，failed 时有 error.json  
A5. 新增一个 skill 目录即可被发现并执行（无需改主流程代码）  
