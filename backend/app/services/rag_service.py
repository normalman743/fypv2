#!/usr/bin/env python3
"""
Production RAG Service
Integrates LangChain RAG functionality into the existing chat/message system
"""

import os
import time
import json
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# LangChain imports
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
from openai import OpenAI

# Database models
from sqlalchemy.orm import Session
from app.models.file import File
from app.models.document_chunk import DocumentChunk
from app.models.course import Course


@dataclass
class RAGSource:
    """RAG检索源"""
    source_file: str
    chunk_id: int
    content: str
    score: float
    file_id: Optional[str] = None
    course_id: Optional[str] = None


class OpenAIEmbeddingsWrapper(Embeddings):
    """OpenAI Embeddings包装器 - 自动降级到Mock"""
    
    def __init__(self, model: str = "text-embedding-ada-002"):
        self.model = model
        self.client = None
        
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "sk-test-key":
            try:
                self.client = OpenAI(api_key=api_key)
                # 测试API连接
                self.client.embeddings.create(model=self.model, input=["test"])
                print("🚀 OpenAI Embeddings initialized successfully")
            except Exception as e:
                print(f"⚠️ OpenAI API initialization failed: {e}")
                print("🔄 Falling back to Mock Embeddings")
                self.client = None
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """为文档列表生成嵌入向量"""
        if self.client:
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts
                )
                return [embedding.embedding for embedding in response.data]
            except Exception as e:
                print(f"⚠️ OpenAI API call failed: {e}")
                print("🔄 Falling back to Mock Embeddings")
        
        return self._mock_embeddings(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """为查询生成嵌入向量"""
        if self.client:
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=[text]
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"⚠️ OpenAI API call failed: {e}")
                print("🔄 Falling back to Mock Embeddings")
        
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


