"""agent_api 客户端的能力检查 + 接口契约测试。

不调真实网络，只验证：
  - can_use_lite_api 在不同文件上的正确判断
  - AgentParseError 异常构造
  - 常量和支持格式集
"""
import pytest

import agent_api as AA


pytestmark = pytest.mark.integration


def test_constants_match_server_limits():
    assert AA.MAX_SIZE_MB == 10
    assert AA.MAX_PAGES == 20


def test_supported_formats_complete():
    # 至少应支持这些常见格式
    must = {"pdf", "doc", "docx", "ppt", "pptx",
            "xls", "xlsx", "png", "jpg", "jpeg"}
    assert must.issubset(AA.SUPPORTED_EXTS)
    # 不应支持 html（轻量 API 文档明确说不支持）
    assert "html" not in AA.SUPPORTED_EXTS


def test_can_use_lite_api_rejects_missing_file(tmp_path):
    ok, reason = AA.can_use_lite_api(tmp_path / "nope.pdf")
    assert ok is False
    assert "不存在" in reason


def test_can_use_lite_api_rejects_unsupported_format(tmp_path):
    f = tmp_path / "doc.html"
    f.write_bytes(b"<html></html>")
    ok, reason = AA.can_use_lite_api(f)
    assert ok is False
    assert "html" in reason.lower() or "支持" in reason


def test_can_use_lite_api_rejects_oversize_pdf(tmp_path, make_pdf):
    """构造一个 5 页但极小的 PDF；用 monkeypatch 模拟 size 超限。"""
    pdf = make_pdf("small.pdf", 5)
    # 直接物理超过 10MB 太慢，所以用 file_path 包装一层
    # 这里我们另造一个 13MB 的伪文件
    huge = tmp_path / "huge.pdf"
    huge.write_bytes(b"\x00" * (11 * 1024 * 1024))  # 11MB
    ok, reason = AA.can_use_lite_api(huge)
    assert ok is False
    assert "MB" in reason or "10MB" in reason


def test_can_use_lite_api_rejects_too_many_pages(make_pdf):
    pdf = make_pdf("med.pdf", 50)
    ok, reason = AA.can_use_lite_api(pdf)
    assert ok is False
    assert "页" in reason or "pages" in reason.lower()


def test_can_use_lite_api_accepts_small_pdf(make_pdf):
    pdf = make_pdf("tiny.pdf", 5)
    ok, reason = AA.can_use_lite_api(pdf)
    assert ok is True


def test_agent_parse_error_format():
    err = AA.AgentParseError("-30001", "file size exceeds 10MB")
    msg = str(err)
    assert "-30001" in msg
    assert "10MB" in msg or "轻量" in msg


def test_agent_api_client_constructs_without_session():
    """无 session 也能创建客户端（每次调用临时建）。"""
    client = AA.AgentAPIClient()
    assert client is not None
