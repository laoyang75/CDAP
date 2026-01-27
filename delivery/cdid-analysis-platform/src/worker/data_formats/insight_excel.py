"""Insight raw_data.xlsx / CSV 数据读取与字段标准化

标准输入文件：
- Worker 从上游下载的 `raw_data.xlsx`（也允许 CSV）
- 表头通常是“字段名 + 中文说明”的形式，例如：
  - `did(设备主 ID（DID）)`
  - `oaid(设备 OAID)`
  - `cdid(客户设备 ID（CDID）)`

约定（给未来自定义 Python 脚本使用）：
1) 先用 `load_raw_dataframe()` 读取文件
2) 再用 `standardize_device_columns()` 把关键字段映射为统一列名（按需声明 required/optional）：
   - 常用：`did` / `oaid` / `cdid`
   - 其它常用：`android_id` / `sys__boot__id`
3) 其它字段保持原始列名不变（不会被删除）

DNA/DAA 分 sheet：
- 当 `raw_data.xlsx` 包含多个 worksheet（例如 `dna` / `daa`），`load_raw_dataframe()` 会默认读取
  所有 sheet 并合并成一个 DataFrame，并附加列：
  - `message_type`: 来自 sheet 名（dna/daa/unknown）
  - `source_sheet`: 原始 sheet 名

字段映射维护方式（推荐）：
- 默认映射在本文件内置（保证开箱即用）
- 你也可以在 `config/column_mapping.yaml` 追加/覆盖别名（推荐用于适配上游字段新增/改名）
  - 生效方式：修改后重启 API/Worker
  - 可用环境变量覆盖路径：`CDID_COLUMN_MAPPING_FILE=/abs/path/to/column_mapping.yaml`
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import warnings
import yaml


@dataclass(frozen=True)
class StandardizeResult:
    dataframe: pd.DataFrame
    renamed: dict[str, str]


def _normalize_key(value: object) -> str:
    name = str(value).strip().lower() if value is not None else ""
    # 列名经常是 `did(设备主 ID（DID）)` / `did(设备主 id（did）)` 这种形式
    for sep in ("(", "（"):
        if sep in name:
            name = name.split(sep, 1)[0].strip()
    return name


def load_raw_dataframe(input_file: str) -> pd.DataFrame:
    """读取 raw_data 文件为 DataFrame（CSV / Excel）"""
    file_path = Path(input_file)
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {input_file}")

    if file_path.suffix.lower() in [".xlsx", ".xls"]:
        # 有些上游文件会触发 openpyxl 默认样式警告，属于可忽略噪音
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Workbook contains no default style*",
                category=UserWarning,
            )

            # 极端情况下：Excel 容器存在，但没有任何 worksheet（0 worksheets found）
            # 这种场景按“空数据”处理，允许后续脚本输出 0 异常，而不是直接失败。
            try:
                all_sheets = pd.read_excel(input_file, sheet_name=None)
            except ValueError as e:
                if "0 worksheets found" in str(e):
                    return pd.DataFrame()
                raise

        if not isinstance(all_sheets, dict) or not all_sheets:
            return pd.DataFrame()

        frames: list[pd.DataFrame] = []
        for sheet_name, df_sheet in all_sheets.items():
            if df_sheet is None:
                continue
            df_sheet = df_sheet.copy()
            sheet_lower = str(sheet_name).strip().lower()
            if sheet_lower in ("dna", "daa"):
                msg_type = sheet_lower
            else:
                msg_type = "unknown"
            if "message_type" not in df_sheet.columns:
                df_sheet["message_type"] = msg_type
            if "source_sheet" not in df_sheet.columns:
                df_sheet["source_sheet"] = str(sheet_name)
            frames.append(df_sheet)

        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True, sort=False)

    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(input_file)
        if "message_type" not in df.columns:
            df["message_type"] = "unknown"
        if "source_sheet" not in df.columns:
            df["source_sheet"] = "csv"
        return df

    raise ValueError(f"不支持的文件格式: {file_path.suffix}")


_MAPPING_CACHE: Optional[dict[str, list[str]]] = None


def _load_mapping_variants() -> dict[str, list[str]]:
    """加载字段别名映射（内置 + 可选 YAML 覆盖）"""
    global _MAPPING_CACHE
    if _MAPPING_CACHE is not None:
        return _MAPPING_CACHE

    defaults: dict[str, list[str]] = {
        "cdid": ["cdid", "c_did", "client_did", "clientid", "client_id"],
        "did": [
            "did",
            "device_id",
            "deviceid",
            "deviceid_md5",
            "device_fingerprint",
            "设备id",
            "设备指纹",
        ],
        "oaid": ["oaid", "o_aid", "oa_id", "openid", "open_aid", "open_id", "设备标识"],
        "android_id": ["android_id", "androidid", "android_id_md5"],
        "sys__boot__id": ["sys__boot__id", "sys_boot_id", "boot_id", "boot__id"],
    }

    mapping_file = os.getenv("CDID_COLUMN_MAPPING_FILE", "config/column_mapping.yaml")
    mapping_path = Path(mapping_file)
    if mapping_path.exists():
        try:
            raw = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
            if isinstance(raw, dict):
                for key, value in raw.items():
                    if not key:
                        continue
                    if isinstance(value, list):
                        defaults[str(key)] = [str(x) for x in value if str(x).strip()]
        except Exception:
            # 映射文件异常时不阻塞主流程，继续使用内置映射
            pass

    _MAPPING_CACHE = defaults
    return defaults


def standardize_device_columns(
    df: pd.DataFrame,
    *,
    required: Iterable[str] = ("did", "oaid"),
    optional: Iterable[str] = ("cdid",),
) -> StandardizeResult:
    """把 raw_data 的关键设备字段映射为统一列名（did/oaid/cdid）

说明：
- 优先通过“去掉括号说明后的列名前缀”匹配（例如 `did(设备主 ID...)` -> `did`）。
- 同时兼容常见同义列名（device_id / openid 等）。

返回：
- StandardizeResult.dataframe: 重命名后的 df（原地修改后的副本引用）
- StandardizeResult.renamed: 发生重命名的映射表（original -> standard）
"""
    df.columns = [str(col) if col is not None else "" for col in df.columns]

    normalized_to_original: dict[str, str] = {}
    for col in df.columns:
        normalized = _normalize_key(col)
        if normalized and normalized not in normalized_to_original:
            normalized_to_original[normalized] = col

    mapping_variants = _load_mapping_variants()

    renamed: dict[str, str] = {}
    for standard_name, variants in mapping_variants.items():
        if standard_name in df.columns:
            continue
        for variant in variants:
            if variant in normalized_to_original:
                original_col = normalized_to_original[variant]
                df.rename(columns={original_col: standard_name}, inplace=True)
                renamed[str(original_col)] = standard_name
                break

    required_missing = [col for col in required if col not in df.columns]
    if required_missing and not df.empty:
        available = list(df.columns)
        raise ValueError(
            f"缺少必需字段: {required_missing}\n"
            f"可用的列: {available}\n"
            f"建议：确认 raw_data.xlsx 是否为标准格式，或在脚本中补充字段映射。"
        )

    # 空数据时允许继续，给后续逻辑留出统一列名（避免 KeyError）
    if df.empty:
        for col in set(required).union(optional):
            if col not in df.columns:
                df[col] = None

    return StandardizeResult(dataframe=df, renamed=renamed)
