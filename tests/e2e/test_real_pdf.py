"""端到端测试：真调 MinerU API。

默认跳过；启用方式：
    pytest tests/e2e -m e2e
    RUN_E2E=1 pytest tests/e2e

需要：
  - 项目根目录有 all_tokens.json 且至少一个 Token 未过期
  - 网络畅通
  - 设置环境变量 MINERU_SAMPLE_PDFS_DIR 指向一个含有 *.pdf 的目录
    示例：export MINERU_SAMPLE_PDFS_DIR=/path/to/pdfs
"""
import asyncio
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def has_valid_token():
    """检查至少有一个有效 Token，否则 skip。"""
    from token_manager import TokenManager
    TokenManager._instance = None  # 重置单例
    mgr = TokenManager()
    if not mgr.valid_tokens():
        pytest.skip("无有效 Token，跳过 e2e")
    return True


def test_process_real_pdf_first_5_pages(has_valid_token, sample_pdf, tmp_path):
    """跑样本目录中最小 PDF 的前 5 页，验证完整链路 + 路径修复。"""
    if sample_pdf is None:
        pytest.skip(
            "未设置 MINERU_SAMPLE_PDFS_DIR 或目录无 PDF。"
            "示例：export MINERU_SAMPLE_PDFS_DIR=/path/to/pdfs"
        )

    from mineru_async import MinerUAsyncProcessor
    from path_fixer import verify_refs_exist

    output_dir = tmp_path / "out"
    output_dir.mkdir()

    proc = MinerUAsyncProcessor()
    result = asyncio.run(proc.process_file(
        str(sample_pdf),
        output_dir=str(output_dir),
        page_ranges="1-5",
        language="ch",
        enable_formula=True,
        enable_table=True,
        data_id="pytest-e2e-small",
    ))

    assert result is not None, "process_file 返回 None"
    md_path = Path(result["output"]["markdown"])
    assert md_path.exists()
    text = md_path.read_text(encoding="utf-8")
    assert len(text) > 100, "Markdown 过短，可能解析失败"

    # 路径修复必须正确
    n_refs, missing = verify_refs_exist(md_path)
    assert len(missing) == 0, f"图片引用缺失：{missing[:3]}"


def test_lite_api_rejects_too_many_pages(sample_pdf):
    """如果样本 PDF 超过 20 页，应被轻量 API 拒绝（fail fast）。"""
    if sample_pdf is None:
        pytest.skip("未设置 MINERU_SAMPLE_PDFS_DIR")

    from agent_api import can_use_lite_api
    from PyPDF2 import PdfReader

    pages = len(PdfReader(str(sample_pdf)).pages)
    ok, reason = can_use_lite_api(sample_pdf)

    if pages > 20:
        assert ok is False
        assert "页" in reason or "page" in reason.lower()
    else:
        # 小 PDF 应该可以用轻量 API
        # 但还要看大小是否 ≤ 10MB
        size_mb = sample_pdf.stat().st_size / 1024 / 1024
        if size_mb <= 10:
            assert ok is True, f"小 PDF 应可用轻量 API，但被拒：{reason}"
