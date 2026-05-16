"""项目级 pytest conftest。

约定：
  - unit / integration / regression 标记的测试默认全部跑
  - e2e 标记的测试默认 skip，除非：
      * 命令行带 -m e2e
      * 或环境变量 RUN_E2E=1
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# 让 tests/ 下任何目录都能直接 import src/ 里的模块
# Path(__file__) = .../tests/conftest.py → parent.parent 才是项目根
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def pytest_collection_modifyitems(config, items):
    """除非命令行 -m 包含 e2e 或环境变量 RUN_E2E=1，否则自动 skip e2e。"""
    explicit_e2e = bool(
        os.environ.get("RUN_E2E")
        or "e2e" in (config.getoption("-m") or "")
    )
    if explicit_e2e:
        return

    skip_e2e = pytest.mark.skip(
        reason="e2e 测试默认跳过；带 -m e2e 或设 RUN_E2E=1 启用"
    )
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def sample_pdfs_dir() -> Path | None:
    """供 e2e 使用的 PDF 样本目录。

    通过环境变量 ``MINERU_SAMPLE_PDFS_DIR`` 指定（绝对路径）。
    未设置或目录不存在时返回 ``None``，e2e 测试会自动 skip。

    示例：
        export MINERU_SAMPLE_PDFS_DIR=/path/to/your/pdf/samples
    """
    env_path = os.environ.get("MINERU_SAMPLE_PDFS_DIR")
    if not env_path:
        return None
    p = Path(env_path).expanduser()
    return p if p.exists() else None


@pytest.fixture(scope="session")
def sample_pdf(sample_pdfs_dir) -> Path | None:
    """从 sample_pdfs_dir 中挑一个最小的 PDF 给 e2e 用。"""
    if sample_pdfs_dir is None:
        return None
    pdfs = sorted(sample_pdfs_dir.glob("*.pdf"), key=lambda p: p.stat().st_size)
    return pdfs[0] if pdfs else None


@pytest.fixture
def make_pdf(tmp_path):
    """造一个 N 页的 PDF（用 PyPDF2 add_blank_page）。供集成/回归测试。"""
    from PyPDF2 import PdfWriter

    def _make(name: str, n_pages: int) -> Path:
        path = tmp_path / name
        w = PdfWriter()
        for _ in range(n_pages):
            w.add_blank_page(width=200, height=200)
        with open(path, "wb") as f:
            w.write(f)
        return path

    return _make
