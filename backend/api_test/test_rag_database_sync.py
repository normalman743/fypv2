#!/usr/bin/env python3
"""
测试RAG数据库同步功能
验证文档切片是否正确保存到数据库
"""

import os
import sys
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from app.models.database import engine
from app.models.file import File
from app.models.document_chunk import DocumentChunk
from app.services.rag_service import ProductionRAGService
import tempfile

def test_rag_database_sync():
    """测试RAG数据库同步"""
    
    # 创建数据库会话
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        print("🧪 测试RAG数据库同步功能...")
        
        # 1. 查找一个已处理的文件
        test_file = db.query(File).filter(
            File.is_processed == True,
            File.processing_status == "completed"
        ).first()
        
        if not test_file:
            print("❌ 没有找到已处理的文件，请先上传文件")
            return
        
        print(f"📄 测试文件: {test_file.original_name} (ID: {test_file.id})")
        
        # 2. 检查当前的document_chunks记录
        current_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.physical_file_id == test_file.id
        ).count()
        
        print(f"📊 当前数据库中的切片数量: {current_chunks}")
        print(f"📊 files表中记录的chunk_count: {test_file.chunk_count}")
        
        # 3. 检查ChromaDB中的数据
        rag_service = ProductionRAGService(db_session=db)
        collection_name = f"course_{test_file.course_id}" if test_file.course_id else "global"
        vectorstore = rag_service._get_vectorstore(collection_name)
        
        if vectorstore:
            # 尝试搜索该文件的内容
            results = vectorstore.similarity_search(
                f"filename:{test_file.original_name}", 
                k=5
            )
            print(f"📊 ChromaDB中找到的相关切片: {len(results)}")
            
            for i, result in enumerate(results[:2]):
                print(f"  切片{i+1}: {result.page_content[:100]}...")
        else:
            print("❌ 未找到对应的ChromaDB集合")
        
        # 4. 数据一致性检查
        if current_chunks == 0 and test_file.chunk_count > 0:
            print("⚠️ 数据不一致: 数据库中无切片记录，但chunk_count>0")
            print("💡 建议重新处理文件以同步数据")
        elif current_chunks > 0 and test_file.chunk_count == current_chunks:
            print("✅ 数据一致: 数据库切片数量与chunk_count匹配")
        else:
            print(f"⚠️ 数据不一致: 数据库切片({current_chunks}) != chunk_count({test_file.chunk_count})")
        
        print("\n📋 总结:")
        print(f"- 文件处理状态: {test_file.processing_status}")
        print(f"- 数据库切片数: {current_chunks}")
        print(f"- 记录chunk_count: {test_file.chunk_count}")
        print(f"- ChromaDB可用: {'是' if vectorstore else '否'}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_rag_database_sync()
