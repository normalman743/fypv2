"""共享向量化服务 - 基于v1的RAG服务重构"""
import os
import time
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

# LangChain imports
try:
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
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# OpenAI imports
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .config import settings
from .exceptions import BaseServiceException


class VectorizationServiceException(BaseServiceException):
    """向量化服务异常"""
    pass


class OpenAIEmbeddingsWrapper:
    """OpenAI Embeddings包装器 - 自动降级到Mock"""
    
    def __init__(self, model: str = "text-embedding-ada-002"):
        self.model = model
        self.client = None
        
        if OPENAI_AVAILABLE and settings.openai_api_key and settings.openai_api_key != "sk-test-key":
            try:
                self.client = OpenAI(api_key=settings.openai_api_key)
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


class RAGSource:
    """RAG检索源"""
    def __init__(self, source_file: str, chunk_id: int, content: str, score: float, 
                 file_id: Optional[int] = None, course_id: Optional[int] = None):
        self.source_file = source_file
        self.chunk_id = chunk_id
        self.content = content
        self.score = score
        self.file_id = file_id
        self.course_id = course_id


class VectorizationService:
    """向量化服务 - 负责文档处理和向量检索"""
    
    METHOD_EXCEPTIONS = {
        "process_file": [VectorizationServiceException],
        "retrieve_context": [VectorizationServiceException],
        "remove_file_chunks": [VectorizationServiceException],
        "get_stats": [VectorizationServiceException],
    }
    
    def __init__(self, data_dir: str = None, db_session: Session = None):
        """
        初始化向量化服务
        
        Args:
            data_dir: ChromaDB数据存储目录
            db_session: 数据库会话（用于同步保存文档切片）
        """
        if not LANGCHAIN_AVAILABLE:
            raise VectorizationServiceException("LangChain未安装，无法使用向量化服务", "DEPENDENCY_ERROR")
        
        self.data_dir = data_dir or settings.vector_data_dir
        self.db_session = db_session
        os.makedirs(self.data_dir, exist_ok=True)
        
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
        self.vectorstores: Dict[str, Any] = {}
        
        # 支持的文档加载器
        self.specialized_loaders = {
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.doc': Docx2txtLoader,
            '.md': UnstructuredMarkdownLoader,
        }
        
        self.text_loader = TextLoader
        
        print(f"📁 Vectorization Service initialized with data directory: {self.data_dir}")
    
    def process_file(self, file_obj, file_path: str) -> Dict[str, Any]:
        """
        处理文件并添加到向量数据库
        
        Args:
            file_obj: 数据库文件对象
            file_path: 实际文件路径
            
        Returns:
            处理结果信息
        """
        try:
            print(f"🚀 Processing file: {file_obj.original_name} (ID: {file_obj.id})")
            start_time = time.time()
            
            # 1. 验证文件类型
            file_ext = os.path.splitext(file_obj.original_name)[1].lower()
            if not self._is_supported_document(file_obj.original_name):
                raise VectorizationServiceException(f"不支持的文件类型: {file_ext}", "UNSUPPORTED_FILE_TYPE")
            
            # 2. 选择加载器
            if file_ext in self.specialized_loaders:
                loader_class = self.specialized_loaders[file_ext]
                print(f"✅ Using specialized loader: {loader_class.__name__}")
            else:
                loader_class = self.text_loader
                print(f"✅ Using TextLoader")
            
            # 3. 加载文档
            print(f"📖 Loading document content...")
            loader = loader_class(file_path)
            documents = loader.load()
            print(f"✅ Loaded {len(documents)} documents")
            
            # 4. 分割文档
            print(f"✂️ Splitting documents into chunks...")
            chunks = self.text_splitter.split_documents(documents)
            print(f"✅ Created {len(chunks)} chunks")
            
            # 5. 添加元数据
            print(f"🏷️ Adding metadata to chunks...")
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "file_id": str(file_obj.id),
                    "course_id": str(getattr(file_obj, "course_id", None) or "global"),
                    "filename": file_obj.original_name,
                    "file_type": getattr(file_obj, "file_type", "document"),
                    "chunk_id": i,
                    "processed_at": datetime.now().isoformat(),
                })
            
            # 6. 确定集合名称
            collection_name = self._get_collection_name(file_obj)
            print(f"✅ Using collection: {collection_name}")
            
            # 7. 存储到向量数据库
            print(f"🧠 Creating embeddings and storing to vector database...")
            vectorstore = self._get_or_create_vectorstore(collection_name)
            vectorstore.add_documents(chunks)
            print(f"✅ Stored in vector database")
            
            # 8. 同步保存到关系数据库
            if self.db_session:
                self._save_chunks_to_db(chunks, file_obj)
            
            processing_time = time.time() - start_time
            print(f"✅ File processed: {len(chunks)} chunks, {processing_time:.2f}s")
            
            return {
                "file_id": file_obj.id,
                "status": "ready",
                "chunks_created": len(chunks),
                "processing_time": processing_time,
                "collection": collection_name
            }
            
        except VectorizationServiceException:
            raise
        except Exception as e:
            raise VectorizationServiceException(f"文件处理失败: {str(e)}", "PROCESSING_ERROR")
    
    def retrieve_context(self, query: str, chat_type: str = "general", 
                        course_id: Optional[int] = None, limit: int = 5) -> List[RAGSource]:
        """
        检索相关上下文
        
        Args:
            query: 查询文本
            chat_type: 聊天类型 ("general" 或 "course")
            course_id: 课程ID
            limit: 返回结果数量限制
            
        Returns:
            相关文档源列表
        """
        try:
            print(f"🔍 Retrieving context for: '{query}' (type: {chat_type}, course: {course_id})")
            
            results = []
            
            if chat_type == "course" and course_id:
                # 课程聊天：优先搜索课程文件
                course_collection = f"course_{course_id}"
                course_vectorstore = self._get_vectorstore(course_collection)
                
                if course_vectorstore:
                    course_results = course_vectorstore.similarity_search_with_score(query, k=limit)
                    results.extend(course_results)
                
                # 补充全局文件
                global_vectorstore = self._get_vectorstore("global")
                if global_vectorstore and len(results) < limit:
                    global_results = global_vectorstore.similarity_search_with_score(
                        query, k=limit - len(results)
                    )
                    results.extend(global_results)
            else:
                # 通用聊天：搜索全局文件
                global_vectorstore = self._get_vectorstore("global")
                if global_vectorstore:
                    results = global_vectorstore.similarity_search_with_score(query, k=limit)
            
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
            
        except Exception as e:
            raise VectorizationServiceException(f"上下文检索失败: {str(e)}", "RETRIEVAL_ERROR")
    
    def remove_file_chunks(self, file_id: int) -> None:
        """删除指定文件的所有chunks"""
        try:
            print(f"🗑️ Removing chunks for file {file_id}")
            
            # 1. 从关系数据库删除
            if self.db_session:
                from src.storage.models import DocumentChunk
                deleted_count = self.db_session.query(DocumentChunk).filter(
                    DocumentChunk.file_id == file_id
                ).delete()
                self.db_session.commit()
                print(f"✅ Deleted {deleted_count} chunks from database")
            
            # 2. 从向量数据库删除
            removed_count = 0
            for collection_name, vectorstore in self.vectorstores.items():
                try:
                    collection = vectorstore._collection
                    results = collection.get(include=['metadatas'])
                    
                    ids_to_delete = []
                    if results['metadatas']:
                        for i, metadata in enumerate(results['metadatas']):
                            if metadata and metadata.get('file_id') == str(file_id):
                                ids_to_delete.append(results['ids'][i])
                    
                    if ids_to_delete:
                        collection.delete(ids=ids_to_delete)
                        removed_count += len(ids_to_delete)
                        print(f"✅ Deleted {len(ids_to_delete)} chunks from collection '{collection_name}'")
                        
                except Exception as e:
                    print(f"⚠️ Failed to delete from collection '{collection_name}': {e}")
            
            print(f"✅ Removed {removed_count} chunks from vector databases")
            
        except Exception as e:
            if self.db_session:
                self.db_session.rollback()
            raise VectorizationServiceException(f"删除文件chunks失败: {str(e)}", "DELETION_ERROR")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取向量化统计信息"""
        try:
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
            
        except Exception as e:
            raise VectorizationServiceException(f"获取统计信息失败: {str(e)}", "STATS_ERROR")
    
    def _is_supported_document(self, filename: str) -> bool:
        """检查是否为支持的文档类型"""
        # 简化的文件类型验证
        supported_extensions = {'.pdf', '.docx', '.doc', '.md', '.txt', '.py', '.js', '.html', '.css', '.json'}
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in supported_extensions
    
    def _get_collection_name(self, file_obj) -> str:
        """获取集合名称"""
        file_scope = getattr(file_obj, "scope", "course")
        if file_scope == "global":
            return "global"
        elif hasattr(file_obj, "course_id") and getattr(file_obj, "course_id", None):
            return f"course_{file_obj.course_id}"
        else:
            return "personal"
    
    def _get_or_create_vectorstore(self, collection_name: str):
        """获取或创建向量存储"""
        if collection_name not in self.vectorstores:
            self.vectorstores[collection_name] = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=os.path.join(self.data_dir, collection_name)
            )
        return self.vectorstores[collection_name]
    
    def _get_vectorstore(self, collection_name: str):
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
    
    def _save_chunks_to_db(self, chunks: List[Document], file_obj) -> None:
        """将文档切片保存到关系数据库"""
        try:
            from src.storage.models import DocumentChunk
            
            # 检查是否已处理
            existing_chunks = self.db_session.query(DocumentChunk).filter(
                DocumentChunk.file_id == file_obj.id
            ).count()
            
            if existing_chunks > 0:
                print(f"⚠️ File {file_obj.id} already has {existing_chunks} chunks, skipping")
                return
            
            print(f"💾 Saving {len(chunks)} chunks to database")
            
            for i, chunk in enumerate(chunks):
                chunk_record = DocumentChunk(
                    file_id=file_obj.id,
                    chunk_index=i,
                    content=chunk.page_content,
                    chunk_metadata=chunk.metadata,
                    vector_id=str(uuid.uuid4())
                )
                self.db_session.add(chunk_record)
            
            self.db_session.commit()
            print(f"✅ Successfully saved {len(chunks)} chunks to database")
            
        except Exception as e:
            print(f"❌ Failed to save chunks to database: {e}")
            self.db_session.rollback()


# 全局向量化服务实例
_vectorization_service = None

def get_vectorization_service(db_session: Session = None) -> VectorizationService:
    """获取向量化服务实例"""
    global _vectorization_service
    if _vectorization_service is None:
        _vectorization_service = VectorizationService(db_session=db_session)
    return _vectorization_service