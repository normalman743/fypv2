from typing import List, Dict, Any
import random
import time
from datetime import datetime

class AIResponse:
    def __init__(self, content: str, tokens_used: int, cost: float, rag_sources: List[Dict[str, Any]] = None):
        self.content = content
        self.tokens_used = tokens_used
        self.cost = cost
        self.rag_sources = rag_sources or []

class MockAIService:
    """Mock AI service for MVP implementation. Easy to replace with real LLM later."""
    
    def __init__(self):
        # Mock responses for different scenarios
        self.mock_responses = {
            "general": [
                "Based on my knowledge, I can help you with that question.",
                "Let me provide you with a comprehensive answer based on available information.",
                "Here's what I found about your query from the knowledge base.",
                "I'll help you understand this topic with relevant information."
            ],
            "course": [
                "According to the course materials, here's the explanation:",
                "Based on the lecture content and resources, I can explain:",
                "From the course documentation and materials:",
                "The course materials indicate that:"
            ]
        }
        
        self.mock_rag_sources = [
            {"source_file": "校园设施指南.pdf", "chunk_id": 25},
            {"source_file": "数据结构第一讲.pdf", "chunk_id": 101},
            {"source_file": "计算机网络基础.docx", "chunk_id": 45},
            {"source_file": "课程大纲.pdf", "chunk_id": 12},
            {"source_file": "学习指南.md", "chunk_id": 33}
        ]

    def generate_response(self, message: str, chat_type: str = "general", course_id: int = None) -> AIResponse:
        """Generate mock AI response based on message and context"""
        
        # Simulate processing time
        time.sleep(0.1)
        
        # Choose response template based on chat type
        templates = self.mock_responses.get(chat_type, self.mock_responses["general"])
        base_response = random.choice(templates)
        
        # Generate contextual content based on message
        contextual_content = self._generate_contextual_content(message, chat_type)
        
        full_content = f"{base_response}\n\n{contextual_content}"
        
        # Mock token usage and cost
        tokens_used = len(full_content) // 4  # Rough estimation
        cost = tokens_used * 0.000002  # Mock pricing
        
        # Select relevant RAG sources
        rag_sources = random.sample(self.mock_rag_sources, random.randint(1, 3))
        
        return AIResponse(
            content=full_content,
            tokens_used=tokens_used,
            cost=cost,
            rag_sources=rag_sources
        )

    def generate_chat_title(self, first_message: str) -> str:
        """Generate a chat title based on the first message"""
        
        # Simple title generation logic - extract key concepts
        message_lower = first_message.lower()
        
        if "体育馆" in message_lower:
            return "体育馆相关咨询"
        elif "二叉树" in message_lower:
            return "二叉树学习讨论"
        elif "网络" in message_lower:
            return "计算机网络问题"
        elif "算法" in message_lower:
            return "算法学习讨论"
        elif "数据结构" in message_lower:
            return "数据结构相关问题"
        elif "课程" in message_lower:
            return "课程相关咨询"
        elif "校园" in message_lower:
            return "校园生活咨询"
        else:
            # Extract first few words for generic title
            words = first_message.split()[:3]
            return " ".join(words) + "讨论" if len(words) > 0 else "新的讨论"

    def _generate_contextual_content(self, message: str, chat_type: str) -> str:
        """Generate contextual content based on the message"""
        
        message_lower = message.lower()
        
        # Course-specific responses
        if "二叉树" in message_lower:
            if "遍历" in message_lower:
                return "二叉树的遍历是指按照特定顺序访问二叉树中所有节点的过程。主要有三种遍历方式：\n\n1. **前序遍历**：根节点 → 左子树 → 右子树\n2. **中序遍历**：左子树 → 根节点 → 右子树\n3. **后序遍历**：左子树 → 右子树 → 根节点\n\n每种遍历方式都有其特定的应用场景，比如中序遍历常用于二叉搜索树的有序输出。"
            else:
                return "二叉树是一种树形数据结构，其中每个节点最多有两个子节点，通常称为左子节点和右子节点。二叉树具有以下特点：\n\n1. 每个节点最多有两个子节点\n2. 子节点分为左子节点和右子节点\n3. 左右子树的顺序不能颠倒\n\n二叉树是许多高级数据结构的基础，如二叉搜索树、堆等。"
        
        elif "体育馆" in message_lower:
            return "崇基学院体育馆的开放时间如下：\n\n**平日时间**：\n- 周一至周五：上午9:00 - 晚上10:00\n\n**周末时间**：\n- 周六、周日：上午10:00 - 晚上8:00\n\n**特别说明**：\n- 节假日按周末时间执行\n- 如遇学校大型活动，可能临时调整开放时间\n- 建议前往前查看体育馆门口的最新通知"
        
        elif "网络" in message_lower:
            return "计算机网络是现代信息技术的重要组成部分。主要包括：\n\n1. **网络协议**：TCP/IP、HTTP、HTTPS等\n2. **网络架构**：OSI七层模型、TCP/IP四层模型\n3. **网络设备**：路由器、交换机、防火墙等\n4. **网络安全**：加密、认证、访问控制\n\n理解这些概念对于计算机科学学习非常重要。"
        
        elif "课程" in message_lower and chat_type == "course":
            return "本课程的主要内容包括：\n\n1. **理论基础**：核心概念和原理讲解\n2. **实践应用**：动手实验和项目实战\n3. **案例分析**：真实场景的问题解决\n4. **课后作业**：巩固学习效果\n\n建议大家：\n- 课前预习相关材料\n- 课堂积极参与讨论\n- 课后及时复习和练习\n- 有问题随时提出"
        
        else:
            # Generic helpful response
            return "我会根据您的问题提供相关的信息和建议。如果您需要更具体的帮助，请提供更多详细信息，我将为您提供更准确的答案。\n\n如果这是课程相关的问题，我可以结合课程材料为您详细解答。"