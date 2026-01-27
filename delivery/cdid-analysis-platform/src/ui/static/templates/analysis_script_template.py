"""
CDID 分析脚本模板（analysis）

用途：
- 这个脚本会在 Worker 中运行（由“管线管理”选择分析脚本）
- 输入是上游下载到本地的 `raw_data.xlsx`（也可能是 CSV）
- 你只需要写 pandas 统计逻辑，输出一个 dict（会被序列化成 JSON）

重要说明（字段与 Excel 变化）：
- raw_data.xlsx 的列名经常是：字段名 + 括号中文说明，例如 `did(设备主 ID（DID）)`
- 平台会做一层“字段标准化”，把关键字段统一重命名成：
  - did / oaid / cdid / android_id / sys__boot__id
- 当上游字段**新增别名/改名**时，优先去改映射文件：
  - `config/column_mapping.yaml`
  修改后重启 API/Worker 即可生效
- 当上游返回的 xlsx 分为多个 sheet（例如 `dna` / `daa`），平台会读取所有 sheet 并合并，
  并自动补充列：
  - message_type：dna/daa/unknown（来自 sheet 名）
  - source_sheet：原始 sheet 名

约定：
- 必须提供函数：analyze(input_file: str, job_info: dict) -> dict
"""

from __future__ import annotations

import pandas as pd

from src.worker.data_formats.insight_excel import (
    load_raw_dataframe,
    standardize_device_columns,
)


def analyze(input_file: str, job_info: dict) -> dict:
    """
    input_file:
      - Worker 下载的 raw_data.xlsx 路径（字符串）
    job_info:
      - 任务信息（dict），包含 job_id/name/package_name/start_date/end_date/message_types 等

    返回：
      - dict（会写入 pipelines/<pipeline_id>/analysis.json，供 Gemini 生成 report.html）
    """

    # 1) 读取原始数据
    df = load_raw_dataframe(input_file)

    # 2) 字段标准化：把各种列名映射到统一列名
    # required：你的统计逻辑必须依赖的字段
    # optional：可能用到但不强依赖的字段
    df = standardize_device_columns(
        df,
        required=("did", "oaid"),
        optional=("cdid", "android_id", "sys__boot__id"),
    ).dataframe

    # 3) 空数据兜底：必须返回结构化结果，不能抛异常（否则任务会失败）
    if df.empty:
        return {
            "task_info": {
                "job_id": job_info.get("job_id"),
                "name": job_info.get("name"),
                "package_name": job_info.get("package_name"),
                "start_date": job_info.get("start_date"),
                "end_date": job_info.get("end_date"),
                "message_types": job_info.get("message_types"),
            },
            "statistics": {
                "total_rows": 0,
                "unique_did": 0,
                "unique_oaid": 0,
            },
            "notes": [
                "raw_data 为空：可能是上游返回空表、或 Excel 解析失败（0 worksheets）。",
                "如果是字段名变化，请在 config/column_mapping.yaml 增加别名映射后重试。",
            ],
            "samples": [],
        }

    # 4) 你自己的统计逻辑（示例：计算 did/oaid 比例）
    total_rows = int(len(df))
    unique_did = int(df["did"].nunique(dropna=True))
    unique_oaid = int(df["oaid"].nunique(dropna=True))
    ratio = round(unique_did / unique_oaid, 4) if unique_oaid else None

    # 若需要分别统计 dna/daa，可按 message_type 分组：
    # by_type = df.groupby('message_type').size().to_dict()

    # 5) 返回结果（建议字段命名清晰、便于 Prompt 引用）
    # 注意：不要塞入过大的原始数据（会导致 Gemini 输入过大、生成慢甚至卡住）
    # 建议只返回：
    # - 汇总指标 statistics
    # - 少量 samples（例如 head(20)）
    return {
        "task_info": {
            "job_id": job_info.get("job_id"),
            "name": job_info.get("name"),
            "package_name": job_info.get("package_name"),
            "start_date": job_info.get("start_date"),
            "end_date": job_info.get("end_date"),
            "message_types": job_info.get("message_types"),
        },
        "statistics": {
            "total_rows": total_rows,
            "unique_did": unique_did,
            "unique_oaid": unique_oaid,
            "did_per_oaid_ratio": ratio,
        },
        "samples": df[["did", "oaid"]].head(20).to_dict(orient="records"),
    }
