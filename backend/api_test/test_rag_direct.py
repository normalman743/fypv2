#!/usr/bin/env python3
"""
直接测试RAG服务的document_chunks自动创建功能
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from app.models.database import engine
from app.models.file import File
from app.models.document_chunk import DocumentChunk
from app.services.rag_service import ProductionRAGService

def test_rag_direct():
    """直接测试RAG服务"""
    
    # 创建数据库会话
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        print("🧪 直接测试RAG服务的document_chunks创建...")
        
        # 1. 创建一个测试文件
        test_content = """# 直接测试文档

这是一个用于直接测试RAG服务的文档。

## 测试内容
- 第一部分：基础测试
- 第二部分：高级测试
- 第三部分：完整性验证

## 结论
如果你看到这个内容被正确分割并保存到数据库，说明RAG服务工作正常。
"""
        
        # 2. 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        print(f"📄 创建临时文件: {temp_file_path}")
        
        # 3. 查找一个现有的文件记录用于测试
        test_file = db.query(File).filter(File.id >= 1).first()
        if not test_file:
            print("❌ 没有找到测试文件记录")
            return
        
        print(f"📄 使用文件记录: ID={test_file.id}, 名称={test_file.original_name}")
        
        # 4. 检查处理前的状态
        before_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.physical_file_id == test_file.id
        ).count()
        print(f"📊 处理前数据库切片数: {before_chunks}")
        
        # 5. 直接调用RAG服务
        print("🚀 开始调用RAG服务...")
        rag_service = ProductionRAGService(db_session=db)
        
        try:
            result = rag_service.process_file(test_file, temp_file_path)
            print(f"✅ RAG处理结果: {result}")
            
            # 6. 检查处理后的状态
            after_chunks = db.query(DocumentChunk).filter(
                DocumentChunk.physical_file_id == test_file.id
            ).count()
            print(f"📊 处理后数据库切片数: {after_chunks}")
            
            # 7. 检查文件的chunk_count是否更新
            db.refresh(test_file)
            print(f"📊 文件chunk_count: {test_file.chunk_count}")
            
            # 8. 显示新创建的切片
            if after_chunks > before_chunks:
                new_chunks = db.query(DocumentChunk).filter(
                    DocumentChunk.physical_file_id == test_file.id
                ).limit(3).all()
                
                print("\n📝 新创建的切片:")
                for i, chunk in enumerate(new_chunks):
                    print(f"  切片{i+1}: ID={chunk.id}, 索引={chunk.chunk_index}, 长度={len(chunk.chunk_text)}")
                    print(f"    内容预览: {chunk.chunk_text[:100]}...")
                    print(f"    ChromaID: {chunk.chroma_id}")
            else:
                print("⚠️ 没有新的切片被创建")
                
        except Exception as e:
            print(f"❌ RAG处理失败: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                print(f"🗑️ 清理临时文件: {temp_file_path}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_rag_direct()
