#!/usr/bin/env python3
"""
快速RAG状态检查脚本
用于快速检查RAG系统的整体状态
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from app.models.database import engine
from app.models.file import File
from app.models.document_chunk import DocumentChunk

def quick_rag_status():
    """快速检查RAG系统状态"""
    
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        print("🔍 RAG系统状态检查")
        print("="*40)
        
        # 1. 检查文件统计
        total_files = db.query(File).count()
        processed_files = db.query(File).filter(File.is_processed == True).count()
        completed_files = db.query(File).filter(File.processing_status == "completed").count()
        
        print(f"📄 文件统计:")
        print(f"  总文件数: {total_files}")
        print(f"  已处理文件: {processed_files}")
        print(f"  完成处理文件: {completed_files}")
        
        # 2. 检查切片统计
        total_chunks = db.query(DocumentChunk).count()
        print(f"\n📊 切片统计:")
        print(f"  总切片数: {total_chunks}")
        
        # 3. 检查数据一致性
        print(f"\n🔍 数据一致性检查:")
        inconsistent_files = []
        
        files_with_chunks = db.query(File).filter(File.chunk_count > 0).all()
        
        for file in files_with_chunks:
            actual_chunks = db.query(DocumentChunk).filter(
                DocumentChunk.physical_file_id == file.id
            ).count()
            
            if actual_chunks != file.chunk_count:
                inconsistent_files.append({
                    'id': file.id,
                    'name': file.original_name,
                    'recorded': file.chunk_count,
                    'actual': actual_chunks
                })
        
        if inconsistent_files:
            print("  ❌ 发现数据不一致:")
            for file_info in inconsistent_files:
                print(f"    文件{file_info['id']}: 记录={file_info['recorded']}, 实际={file_info['actual']}")
        else:
            print("  ✅ 数据一致性正常")
        
        # 4. 检查最近处理的文件
        print(f"\n📅 最近处理的文件:")
        recent_files = db.query(File).filter(
            File.is_processed == True
        ).order_by(File.created_at.desc()).limit(3).all()
        
        if recent_files:
            for file in recent_files:
                print(f"  {file.id}: {file.original_name} (chunks: {file.chunk_count})")
        else:
            print("  无已处理文件")
        
        # 5. ChromaDB目录检查
        chroma_dir = "../data/chroma"  # 相对于api_test目录的路径
        abs_chroma_dir = os.path.abspath(chroma_dir)
        
        if os.path.exists(chroma_dir):
            chroma_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(chroma_dir)
                for filename in filenames
            )
            
            # 计算集合数量
            collections = []
            try:
                for item in os.listdir(chroma_dir):
                    item_path = os.path.join(chroma_dir, item)
                    if os.path.isdir(item_path) and not item.startswith('.'):
                        collections.append(item)
            except:
                pass
            
            print(f"\n💾 ChromaDB状态:")
            print(f"  数据目录: {abs_chroma_dir}")
            print(f"  数据大小: {chroma_size / 1024:.2f} KB")
            print(f"  集合数量: {len(collections)}")
            if collections:
                print(f"  集合列表: {', '.join(collections)}")
        else:
            print(f"\n💾 ChromaDB状态:")
            print(f"  ❌ 数据目录不存在: {abs_chroma_dir}")
            print(f"  (检查路径: {chroma_dir})")
        
        # 6. 整体健康度评估
        print(f"\n🏥 整体健康度:")
        
        health_score = 0
        max_score = 4
        
        if processed_files > 0:
            health_score += 1
            print("  ✅ 有已处理文件")
        else:
            print("  ❌ 无已处理文件")
        
        if total_chunks > 0:
            health_score += 1
            print("  ✅ 有文档切片")
        else:
            print("  ❌ 无文档切片")
        
        if not inconsistent_files:
            health_score += 1
            print("  ✅ 数据一致性良好")
        else:
            print("  ❌ 存在数据不一致")
        
        if os.path.exists(chroma_dir):
            health_score += 1
            print("  ✅ ChromaDB可用")
        else:
            print("  ❌ ChromaDB不可用")
        
        health_percentage = (health_score / max_score) * 100
        print(f"\n📊 健康度得分: {health_score}/{max_score} ({health_percentage:.1f}%)")
        
        if health_percentage >= 75:
            print("🎉 RAG系统状态良好")
        elif health_percentage >= 50:
            print("⚠️ RAG系统基本正常，建议检查异常项")
        else:
            print("❌ RAG系统存在问题，需要修复")
        
    except Exception as e:
        print(f"❌ 状态检查失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    quick_rag_status()
