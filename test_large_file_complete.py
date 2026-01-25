#!/usr/bin/env python3
"""
测试超大文件完整流程：拆分 → 处理 → 合并
"""
import asyncio
import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mineru_async import MinerUAsyncProcessor
from split_large_file import split_large_pdf

async def process_large_file_complete(file_path: str):
    """完整处理超大文件"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║              超大文件完整流程测试                            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    # 1. 拆分文件
    print("\n步骤1: 拆分文件")
    print("="*60)
    chunks = split_large_pdf(file_path)
    
    if len(chunks) == 1:
        print("✅ 文件无需拆分")
        return
    
    # 2. 并行处理所有分片
    print(f"\n步骤2: 并行处理 {len(chunks)} 个分片")
    print("="*60)
    
    processor = MinerUAsyncProcessor()
    
    tasks = [processor.process_file(chunk) for chunk in chunks]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 检查结果
    success_results = []
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"❌ 分片{i} 处理异常: {result}")
        elif result:
            print(f"✅ 分片{i} 处理成功")
            success_results.append(result)
        else:
            print(f"❌ 分片{i} 处理失败")
    
    if len(success_results) != len(chunks):
        print(f"\n❌ 部分分片处理失败")
        return None
    
    # 3. 合并结果
    print(f"\n步骤3: 合并结果")
    print("="*60)
    
    original_name = Path(file_path).stem
    output_dir = Path(file_path).parent
    
    merged_md = output_dir / f"{original_name}_merged.md"
    merged_images = output_dir / f"{original_name}_merged_images"
    
    # 合并Markdown
    print("📝 合并Markdown...")
    with open(merged_md, 'w', encoding='utf-8') as out:
        for i, result in enumerate(success_results, 1):
            if i > 1:
                out.write("\n\n" + "="*60 + "\n")
                out.write(f"# 分片 {i}\n")
                out.write("="*60 + "\n\n")
            
            md_file = result['output']['markdown']
            with open(md_file, 'r', encoding='utf-8') as f:
                out.write(f.read())
    
    print(f"✅ Markdown合并完成: {merged_md}")
    
    # 合并图片
    print("🖼️  合并图片...")
    merged_images.mkdir(exist_ok=True)
    
    total_images = 0
    for i, result in enumerate(success_results, 1):
        images_dir = Path(result['output']['images'])
        if images_dir.exists():
            for img in images_dir.glob("*"):
                new_name = f"part{i}_{img.name}"
                shutil.copy(img, merged_images / new_name)
                total_images += 1
    
    print(f"✅ 图片合并完成: {total_images}个 → {merged_images}")
    
    # 4. 清理分片文件（可选）
    print(f"\n步骤4: 清理临时文件")
    print("="*60)
    
    chunks_dir = Path(chunks[0]).parent
    print(f"保留分片目录: {chunks_dir}")
    print(f"（如需清理，手动删除）")
    
    # 5. 输出结果
    print(f"\n" + "="*60)
    print("最终输出")
    print("="*60)
    print(f"✅ 合并后的Markdown: {merged_md}")
    print(f"✅ 合并后的图片: {merged_images}")
    print(f"✅ 总图片数: {total_images}")
    
    return {
        'merged_markdown': str(merged_md),
        'merged_images': str(merged_images),
        'total_images': total_images,
        'chunks_processed': len(success_results)
    }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 test_large_file_complete.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    result = asyncio.run(process_large_file_complete(file_path))
    
    if result:
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║              ✅ 超大文件完整流程测试通过！                   ║")
        print("╚══════════════════════════════════════════════════════════════╝")
    else:
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║              ❌ 测试失败！                                   ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        sys.exit(1)
