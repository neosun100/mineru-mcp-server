"""auto_split 完整链路集成测试。

不调真实 API，但验证：
  1. prepare_files 拆分超页 PDF
  2. 模拟每个 chunk 都被处理过（手工造 .md + _images）
  3. merge_results 拼接 .md + 合并图片目录 + 路径修复
"""
import shutil

import pytest

import auto_split as AS


pytestmark = pytest.mark.integration


def _simulate_chunk_processing(chunk_pdf, n_images=2):
    """模拟某个 chunk 处理完成：在 chunks 目录下生成 _part.md 和 _part_images/。"""
    from pathlib import Path
    p = Path(chunk_pdf)
    chunks_dir = p.parent
    stem = p.stem  # e.g. big_part1of3

    # 假装的 markdown 内容（包含图片引用，模拟 mineru_async 修复后的格式）
    img_refs = "\n".join(
        f"![](images/{stem}_img{i}.jpg)" for i in range(n_images)
    )
    md_text = f"# {stem}\n\n这是分片 {stem} 的内容。\n\n{img_refs}\n\n正文段落。"
    (chunks_dir / f"{stem}.md").write_text(md_text, encoding="utf-8")

    # 假装的图片目录
    imgs_dir = chunks_dir / f"{stem}_images"
    imgs_dir.mkdir(exist_ok=True)
    for i in range(n_images):
        (imgs_dir / f"{stem}_img{i}.jpg").write_bytes(b"fake-jpg-data")


def test_prepare_then_merge_full_flow(make_pdf, tmp_path):
    """500 页 PDF → 拆 3 片 → 模拟处理 → 合并 → 验证 .md 和图片完整。"""
    big = make_pdf("big.pdf", 500)

    # Step 1: 拆分
    expanded, plans = AS.prepare_files([str(big)])
    assert len(plans) == 1
    n_parts = plans[0]["n"]
    assert n_parts == 3   # 500 / 180 → 3 片

    # Step 2: 模拟每个 chunk 都被处理
    for chunk in plans[0]["chunks"]:
        _simulate_chunk_processing(chunk, n_images=2)

    # Step 3: 合并
    merged = AS.merge_results(plans)
    assert len(merged) == 1
    final = merged[0]

    final_md = tmp_path / "big.md"
    final_imgs = tmp_path / "big_images"
    assert final_md.exists()
    assert final_imgs.exists()

    # Step 4: 验证字段
    assert final["original"] == str(big)
    assert final["markdown"] == str(final_md)
    assert final["image_count"] == 2 * n_parts  # 每片 2 图

    # Step 5: 验证 .md 内容
    text = final_md.read_text(encoding="utf-8")
    # 每片都有 Part 标记
    for i in range(1, n_parts + 1):
        assert f"<!-- ===== Part {i}/{n_parts} =====" in text
    # 图片引用全部改写到统一目录 + 加 partN_ 前缀
    import re
    refs = re.findall(r"!\[\]\(([^)]+)\)", text)
    assert len(refs) == 2 * n_parts
    for ref in refs:
        assert ref.startswith("big_images/part")
        # 验证物理文件存在
        assert (tmp_path / ref).exists()


def test_prepare_skips_in_limit_files(make_pdf):
    small = make_pdf("small.pdf", 100)
    expanded, plans = AS.prepare_files([str(small)])
    assert expanded == [str(small)]
    assert plans == []


def test_merge_handles_failed_chunk(make_pdf, tmp_path):
    """如果某个 chunk 没有 .md（处理失败），合并时跳过但保留标记。"""
    big = make_pdf("big.pdf", 360)
    expanded, plans = AS.prepare_files([str(big)])
    assert plans[0]["n"] == 2

    # 只模拟第 1 片成功，第 2 片失败
    _simulate_chunk_processing(plans[0]["chunks"][0], n_images=1)
    # 不动 chunks[1]

    merged = AS.merge_results(plans)
    final_md = tmp_path / "big.md"
    text = final_md.read_text(encoding="utf-8")
    assert "Part 1/2" in text
    assert "Part 2/2 (FAILED)" in text


def test_no_image_pdf_merges_to_zero(make_pdf, tmp_path):
    """纯文本 PDF（无图片）合并后图片数应为 0。"""
    big = make_pdf("text_only.pdf", 400)
    expanded, plans = AS.prepare_files([str(big)])

    for chunk in plans[0]["chunks"]:
        _simulate_chunk_processing(chunk, n_images=0)

    merged = AS.merge_results(plans)
    assert merged[0]["image_count"] == 0
    assert merged[0]["images"] is None
