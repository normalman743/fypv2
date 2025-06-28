#!/usr/bin/env python3
"""
LangChain RAG Mock 测试
使用LangChain的文档加载器、文本分割器、向量存储等组件
"""

import os
import tempfile
import time
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# LangChain imports - 使用正确的模块路径
from langchain_community.document_loaders import (
    PyPDFLoader, 
    Docx2txtLoader, 
    TextLoader,
    UnstructuredMarkdownLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from langchain.embeddings.base import Embeddings

# OpenAI imports
import openai
from openai import OpenAI

@dataclass
class FileMetadata:
    """文件元数据"""
    file_id: int
    filename: str
    file_type: str
    course_id: Optional[int] = None
    chunk_count: int = 0
    processed_at: str = ""

class OpenAIEmbeddingsWrapper(Embeddings):
    """OpenAI Embeddings包装器"""
    
    def __init__(self, model: str = "text-embedding-ada-002"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """为文档列表生成嵌入向量"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            print(f"⚠️ OpenAI API调用失败: {e}")
            print("🔄 回退到Mock Embeddings")
            return self._mock_embeddings(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """为查询生成嵌入向量"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=[text]
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"⚠️ OpenAI API调用失败: {e}")
            print("🔄 回退到Mock Embeddings")
            return self._mock_embeddings([text])[0]
    
    def _mock_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Mock embeddings作为备用"""
        import random
        embeddings = []
        for text in texts:
            random.seed(hash(text) % 10000)
            embedding = [random.uniform(-1, 1) for _ in range(1536)]
            embeddings.append(embedding)
        return embeddings

class LangChainRAGService:
    """使用LangChain的RAG服务"""
    
    def __init__(self, use_openai: bool = True):
        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", " ", ""]
        )
        
        # 选择嵌入模型
        if use_openai and os.getenv("OPENAI_API_KEY"):
            print("🚀 使用OpenAI Embeddings")
            self.embeddings = OpenAIEmbeddingsWrapper()
        else:
            print("🤖 使用Mock Embeddings")
            self.embeddings = OpenAIEmbeddingsWrapper()  # 会回退到mock
        
        # 向量存储
        self.vectorstores: Dict[str, Chroma] = {}
        
        # 文件元数据
        self.file_metadata: Dict[int, FileMetadata] = {}
        
        # 支持的文档加载器
        self.loaders = {
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.txt': TextLoader,
            '.md': UnstructuredMarkdownLoader,
            '.py': TextLoader,
            '.js': TextLoader,
            '.html': TextLoader,
            '.json': TextLoader,
            '.csv': TextLoader
        }
    
    def process_file(self, file_id: int, file_path: str, course_id: Optional[int] = None) -> Dict[str, Any]:
        """处理文件：加载、分割、向量化、存储"""
        print(f"🚀 开始处理文件: {file_path} (ID: {file_id})")
        start_time = time.time()
        
        # 1. 获取文件类型
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in self.loaders:
            raise ValueError(f"不支持的文件类型: {file_ext}")
        
        # 2. 加载文档
        loader_class = self.loaders[file_ext]
        loader = loader_class(file_path)
        documents = loader.load()
        print(f"📄 加载完成: {len(documents)} 个文档")
        
        # 3. 分割文档
        chunks = self.text_splitter.split_documents(documents)
        print(f"✂️ 分割完成: {len(chunks)} 个块")
        
        # 4. 添加元数据
        for chunk in chunks:
            chunk.metadata.update({
                "file_id": str(file_id),
                "course_id": str(course_id) if course_id else "global",
                "filename": os.path.basename(file_path)
            })
        
        # 5. 存储到向量数据库
        collection_name = f"course_{course_id}" if course_id else "global"
        
        if collection_name not in self.vectorstores:
            # 创建新的向量存储
            self.vectorstores[collection_name] = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                collection_name=collection_name
            )
        else:
            # 添加到现有向量存储
            self.vectorstores[collection_name].add_documents(chunks)
        
        # 6. 保存元数据
        self.file_metadata[file_id] = FileMetadata(
            file_id=file_id,
            filename=os.path.basename(file_path),
            file_type=file_ext,
            course_id=course_id,
            chunk_count=len(chunks),
            processed_at=datetime.now().isoformat()
        )
        
        processing_time = time.time() - start_time
        print(f"✅ 文件处理完成! 耗时: {processing_time:.2f}秒")
        
        return {
            "file_id": file_id,
            "status": "ready",
            "chunks_created": len(chunks),
            "processing_time": processing_time,
            "collection": collection_name
        }
    
    def search(self, query: str, chat_type: str = "general", course_id: Optional[int] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索相关文档"""
        print(f"🔍 搜索: '{query}' (类型: {chat_type}, 课程: {course_id})")
        
        results = []
        
        if chat_type == "course" and course_id:
            # 课程聊天：优先搜索课程文件，补充全局文件
            course_collection = f"course_{course_id}"
            if course_collection in self.vectorstores:
                course_results = self.vectorstores[course_collection].similarity_search_with_score(
                    query, k=limit
                )
                results.extend(course_results)
            
            # 补充全局文件
            if "global" in self.vectorstores:
                global_results = self.vectorstores["global"].similarity_search_with_score(
                    query, k=limit//2
                )
                results.extend(global_results)
        else:
            # 通用聊天：只搜索全局文件
            if "global" in self.vectorstores:
                results = self.vectorstores["global"].similarity_search_with_score(
                    query, k=limit
                )
        
        # 按相关性排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        # 格式化结果
        formatted_results = []
        for doc, score in results[:limit]:
            formatted_results.append({
                "content": doc.page_content,
                "score": score,
                "source_file": doc.metadata.get("filename", "unknown"),
                "file_id": doc.metadata.get("file_id"),
                "course_id": doc.metadata.get("course_id")
            })
        
        print(f"📊 找到 {len(formatted_results)} 个相关结果")
        return formatted_results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "total_files": len(self.file_metadata),
            "collections": {}
        }
        
        for collection_name, vectorstore in self.vectorstores.items():
            stats["collections"][collection_name] = vectorstore._collection.count()
        
        return stats

