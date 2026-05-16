"""统一的进度回调封装。

跨模块的进度上报有不同的形式（CLI rich、MCP 通知、回调函数），
本模块提供一个统一接口，让上层只需关心"现在到第几步"。
"""
from __future__ import annotations

import asyncio
import inspect
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Awaitable, Callable, Optional, Union

logger = logging.getLogger(__name__)


class ProgressStage(Enum):
    """处理阶段。配合 step/total 一起上报。"""

    VALIDATE = "validate"
    UPLOAD = "upload"
    SUBMIT = "submit"
    EXTRACT = "extract"
    DOWNLOAD = "download"
    EXTRACT_ZIP = "extract_zip"
    POST_PROCESS = "post_process"
    DONE = "done"
    FAILED = "failed"


@dataclass
class ProgressEvent:
    stage: ProgressStage
    current: int
    total: int
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    extra: dict = field(default_factory=dict)


# Callback 类型 —— 同步或异步均可
ProgressCallback = Callable[[ProgressEvent], Union[None, Awaitable[None]]]


class ProgressReporter:
    """进度上报器。可以装多个 callback。"""

    def __init__(self, callbacks: Optional[list[ProgressCallback]] = None):
        self._callbacks: list[ProgressCallback] = list(callbacks or [])
        self._last_event: Optional[ProgressEvent] = None
        self._start_time = time.time()

    def add_callback(self, cb: ProgressCallback) -> None:
        self._callbacks.append(cb)

    @property
    def elapsed(self) -> float:
        return time.time() - self._start_time

    @property
    def last(self) -> Optional[ProgressEvent]:
        return self._last_event

    async def report(
        self,
        stage: ProgressStage,
        current: int = 0,
        total: int = 100,
        message: str = "",
        **extra,
    ) -> None:
        """上报一个进度事件，调度所有 callback。"""
        event = ProgressEvent(
            stage=stage, current=current, total=total,
            message=message, extra=extra,
        )
        self._last_event = event

        for cb in self._callbacks:
            try:
                ret = cb(event)
                if inspect.isawaitable(ret):
                    await ret
            except Exception as e:
                logger.warning(f"progress callback 异常: {e}")

    # 便捷方法
    async def validate(self, msg: str = "验证文件…"):
        await self.report(ProgressStage.VALIDATE, 1, 10, msg)

    async def upload(self, current: int = 2, total: int = 10, msg: str = "上传文件…"):
        await self.report(ProgressStage.UPLOAD, current, total, msg)

    async def submit(self, msg: str = "提交解析任务…"):
        await self.report(ProgressStage.SUBMIT, 3, 10, msg)

    async def extract(self, current: int, total: int, msg: str = ""):
        msg = msg or f"解析中 {current}/{total} 页"
        await self.report(ProgressStage.EXTRACT, current, total, msg)

    async def download(self, msg: str = "下载结果…"):
        await self.report(ProgressStage.DOWNLOAD, 8, 10, msg)

    async def post_process(self, msg: str = "整理输出…"):
        await self.report(ProgressStage.POST_PROCESS, 9, 10, msg)

    async def done(self, msg: str = "处理完成"):
        await self.report(ProgressStage.DONE, 10, 10, msg)

    async def failed(self, msg: str):
        await self.report(ProgressStage.FAILED, 0, 0, msg)


# ───────────────────────────────────────────────────────────────────
# 兼容旧 progress_callback(extracted, total, msg) 三参数签名
# ───────────────────────────────────────────────────────────────────


def adapt_legacy_callback(
    legacy_cb: Optional[Callable[[int, int, str], Union[None, Awaitable[None]]]],
) -> Optional[ProgressCallback]:
    """把旧的 (extracted, total, msg) 三参数 callback 适配为 ProgressCallback。"""
    if legacy_cb is None:
        return None

    async def adapter(event: ProgressEvent) -> None:
        ret = legacy_cb(event.current, event.total, event.message)
        if inspect.isawaitable(ret):
            await ret

    return adapter
