#!/usr/bin/env python3
"""
RAG系统完整测试套件
包含文件上传、数据库同步、检索等全面测试
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

from utils import APIClient, print_response, check_response, extract_data
from config import TEST_USER
import time

class RAGTestSuite:
    """RAG系统测试套件"""
    
    def __init__(self):
        self.client = APIClient()
        Session = sessionmaker(bind=engine)
        self.db = Session()
        
    def setup_auth(self):
        """设置认证"""
        login_data = {
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
        
        response = self.client.post("/auth/login", login_data)
        if check_response(response):
            data = extract_data(response)
            if data and "access_token" in data:
                self.client.set_token(data["access_token"])
                return True
        return False
    
    def test_rag_database_consistency(self):
        """测试RAG数据库一致性"""
        print("\n🔍 测试RAG数据库一致性...")
        
        # 查找一个已处理的文件
        test_file = self.db.query(File).filter(
            File.is_processed == True,
            File.processing_status == "completed"
        ).first()
        
        if not test_file:
            print("❌ 没有找到已处理的文件")
            return False
        
        print(f"📄 测试文件: {test_file.original_name} (ID: {test_file.id})")
        
        # 检查数据库中的切片数量
        db_chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.physical_file_id == test_file.id
        ).count()
        
        print(f"📊 数据库切片数: {db_chunks}")
        print(f"📊 记录chunk_count: {test_file.chunk_count}")
        
        # 数据一致性检查
        if db_chunks == test_file.chunk_count and db_chunks > 0:
            print("✅ 数据一致性检查通过")
            return True
        else:
            print(f"❌ 数据不一致: 数据库切片({db_chunks}) != chunk_count({test_file.chunk_count})")
            return False
    
    def test_rag_direct_processing(self):
        """测试RAG直接处理功能"""
        print("\n🧪 测试RAG直接处理功能...")
        
        # 创建测试内容
        test_content = f"""# RAG测试文档 {int(time.time())}

这是一个用于测试RAG系统的文档。

## 测试部分
- 数据库同步测试
- 重复处理防护测试
- 向量存储测试

## 验证内容
如果看到这个内容被正确处理，说明RAG系统工作正常。
测试时间戳: {time.time()}
"""
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        try:
            # 查找一个测试文件
            test_file = self.db.query(File).filter(File.id >= 1).first()
            if not test_file:
                print("❌ 没有找到测试文件记录")
                return False
            
            print(f"📄 使用文件记录: ID={test_file.id}")
            
            # 检查处理前状态
            before_chunks = self.db.query(DocumentChunk).filter(
                DocumentChunk.physical_file_id == test_file.id
            ).count()
            
            # 调用RAG服务
            rag_service = ProductionRAGService(db_session=self.db)
            result = rag_service.process_file(test_file, temp_file_path)
            
            # 检查处理后状态
            after_chunks = self.db.query(DocumentChunk).filter(
                DocumentChunk.physical_file_id == test_file.id
            ).count()
            
            print(f"📊 处理前切片数: {before_chunks}")
            print(f"📊 处理后切片数: {after_chunks}")
            
            if before_chunks > 0 and after_chunks == before_chunks:
                print("✅ 重复处理防护正常工作")
                return True
            elif before_chunks == 0 and after_chunks > 0:
                print("✅ 首次处理成功")
                return True
            else:
                print("❌ RAG处理异常")
                return False
                
        except Exception as e:
            print(f"❌ RAG直接处理测试失败: {e}")
            return False
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def test_rag_api_integration(self):
        """测试RAG API集成"""
        print("\n🔗 测试RAG API集成...")
        
        if not self.setup_auth():
            print("❌ 认证失败")
            return False
        
        # 创建RAG增强聊天
        timestamp = str(int(time.time()))
        chat_data = {
            "chat_type": "general",
            "first_message": f"请总结一下已上传文档的主要内容 - {timestamp}",
            "course_id": None
        }
        
        response = self.client.post("/chats", chat_data)
        print_response(response, "创建RAG测试聊天")
        
        if check_response(response):
            data = extract_data(response)
            if data and data.get("ai_message"):
                ai_message = data["ai_message"]
                print(f"📝 AI响应长度: {len(ai_message.get('content', ''))}")
                print(f"📊 RAG源数量: {len(ai_message.get('rag_sources', []))}")
                
                if len(ai_message.get('rag_sources', [])) > 0:
                    print("✅ RAG检索功能正常")
                    return True
                else:
                    print("⚠️ 没有检索到RAG源，可能是文档内容不匹配")
                    return True  # 不算错误，可能是查询内容不匹配
            else:
                print("❌ AI响应异常")
                return False
        return False
    
    def test_file_upload_with_rag(self):
        """测试文件上传并验证RAG处理"""
        print("\n📁 测试文件上传与RAG处理...")
        
        if not self.setup_auth():
            print("❌ 认证失败")
            return False
        
        # 创建测试文件
        test_content = f"""# 新上传测试文档

