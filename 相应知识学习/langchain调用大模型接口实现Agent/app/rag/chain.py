"""RAG 推理链构建

将检索器与提示词、LLM 串联为可调用的链，用于问答生成。
"""

from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from app.prompts.rag_prompt import RAG_PROMPT

def format_docs(docs):
    """将检索到的文档片段格式化为上下文字符串。"""
    return "\n\n".join([f"【片段】\n{d.page_content}" for d in docs])

def build_rag_chain(retriever, llm):
    """构建 RAG 推理链。

    Args:
        retriever: 文档检索器（实现 as_retriever 的对象）
        llm: 语言模型实例
    Returns:
        Runnable: 可直接 .invoke(question) 的链
    """
    chain = RunnableParallel(
        context=retriever | format_docs,
        question=RunnablePassthrough()
    ) | RAG_PROMPT | llm | StrOutputParser()
    return chain
