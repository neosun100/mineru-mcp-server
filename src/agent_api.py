"""MinerU Agent 轻量解析 API 客户端。

官方文档：https://mineru.net/apiManage/docs（"Agent 轻量解析 API"章节）

特点：
  - 无需 Token，IP 限频
  - 仅支持 PDF / 图片 / Doc(x) / PPT(x) / Excel
  - 文件上限 ≤ 10MB / ≤ 20 页
  - 仅输出 Markdown（CDN 链接）
  - 异步：提交 → 轮询 → 拿到 markdown_url → 下载

适用场景：
  - 小文档（票据、单页扫描、短论文等）
  - AI Agent 工作流（无登录态）
  - 当主账号每日 1000 页配额耗尽时的兜底
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Optional

from niquests import AsyncSession

from api_errors import (
    ErrorCategory,
    classify,
    classify_by_message,
    format_for_user,
    is_retryable,
)

logger = logging.getLogger(__name__)


BASE_URL = "https://mineru.net/api/v1/agent"
ENDPOINT_URL = f"{BASE_URL}/parse/url"
ENDPOINT_FILE = f"{BASE_URL}/parse/file"
ENDPOINT_QUERY = f"{BASE_URL}/parse"  # /{task_id}

# 服务端硬限制（与 mineru.net 文档一致）
MAX_SIZE_MB = 10
MAX_PAGES = 20
SUPPORTED_EXTS = {
    "pdf", "png", "jpg", "jpeg", "jp2", "webp", "gif", "bmp",
    "doc", "docx", "ppt", "pptx", "xls", "xlsx",
}


@dataclass
class AgentParseResult:
    """轻量 API 解析成功的返回。"""

    task_id: str
    markdown_url: str
    markdown_text: Optional[str] = None
    elapsed_seconds: float = 0.0


class AgentParseError(RuntimeError):
    """轻量 API 解析失败的统一异常。"""

    def __init__(self, code: Optional[str], err_msg: str = "", task_id: Optional[str] = None):
        self.code = code
        self.err_msg = err_msg
        self.task_id = task_id
        super().__init__(format_for_user(code, err_msg))


# ProgressCallback 签名兼容
ProgressFn = Callable[[str, str], Any]  # (state, message) -> sync/async None


class AgentAPIClient:
    """MinerU Agent 轻量 API 异步客户端。"""

    def __init__(self, session: Optional[AsyncSession] = None):
        # 允许外部传入复用的 session；不传时每个调用临时建一个
        self._external_session = session

    # ────────────────────────────────────────────────────────────
    # 提交
    # ────────────────────────────────────────────────────────────

    async def submit_url(
        self,
        url: str,
        *,
        file_name: Optional[str] = None,
        language: str = "ch",
        page_range: Optional[str] = None,
        enable_table: bool = True,
        is_ocr: bool = False,
        enable_formula: bool = True,
    ) -> str:
        """提交一个远程 URL 解析任务，返回 task_id。"""
        payload: Dict[str, Any] = {
            "url": url,
            "language": language,
            "enable_table": enable_table,
            "is_ocr": is_ocr,
            "enable_formula": enable_formula,
        }
        if file_name:
            payload["file_name"] = file_name
        if page_range:
            payload["page_range"] = page_range

        async with self._session_ctx() as sess:
            resp = await sess.post(ENDPOINT_URL, json=payload, timeout=30)
            data = self._unwrap(resp.json())
            return data["task_id"]

    async def submit_file(
        self,
        file_path: str | Path,
        *,
        language: str = "ch",
        page_range: Optional[str] = None,
        enable_table: bool = True,
        is_ocr: bool = False,
        enable_formula: bool = True,
    ) -> str:
        """提交本地文件（签名上传）解析任务，返回 task_id。

        流程：
          1. POST /parse/file 拿 task_id 和签名上传 URL
          2. PUT 文件到签名 URL
          3. 后端自动检测并开始解析（waiting-file → running → done）
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise AgentParseError(None, f"文件不存在：{file_path}")
        size_mb = file_path.stat().st_size / 1024 / 1024
        if size_mb > MAX_SIZE_MB:
            raise AgentParseError(
                "-30001",
                f"文件 {size_mb:.1f}MB 超过轻量 API 的 10MB 限制",
            )
        ext = file_path.suffix.lower().lstrip(".")
        if ext not in SUPPORTED_EXTS:
            raise AgentParseError("-30002", f"轻量 API 不支持的格式 {ext}")

        payload: Dict[str, Any] = {
            "file_name": file_path.name,
            "language": language,
            "enable_table": enable_table,
            "is_ocr": is_ocr,
            "enable_formula": enable_formula,
        }
        if page_range:
            payload["page_range"] = page_range

        async with self._session_ctx() as sess:
            # Step 1: 申请签名上传 URL
            resp = await sess.post(ENDPOINT_FILE, json=payload, timeout=30)
            data = self._unwrap(resp.json())
            task_id = data["task_id"]
            file_url = data["file_url"]
            logger.info(f"轻量 API 任务已创建 task_id={task_id}")

            # Step 2: PUT 上传文件
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            put_resp = await sess.put(file_url, data=file_bytes, timeout=300)
            if put_resp.status_code not in (200, 201):
                raise AgentParseError(
                    None, f"文件上传失败 HTTP {put_resp.status_code}", task_id=task_id,
                )
            logger.info(f"轻量 API 文件已上传，等待后端解析…")
            return task_id

    # ────────────────────────────────────────────────────────────
    # 查询 / 轮询
    # ────────────────────────────────────────────────────────────

    async def query(self, task_id: str) -> Dict[str, Any]:
        """查询单次任务状态。"""
        async with self._session_ctx() as sess:
            resp = await sess.get(f"{ENDPOINT_QUERY}/{task_id}", timeout=30)
            return self._unwrap(resp.json())

    async def wait_for_completion(
        self,
        task_id: str,
        *,
        timeout: int = 300,
        interval: float = 3.0,
        progress: Optional[ProgressFn] = None,
    ) -> AgentParseResult:
        """轮询直到 done 或超时。"""
        start = time.time()
        elapsed = 0.0

        async with self._session_ctx() as sess:
            while elapsed < timeout:
                resp = await sess.get(f"{ENDPOINT_QUERY}/{task_id}", timeout=30)
                data = self._unwrap(resp.json())
                state = data.get("state", "unknown")
                elapsed = time.time() - start

                if progress:
                    ret = progress(state, data.get("err_msg", ""))
                    if asyncio.iscoroutine(ret):
                        await ret

                if state == "done":
                    return AgentParseResult(
                        task_id=task_id,
                        markdown_url=data["markdown_url"],
                        elapsed_seconds=elapsed,
                    )
                if state == "failed":
                    raise AgentParseError(
                        str(data.get("err_code")),
                        data.get("err_msg", ""),
                        task_id=task_id,
                    )
                await asyncio.sleep(interval)

        raise AgentParseError(None, f"轮询超时 ({timeout}s)", task_id=task_id)

    async def fetch_markdown(self, markdown_url: str) -> str:
        """下载 markdown_url 指向的 .md 内容。"""
        async with self._session_ctx() as sess:
            resp = await sess.get(markdown_url, timeout=120)
            if resp.status_code != 200:
                raise AgentParseError(
                    None, f"Markdown 下载失败 HTTP {resp.status_code}",
                )
            return resp.text

    # ────────────────────────────────────────────────────────────
    # 一键流程
    # ────────────────────────────────────────────────────────────

    async def parse_url(
        self,
        url: str,
        *,
        progress: Optional[ProgressFn] = None,
        **options,
    ) -> AgentParseResult:
        """提交 URL → 轮询 → 下载 markdown 的端到端流程。"""
        task_id = await self.submit_url(url, **options)
        result = await self.wait_for_completion(task_id, progress=progress)
        result.markdown_text = await self.fetch_markdown(result.markdown_url)
        return result

    async def parse_file(
        self,
        file_path: str | Path,
        *,
        progress: Optional[ProgressFn] = None,
        **options,
    ) -> AgentParseResult:
        """本地文件 → 签名上传 → 轮询 → 下载 markdown 的端到端流程。"""
        task_id = await self.submit_file(file_path, **options)
        result = await self.wait_for_completion(task_id, progress=progress)
        result.markdown_text = await self.fetch_markdown(result.markdown_url)
        return result

    # ────────────────────────────────────────────────────────────
    # 内部
    # ────────────────────────────────────────────────────────────

    def _session_ctx(self):
        if self._external_session is not None:
            class _Ctx:
                def __init__(self, sess):
                    self.sess = sess
                async def __aenter__(self):
                    return self.sess
                async def __aexit__(self, exc_type, exc, tb):
                    pass
            return _Ctx(self._external_session)
        return AsyncSession()

    @staticmethod
    def _unwrap(payload: Dict[str, Any]) -> Dict[str, Any]:
        """从 {code, msg, data} 包装中取 data；非 0 抛异常。"""
        code = payload.get("code")
        if code != 0:
            err_msg = payload.get("msg", "")
            raise AgentParseError(str(code) if code is not None else None, err_msg)
        return payload.get("data", {})


# ───────────────────────────────────────────────────────────────────
# 工具函数
# ───────────────────────────────────────────────────────────────────


def can_use_lite_api(file_path: str | Path) -> tuple[bool, str]:
    """快速检查文件是否符合轻量 API 的硬限制。"""
    p = Path(file_path)
    if not p.exists():
        return False, "文件不存在"
    size_mb = p.stat().st_size / 1024 / 1024
    if size_mb > MAX_SIZE_MB:
        return False, f"文件 {size_mb:.1f}MB 超过轻量 API 的 10MB 限制"
    ext = p.suffix.lower().lstrip(".")
    if ext not in SUPPORTED_EXTS:
        return False, f"轻量 API 不支持 .{ext}"
    if ext == "pdf":
        try:
            from PyPDF2 import PdfReader
            pages = len(PdfReader(str(p)).pages)
            if pages > MAX_PAGES:
                return False, f"PDF {pages} 页超过轻量 API 的 20 页限制"
        except Exception:
            pass  # 读不到页数就不拦截，让服务端判断
    return True, "ok"
