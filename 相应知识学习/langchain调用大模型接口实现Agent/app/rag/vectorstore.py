"""向量库包装

提供获取 Embeddings 与 Chroma 向量库实例的便捷方法，统一配置来源。
"""

from langchain_chroma import Chroma
from app.providers.embeddings import make_embeddings
from app.config import CHROMA_DIR, COLLECTION_NAME

_embeddings = None
def get_embeddings():
    """单例化 Embeddings，避免重复初始化。"""
    global _embeddings
    if _embeddings is None:
        _embeddings = make_embeddings()
    return _embeddings

def get_vectorstore():
    """创建并返回 Chroma 向量库实例。"""
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR,
        embedding_function=get_embeddings(),
    )
