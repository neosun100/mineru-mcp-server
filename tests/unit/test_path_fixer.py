"""path_fixer 模块单元测试。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import path_fixer as PF


def test_rewrite_basic():
    md = "# 标题\n\n![](images/abc.jpg)\n"
    out = PF.rewrite_md_image_refs(md, "report_images")
    assert "![](report_images/abc.jpg)" in out
    # 不应该残留任何 ](images/ 形式（裸 images/ 前缀）
    assert "](images/" not in out


def test_rewrite_with_alt():
    md = "![figure 1](images/x.png)\n"
    out = PF.rewrite_md_image_refs(md, "doc_images")
    assert "![figure 1](doc_images/x.png)" in out


def test_rewrite_keeps_remote_url():
    md = "![remote](https://cdn.example.com/img.jpg)\n"
    out = PF.rewrite_md_image_refs(md, "any_dir")
    assert "https://cdn.example.com/img.jpg" in out


def test_rewrite_idempotent_when_already_prefixed():
    md = "![](report_images/abc.jpg)"
    out = PF.rewrite_md_image_refs(md, "report_images")
    # 不应该重复加前缀
    assert out.count("report_images/") == 1


def test_part_prefix_form_1():
    """形式 1: ![](images/x) → ![](final/partN_x)"""
    md = "![](images/abc.jpg)"
    out = PF.rewrite_md_with_part_prefix(md, "千门_images", part_index=1)
    assert "千门_images/part1_abc.jpg" in out


def test_part_prefix_form_2():
    """形式 2: ![](chunk_images/x) → ![](final/partN_x)"""
    md = "![](千门_part1of3_images/abc.jpg)"
    out = PF.rewrite_md_with_part_prefix(
        md, "千门_images", part_index=1,
        chunk_dir_name="千门_part1of3_images",
    )
    assert "千门_images/part1_abc.jpg" in out
    assert "千门_part1of3_images" not in out


def test_part_prefix_does_not_affect_other_parts():
    """同一文件内多张图片，加同一个 partN 前缀。"""
    md = "![](images/a.jpg)\n![](images/b.jpg)"
    out = PF.rewrite_md_with_part_prefix(md, "doc_images", part_index=2)
    assert "doc_images/part2_a.jpg" in out
    assert "doc_images/part2_b.jpg" in out


def test_verify_refs_exist(tmp_path):
    img_dir = tmp_path / "doc_images"
    img_dir.mkdir()
    (img_dir / "a.jpg").write_bytes(b"x")
    (img_dir / "b.jpg").write_bytes(b"x")

    md_path = tmp_path / "doc.md"
    md_path.write_text(
        "![](doc_images/a.jpg)\n![](doc_images/b.jpg)\n![](doc_images/missing.jpg)\n",
        encoding="utf-8",
    )

    total, missing = PF.verify_refs_exist(md_path)
    assert total == 3
    assert "doc_images/missing.jpg" in missing


def test_empty_md_text():
    assert PF.rewrite_md_image_refs("", "any") == ""
    assert PF.rewrite_md_with_part_prefix("", "any", 1) == ""
