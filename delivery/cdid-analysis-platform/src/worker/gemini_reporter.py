"""Gemini CLI 报告生成器

通过管道将分析结果传递给 Gemini CLI，生成 HTML 报告
"""

import asyncio
import contextlib
import json
import os
import subprocess
from pathlib import Path
from typing import Callable, Dict, Optional

from src.config import Config


class GeminiReporter:
    """Gemini CLI 报告生成器"""

    def __init__(self, config: Config):
        self.config = config
        self.cli_path = config.gemini_cli_path
        self.skill_name = config.gemini_skill_name
        self.timeout = config.gemini_timeout

    @staticmethod
    def _extract_html(text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines and lines[0].lstrip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            stripped = "\n".join(lines).strip()
        return stripped

    @staticmethod
    def _should_retry_with_fallback(stderr: str) -> bool:
        lower = (stderr or "").lower()
        return any(
            marker in lower
            for marker in [
                "model_capacity_exhausted",
                "no capacity available",
                "\"code\": 429",
                "resource_exhausted",
                "rateLimitExceeded".lower(),
            ]
        )

    @staticmethod
    def _build_html_only_prompt(custom_prompt: Optional[str] = None) -> str:
        base = (
            "你是一个文本生成模型。不要调用任何工具/技能，不要解释过程，不要输出 markdown code fence。"
            "只输出一个完整可直接保存为 report.html 的 HTML 文本（必须以 <!doctype html> 或 <html> 开头）。"
        )
        if custom_prompt and custom_prompt.strip():
            return base + "\n\n" + custom_prompt.strip()
        return (
            base
            + "基于输入 JSON 生成中文数据分析报告：包含执行摘要、数据统计（表格）、分析结论、建议。"
            "如果数据为空或字段缺失，也要给出原因说明和后续建议。"
        )

    @staticmethod
    def _compact_payload(value: object, *, max_str: int = 2000, max_list: int = 50, max_depth: int = 6) -> object:
        """裁剪传给 Gemini 的 JSON，避免超大字段/列表导致 CLI 卡死或生成极慢。

        规则（保守）：
        - str 超过 max_str 截断
        - list 超过 max_list 截断并附带 `__truncated__`
        - dict 深度超过 max_depth 时停止递归
        """
        if max_depth <= 0:
            return "__truncated_depth__"

        if isinstance(value, str):
            if len(value) > max_str:
                return value[:max_str] + f"...(__truncated__:{len(value) - max_str})"
            return value
        if isinstance(value, (int, float)) or value is None or isinstance(value, bool):
            return value
        if isinstance(value, list):
            if len(value) > max_list:
                return (
                    [GeminiReporter._compact_payload(v, max_str=max_str, max_list=max_list, max_depth=max_depth - 1) for v in value[:max_list]]
                    + [{"__truncated__": len(value) - max_list}]
                )
            return [GeminiReporter._compact_payload(v, max_str=max_str, max_list=max_list, max_depth=max_depth - 1) for v in value]
        if isinstance(value, dict):
            out: dict = {}
            for k, v in list(value.items())[:200]:
                out[str(k)] = GeminiReporter._compact_payload(v, max_str=max_str, max_list=max_list, max_depth=max_depth - 1)
            if len(value) > 200:
                out["__truncated_keys__"] = len(value) - 200
            return out
        return str(value)

    async def _run_gemini(
        self,
        prompt: str,
        data_json: str,
        model: Optional[str],
        *,
        pid_callback: Optional[Callable[[int], None]] = None,
    ) -> tuple[str, str, int]:
        cmd = [self.cli_path]
        if model:
            cmd += ["-m", model]
        # -p 已 deprecated，但当前版本仍支持；后续可切到 positional prompt
        cmd += ["-p", prompt]

        # asyncio 子进程在 macOS + 大 stdin 场景偶发卡住，改为 Popen + communicate 放到线程池
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy(),
        )
        if pid_callback:
            pid_callback(proc.pid)

        try:
            stdout, stderr = await asyncio.wait_for(
                asyncio.to_thread(proc.communicate, data_json.encode("utf-8")),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError as e:
            with contextlib.suppress(Exception):
                proc.kill()
            with contextlib.suppress(Exception):
                await asyncio.to_thread(proc.communicate)
            raise e

        rc = proc.returncode or 0
        return (
            (stdout or b"").decode("utf-8", errors="replace"),
            (stderr or b"").decode("utf-8", errors="replace"),
            rc,
        )

    async def generate_report(
        self,
        analysis_result: Dict,
        output_path: str,
        *,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
        pid_callback: Optional[Callable[[int], None]] = None,
    ) -> None:
        """生成 HTML 报告

        Args:
            analysis_result: 分析结果（字典）
            output_path: 输出文件路径

        Raises:
            subprocess.CalledProcessError: Gemini CLI 执行失败
            TimeoutError: 执行超时
            FileNotFoundError: Gemini CLI 未找到
        """
        # 准备数据包（对 Gemini 输入做裁剪，避免超大字段导致卡死/极慢）
        compacted = self._compact_payload(analysis_result)
        data_json = json.dumps(compacted, ensure_ascii=False, indent=2)

        # Prompt：强制输出 HTML，避免 Gemini CLI 进入“工具/技能”执行模式
        final_prompt = self._build_html_only_prompt(prompt)

        models_to_try: list[Optional[str]] = []
        models_to_try.append(model if model else self.config.gemini_model)
        for fallback in getattr(self.config, "gemini_fallback_models", []) or []:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        # 调用 Gemini CLI（通过管道传递数据）
        try:
            last_stderr = ""
            last_rc = 0
            last_model = None
            last_cmd = []

            for idx, model in enumerate(models_to_try):
                stdout_text, stderr_text, rc = await self._run_gemini(
                    final_prompt,
                    data_json,
                    model,
                    pid_callback=pid_callback,
                )
                last_stderr = stderr_text
                last_rc = rc
                last_model = model
                last_cmd = [self.cli_path] + (["-m", model] if model else []) + ["-p", final_prompt]

                if rc == 0 and stdout_text.strip():
                    html_content = self._extract_html(stdout_text)
                    if html_content:
                        break
                else:
                    # 只有“模型容量/限流”类问题才尝试备用模型；其他错误直接退出
                    if idx == 0 and self._should_retry_with_fallback(stderr_text):
                        continue
                    raise subprocess.CalledProcessError(
                        rc or 1, last_cmd, stderr=stderr_text
                    )
            else:
                raise subprocess.CalledProcessError(
                    last_rc or 1, last_cmd, stderr=last_stderr
                )

            # 保存报告
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Gemini CLI 执行超时（超过 {self.timeout} 秒）"
            )
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Gemini CLI 未找到: {self.cli_path}. "
                f"请检查配置或安装 Gemini CLI"
            )

    def validate_gemini_cli(self) -> bool:
        """验证 Gemini CLI 是否可用

        Returns:
            bool: True 如果可用，False 否则
        """
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def list_available_skills(self) -> list:
        """列出可用的 Gemini Skills

        Returns:
            list: 可用的 skill 名称列表
        """
        try:
            result = subprocess.run(
                [self.cli_path, "skills", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return []

            # 解析输出（假设每行一个 skill）
            skills = [
                line.strip()
                for line in result.stdout.splitlines()
                if line.strip()
            ]
            return skills

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    def check_skill_available(self) -> bool:
        """检查目标 skill 是否可用

        Returns:
            bool: True 如果可用，False 否则
        """
        skills = self.list_available_skills()
        return self.skill_name in skills
