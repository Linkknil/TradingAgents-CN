"""
高级记忆管理模块

提供多种记忆类型：
1. ConversationBufferMemory - 基础缓冲记忆（保留所有对话）
2. ConversationSummaryMemory - 摘要记忆（压缩历史为摘要）
3. ConversationSummaryBufferMemory - 混合记忆（最近对话+历史摘要）
4. VectorStoreRetrieverMemory - 向量记忆（基于语义检索历史）
"""

from langchain.memory import (
    ConversationBufferMemory,
    ConversationSummaryMemory,
    ConversationSummaryBufferMemory,
    VectorStoreRetrieverMemory
)
from langchain_core.memory import BaseMemory
from app.providers.llm import make_llm
from app.rag.vectorstore import get_vectorstore
from app.config import COLLECTION_NAME

def make_memory(memory_type: str = "buffer") -> BaseMemory:
    """
    创建指定类型的记忆管理器
    
    Args:
        memory_type: 记忆类型
            - "buffer": 基础缓冲记忆（默认）
            - "summary": 摘要记忆
            - "summary_buffer": 混合记忆
            - "vector": 向量记忆
    
    Returns:
        BaseMemory: 记忆管理器实例
    """
    llm = make_llm()
    
    if memory_type == "buffer":
        return ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="input",
            output_key="output"
        )
    
    elif memory_type == "summary":
        return ConversationSummaryMemory(
            llm=llm,
            memory_key="chat_history",
            input_key="input",
            output_key="output"
        )
    
    elif memory_type == "summary_buffer":
        return ConversationSummaryBufferMemory(
            llm=llm,
            memory_key="chat_history",
            input_key="input",
            output_key="output",
            max_token_limit=1000,  # 最近对话的最大token数
            return_messages=True
        )
    
    elif memory_type == "vector":
        vectorstore = get_vectorstore()
        # 为记忆创建专门的检索器
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}  # 检索最近5条相关对话
        )
        return VectorStoreRetrieverMemory(
            retriever=retriever,
            memory_key="chat_history",
            input_key="input",
            output_key="output",
            return_docs=True
        )
    
    else:
        raise ValueError(f"不支持的记忆类型: {memory_type}")

def get_memory_info(memory: BaseMemory) -> dict:
    """
    获取记忆管理器的信息
    
    Args:
        memory: 记忆管理器实例
    
    Returns:
        dict: 记忆信息
    """
    info = {
        "type": memory.__class__.__name__,
        "memory_key": getattr(memory, 'memory_key', 'unknown'),
        "return_messages": getattr(memory, 'return_messages', False)
    }
    
    # 添加特定类型的额外信息
    if isinstance(memory, ConversationSummaryBufferMemory):
        info["max_token_limit"] = getattr(memory, 'max_token_limit', 'unknown')
    elif isinstance(memory, VectorStoreRetrieverMemory):
        info["retriever_type"] = memory.retriever.__class__.__name__
        info["search_kwargs"] = getattr(memory.retriever, 'search_kwargs', {})
    
    return info

def clear_memory(memory: BaseMemory) -> bool:
    """
    清空记忆
    
    Args:
        memory: 记忆管理器实例
    
    Returns:
        bool: 是否成功清空
    """
    try:
        memory.clear()
        return True
    except Exception as e:
        print(f"清空记忆失败: {e}")
        return False
