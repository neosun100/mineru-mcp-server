"""回归测试：防止"页数限制不一致"问题复发。

历史背景：
  - 2026 年某次 MinerU 服务端把单文件页数从 600 → 200，但 README/代码仍写 600
  - mineru_async.py.MAX_PAGES = 600 vs 服务端实际 200 → 文件 200-599 页直接报错
  - split_large_file.py 默认按 600 拆 → 拆出来的分片仍超 200 服务端限制
  - v4.0.0 已统一到 200（服务端真值）+ 180（业务默认 buffer）

本测试确保所有相关常量都对齐，谁都不能私自改回 600。
"""
import pytest

pytestmark = pytest.mark.regression


def test_file_validator_max_pages_is_200():
    from mineru_async import FileValidator
    assert FileValidator.MAX_PAGES == 200, \
        "服务端硬限制是 200 页，不要改回 600"


def test_file_validator_max_size_is_200_mb():
    from mineru_async import FileValidator
    assert FileValidator.MAX_SIZE == 200 * 1024 * 1024


def test_split_constants_aligned():
    """split_large_file 的所有相关常量必须 ≤ 服务端真值。"""
    from split_large_file import (
        SERVER_MAX_PAGES, SERVER_MAX_SIZE_MB,
        DEFAULT_MAX_PAGES, DEFAULT_MAX_SIZE_MB,
    )
    assert SERVER_MAX_PAGES == 200
    assert SERVER_MAX_SIZE_MB == 200
    # 业务默认必须 ≤ 服务端，且应该有 buffer（≤ 90%）
    assert DEFAULT_MAX_PAGES <= SERVER_MAX_PAGES
    assert DEFAULT_MAX_SIZE_MB <= SERVER_MAX_SIZE_MB
    assert DEFAULT_MAX_PAGES <= int(SERVER_MAX_PAGES * 0.95), \
        "DEFAULT_MAX_PAGES 应至少留 5% buffer，建议 180"


def test_no_600_literal_in_active_code():
    """src/ 中不应再有 ' 600' 作为页数硬编码（注释里允许说明历史变化）。"""
    import re
    from pathlib import Path
    src_dir = Path(__file__).resolve().parents[2] / "src"

    # 只扫核心模块（排除 batch_login 等无关文件）
    files = ["mineru_async.py", "mineru_batch_async.py",
             "split_large_file.py", "auto_split.py"]

    for fname in files:
        text = (src_dir / fname).read_text(encoding="utf-8")
        # 找 'pages = 600' / 'MAX_PAGES = 600' / 'pages > 600' / '/600' 等
        forbidden_patterns = [
            r"MAX_PAGES\s*=\s*600",
            r"pages\s*>\s*600",
            r"pages\s*<=\s*600",
            r"//\s*600\b",
        ]
        for pat in forbidden_patterns:
            assert not re.search(pat, text), \
                f"{fname} 中发现禁止的 600 字面量模式: {pat}"


def test_auto_split_correctly_handles_200_to_400_pages(make_pdf):
    """200-400 页文件必须被拆分（这是历史 bug 区间，曾经 600 阈值会漏掉）。"""
    from auto_split import prepare_files
    pdf = make_pdf("border.pdf", 250)
    expanded, plans = prepare_files([str(pdf)])
    assert len(plans) == 1, "250 页必须拆分"
    assert plans[0]["n"] >= 2


def test_auto_split_does_not_split_under_180(make_pdf):
    """180 页以下不拆（business buffer 内）。"""
    from auto_split import prepare_files
    pdf = make_pdf("ok.pdf", 150)
    expanded, plans = prepare_files([str(pdf)])
    assert plans == []
