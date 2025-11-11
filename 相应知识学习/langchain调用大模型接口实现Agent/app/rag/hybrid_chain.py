"""混合检索RAG链

使用混合检索器构建的RAG推理链，提供更准确的文档检索。
"""

from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from app.prompts.rag_prompt import RAG_PROMPT
from app.rag.hybrid_retriever import create_hybrid_retriever
from app.rag.vectorstore import get_vectorstore
from app.rag.loaders import load_documents
from typing import List, Dict, Any


def format_docs(docs):
    """将检索到的文档片段格式化为上下文字符串。"""
    return "\n\n".join([f"【片段】\n{d.page_content}" for d in docs])


def build_hybrid_rag_chain(
    documents: List[Any] = None,
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3,
    k: int = 5,
    advanced: bool = False,
    llm=None
):
    """构建混合检索RAG推理链。

    Args:
        documents: 文档列表，如果为None则从默认路径加载
        vector_weight: 向量检索权重 (0-1)
        bm25_weight: BM25检索权重 (0-1)
        k: 返回文档数量
        advanced: 是否使用高级混合检索器
        llm: 语言模型实例

    Returns:
        Runnable: 可直接 .invoke(question) 的链
    """
    # 获取向量数据库
    vectorstore = get_vectorstore()
    
    # 如果没有提供文档，从默认路径加载
    if documents is None:
        documents = load_documents()
    
    # 创建混合检索器
    retriever = create_hybrid_retriever(
        vectorstore=vectorstore,
        documents=documents,
        vector_weight=vector_weight,
        bm25_weight=bm25_weight,
        k=k,
        advanced=advanced
    )
    
    # 构建RAG链
    chain = RunnableParallel(
        context=retriever | format_docs,
        question=RunnablePassthrough()
    ) | RAG_PROMPT | llm | StrOutputParser()
    
    return chain


def compare_retrieval_methods(
    query: str,
    documents: List[Any] = None,
    llm=None
) -> Dict[str, Any]:
    """比较不同检索方法的效果
    
    Args:
        query: 查询问题
        documents: 文档列表
        llm: 语言模型实例
    
    Returns:
        包含不同检索方法结果的字典
    """
    if documents is None:
        documents = load_documents()
    
    vectorstore = get_vectorstore()
    
    # 1. 纯向量检索
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    vector_docs = vector_retriever.get_relevant_documents(query)
    
    # 2. 混合检索（平衡权重）
    hybrid_retriever = create_hybrid_retriever(
        vectorstore=vectorstore,
        documents=documents,
        vector_weight=0.5,
        bm25_weight=0.5,
        k=5
    )
    hybrid_docs = hybrid_retriever.get_relevant_documents(query)
    
    # 3. 混合检索（向量权重高）
    vector_heavy_retriever = create_hybrid_retriever(
        vectorstore=vectorstore,
        documents=documents,
        vector_weight=0.8,
        bm25_weight=0.2,
        k=5
    )
    vector_heavy_docs = vector_heavy_retriever.get_relevant_documents(query)
    
    # 4. 混合检索（关键词权重高）
    keyword_heavy_retriever = create_hybrid_retriever(
        vectorstore=vectorstore,
        documents=documents,
        vector_weight=0.2,
        bm25_weight=0.8,
        k=5
    )
    keyword_heavy_docs = keyword_heavy_retriever.get_relevant_documents(query)
    
    # 5. 高级混合检索
    advanced_retriever = create_hybrid_retriever(
        vectorstore=vectorstore,
        documents=documents,
        vector_weight=0.7,
        bm25_weight=0.3,
        k=5,
        advanced=True
    )
    advanced_docs = advanced_retriever.get_relevant_documents(query)
    
    return {
        "query": query,
        "vector_only": {
            "docs": [doc.page_content[:200] + "..." for doc in vector_docs],
            "count": len(vector_docs)
        },
        "hybrid_balanced": {
            "docs": [doc.page_content[:200] + "..." for doc in hybrid_docs],
            "count": len(hybrid_docs)
        },
        "hybrid_vector_heavy": {
            "docs": [doc.page_content[:200] + "..." for doc in vector_heavy_docs],
            "count": len(vector_heavy_docs)
        },
        "hybrid_keyword_heavy": {
            "docs": [doc.page_content[:200] + "..." for doc in keyword_heavy_docs],
            "count": len(keyword_heavy_docs)
        },
        "hybrid_advanced": {
            "docs": [doc.page_content[:200] + "..." for doc in advanced_docs],
            "count": len(advanced_docs)
        }
    }


# 使用示例
if __name__ == "__main__":
    # 示例：比较不同检索方法
    query = "苹果公司股票表现如何？"
    
    # 这里需要实际的文档和LLM实例
    # results = compare_retrieval_methods(query)
    
    # 打印比较结果
    # for method, result in results.items():
    #     if method != "query":
    #         print(f"\n{method}:")
    #         print(f"  文档数量: {result['count']}")
    #         for i, doc in enumerate(result['docs'], 1):
    #             print(f"  {i}. {doc}")
    
    print("混合检索器已创建，可以在RAG链中使用。")

