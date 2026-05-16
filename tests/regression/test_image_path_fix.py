"""回归测试：防止"图片引用路径错位"bug 复发。

历史背景：
  v3.x 时代 mineru_async.py 在解压 zip 后，把 .md 直接 shutil.copy 到目标，
  没有改写其中的 `images/x.jpg` 引用，但又把图片复制到 `{stem}_images/`，
  导致渲染器找不到任何图片（用户看到全是 broken image）。
  v4.0.0 抽出 path_fixer 模块统一处理。

本测试确保：
  1. mineru_async.py 中没有"裸 shutil.copy(source_md)"
  2. mineru_batch_async.py 中也没有
  3. 两处都使用 path_fixer.rewrite_md_image_refs
"""
import re
from pathlib import Path

import pytest

import path_fixer as PF


pytestmark = pytest.mark.regression


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"


def test_mineru_async_uses_path_fixer():
    """mineru_async.py 必须用 rewrite_md_image_refs，不能裸 shutil.copy(source_md, ...)。"""
    text = (SRC / "mineru_async.py").read_text(encoding="utf-8")
    assert "rewrite_md_image_refs" in text, \
        "mineru_async.py 应使用 path_fixer.rewrite_md_image_refs"
    # 不应有裸的 shutil.copy(source_md, ...) 直接拷到 md_file
    assert not re.search(r"shutil\.copy\(\s*source_md\s*,\s*md_file\s*\)", text), \
        "禁止 shutil.copy(source_md, md_file)，应用 path_fixer 改写后再写入"


def test_batch_async_uses_path_fixer():
    """mineru_batch_async.py 同样要用 path_fixer。"""
    text = (SRC / "mineru_batch_async.py").read_text(encoding="utf-8")
    assert "rewrite_md_image_refs" in text
    assert not re.search(r"shutil\.copy\(\s*source_md\s*,\s*md_file\s*\)", text)


def test_path_fixer_full_flow_on_realistic_md():
    """模拟 mineru 返回的真实 markdown 形态，验证修复后不再有 ](images/。"""
    realistic_md = """# 第一章

第一段内容。

![](images/abc123.jpg)

第二段。表格如下：

| col1 | col2 |
|------|------|
| a | b |

![figure 2](images/def456.png)

公式 $E=mc^2$。

最后一图：

![](images/ghi789.gif)
"""
    fixed = PF.rewrite_md_image_refs(realistic_md, "report_images")
    # 不应再有裸 images/
    assert "](images/" not in fixed
    # 三个图片都应在新目录
    for h in ("abc123.jpg", "def456.png", "ghi789.gif"):
        assert f"](report_images/{h})" in fixed
    # 原 alt 文本保留
    assert "![figure 2]" in fixed


def test_chunk_merge_path_rewrite_with_part_prefix():
    """合并 chunks 时图片必须加 partN_ 前缀避免冲突。"""
    chunk_md = "![](images/x.jpg)\n![](images/y.jpg)"
    out = PF.rewrite_md_with_part_prefix(chunk_md, "doc_images", part_index=2)
    assert "](doc_images/part2_x.jpg)" in out
    assert "](doc_images/part2_y.jpg)" in out


def test_path_fixer_does_not_break_remote_images():
    """远程 URL 图片（http/https/data:）应原样保留。"""
    md = """
![local](images/local.jpg)
![remote](https://cdn.example.com/x.jpg)
![data](data:image/png;base64,iVBOR...)
"""
    fixed = PF.rewrite_md_image_refs(md, "doc_images")
    assert "doc_images/local.jpg" in fixed
    assert "https://cdn.example.com/x.jpg" in fixed
    assert "data:image/png;base64" in fixed


def test_real_world_5_pdf_outputs_have_no_broken_refs(sample_pdfs_dir):
    """如果设置了 MINERU_SAMPLE_PDFS_DIR 且目录里有 .md 产物，验证图片引用都能找到文件。

    这是 v4.0.0 端到端跑过的真实数据；如果某天产物被破坏，本测试会立刻警报。
    """
    if sample_pdfs_dir is None:
        pytest.skip("未设置 MINERU_SAMPLE_PDFS_DIR，跳过（仅在有产物时运行）")

    md_files = list(sample_pdfs_dir.glob("*.md"))
    if not md_files:
        pytest.skip("样本目录没有 .md 产物")

    total_refs = 0
    total_missing = 0
    for md in md_files:
        n_refs, missing = PF.verify_refs_exist(md)
        total_refs += n_refs
        total_missing += len(missing)
        assert len(missing) == 0, \
            f"{md.name} 有 {len(missing)} 个图片引用缺失：{missing[:3]}"

    print(f"\n  ✅ {len(md_files)} 个 .md 产物：{total_refs} 个图片引用全部存在")
