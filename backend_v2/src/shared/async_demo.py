"""异步支持演示和最佳实践"""
import asyncio
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from .base_service import BaseService
from .async_utils import async_retry, AsyncBatch, gather_with_limit
from .exceptions import BaseServiceException


class AsyncDemoServiceException(BaseServiceException):
    """演示服务异常"""
    pass


class AsyncDemoService(BaseService):
    """异步支持演示服务"""
    
    METHOD_EXCEPTIONS = {
        "process_multiple_items": {AsyncDemoServiceException},
        "send_bulk_notifications": {AsyncDemoServiceException},
        "heavy_computation": {AsyncDemoServiceException},
    }
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    # 演示1：CPU密集型任务的异步处理
    async def heavy_computation_async(self, data: List[int]) -> List[int]:
        """异步处理CPU密集型任务"""
        
        async def process_item(item: int) -> int:
            # 在线程池中运行CPU密集型计算
            return await self.run_sync_in_async(self._cpu_intensive_task, item)
        
        # 批处理，限制并发数量
        batch_processor = AsyncBatch(batch_size=50, max_concurrency=4)
        results = await batch_processor.process_items(data, process_item)
        
        return results
    
    def _cpu_intensive_task(self, item: int) -> int:
        """模拟CPU密集型任务"""
        # 这里可以是复杂计算、数据处理等
        result = sum(i * i for i in range(item, item + 1000))
        return result
    
    # 演示2：网络请求的异步处理（带重试）
    @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
    async def send_notification_async(self, user_id: int, message: str) -> bool:
        """异步发送通知（带重试机制）"""
        try:
            # 模拟网络请求
            await asyncio.sleep(0.1)  # 模拟网络延迟
            
            # 这里可以是实际的HTTP请求、邮件发送等
            print(f"📧 Sending notification to user {user_id}: {message}")
            
            # 随机失败模拟（实际应用中移除）
            import random
            if random.random() < 0.2:  # 20%失败率
                raise AsyncDemoServiceException("Network error", "NETWORK_ERROR")
            
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to send notification: {e}")
            raise AsyncDemoServiceException(f"发送通知失败: {str(e)}", "SEND_ERROR")
    
    # 演示3：批量操作的异步处理
    async def send_bulk_notifications_async(self, notifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """异步批量发送通知"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            # 限制并发数量，避免过载
            async def send_single(notification: Dict[str, Any]) -> bool:
                return await self.send_notification_async(
                    notification["user_id"], 
                    notification["message"]
                )
            
            # 使用限制并发的gather
            results = await gather_with_limit(
                10,  # 最大并发数
                *[send_single(notif) for notif in notifications]
            )
            
            end_time = asyncio.get_event_loop().time()
            processing_time = end_time - start_time
            
            successful = sum(1 for result in results if result)
            failed = len(results) - successful
            
            return {
                "total": len(notifications),
                "successful": successful,
                "failed": failed,
                "processing_time": processing_time
            }
            
        except Exception as e:
            raise AsyncDemoServiceException(f"批量发送失败: {str(e)}", "BULK_SEND_ERROR")
    
    # 演示4：数据库操作的异步处理
    async def process_multiple_items_async(self, items: List[str]) -> List[Dict[str, Any]]:
        """异步处理多个项目（包含数据库操作）"""
        try:
            results = []
            
            for item in items:
                # 异步数据库查询（模拟）
                await asyncio.sleep(0.01)  # 模拟数据库延迟
                
                result = {
                    "item": item,
                    "processed_at": asyncio.get_event_loop().time(),
                    "status": "completed"
                }
                results.append(result)
            
            # 批量提交到数据库
            if await self.safe_commit_async("process_multiple_items"):
                return results
            else:
                raise AsyncDemoServiceException("数据库提交失败", "COMMIT_ERROR")
                
        except Exception as e:
            raise AsyncDemoServiceException(f"处理多个项目失败: {str(e)}", "PROCESSING_ERROR")
    
    # 同步版本（使用装饰器自动生成）
    def heavy_computation(self, data: List[int]) -> List[int]:
        """CPU密集型任务的同步版本"""
        return self.run_async_in_sync(self.heavy_computation_async(data))
    
    def send_bulk_notifications(self, notifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量发送通知的同步版本"""
        return self.run_async_in_sync(self.send_bulk_notifications_async(notifications))
    
    def process_multiple_items(self, items: List[str]) -> List[Dict[str, Any]]:
        """处理多个项目的同步版本"""
        return self.run_async_in_sync(self.process_multiple_items_async(items))


# 使用示例
async def demo_usage():
    """演示如何使用异步服务"""
    # 模拟数据库会话
    db = None  # 在实际应用中，这里是真实的数据库会话
    
    service = AsyncDemoService(db)
    
    print("🚀 开始异步操作演示...")
    
    # 演示1：CPU密集型任务
    print("\n📊 CPU密集型任务演示:")
    start = asyncio.get_event_loop().time()
    data = list(range(1, 101))  # 100个数据项
    results = await service.heavy_computation_async(data)
    end = asyncio.get_event_loop().time()
    print(f"处理了 {len(results)} 个项目，耗时 {end - start:.2f}s")
    
    # 演示2：批量通知
    print("\n📧 批量通知演示:")
    notifications = [
        {"user_id": i, "message": f"Hello user {i}"}
        for i in range(1, 21)  # 20个通知
    ]
    bulk_result = await service.send_bulk_notifications_async(notifications)
    print(f"批量发送结果: {bulk_result}")
    
    # 演示3：数据处理
    print("\n🔄 数据处理演示:")
    items = [f"item_{i}" for i in range(1, 11)]
    process_results = await service.process_multiple_items_async(items)
    print(f"处理了 {len(process_results)} 个项目")
    
    print("\n✅ 异步操作演示完成!")


# 运行演示
if __name__ == "__main__":
    asyncio.run(demo_usage())