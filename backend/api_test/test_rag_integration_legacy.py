#!/usr/bin/env python3
"""
RAG Integration Test Script
Test OpenAI API + ChromaDB functionality
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add app to Python path
sys.path.append(str(Path(__file__).parent))

from app.services.enhanced_ai_service import create_ai_service
from app.services.rag_service import get_rag_service
from app.models.database import SessionLocal
from app.models.file import File
from app.models.course import Course
from app.models.user import User
from sqlalchemy.orm import Session

def test_environment():
    """Test environment configuration"""
    print("🔍 Testing Environment Configuration")
    print("=" * 50)
    
    # Check OpenAI API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    if api_key == "sk-test-key" or api_key == "your_openai_api_key_here":
        print("❌ OPENAI_API_KEY is still placeholder value")
        return False
    
    print(f"✅ OPENAI_API_KEY configured: {api_key[:10]}...{api_key[-4:]}")
    
    # Check data directory
    data_dir = Path("./data/chroma")
    if data_dir.exists():
        print(f"✅ ChromaDB data directory exists: {data_dir}")
    else:
        print(f"📁 Creating ChromaDB data directory: {data_dir}")
        data_dir.mkdir(parents=True, exist_ok=True)
    
    return True

def test_rag_service():
    """Test RAG service initialization and basic functionality"""
    print("\n🚀 Testing RAG Service")
    print("=" * 50)
    
    try:
        rag_service = get_rag_service()
        print("✅ RAG Service initialized successfully")
        
        # Get service stats
        stats = rag_service.get_stats()
        print(f"📊 RAG Stats: {stats}")
        
        return rag_service
    except Exception as e:
        print(f"❌ RAG Service initialization failed: {e}")
        return None

def test_ai_service():
    """Test Enhanced AI Service"""
    print("\n🤖 Testing Enhanced AI Service")
    print("=" * 50)
    
    try:
        ai_service = create_ai_service()
        print("✅ Enhanced AI Service initialized successfully")
        
        # Get service info
        info = ai_service.get_service_info()
        print(f"📋 Service Info:")
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        return ai_service
    except Exception as e:
        print(f"❌ Enhanced AI Service initialization failed: {e}")
        return None

def create_test_file():
    """Create a test file for RAG processing"""
    print("\n📄 Creating Test Document")
    print("=" * 50)
    
    test_content = """
数据结构与算法 - 二叉树专题

什么是二叉树？
二叉树是一种树形数据结构，其中每个节点最多有两个子节点，通常称为左子节点和右子节点。

二叉树的遍历方法：
1. 前序遍历（Pre-order）：根节点 → 左子树 → 右子树
2. 中序遍历（In-order）：左子树 → 根节点 → 右子树  
3. 后序遍历（Post-order）：左子树 → 右子树 → 根节点

二叉搜索树：
二叉搜索树是一种特殊的二叉树，对于任何节点：
- 左子树中所有节点的值都小于该节点的值
- 右子树中所有节点的值都大于该节点的值

