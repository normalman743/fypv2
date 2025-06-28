#!/usr/bin/env python3
"""
RAG Upgrade Script
Seamlessly upgrade from Mock AI to Production RAG + LLM
"""

import os
import sys
from pathlib import Path

def update_chat_service():
    """Update chat service to use Enhanced AI Service"""
    
    chat_service_path = Path("app/services/chat_service.py")
    
    if not chat_service_path.exists():
        print("❌ Chat service not found")
        return False
    
    # Read current file
    with open(chat_service_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace import
    old_import = "from app.services.ai_service import MockAIService"
    new_import = "from app.services.enhanced_ai_service import create_ai_service"
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        
        # Replace service initialization
        old_init = "self.ai_service = MockAIService()"
        new_init = "self.ai_service = create_ai_service()"
        
        content = content.replace(old_init, new_init)
        
        # Write back
        with open(chat_service_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Chat service updated to use Enhanced AI Service")
        return True
    else:
        print("ℹ️ Chat service already using Enhanced AI Service")
        return True

def update_message_service():
    """Update message service to use Enhanced AI Service"""
    
    message_service_path = Path("app/services/message_service.py")
    
    if not message_service_path.exists():
        print("❌ Message service not found")
        return False
    
    # Read current file
    with open(message_service_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace import
    old_import = "from app.services.ai_service import MockAIService"
    new_import = "from app.services.enhanced_ai_service import create_ai_service"
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        
        # Replace service initialization
        old_init = "self.ai_service = MockAIService()"
        new_init = "self.ai_service = create_ai_service()"
        
        content = content.replace(old_init, new_init)
        
        # Write back
        with open(message_service_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Message service updated to use Enhanced AI Service")
        return True
    else:
        print("ℹ️ Message service already using Enhanced AI Service")
        return True

def check_environment():
    """Check if environment is ready for RAG upgrade"""
    
    print("🔍 Checking environment...")
    
    # Check if .env exists
    env_path = Path(".env")
    if not env_path.exists():
        print("⚠️ .env file not found. Creating template...")
        with open(env_path, 'w') as f:
            f.write("""# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration  
DATABASE_URL=mysql+pymysql://user:password@localhost/dbname

# Application Configuration
DEBUG=True
SECRET_KEY=your_secret_key_here
""")
        print("📝 .env template created. Please add your OpenAI API key.")
        return False
    
    # Check if OpenAI key is configured
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("⚠️ OpenAI API key not configured in .env file")
        print("💡 Add your key: OPENAI_API_KEY=sk-your-key-here")
        return False
    
    print("✅ Environment looks good")
    return True

def install_dependencies():
    """Install RAG dependencies"""
    
    print("📦 Installing RAG dependencies...")
    
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "chromadb==0.4.18",
            "langchain==0.1.0", 
            "langchain-community==0.0.10",
            "langchain-openai==0.0.2",
            "openai==1.23.6",
            "python-docx==0.8.11",
            "PyPDF2==3.0.1",
            "unstructured==0.11.0"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_data_directory():
    """Create data directory for ChromaDB"""
    
    data_dir = Path("data/chroma")
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Created data directory: {data_dir}")

def test_rag_service():
    """Test if RAG service works"""
    
    print("🧪 Testing RAG service...")
    
    try:
        from app.services.enhanced_ai_service import create_ai_service
        
        ai_service = create_ai_service()
        service_info = ai_service.get_service_info()
        
        print(f"🤖 AI Service Mode: {service_info['mode']}")
        print(f"📚 RAG Available: {service_info['rag_available']}")
        print(f"🚀 OpenAI Available: {service_info['openai_available']}")
        
        # Test a simple response
        response = ai_service.generate_response("Hello, test message")
        print(f"✅ Test response generated: {len(response.content)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG service test failed: {e}")
        return False

def main():
    """Main upgrade process"""
    
    print("🚀 Starting RAG Upgrade Process")
    print("=" * 50)
    
    # Step 1: Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please fix issues and try again.")
        return
    
    # Step 2: Install dependencies (optional, user might have done this)
    print("\n📦 Checking dependencies...")
    try:
        import chromadb
        import langchain
        print("✅ Dependencies already installed")
    except ImportError:
        if not install_dependencies():
            print("\n❌ Failed to install dependencies")
            return
    
    # Step 3: Create data directory
    create_data_directory()
    
    # Step 4: Update services
    print("\n🔄 Updating services...")
    if not update_chat_service() or not update_message_service():
        print("\n❌ Service update failed")
        return
    
    # Step 5: Test RAG service
    print("\n🧪 Testing RAG integration...")
    if not test_rag_service():
        print("\n❌ RAG test failed")
        return
    
    print("\n" + "=" * 50)
    print("🎉 RAG Upgrade Complete!")
    print("""
Next steps:
1. Restart your FastAPI server
2. Upload some test documents via the file API
3. Create chats and test the enhanced AI responses
4. Monitor logs for RAG retrieval information

Your system now supports:
✅ Real document processing and vector storage
✅ OpenAI LLM integration with fallback
✅ Automatic Mock/Production switching
✅ Course-specific vs global knowledge retrieval
    """)

if __name__ == "__main__":
    main()