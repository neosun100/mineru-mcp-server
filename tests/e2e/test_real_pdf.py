"""端到端测试：真调 MinerU API。

默认跳过；启用方式：
    pytest tests/e2e -m e2e
    RUN_E2E=1 pytest tests/e2e

需要：
  - 项目根目录有 all_tokens.json 且至少一个 Token 未过期
  - 网络畅通
  - 测试文件 ~/Downloads/sample_pdfs/PDF-A..pdf 存在
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


@pytest.fixture(scope="module")
def small_pdf(sample_pdfs_dir):
    if sample_pdfs_dir is None:
        pytest.skip("~/Downloads/sample_pdfs 不存在")
    p = sample_pdfs_dir / "PDF-A..pdf"
    if not p.exists():
        pytest.skip(f"{p} 不存在")
    return p


def test_process_small_pdf_first_5_pages(has_valid_token, small_pdf, tmp_path):
    """跑PDF-A.pdf 前 5 页，验证完整链路 + 路径修复。"""
    from mineru_async import MinerUAsyncProcessor
    from path_fixer import verify_refs_exist

    output_dir = tmp_path / "out"
    output_dir.mkdir()

    proc = MinerUAsyncProcessor()
    result = asyncio.run(proc.process_file(
        str(small_pdf),
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


def test_lite_api_skipped_when_pdf_too_big(small_pdf):
    """PDF-A 91 页，应被轻量 API 拒绝（fail fast，不真发请求）。"""
    from agent_api import can_use_lite_api
    ok, reason = can_use_lite_api(small_pdf)
    assert ok is False
    assert "页" in reason