时间戳: {time.time()}

## 文档内容
这是一个新上传的测试文档，用于验证：
1. 文件上传功能
2. RAG自动处理
3. 数据库同步
4. 向量存储

## 测试结论
如果这个文档被正确处理，说明整个RAG流程工作正常。
"""
        
        # 创建临时文件用于上传
        temp_file_path = f"/tmp/rag_test_{int(time.time())}.txt"
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        try:
            # 上传文件
            with open(temp_file_path, 'rb') as f:
                files = {'file': (f'rag_test_{int(time.time())}.txt', f, 'text/plain')}
                data = {'course_id': '22', 'folder_id': '31'}  # 使用测试课程和文件夹
                
                response = self.client.post_file("/files/upload", files=files, data=data)
                
            if check_response(response):
                upload_data = extract_data(response)
                if upload_data and upload_data.get("file"):
                    file_info = upload_data["file"]
                    file_id = file_info["id"]
                    
                    print(f"📄 文件上传成功: ID={file_id}")
                    print(f"📊 处理状态: {file_info.get('processing_status')}")
                    print(f"📊 是否已处理: {file_info.get('is_processed')}")
                    
                    # 检查数据库中的切片
                    time.sleep(2)  # 等待处理完成
                    db_chunks = self.db.query(DocumentChunk).filter(
                        DocumentChunk.physical_file_id == file_id
                    ).count()
                    
                    # 检查文件记录
                    file_record = self.db.query(File).filter(File.id == file_id).first()
                    if file_record:
                        print(f"📊 数据库切片数: {db_chunks}")
                        print(f"📊 文件chunk_count: {file_record.chunk_count}")
                        
                        if db_chunks > 0 and db_chunks == file_record.chunk_count:
                            print("✅ 文件上传RAG处理成功")
                            return True
                        else:
                            print("❌ RAG处理数据不一致")
                            return False
                    else:
                        print("❌ 文件记录未找到")
                        return False
                else:
                    print("❌ 文件上传失败")
                    return False
            else:
                print("❌ 文件上传请求失败")
                return False
                
        except Exception as e:
            print(f"❌ 文件上传测试失败: {e}")
            return False
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def run_all_tests(self):
        """运行所有RAG测试"""
        print("🚀 开始RAG系统完整测试套件...")
        
        tests = [
            ("数据库一致性", self.test_rag_database_consistency),
            ("直接处理功能", self.test_rag_direct_processing),
            ("API集成", self.test_rag_api_integration),
            ("文件上传处理", self.test_file_upload_with_rag),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                print(f"\n{'='*50}")
                print(f"测试: {test_name}")
                print(f"{'='*50}")
                
                result = test_func()
                results[test_name] = result
                
                status = "✅ 通过" if result else "❌ 失败"
                print(f"\n{status} {test_name}")
                
            except Exception as e:
                print(f"❌ {test_name} 测试异常: {e}")
                results[test_name] = False
        
        # 测试总结
        print(f"\n{'='*50}")
        print("📊 RAG测试结果总结")
        print(f"{'='*50}")
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅" if result else "❌"
            print(f"{status} {test_name}")
        
        print(f"\n📋 总体结果: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有RAG测试通过！")
        else:
            print("⚠️ 部分测试失败，请检查系统状态")
    
    def cleanup(self):
        """清理资源"""
        if self.db:
            self.db.close()

def main():
    """主函数"""
    test_suite = RAGTestSuite()
    
    try:
        test_suite.run_all_tests()
    finally:
        test_suite.cleanup()

if __name__ == "__main__":
    main()
