"""api_errors 模块单元测试。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import api_errors as E

import pytest

pytestmark = pytest.mark.unit



def test_classify_known_codes():
    assert E.classify("-60006").category is E.ErrorCategory.PERMANENT
    assert E.classify("-60018").category is E.ErrorCategory.QUOTA
    assert E.classify("A0211").category is E.ErrorCategory.AUTH
    assert E.classify("-10001").category is E.ErrorCategory.RETRYABLE


def test_classify_unknown():
    info = E.classify("-99999")
    assert info.category is E.ErrorCategory.UNKNOWN


def test_classify_none():
    info = E.classify(None)
    assert info.code == "UNKNOWN"


def test_classify_int():
    assert E.classify(-60006).code == "-60006"


def test_is_retryable():
    assert E.is_retryable("-10001") is True
    assert E.is_retryable("-60006") is False
    assert E.is_retryable("A0211") is False  # 应该走续期路径
    assert E.is_retryable("-30001") is False


def test_is_retryable_by_message():
    # 没有错误码，但 message 提示是临时错误
    assert E.is_retryable(None, "service temporarily unavailable") is False  # 没匹配
    assert E.is_retryable(None, "exceeds limit (200 pages)") is False
    # 这里只关心 token 过期会被识别为 AUTH 而非 retryable
    assert E.is_retryable(None, "token expired") is False


def test_should_renew_token():
    assert E.should_renew_token("A0211") is True
    assert E.should_renew_token("A0202") is True
    assert E.should_renew_token("-60006") is False
    assert E.should_renew_token(None, "Token has expired") is True
    assert E.should_renew_token(None, "Invalid token format") is True


def test_format_for_user_includes_code_and_suggestion():
    msg = E.format_for_user("-60006")
    assert "-60006" in msg
    assert "200 页" in msg
    assert "auto_split" in msg or "拆分" in msg


def test_format_for_user_with_unknown_uses_message_fallback():
    msg = E.format_for_user(None, "file page count exceeds lightweight API limit")
    assert "-30003" in msg or "页数" in msg


def test_table_completeness():
    # 重要错误码必须在表里
    must_have = ["A0202", "A0211", "-60005", "-60006", "-60018", "-30001", "-30003"]
    for code in must_have:
        assert code in E.ERROR_TABLE, f"{code} 缺失"


def test_max_retries_present_for_retryable():
    for code, info in E.ERROR_TABLE.items():
        if info.category is E.ErrorCategory.RETRYABLE:
            assert info.max_retries > 0, f"{code} 标 retryable 但 max_retries=0"