def create_test_files():
    """创建测试文件"""
    test_files = []
    
    # 创建PDF测试文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""
数据结构与算法课程

第一章：线性数据结构
数组是最基本的数据结构，它是一块连续的内存空间，用于存储相同类型的数据。数组的优点是访问速度快，缺点是插入和删除操作较慢。

链表是另一种重要的线性数据结构。链表由节点组成，每个节点包含数据和指向下一个节点的指针。链表的优点是插入和删除操作快，缺点是访问速度较慢。

第二章：树形数据结构
二叉树是一种特殊的树形结构，每个节点最多有两个子节点。二叉树在计算机科学中有广泛应用，如二叉搜索树、AVL树、红黑树等。

快速排序是一种高效的排序算法，平均时间复杂度为O(nlogn)。它使用分治策略，将数组分成两部分，然后递归地对这两部分进行排序。
        """)
        test_files.append(("course_content.txt", f.name))
    
    # 创建全局内容文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""
校园生活指南

崇基学院体育馆位于学院的中心位置，提供各种体育设施。体育馆的开放时间是周一至周五上午9点至晚上10点，周末和节假日为上午10点至晚上8点。

崇基学院图书馆是学生学习的重要场所。图书馆提供丰富的图书资源和安静的学习环境。开放时间为每天上午8点至晚上11点。

学生餐厅提供各种美食选择，包括中餐、西餐和素食。餐厅的营业时间是早上7点至晚上9点。
        """)
        test_files.append(("global_content.txt", f.name))
    
    return test_files

def test_langchain_rag():
    """测试LangChain RAG功能"""
    print("🧪 开始LangChain RAG测试\n")
    
    # 检查OpenAI API密钥
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "sk-test-key":
        print("🔑 检测到OpenAI API密钥，将使用真实API")
        use_openai = True
    else:
        print("🔑 未检测到有效OpenAI API密钥，将使用Mock模式")
        use_openai = False
    
    # 初始化RAG服务
    rag_service = LangChainRAGService(use_openai=use_openai)
    
    # 创建测试文件
    test_files = create_test_files()
    
    try:
        # 测试1：处理课程文件
        print("=" * 50)
        print("测试1：处理课程文件")
        print("=" * 50)
        
        result1 = rag_service.process_file(
            file_id=1,
            file_path=test_files[0][1],
            course_id=101
        )
        print(f"处理结果: {json.dumps(result1, indent=2, ensure_ascii=False)}\n")
        
        # 测试2：处理全局文件
        print("=" * 50)
        print("测试2：处理全局文件")
        print("=" * 50)
        
        result2 = rag_service.process_file(
            file_id=2,
            file_path=test_files[1][1]
        )
        print(f"处理结果: {json.dumps(result2, indent=2, ensure_ascii=False)}\n")
        
        # 测试3：课程聊天搜索
        print("=" * 50)
        print("测试3：课程聊天搜索")
        print("=" * 50)
        
        results = rag_service.search("什么是二叉树？", chat_type="course", course_id=101)
        print(f"\n查询: '什么是二叉树？'")
        for i, result in enumerate(results[:3]):
            print(f"  {i+1}. 文件: {result['source_file']}")
            print(f"     内容: {result['content'][:100]}...")
            print(f"     相关性: {result['score']:.3f}")
        
        # 测试4：通用聊天搜索
        print("\n" + "=" * 50)
        print("测试4：通用聊天搜索")
        print("=" * 50)
        
        results = rag_service.search("体育馆的开放时间是什么？", chat_type="general")
        print(f"\n查询: '体育馆的开放时间是什么？'")
        for i, result in enumerate(results[:3]):
            print(f"  {i+1}. 文件: {result['source_file']}")
            print(f"     内容: {result['content'][:100]}...")
            print(f"     相关性: {result['score']:.3f}")
        
        # 测试5：统计信息
        print("\n" + "=" * 50)
        print("测试5：统计信息")
        print("=" * 50)
        
        stats = rag_service.get_stats()
        print(f"统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
        print("\n🎉 LangChain RAG测试完成！")
        
    finally:
        # 清理测试文件
        for _, file_path in test_files:
            try:
                os.unlink(file_path)
            except:
                pass

if __name__ == "__main__":
    test_langchain_rag() 