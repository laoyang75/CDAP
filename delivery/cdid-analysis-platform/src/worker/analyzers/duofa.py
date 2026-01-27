"""多发检测分析器

实现：did 去重数 / oaid 去重数 > threshold 的判定逻辑。

输入约定：上游下载的 `raw_data.xlsx`，列名可能带中文说明（例如 `did(设备主 ID（DID）)`）。
解析与字段标准化统一放在 `src.worker.data_formats.insight_excel`，便于后续新增脚本复用。
"""

from typing import Dict, List

import pandas as pd

from src.config import Config
from src.worker.data_formats.insight_excel import load_raw_dataframe, standardize_device_columns


class DuofaAnalyzer:
    """多发检测分析器"""

    def __init__(self, config: Config):
        self.config = config
        self.threshold = config.duofa_threshold

    def analyze(self, input_file: str, job_info: dict) -> dict:
        """执行多发检测分析

        Args:
            input_file: 输入文件路径（CSV/Excel）
            job_info: 任务信息

        Returns:
            dict: 分析结果，包含:
                - task_info: 任务基本信息
                - statistics: 统计数据
                - background: 背景知识
                - sample_data: 样本数据

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 数据格式错误
        """
        df = load_raw_dataframe(input_file)
        df = standardize_device_columns(df).dataframe

        # 基本统计
        total_count = len(df)
        if "cdid" not in df.columns:
            df["cdid"] = None
        unique_cdid_count = df["cdid"].nunique()
        unique_did_count = df["did"].nunique()
        unique_oaid_count = df["oaid"].nunique()

        # 计算多发比率
        ratio = unique_did_count / unique_oaid_count if unique_oaid_count > 0 else 0
        is_duofa = ratio > self.threshold

        # 分析多发分组（按 oaid 分组，统计关联的 did 数量）
        duofa_groups = []
        if is_duofa:
            oaid_groups = df.groupby("oaid")["did"].nunique().reset_index()
            oaid_groups.columns = ["oaid", "did_count"]
            oaid_groups = oaid_groups[oaid_groups["did_count"] > 1].sort_values(
                "did_count", ascending=False
            )

            for _, row in oaid_groups.head(10).iterrows():
                oaid = row["oaid"]
                did_count = row["did_count"]

                # 获取该 oaid 关联的所有 did
                associated_dids = (
                    df[df["oaid"] == oaid]["did"].unique().tolist()[:5]
                )  # 最多取5个

                duofa_groups.append(
                    {
                        "oaid": oaid,
                        "did_count": int(did_count),
                        "associated_dids": associated_dids,
                    }
                )

        # 准备样本数据（前20行）
        sample_data = df.head(20).to_dict(orient="records")

        # 构建结果
        result = {
            "task_info": {
                "job_id": job_info.get("job_id"),
                "name": job_info.get("name"),
                "package_name": job_info.get("package_name"),
                "start_date": job_info.get("start_date"),
                "end_date": job_info.get("end_date"),
            },
            "statistics": {
                "total_count": int(total_count),
                "unique_cdid_count": int(unique_cdid_count),
                "unique_did_count": int(unique_did_count),
                "unique_oaid_count": int(unique_oaid_count),
                "ratio": round(ratio, 2),
                "threshold": self.threshold,
                "is_duofa": is_duofa,
                "duofa_groups": duofa_groups,
            },
            "background": {
                "what_is_duofa": "多发是指多个不同的设备指纹（DID）共享相同的开放匿名设备标识符（OAID）的现象。",
                "why_detect": "多发检测可以识别异常的设备行为模式，帮助发现潜在的作弊、刷量等风险行为。",
                "detection_method": f"通过计算 DID去重数 / OAID去重数 的比率，当比率大于 {self.threshold} 时判定为多发。",
                "interpretation": {
                    "normal": f"正常情况下，比率应接近 1，表示一个 OAID 对应一个 DID。",
                    "duofa": f"比率 > {self.threshold} 表示一个 OAID 对应多个 DID，存在多发现象。",
                    "current_status": "存在多发现象" if is_duofa else "未检测到多发现象",
                },
            },
            "sample_data": sample_data,
        }

        return result

    def get_field_mapping(self) -> Dict[str, str]:
        """获取字段映射说明

        Returns:
            Dict: 字段名称和说明的映射
        """
        return {
            "cdid": "CDID - 客户端设备唯一标识",
            "did": "DID - 设备指纹",
            "oaid": "OAID - 开放匿名设备标识符",
            "imei": "IMEI - 国际移动设备识别码（可选）",
            "android_id": "Android ID - Android 设备标识（可选）",
            "rc_rules": "风控规则版本（可选）",
            "rc_scenes": "风控场景标识（可选）",
        }
