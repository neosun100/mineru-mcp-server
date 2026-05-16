"""split_large_file + auto_split 单元测试。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import split_large_file as SL
import auto_split as AS

import pytest

pytestmark = pytest.mark.unit



def test_constants_match_server_limits():
    assert SL.SERVER_MAX_PAGES == 200
    assert SL.SERVER_MAX_SIZE_MB == 200
    assert SL.DEFAULT_MAX_PAGES <= SL.SERVER_MAX_PAGES
    assert SL.DEFAULT_MAX_SIZE_MB <= SL.SERVER_MAX_SIZE_MB


def test_default_buffer():
    """默认值留 buffer。"""
    assert SL.DEFAULT_MAX_PAGES == 180
    assert SL.DEFAULT_MAX_SIZE_MB == 180


def _make_pdf(path: Path, n_pages: int) -> Path:
    """造一个 N 页的 PDF 用于测试。"""
    from PyPDF2 import PdfWriter
    w = PdfWriter()
    for _ in range(n_pages):
        w.add_blank_page(width=200, height=200)
    with open(path, "wb") as f:
        w.write(f)
    return path


def test_no_split_for_small_file(tmp_path):
    pdf = _make_pdf(tmp_path / "small.pdf", 50)
    chunks = SL.split_large_pdf(str(pdf))
    assert chunks == [str(pdf)]


def test_split_309_pages(tmp_path):
    """309 页应该拆成 2 片（因为 default 180 页）。"""
    pdf = _make_pdf(tmp_path / "med.pdf", 309)
    chunks = SL.split_large_pdf(str(pdf))
    assert len(chunks) == 2
    assert all(Path(c).exists() for c in chunks)
    # 验证第一个 chunk 就在限制内
    from PyPDF2 import PdfReader
    for c in chunks:
        assert len(PdfReader(c).pages) <= SL.SERVER_MAX_PAGES


def test_split_496_pages(tmp_path):
    """496 页应该拆成 3 片。"""
    pdf = _make_pdf(tmp_path / "big.pdf", 496)
    chunks = SL.split_large_pdf(str(pdf))
    assert len(chunks) == 3
    from PyPDF2 import PdfReader
    total = sum(len(PdfReader(c).pages) for c in chunks)
    assert total == 496


def test_custom_max_pages(tmp_path):
    pdf = _make_pdf(tmp_path / "x.pdf", 100)
    chunks = SL.split_large_pdf(str(pdf), max_pages=30)
    assert len(chunks) == 4   # 100 / 30 = 4 片（25 页/片）


def test_auto_split_prepare_skips_small(tmp_path):
    pdf = _make_pdf(tmp_path / "small.pdf", 50)
    expanded, plans = AS.prepare_files([str(pdf)])
    assert expanded == [str(pdf)]
    assert plans == []


def test_auto_split_prepare_splits_big(tmp_path):
    big = _make_pdf(tmp_path / "big.pdf", 309)
    expanded, plans = AS.prepare_files([str(big)])
    assert len(expanded) == 2
    assert len(plans) == 1
    assert plans[0]["n"] == 2


def test_auto_split_mixed(tmp_path):
    small = _make_pdf(tmp_path / "small.pdf", 50)
    big = _make_pdf(tmp_path / "big.pdf", 250)
    expanded, plans = AS.prepare_files([str(small), str(big)])
    # 小的直接进 expanded，大的拆分
    assert len(expanded) == 1 + 2  # small + 2 chunks
    assert len(plans) == 1
    assert plans[0]["original"] == str(big)


def test_chunks_dir_name_uses_stem(tmp_path):
    """chunks 输出目录用 stem，不要重复扩展名。"""
    pdf = _make_pdf(tmp_path / "report..pdf", 250)  # 双点 stem
    chunks = SL.split_large_pdf(str(pdf))
    chunks_dir = Path(chunks[0]).parent
    assert chunks_dir.name == "report._chunks"
