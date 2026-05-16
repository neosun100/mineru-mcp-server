"""MinerU API 错误码表 + 智能重试策略。

服务端错误码参考：https://mineru.net/doc/docs/index_en/

错误分为 4 类：
  - RETRYABLE   可自动重试（服务异常、超时、队列满等瞬时问题）
  - QUOTA       配额耗尽（每日额度、HTML 额度等），需提示用户等待
  - AUTH        认证错误（Token 错/过期），可触发自动续期
  - PERMANENT   永久失败（文件损坏、格式不支持、超规格等），不应重试
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Dict, Optional


class ErrorCategory(enum.Enum):
    """错误分类。决定上层如何应对。"""

    RETRYABLE = "retryable"   # 可自动重试
    QUOTA = "quota"           # 配额耗尽
    AUTH = "auth"             # 认证错误
    PERMANENT = "permanent"   # 永久失败
    UNKNOWN = "unknown"       # 未知（按 PERMANENT 处理）


@dataclass(frozen=True)
class ErrorInfo:
    """错误信息条目。"""

    code: str
    category: ErrorCategory
    description: str            # 官方简短说明
    user_message: str           # 中文友好提示（给最终用户看）
    suggestion: str = ""        # 建议的应对动作
    max_retries: int = 0        # 建议的最大重试次数（0 = 不重试）


# 完整错误码表（基于 mineru.net 官方文档 2026 年版本）
ERROR_TABLE: Dict[str, ErrorInfo] = {
    # ─── 认证错误 ───────────────────────────────────────────────
    "A0202": ErrorInfo(
        "A0202", ErrorCategory.AUTH,
        "Token 错误",
        "Token 不正确或格式有误",
        "检查 Bearer 前缀，或重新登录获取 Token",
    ),
    "A0211": ErrorInfo(
        "A0211", ErrorCategory.AUTH,
        "Token 过期",
        "Token 已过期",
        "正在自动续期，请稍候…",
        max_retries=1,
    ),

    # ─── 参数错误 ───────────────────────────────────────────────
    "-500": ErrorInfo(
        "-500", ErrorCategory.PERMANENT,
        "传参错误",
        "请求参数类型错误或 Content-Type 不正确",
        "检查参数类型是否符合文档要求",
    ),
    "-10002": ErrorInfo(
        "-10002", ErrorCategory.PERMANENT,
        "请求参数错误",
        "请求参数格式不正确",
        "检查参数名拼写和取值范围",
    ),

    # ─── 服务瞬时异常（可重试）─────────────────────────────────
    "-10001": ErrorInfo(
        "-10001", ErrorCategory.RETRYABLE,
        "服务异常",
        "服务暂时异常",
        "等几秒后会自动重试",
        max_retries=3,
    ),
    "-60001": ErrorInfo(
        "-60001", ErrorCategory.RETRYABLE,
        "生成上传 URL 失败",
        "生成文件上传链接失败",
        "等几秒后会自动重试",
        max_retries=3,
    ),
    "-60007": ErrorInfo(
        "-60007", ErrorCategory.RETRYABLE,
        "模型服务暂时不可用",
        "模型服务繁忙",
        "等几秒后会自动重试",
        max_retries=3,
    ),
    "-60008": ErrorInfo(
        "-60008", ErrorCategory.RETRYABLE,
        "文件读取超时",
        "URL 文件读取超时（可能源站慢或被屏蔽）",
        "确认 URL 可访问；GitHub/AWS 等域名可能需要本地下载后再上传",
        max_retries=2,
    ),
    "-60009": ErrorInfo(
        "-60009", ErrorCategory.RETRYABLE,
        "任务提交队列已满",
        "提交队列已满",
        "等几秒后会自动重试",
        max_retries=3,
    ),
    "-60010": ErrorInfo(
        "-60010", ErrorCategory.RETRYABLE,
        "解析失败",
        "解析失败（瞬时错误）",
        "等几秒后会自动重试一次",
        max_retries=1,
    ),
    "-60020": ErrorInfo(
        "-60020", ErrorCategory.RETRYABLE,
        "文件拆分失败",
        "服务端文件拆分失败",
        "等几秒后会自动重试",
        max_retries=2,
    ),
    "-60021": ErrorInfo(
        "-60021", ErrorCategory.RETRYABLE,
        "读取文件页数失败",
        "读取文件页数失败",
        "等几秒后会自动重试",
        max_retries=2,
    ),
    "-60022": ErrorInfo(
        "-60022", ErrorCategory.RETRYABLE,
        "网页读取失败",
        "网页读取失败（网络或限频）",
        "等几秒后会自动重试",
        max_retries=2,
    ),

    # ─── 文件级永久错误 ────────────────────────────────────────
    "-60002": ErrorInfo(
        "-60002", ErrorCategory.PERMANENT,
        "文件格式不支持",
        "文件格式无法识别或不在支持列表",
        "确认文件后缀是 pdf/doc/docx/ppt/pptx/xls/xlsx/png/jpg/jpeg/jp2/webp/gif/bmp/html",
    ),
    "-60003": ErrorInfo(
        "-60003", ErrorCategory.PERMANENT,
        "文件读取失败",
        "文件可能损坏",
        "重新生成或下载该文件后再试",
    ),
    "-60004": ErrorInfo(
        "-60004", ErrorCategory.PERMANENT,
        "空文件",
        "文件内容为空",
        "确认文件确实有内容",
    ),
    "-60005": ErrorInfo(
        "-60005", ErrorCategory.PERMANENT,
        "文件大小超出限制",
        "文件超过 200MB 限制",
        "用 split_large_pdf 拆分后再处理",
    ),
    "-60006": ErrorInfo(
        "-60006", ErrorCategory.PERMANENT,
        "文件页数超过限制",
        "文件超过 200 页限制",
        "用 auto_split.prepare_files() 拆分成 ≤180 页的分片再处理",
    ),
    "-60011": ErrorInfo(
        "-60011", ErrorCategory.PERMANENT,
        "获取有效文件失败",
        "未检测到有效文件（可能未上传完成）",
        "确认上传链接已成功 PUT 文件",
    ),
    "-60012": ErrorInfo(
        "-60012", ErrorCategory.PERMANENT,
        "找不到任务",
        "task_id 无效或已被删除",
        "确认 task_id 正确",
    ),
    "-60013": ErrorInfo(
        "-60013", ErrorCategory.PERMANENT,
        "无权访问该任务",
        "无权访问此任务（不是当前 Token 提交的）",
        "用提交时同一账号的 Token 查询",
    ),
    "-60014": ErrorInfo(
        "-60014", ErrorCategory.PERMANENT,
        "运行中的任务不可删除",
        "运行中任务暂不支持删除",
        "等任务结束后再删",
    ),
    "-60015": ErrorInfo(
        "-60015", ErrorCategory.PERMANENT,
        "文件转换失败",
        "Office → PDF 转换失败",
        "手动转 PDF 后再上传",
    ),
    "-60016": ErrorInfo(
        "-60016", ErrorCategory.PERMANENT,
        "导出格式转换失败",
        "导出指定格式失败（如 docx/html/latex）",
        "尝试其他 extra_formats 或省略此参数",
    ),
    "-60017": ErrorInfo(
        "-60017", ErrorCategory.PERMANENT,
        "重试次数达到上限",
        "服务端重试次数已达上限",
        "等模型升级后再试",
    ),

    # ─── 配额耗尽 ───────────────────────────────────────────────
    "-60018": ErrorInfo(
        "-60018", ErrorCategory.QUOTA,
        "每日解析任务数量已达上限",
        "今日解析额度已用完",
        "明日再来；或换用其他账号；或用 Agent 轻量 API（小文件）",
    ),
    "-60019": ErrorInfo(
        "-60019", ErrorCategory.QUOTA,
        "html 解析额度不足",
        "今日 HTML 解析额度已用完",
        "明日再来",
    ),

    # ─── Agent 轻量 API 专属 ────────────────────────────────────
    "-30001": ErrorInfo(
        "-30001", ErrorCategory.PERMANENT,
        "文件大小超出轻量接口限制（10MB）",
        "文件超过轻量 API 的 10MB 限制",
        "改用精准 API（process_document）",
    ),
    "-30002": ErrorInfo(
        "-30002", ErrorCategory.PERMANENT,
        "轻量接口不支持该文件类型",
        "文件类型在轻量 API 中不支持",
        "支持的格式：PDF / 图片 / Doc / PPT / Excel",
    ),
    "-30003": ErrorInfo(
        "-30003", ErrorCategory.PERMANENT,
        "文件页数超出轻量接口限制",
        "文件超过轻量 API 的页数限制（20 页）",
        "改用精准 API，或指定 page_range 只取前 20 页",
    ),
    "-30004": ErrorInfo(
        "-30004", ErrorCategory.PERMANENT,
        "请求参数错误",
        "轻量 API 请求参数错误",
        "检查 file_name / url 等必填参数",
    ),
}


def classify(code: str | int | None) -> ErrorInfo:
    """根据错误码返回 ErrorInfo。未知错误码归为 UNKNOWN。"""
    if code is None:
        return ErrorInfo(
            "UNKNOWN", ErrorCategory.UNKNOWN,
            "未知错误", "未知错误", "查看完整响应内容定位",
        )
    code_str = str(code)
    return ERROR_TABLE.get(
        code_str,
        ErrorInfo(
            code_str, ErrorCategory.UNKNOWN,
            f"未知错误码 {code_str}",
            f"未识别的错误码 {code_str}",
            "查看 https://mineru.net/doc/docs/index/ 错误码表",
        ),
    )


def classify_by_message(err_msg: str) -> Optional[ErrorInfo]:
    """从 err_msg 文本中识别错误（一些场景下没有错误码，只有文本）。"""
    if not err_msg:
        return None
    text = err_msg.lower()
    if "exceeds limit" in text and "pages" in text:
        return ERROR_TABLE["-60006"]
    if "exceeds" in text and "10mb" in text:
        return ERROR_TABLE["-30001"]
    if "lightweight api limit" in text:
        return ERROR_TABLE["-30003"]
    if "token" in text and ("expire" in text or "expired" in text):
        return ERROR_TABLE["A0211"]
    if "token" in text and "invalid" in text:
        return ERROR_TABLE["A0202"]
    return None


def is_retryable(code: str | int | None, err_msg: str = "") -> bool:
    """判断该错误是否应该自动重试。"""
    info = classify(code)
    if info.category == ErrorCategory.RETRYABLE:
        return True
    if info.category == ErrorCategory.UNKNOWN:
        # 通过 message 兜底识别
        from_msg = classify_by_message(err_msg)
        if from_msg and from_msg.category == ErrorCategory.RETRYABLE:
            return True
    return False


def should_renew_token(code: str | int | None, err_msg: str = "") -> bool:
    """判断该错误是否应该触发 Token 自动续期。"""
    info = classify(code)
    if info.category == ErrorCategory.AUTH:
        return True
    from_msg = classify_by_message(err_msg)
    return from_msg is not None and from_msg.category == ErrorCategory.AUTH


def format_for_user(code: str | int | None, err_msg: str = "") -> str:
    """生成给最终用户看的中文友好错误描述。"""
    info = classify(code)
    if info.category == ErrorCategory.UNKNOWN:
        from_msg = classify_by_message(err_msg)
        if from_msg:
            info = from_msg
    parts = [f"[{info.code}] {info.user_message}"]
    if info.suggestion:
        parts.append(f"建议：{info.suggestion}")
    if err_msg and err_msg not in info.user_message:
        parts.append(f"原始信息：{err_msg}")
    return "\n".join(parts)
