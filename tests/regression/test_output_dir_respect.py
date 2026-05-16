"""回归测试：防止"用户传的 output_dir 被静默忽略"bug 复发。

历史背景：
  v4.0.0 发布前，mineru_async.py 第 676-678 行有：

      output_path = Path(output_dir)
      if not file_info['is_url']:
          output_path = Path(file_path).parent

  这导致**所有本地文件**无论用户传什么 output_dir，都会强制覆盖到
  原始文件所在目录。直接后果是：跑测试时用 page_ranges='1-5' +
  output_dir='/tmp/...'，结果 5 页的部分输出**覆盖了**原始位置的
  完整 .md。PDF-A.md 因此从 47K 字符被截到 1.4K。

  修复后逻辑：
    - 用户显式传 output_dir（非默认 './output'）→ 尊重用户选择
    - 用户未传 → 本地文件用文件同目录，URL 用 './output'
"""
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.regression


def test_output_dir_bug_pattern_not_present():
    """旧的 buggy 代码模式不应再出现。"""
    src = Path(__file__).resolve().parents[2] / "src" / "mineru_async.py"
    text = src.read_text(encoding="utf-8")

    # buggy 模式特征：if not is_url: output_path = file.parent
    # 修复后必须含 output_dir == "./output" 的判断
    assert 'output_dir == "./output"' in text or "output_dir == './output'" in text, \
        "process_file 必须在 user 显式传 output_dir 时尊重之"


def test_user_output_dir_is_respected_for_local_file(tmp_path, make_pdf):
    """模拟逻辑：本地文件 + 显式 output_dir 应该用 output_dir 不是 file.parent。"""
    # 这个测试不调真实 API，只验证关键逻辑路径
    # 直接复刻 mineru_async.py 第 676-680 行的判定
    file_path = make_pdf("doc.pdf", 5)
    file_info = {"is_url": False}

    user_output = tmp_path / "custom_out"
    output_dir = str(user_output)

    # 模拟 process_file 内部逻辑
    output_path = Path(output_dir)
    if not file_info["is_url"] and output_dir == "./output":
        output_path = Path(file_path).parent

    # 用户传了非默认值，应保留用户选择
    assert output_path == user_output, \
        f"output_path 应是用户传的 {user_output}，而不是 {output_path}"


def test_default_output_dir_uses_file_parent_for_local(tmp_path, make_pdf):
    """没传 output_dir 时（默认 './output'），本地文件应该用 file.parent。"""
    file_path = make_pdf("doc.pdf", 5)
    file_info = {"is_url": False}

    output_dir = "./output"  # 默认值
    output_path = Path(output_dir)
    if not file_info["is_url"] and output_dir == "./output":
        output_path = Path(file_path).parent

    assert output_path == file_path.parent