class ProductionRAGService:
    """生产级RAG服务 - 可插拔替换MockAIService"""
    
    def __init__(self, data_dir: str = "./data/chroma", use_openai: bool = True, db_session: Session = None):
        """
        初始化RAG服务
        
        Args:
            data_dir: ChromaDB数据存储目录
            use_openai: 是否尝试使用OpenAI API
            db_session: 数据库会话（用于同步保存文档切片）
        """
        self.data_dir = data_dir
        self.db_session = db_session
        os.makedirs(data_dir, exist_ok=True)
        
        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", " ", ""]
        )
        
        # 嵌入模型
        self.embeddings = OpenAIEmbeddingsWrapper()
        
        # 向量存储缓存
        self.vectorstores: Dict[str, Chroma] = {}
        
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
        
        print(f"📁 RAG Service initialized with data directory: {data_dir}")
    
    def process_file(self, file, file_path: str) -> Dict[str, Any]:
        """
        处理文件并添加到向量数据库
        
        Args:
            file: 数据库文件对象
            file_path: 实际文件路径
            
        Returns:
            处理结果信息
        """
        print(f"🚀 Processing file: {file.original_name} (ID: {file.id})")
        start_time = time.time()
        
        # 1. 检查文件类型
        file_ext = os.path.splitext(file.original_name)[1].lower()
        if file_ext not in self.loaders:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # 2. 加载文档
        loader_class = self.loaders[file_ext]
        loader = loader_class(file_path)
        documents = loader.load()
        
        # 3. 分割文档
        chunks = self.text_splitter.split_documents(documents)
        
        # 4. 添加元数据
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "file_id": str(file.id),
                "course_id": str(file.course_id) if hasattr(file, "course_id") and getattr(file, "course_id", None) else "global",
                "filename": file.original_name,
                "file_type": getattr(file, "file_type", "global"),
                "chunk_id": i,
                "processed_at": datetime.now().isoformat()
            })
        
        # 5. 根据文件作用域确定集合名称
        file_scope = getattr(file, "scope", "course")
        if file_scope == "global":
            collection_name = "global"
        elif hasattr(file, "course_id") and getattr(file, "course_id", None):
            collection_name = f"course_{file.course_id}"
        else:
            collection_name = "personal"
        
        # 6. 存储到向量数据库
        vectorstore = self._get_or_create_vectorstore(collection_name)
        vectorstore.add_documents(chunks)
        
        # 7. 同步保存文档切片到数据库
        if self.db_session:
            print(f"🔧 数据库会话可用，开始保存切片到数据库...")
            # 获取文件信息
            course_id = getattr(file, "course_id", None) if hasattr(file, "course_id") else None
            file_scope = getattr(file, "scope", "course")
            self._save_chunks_to_db(chunks, file, course_id, file_scope)
        else:
            print(f"⚠️ 数据库会话不可用，跳过数据库同步")
        
        processing_time = time.time() - start_time
        print(f"✅ File processed: {len(chunks)} chunks, {processing_time:.2f}s")
        
        return {
            "file_id": file.id,
            "status": "ready",
            "chunks_created": len(chunks),
            "processing_time": processing_time,
            "collection": collection_name
        }
    
    def _save_chunks_to_db(self, chunks: List[Document], file_obj, course_id: Optional[int], file_scope: str = "course"):
        """将文档切片同步保存到数据库"""
        try:
            # 获取正确的 ID
            file_id = file_obj.id
            
            # 检查文件是否已经处理过 (使用统一的 file_id)
            existing_chunks = self.db_session.query(DocumentChunk).filter(
                DocumentChunk.file_id == file_id
            ).count()

            if existing_chunks > 0:
                print(f"⚠️ 文件 {file_id} 已有 {existing_chunks} 个切片，跳过重复处理")
                return

            print(f"💾 Saving {len(chunks)} chunks to database for file {file_id}")

            for i, chunk in enumerate(chunks):
                chroma_id = str(uuid.uuid4())
                token_count = len(chunk.page_content.split())
                
                # 使用统一的文件模型
                chunk_record = DocumentChunk(
                    file_id=file_id,
                    chunk_text=chunk.page_content,
                    chunk_index=i,
                    token_count=token_count,
                    chroma_id=chroma_id,
                    chunk_metadata=chunk.metadata
                )
                self.db_session.add(chunk_record)

            self.db_session.commit()
            print(f"✅ Successfully saved {len(chunks)} chunks to database")

        except Exception as e:
            print(f"❌ Failed to save chunks to database: {e}")
            self.db_session.rollback()
            
    def retrieve_context(self, query: str, chat_type: str = "general",
                        course_id: Optional[int] = None, limit: int = 5) -> List[RAGSource]:
        """
        检索相关上下文
        
        Args:
            query: 查询文本
            chat_type: 聊天类型 ("general" 或 "course")
            course_id: 课程ID (课程聊天时需要)
            limit: 返回结果数量限制
            
        Returns:
            相关文档源列表
        """
        print(f"🔍 Retrieving context for: '{query}' (type: {chat_type}, course: {course_id})")
        
        results = []
        
        if chat_type == "course" and course_id:
            # 课程聊天：优先搜索课程文件，补充全局文件
            course_collection = f"course_{course_id}"
            course_vectorstore = self._get_vectorstore(course_collection)
            
            if course_vectorstore:
                course_results = course_vectorstore.similarity_search_with_score(
                    query, k=limit
                )
                results.extend(course_results)
            
            # 补充全局文件
            global_vectorstore = self._get_vectorstore("global")
            if global_vectorstore:
                global_results = global_vectorstore.similarity_search_with_score(
                    query, k=limit//2
                )
                results.extend(global_results)
        else:
            # 通用聊天：只搜索全局文件
            global_vectorstore = self._get_vectorstore("global")
            if global_vectorstore:
                results = global_vectorstore.similarity_search_with_score(
                    query, k=limit
                )
        
        # 转换为RAGSource对象
        rag_sources = []
        for doc, score in results[:limit]:
            rag_source = RAGSource(
                source_file=doc.metadata.get("filename", "unknown"),
                chunk_id=int(doc.metadata.get("chunk_id", 0)),
                content=doc.page_content,
                score=float(score),
                file_id=doc.metadata.get("file_id"),
                course_id=doc.metadata.get("course_id")
            )
            rag_sources.append(rag_source)
        
        print(f"📊 Retrieved {len(rag_sources)} relevant sources")
        return rag_sources
    
    def _get_or_create_vectorstore(self, collection_name: str) -> Chroma:
        """获取或创建向量存储"""
        if collection_name not in self.vectorstores:
            self.vectorstores[collection_name] = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=os.path.join(self.data_dir, collection_name)
            )
        return self.vectorstores[collection_name]
    
    def _get_vectorstore(self, collection_name: str) -> Optional[Chroma]:
        """获取向量存储（如果存在）"""
        if collection_name in self.vectorstores:
            return self.vectorstores[collection_name]
        
        # 尝试从磁盘加载
        collection_path = os.path.join(self.data_dir, collection_name)
        if os.path.exists(collection_path):
            try:
                self.vectorstores[collection_name] = Chroma(
                    collection_name=collection_name,
                    embedding_function=self.embeddings,
                    persist_directory=collection_path
                )
                return self.vectorstores[collection_name]
            except Exception as e:
                print(f"⚠️ Failed to load collection {collection_name}: {e}")
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取RAG统计信息"""
        stats = {
            "total_collections": len(self.vectorstores),
            "collections": {}
        }
        
        for collection_name, vectorstore in self.vectorstores.items():
            try:
                count = vectorstore._collection.count()
                stats["collections"][collection_name] = count
            except:
                stats["collections"][collection_name] = "unknown"
        
        return stats


# 全局RAG服务实例 - 单例模式
_rag_service = None

def get_rag_service() -> ProductionRAGService:
    """获取RAG服务实例"""
    global _rag_service
    if _rag_service is None:
        _rag_service = ProductionRAGService()
    return _rag_service