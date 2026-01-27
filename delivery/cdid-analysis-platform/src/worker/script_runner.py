"""数据库脚本执行器（Python）

用于在 Worker 中执行管理员维护的 Python 脚本（pandas 统计分析），输出 JSON 摘要。

约定：
- 脚本必须提供函数：`analyze(input_file: str, job_info: dict) -> dict`
- `input_file` 为下载到本地的 `raw_data.xlsx` 路径
- 建议脚本使用 `src.worker.data_formats.insight_excel` 做标准化读取
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional


class ScriptExecutionError(RuntimeError):
    pass


def _build_runner_source(user_code: str) -> str:
    return (
        user_code
        + "\n\n"
        + "import json\n"
        + "import sys\n"
        + "\n"
        + "def __codex_entrypoint__():\n"
        + "    payload = json.loads(sys.stdin.read() or '{}')\n"
        + "    input_file = payload.get('input_file')\n"
        + "    job_info = payload.get('job_info') or {}\n"
        + "    if 'analyze' not in globals():\n"
        + "        raise RuntimeError('脚本缺少 analyze(input_file, job_info) 函数')\n"
        + "    result = analyze(input_file, job_info)\n"
        + "    print(json.dumps(result, ensure_ascii=False))\n"
        + "\n"
        + "if __name__ == '__main__':\n"
        + "    __codex_entrypoint__()\n"
    )


async def run_analysis_script(
    *,
    code: str,
    input_file: str,
    job_info: Dict[str, Any],
    timeout_seconds: int = 300,
    cwd: Optional[str] = None,
) -> Dict[str, Any]:
    """执行 Python 分析脚本并返回 JSON"""
    payload = {"input_file": input_file, "job_info": job_info}
    stdin_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    project_root = cwd or os.getcwd()
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = (
        f"{project_root}{os.pathsep}{env.get('PYTHONPATH', '')}".strip(os.pathsep)
    )

    with tempfile.TemporaryDirectory(prefix="cdid_script_") as tmpdir:
        script_path = Path(tmpdir) / "script.py"
        script_path.write_text(_build_runner_source(code), encoding="utf-8")

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            cwd=project_root,
            env=env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(stdin_bytes),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError as e:
            process.kill()
            raise ScriptExecutionError(
                f"脚本执行超时（>{timeout_seconds}s）"
            ) from e

        stdout_text = (stdout or b"").decode("utf-8", errors="replace").strip()
        stderr_text = (stderr or b"").decode("utf-8", errors="replace").strip()

        if process.returncode != 0:
            raise ScriptExecutionError(stderr_text or "脚本执行失败")

        if not stdout_text:
            raise ScriptExecutionError("脚本未输出任何 JSON 结果")

        try:
            result = json.loads(stdout_text)
        except json.JSONDecodeError as e:
            raise ScriptExecutionError(
                f"脚本输出不是合法 JSON：{stdout_text[:200]}"
            ) from e

        if not isinstance(result, dict):
            raise ScriptExecutionError("脚本输出必须是 JSON object（dict）")

        if stderr_text:
            result.setdefault("_warnings", []).append(stderr_text)

        return result

