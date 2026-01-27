"""管理端默认数据初始化

目标：
- 本地首次启动时，让“管线管理/脚本管理”页面有可用数据可操作
- 避免每次启动重复插入（幂等）
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.db import Pipeline, Script


DEFAULT_PROMPT_SCRIPT_NAME = "default_report_prompt"
DEFAULT_ANALYSIS_SCRIPT_NAME = "default_duofa_analysis"
DEFAULT_PIPELINE_NAME = "标准多发检测管线"

SYSBOOT_ANALYSIS_SCRIPT_NAME = "sysboot_anomaly_analysis"
SYSBOOT_PROMPT_SCRIPT_NAME = "sysboot_anomaly_report_prompt"
SYSBOOT_PIPELINE_NAME = "SYSBOOT 异常分析管线"


def init_default_admin_assets(db: Session) -> None:
    """初始化默认 Prompt 脚本与默认管线（幂等）"""

    def upsert_script(*, name: str, description: str, script_type: str, code: str) -> Script:
        script = db.query(Script).filter(Script.name == name).first()
        if not script:
            script = Script(
                name=name,
                description=description,
                script_type=script_type,
                is_active=True,
                code=code,
            )
            db.add(script)
            db.commit()
            db.refresh(script)
            return script

        changed = False
        if script.description != description:
            script.description = description
            changed = True
        if script.script_type != script_type:
            script.script_type = script_type
            changed = True
        if script.code != code:
            script.code = code
            changed = True
        if script.is_active is not True:
            script.is_active = True
            changed = True
        if changed:
            db.commit()
            db.refresh(script)
        return script

    prompt_script = upsert_script(
        name=DEFAULT_PROMPT_SCRIPT_NAME,
        description="默认报告 Prompt（用于 Gemini 输出控制）",
        script_type="prompt",
        code=(
            "请基于输入 JSON 生成一份专业的中文 HTML 数据分析报告。\n"
            "要求：\n"
            "1) 包含：执行摘要、数据统计（表格）、分析结论、建议。\n"
            "2) 若数据为空或字段缺失，请明确原因并给出下一步建议。\n"
            "3) 若输入中包含 statistics.by_message_type（dna/daa），请分别展示两类数据的统计对比。\n"
            "4) 只输出完整 HTML（包含 <html><head><body>）。\n"
        ),
    )

    analysis_script = upsert_script(
        name=DEFAULT_ANALYSIS_SCRIPT_NAME,
        description="默认多发检测分析脚本（支持 dna/daa 分 sheet；pandas 统计输出摘要 JSON）",
        script_type="analysis",
        code=(
            "import pandas as pd\n"
            "from src.worker.data_formats.insight_excel import load_raw_dataframe, standardize_device_columns\n"
            "\n"
            "def _calc(sub: pd.DataFrame) -> dict:\n"
            "    total_count = int(len(sub))\n"
            "    if total_count == 0:\n"
            "        return {\n"
            "            'total_count': 0,\n"
            "            'unique_cdid_count': 0,\n"
            "            'unique_did_count': 0,\n"
            "            'unique_oaid_count': 0,\n"
            "            'ratio': 0,\n"
            "        }\n"
            "    unique_did_count = int(sub['did'].nunique(dropna=True))\n"
            "    unique_oaid_count = int(sub['oaid'].nunique(dropna=True))\n"
            "    unique_cdid_count = int(sub['cdid'].nunique(dropna=True)) if 'cdid' in sub.columns else 0\n"
            "    ratio = round(unique_did_count / unique_oaid_count, 4) if unique_oaid_count else 0\n"
            "    return {\n"
            "        'total_count': total_count,\n"
            "        'unique_cdid_count': unique_cdid_count,\n"
            "        'unique_did_count': unique_did_count,\n"
            "        'unique_oaid_count': unique_oaid_count,\n"
            "        'ratio': ratio,\n"
            "    }\n"
            "\n"
            "def analyze(input_file: str, job_info: dict) -> dict:\n"
            "    df = load_raw_dataframe(input_file)\n"
            "    if 'message_type' not in df.columns:\n"
            "        df['message_type'] = 'unknown'\n"
            "    df = standardize_device_columns(df).dataframe\n"
            "\n"
            "    overall = _calc(df)\n"
            "    by_type = {}\n"
            "    for t in ['dna', 'daa']:\n"
            "        by_type[t] = _calc(df[df['message_type'] == t])\n"
            "    if 'unknown' in df['message_type'].astype(str).unique().tolist():\n"
            "        by_type['unknown'] = _calc(df[df['message_type'] == 'unknown'])\n"
            "\n"
            "    sample_data = {\n"
            "        'dna': df[df['message_type'] == 'dna'].head(20).to_dict(orient='records'),\n"
            "        'daa': df[df['message_type'] == 'daa'].head(20).to_dict(orient='records'),\n"
            "    }\n"
            "\n"
            "    return {\n"
            "        'task_info': {\n"
            "            'job_id': job_info.get('job_id'),\n"
            "            'name': job_info.get('name'),\n"
            "            'package_name': job_info.get('package_name'),\n"
            "            'start_date': job_info.get('start_date'),\n"
            "            'end_date': job_info.get('end_date'),\n"
            "            'message_types': job_info.get('message_types'),\n"
            "        },\n"
            "        'statistics': {\n"
            "            **overall,\n"
            "            'by_message_type': by_type,\n"
            "        },\n"
            "        'sample_data': sample_data,\n"
            "    }\n"
        ),
    )

    sysboot_analysis_script = upsert_script(
        name=SYSBOOT_ANALYSIS_SCRIPT_NAME,
        description="SYSBOOT 异常分析（支持 dna/daa 分 sheet）：同一 sys__boot__id 不应对应多个 android_id",
        script_type="analysis",
        code=(
            "import pandas as pd\n"
            "from src.worker.data_formats.insight_excel import load_raw_dataframe, standardize_device_columns\n"
            "\n"
            "def _analyze_one(df: pd.DataFrame) -> dict:\n"
            "    total_count = int(len(df))\n"
            "    total_unique_did = int(df['did'].nunique(dropna=True)) if total_count else 0\n"
            "    if total_count == 0:\n"
            "        return {\n"
            "            'total_count': 0,\n"
            "            'total_unique_did_count': 0,\n"
            "            'abnormal_group_count': 0,\n"
            "            'abnormal_row_count': 0,\n"
            "            'abnormal_report_ratio': 0,\n"
            "            'abnormal_unique_did_count': 0,\n"
            "            'abnormal_did_ratio': 0,\n"
            "            'abnormal_groups': [],\n"
            "        }\n"
            "\n"
            "    g = df.groupby('sys__boot__id')['android_id'].nunique(dropna=True)\n"
            "    abnormal_sysboots = g[g > 1].index\n"
            "    abnormal_rows = df[df['sys__boot__id'].isin(abnormal_sysboots)]\n"
            "    abnormal_row_count = int(len(abnormal_rows))\n"
            "    abnormal_report_ratio = round(abnormal_row_count / total_count, 4) if total_count else 0\n"
            "    abnormal_unique_did_count = int(abnormal_rows['did'].nunique(dropna=True)) if abnormal_row_count else 0\n"
            "    abnormal_did_ratio = round(abnormal_unique_did_count / total_unique_did, 4) if total_unique_did else 0\n"
            "\n"
            "    abnormal_groups = []\n"
            "    if abnormal_row_count:\n"
            "        group_df = (\n"
            "            abnormal_rows.groupby('sys__boot__id')\n"
            "            .agg(\n"
            "                android_id_count=('android_id', lambda s: int(pd.Series(s).nunique(dropna=True))),\n"
            "                did_count=('did', lambda s: int(pd.Series(s).nunique(dropna=True))),\n"
            "                row_count=('did', 'size'),\n"
            "            )\n"
            "            .reset_index()\n"
            "            .sort_values(['android_id_count', 'row_count'], ascending=False)\n"
            "        )\n"
            "        for _, row in group_df.head(20).iterrows():\n"
            "            sb = row['sys__boot__id']\n"
            "            subset = abnormal_rows[abnormal_rows['sys__boot__id'] == sb]\n"
            "            abnormal_groups.append({\n"
            "                'sys__boot__id': sb,\n"
            "                'android_id_count': int(row['android_id_count']),\n"
            "                'did_count': int(row['did_count']),\n"
            "                'row_count': int(row['row_count']),\n"
            "                'android_ids_sample': [x for x in subset['android_id'].dropna().astype(str).unique().tolist()[:5]],\n"
            "                'dids_sample': [x for x in subset['did'].dropna().astype(str).unique().tolist()[:5]],\n"
            "            })\n"
            "\n"
            "    return {\n"
            "        'total_count': total_count,\n"
            "        'total_unique_did_count': total_unique_did,\n"
            "        'abnormal_group_count': int(len(abnormal_sysboots)),\n"
            "        'abnormal_row_count': abnormal_row_count,\n"
            "        'abnormal_report_ratio': abnormal_report_ratio,\n"
            "        'abnormal_unique_did_count': abnormal_unique_did_count,\n"
            "        'abnormal_did_ratio': abnormal_did_ratio,\n"
            "        'abnormal_groups': abnormal_groups,\n"
            "    }\n"
            "\n"
            "def analyze(input_file: str, job_info: dict) -> dict:\n"
            "    df = load_raw_dataframe(input_file)\n"
            "    if 'message_type' not in df.columns:\n"
            "        df['message_type'] = 'unknown'\n"
            "    df = standardize_device_columns(\n"
            "        df,\n"
            "        required=('did', 'sys__boot__id', 'android_id'),\n"
            "        optional=('oaid', 'cdid'),\n"
            "    ).dataframe\n"
            "\n"
            "    overall = _analyze_one(df)\n"
            "    by_type = {}\n"
            "    groups_by_type = {}\n"
            "    for t in ['dna', 'daa']:\n"
            "        res = _analyze_one(df[df['message_type'] == t])\n"
            "        by_type[t] = {k: v for k, v in res.items() if k != 'abnormal_groups'}\n"
            "        groups_by_type[t] = res.get('abnormal_groups', [])\n"
            "\n"
            "    return {\n"
            "        'task_info': {\n"
            "            'job_id': job_info.get('job_id'),\n"
            "            'name': job_info.get('name'),\n"
            "            'package_name': job_info.get('package_name'),\n"
            "            'start_date': job_info.get('start_date'),\n"
            "            'end_date': job_info.get('end_date'),\n"
            "            'message_types': job_info.get('message_types'),\n"
            "        },\n"
            "        'statistics': {\n"
            "            **{k: v for k, v in overall.items() if k != 'abnormal_groups'},\n"
            "            'by_message_type': by_type,\n"
            "        },\n"
            "        'abnormal_groups': overall.get('abnormal_groups', []),\n"
            "        'abnormal_groups_by_message_type': groups_by_type,\n"
            "        'sample_data': {\n"
            "            'dna': df[df['message_type'] == 'dna'].head(20).to_dict(orient='records'),\n"
            "            'daa': df[df['message_type'] == 'daa'].head(20).to_dict(orient='records'),\n"
            "        },\n"
            "    }\n"
        ),
    )

    sysboot_prompt_script = upsert_script(
        name=SYSBOOT_PROMPT_SCRIPT_NAME,
        description="SYSBOOT 异常分析报告 Prompt（纯文本）",
        script_type="prompt",
        code=(
            "你是一名专业的数据分析师，请根据输入 JSON 生成中文 HTML 报告。\n"
            "主题：SYSBOOT 异常（同一 sys__boot__id 不应对应多个 android_id）。\n"
            "\n"
            "报告要求：\n"
            "1) 只输出完整 HTML（含 <html><head><body>），不要输出 markdown code fence。\n"
            "2) 报告结构：执行摘要、核心指标、异常明细（表格）、原因分析、排查建议。\n"
            "3) 若 statistics.by_message_type 存在（dna/daa），请分别展示两类数据的异常占比与异常明细对比。\n"
            "4) 若 statistics.abnormal_row_count = 0，请明确说明“未发现异常”，并给出数据质量确认建议。\n"
            "5) 核心指标必须展示：\n"
            "   - abnormal_did_ratio（异常 did 占比，分母为 total_unique_did_count）\n"
            "   - abnormal_report_ratio（异常上报占比，分母为 total_count）\n"
            "6) 异常明细：优先展示 abnormal_groups_by_message_type（dna/daa 各最多 20 条）；如不存在则用 abnormal_groups。\n"
        ),
    )

    pipeline = db.query(Pipeline).filter(Pipeline.name == DEFAULT_PIPELINE_NAME).first()
    desired_config = {
        "analysis_script_id": analysis_script.id,
        "report_prompt_script_id": prompt_script.id,
        "is_default": True,
    }
    if not pipeline:
        pipeline = Pipeline(
            name=DEFAULT_PIPELINE_NAME,
            description="默认管线：Python 分析脚本 + 报告 Prompt",
            is_active=True,
            config=desired_config,
        )
        db.add(pipeline)
        db.commit()
    else:
        cfg = pipeline.config if isinstance(pipeline.config, dict) else {}
        needs_update = any(cfg.get(k) != v for k, v in desired_config.items())
        if needs_update:
            pipeline.config = {**cfg, **desired_config}
            if not pipeline.description:
                pipeline.description = "默认管线：Python 分析脚本 + 报告 Prompt"
            pipeline.is_active = True
            db.commit()

    sysboot_pipeline = db.query(Pipeline).filter(Pipeline.name == SYSBOOT_PIPELINE_NAME).first()
    if not sysboot_pipeline:
        sysboot_pipeline = Pipeline(
            name=SYSBOOT_PIPELINE_NAME,
            description="SYSBOOT 异常分析（sys__boot__id vs android_id）",
            is_active=True,
            config={
                "analysis_script_id": sysboot_analysis_script.id,
                "report_prompt_script_id": sysboot_prompt_script.id,
                "is_default": False,
            },
        )
        db.add(sysboot_pipeline)
        db.commit()