实际应用：
- 数据库索引
- 表达式解析
- 文件系统目录结构
- 决策树算法
"""
    
    test_file_path = Path("./test_document.txt")
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"✅ Test document created: {test_file_path}")
    print(f"📝 Content length: {len(test_content)} characters")
    
    return test_file_path

def test_document_processing(rag_service, test_file_path):
    """Test document processing"""
    print("\n📚 Testing Document Processing")
    print("=" * 50)
    
    try:
        # Create a mock File object
        from dataclasses import dataclass
        
        @dataclass
        class MockFile:
            id: int = 1
            original_name: str = "test_binary_tree.txt"
            file_type: str = "course_material"
            course_id: int = 1
        
        mock_file = MockFile()
        
        # Process the file
        print(f"🔄 Processing file: {mock_file.original_name}")
        result = rag_service.process_file(mock_file, str(test_file_path))
        
        print("✅ Document processing completed:")
        for key, value in result.items():
            print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Document processing failed: {e}")
        return False

def test_rag_retrieval(rag_service):
    """Test RAG context retrieval"""
    print("\n🔍 Testing RAG Context Retrieval")
    print("=" * 50)
    
    test_queries = [
        ("什么是二叉树？", "course", 1),
        ("二叉树遍历有几种方法？", "course", 1),
        ("前序遍历的顺序是什么？", "course", 1),
        ("二叉搜索树的特点", "general", None)
    ]
    
    for query, chat_type, course_id in test_queries:
        print(f"\n📝 Query: '{query}' (type: {chat_type}, course: {course_id})")
        
        try:
            results = rag_service.retrieve_context(
                query=query,
                chat_type=chat_type,
                course_id=course_id,
                limit=3
            )
            
            print(f"✅ Retrieved {len(results)} sources:")
            for i, source in enumerate(results):
                print(f"   {i+1}. {source.source_file} (chunk {source.chunk_id}, score: {source.score:.3f})")
                print(f"      Content preview: {source.content[:100]}...")
        
        except Exception as e:
            print(f"❌ RAG retrieval failed: {e}")

def test_ai_responses(ai_service):
    """Test AI response generation"""
    print("\n💬 Testing AI Response Generation")
    print("=" * 50)
    
    test_conversations = [
        {
            "message": "什么是二叉树的遍历？请详细解释。",
            "chat_type": "course",
            "course_id": 1,
            "description": "Course-specific question with RAG context"
        },
        {
            "message": "前序遍历和中序遍历的区别是什么？",
            "chat_type": "course", 
            "course_id": 1,
            "description": "Detailed comparison question"
        },
        {
            "message": "你好，请介绍一下自己",
            "chat_type": "general",
            "course_id": None,
            "description": "General greeting without RAG"
        }
    ]
    
    for test_case in test_conversations:
        print(f"\n📤 Test: {test_case['description']}")
        print(f"❓ Question: {test_case['message']}")
        
        start_time = time.time()
        
        try:
            response = ai_service.generate_response(
                message=test_case['message'],
                chat_type=test_case['chat_type'],
                course_id=test_case['course_id']
            )
            
            processing_time = time.time() - start_time
            
            print(f"✅ Response generated in {processing_time:.2f}s")
            print(f"📊 Tokens used: {response.tokens_used}")
            print(f"💰 Cost: ${response.cost:.6f}")
            print(f"📚 RAG sources: {len(response.rag_sources)}")
            print(f"📝 Response preview: {response.content[:200]}...")
            
            if response.rag_sources:
                print("📖 RAG Sources used:")
                for source in response.rag_sources:
                    print(f"   - {source['source_file']} (chunk {source['chunk_id']})")
            
        except Exception as e:
            print(f"❌ AI response generation failed: {e}")

def test_mode_switching(ai_service):
    """Test automatic mode switching"""
    print("\n🔄 Testing Mode Switching")
    print("=" * 50)
    
    # Test service info
    info = ai_service.get_service_info()
    
    print("Current service configuration:")
    print(f"   Mode: {info['mode']}")
    print(f"   RAG Available: {info['rag_available']}")
    print(f"   OpenAI Available: {info['openai_available']}")
    print(f"   Forced Mock: {info['forced_mock']}")
    
    if info['rag_stats']:
        print(f"   RAG Stats: {info['rag_stats']}")
    
    # Test forced mock mode
    print("\n🧪 Testing forced mock mode...")
    mock_service = create_ai_service(force_mock=True)
    mock_info = mock_service.get_service_info()
    print(f"Mock mode: {mock_info['mode']}")

def cleanup():
    """Clean up test files"""
    print("\n🧹 Cleaning up test files")
    print("=" * 50)
    
    test_file = Path("./test_document.txt")
    if test_file.exists():
        test_file.unlink()
        print("✅ Test document removed")

def main():
    """Main test function"""
    print("🚀 RAG Integration Comprehensive Test")
    print("=" * 80)
    
    # Test 1: Environment
    if not test_environment():
        print("\n❌ Environment test failed. Please check your configuration.")
        return
    
    # Test 2: RAG Service
    rag_service = test_rag_service()
    if not rag_service:
        print("\n❌ RAG Service test failed.")
        return
    
    # Test 3: AI Service
    ai_service = test_ai_service()
    if not ai_service:
        print("\n❌ AI Service test failed.")
        return
    
    # Test 4: Document Processing
    test_file_path = create_test_file()
    if not test_document_processing(rag_service, test_file_path):
        cleanup()
        return
    
    # Test 5: RAG Retrieval
    test_rag_retrieval(rag_service)
    
    # Test 6: AI Responses
    test_ai_responses(ai_service)
    
    # Test 7: Mode Switching
    test_mode_switching(ai_service)
    
    # Cleanup
    cleanup()
    
    print("\n" + "=" * 80)
    print("🎉 RAG Integration Test Complete!")
    print("Check the output above to verify all components are working as expected.")

if __name__ == "__main__":
    main()