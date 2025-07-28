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

# 禁用Chroma telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

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
        
        # 支持的文档加载器 - 专门格式用专门解析器，其他用TextLoader
        self.specialized_loaders = {
            # 需要专门解析器的格式
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.doc': Docx2txtLoader,  # Word文档的旧格式
            '.md': UnstructuredMarkdownLoader,
        }
        
        # TextLoader作为通用解析器，处理所有文本类文件
        self.text_loader = TextLoader
        
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
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        print(f"📋 File size: {file_size/1024/1024:.2f} MB")
        start_time = time.time()
        
        # 1. 检查文件类型并选择解析器（白名单验证）
        print(f"🔍 Step 1/6: Checking file type...")
        file_ext = os.path.splitext(file.original_name)[1].lower()
        
        # 验证文件类型是否在白名单中
        from app.utils.file_validation import FileValidator
        if not FileValidator.is_supported_document(file.original_name):
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # 选择合适的解析器
        if file_ext in self.specialized_loaders:
            loader_class = self.specialized_loaders[file_ext]
            print(f"✅ File type: {file_ext} - using specialized loader: {loader_class.__name__}")
        else:
            loader_class = self.text_loader
            print(f"✅ File type: {file_ext} - using TextLoader")
        
        # 2. 加载文档
        print(f"📖 Step 2/6: Loading document content...")
        try:
            loader = loader_class(file_path)
            documents = loader.load()
        except Exception as e:
            raise ValueError(f"Failed to parse file {file.original_name}: {str(e)}")
        total_chars = sum(len(doc.page_content) for doc in documents)
        print(f"✅ Loaded {len(documents)} documents, {total_chars:,} characters total")
        
        # 3. 分割文档
        print(f"✂️ Step 3/6: Splitting documents into chunks...")
        chunks = self.text_splitter.split_documents(documents)
        avg_chunk_size = sum(len(chunk.page_content) for chunk in chunks) // len(chunks) if chunks else 0
        print(f"✅ Created {len(chunks)} chunks, average size: {avg_chunk_size} characters")
        
        # 4. 添加元数据
        print(f"🏷️ Step 4/6: Adding metadata to chunks...")
        
        # 根据文件名确定贡献者
        contributor_name = "unknown"
        if file.original_name == "post_messages.txt":
            contributor_name = "triple u"
        # 可以继续添加其他文件的贡献者映射
        
        for i, chunk in enumerate(chunks):
            if i % 100 == 0 and i > 0:  # 每100个chunk输出一次进度
                print(f"   📝 Processing metadata: {i}/{len(chunks)} chunks ({i/len(chunks)*100:.1f}%)")
            chunk.metadata.update({
                "file_id": str(file.id),
                "course_id": str(file.course_id) if hasattr(file, "course_id") and getattr(file, "course_id", None) else "global",
                "filename": file.original_name,
                "file_type": getattr(file, "file_type", "global"),
                "chunk_id": i,
                "processed_at": datetime.now().isoformat(),
                "contributor": contributor_name  # 新增贡献者信息
            })
        print(f"✅ Metadata added to all {len(chunks)} chunks")
        
        # 5. 根据文件作用域确定集合名称
        print(f"📂 Step 5/6: Determining vector collection...")
        file_scope = getattr(file, "scope", "course")
        if file_scope == "global":
            collection_name = "global"
        elif hasattr(file, "course_id") and getattr(file, "course_id", None):
            collection_name = f"course_{file.course_id}"
        else:
            collection_name = "personal"
        print(f"✅ Using collection: {collection_name}")
        
        # 6. 存储到向量数据库
        print(f"🧠 Step 6/6: Creating embeddings and storing to vector database...")
        print(f"   ⚠️ This may take a while for large files (embedding {len(chunks)} chunks)...")
        vectorstore = self._get_or_create_vectorstore(collection_name)
        
        # 分批处理chunks以显示进度
        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            print(f"   🔄 Processing embeddings batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} ({i+len(batch)}/{len(chunks)} chunks)")
            vectorstore.add_documents(batch)
        
        print(f"✅ All chunks stored in vector database")
        
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
    
    def remove_file_chunks(self, file_id: int):
        """
        从向量数据库和MySQL数据库中删除指定文件的所有chunks
        
        Args:
            file_id: 文件ID
        """
        print(f"🗑️ Removing chunks for file {file_id} from both vector and MySQL databases")
        
        try:
            # 1. 从MySQL数据库删除chunks
            if self.db_session:
                print(f"📊 Deleting chunks from MySQL database...")
                deleted_count = self.db_session.query(DocumentChunk).filter(
                    DocumentChunk.file_id == file_id
                ).delete()
                self.db_session.commit()
                print(f"✅ Deleted {deleted_count} chunks from MySQL database")
            else:
                print(f"⚠️ Database session not available, skipping MySQL cleanup")
            
            # 2. 从向量数据库删除chunks
            print(f"🧠 Deleting chunks from vector databases...")
            removed_vector_count = 0
            
            # 遍历所有collection查找并删除相关chunks
            for collection_name, vectorstore in self.vectorstores.items():
                try:
                    # 获取collection中的所有文档
                    collection = vectorstore._collection
                    results = collection.get(include=['metadatas'])
                    
                    # 找到匹配file_id的文档ID
                    ids_to_delete = []
                    if results['metadatas']:
                        for i, metadata in enumerate(results['metadatas']):
                            if metadata and metadata.get('file_id') == str(file_id):
                                ids_to_delete.append(results['ids'][i])
                    
                    # 删除匹配的文档
                    if ids_to_delete:
                        collection.delete(ids=ids_to_delete)
                        removed_vector_count += len(ids_to_delete)
                        print(f"   ✅ Deleted {len(ids_to_delete)} chunks from collection '{collection_name}'")
                    
                except Exception as e:
                    print(f"   ⚠️ Failed to delete from collection '{collection_name}': {e}")
                    continue
            
            print(f"✅ Successfully removed {removed_vector_count} chunks from vector databases")
            print(f"🎯 File {file_id} cleanup completed")
            
        except Exception as e:
            print(f"❌ Error removing chunks for file {file_id}: {e}")
            if self.db_session:
                self.db_session.rollback()
            raise


# 全局RAG服务实例 - 单例模式
_rag_service = None

def get_rag_service() -> ProductionRAGService:
    """获取RAG服务实例"""
    global _rag_service
    if _rag_service is None:
        _rag_service = ProductionRAGService()
    return _rag_service