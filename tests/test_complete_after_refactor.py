#!/usr/bin/env python3
"""
完整验证测试 - 目录结构调整后
测试所有功能是否正常
"""
import asyncio
import sys
import time
from pathlib import Path

# 添加src到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from mineru_async import MinerUAsyncProcessor
from mineru_batch_async import BatchAsyncProcessor

async def test_case(name: str, file_path: str, expected_result: str = "success"):
    """测试单个用例"""
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"{'='*60}")
    print(f"文件: {file_path}")
    
    # 检查文件是否存在
    if not Path(file_path).exists():
        print(f"⚠️  文件不存在，跳过")
        return None
    
    processor = MinerUAsyncProcessor()
    
    start_time = time.time()
    try:
        result = await processor.process_file(file_path)
        elapsed = time.time() - start_time
        
        if result:
            print(f"✅ 成功! 耗时: {elapsed:.1f}秒")
            print(f"  输出: {result['output']['markdown']}")
            return True
        else:
            print(f"❌ 失败! 耗时: {elapsed:.1f}秒")
            return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 异常: {e} (耗时: {elapsed:.1f}秒)")
        return False

async def test_batch():
    """测试批量处理"""
    print(f"\n{'='*60}")
    print(f"测试: 批量异步并行处理（3个文件）")
    print(f"{'='*60}")
    
    files = [
        "/Users/jiasunm/Downloads/2601.12538.pdf",
        "/Users/jiasunm/Downloads/智能湖仓 – 现代化数据架构.pptx",
        "/Users/jiasunm/Downloads/字节流  CDH→EMR 迁移调优.docx"
    ]
    
    # 检查文件
    existing_files = [f for f in files if Path(f).exists()]
    if not existing_files:
        print("⚠️  测试文件不存在，跳过")
        return None
    
    print(f"找到 {len(existing_files)} 个文件")
    
    processor = BatchAsyncProcessor(max_concurrent=3)
    
    start_time = time.time()
    try:
        results = await processor.process_files_parallel(existing_files)
        elapsed = time.time() - start_time
        
        success_count = sum(1 for r in results if r.status == 'done')
        
        print(f"\n✅ 批量处理完成! 耗时: {elapsed:.1f}秒")
        print(f"  成功: {success_count}/{len(existing_files)}")
        
        return success_count == len(existing_files)
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 异常: {e} (耗时: {elapsed:.1f}秒)")
        return False

async def run_all_tests():
    """运行所有测试"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║              完整验证测试 - 目录结构调整后                  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    tests = [
        ("本地PDF", "/Users/jiasunm/Downloads/2601.12538.pdf"),
        ("本地PPTX", "/Users/jiasunm/Downloads/智能湖仓 – 现代化数据架构.pptx"),
        ("本地DOCX", "/Users/jiasunm/Downloads/字节流  CDH→EMR 迁移调优.docx"),
        ("本地图片", "/Users/jiasunm/Downloads/实时大屏应用 (1).jpg"),
    ]
    
    results = {}
    
    for name, file_path in tests:
        result = await test_case(name, file_path)
        results[name] = result
        
        # 短暂延迟，避免API限流
        if result is not None:
            await asyncio.sleep(2)
    
    # 批量处理测试
    batch_result = await test_batch()
    results["批量处理"] = batch_result
    
    # 汇总
    print(f"\n{'='*60}")
    print("测试结果汇总")
    print(f"{'='*60}")
    
    for name, result in results.items():
        if result is True:
            print(f"  ✅ {name}: 通过")
        elif result is False:
            print(f"  ❌ {name}: 失败")
        else:
            print(f"  ⚠️  {name}: 跳过")
    
    success_count = sum(1 for r in results.values() if r is True)
    total_count = len([r for r in results.values() if r is not None])
    
    print(f"\n总计: {success_count}/{total_count} 通过")
    
    if success_count == total_count and total_count > 0:
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║              ✅ 所有测试通过！                               ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        return True
    else:
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║              ⚠️  部分测试失败或跳过                          ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        return False

if __name__ == '__main__':
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
