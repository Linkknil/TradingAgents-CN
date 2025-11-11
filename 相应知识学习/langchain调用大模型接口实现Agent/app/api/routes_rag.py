"""RAG（检索增强生成）相关 API 路由

提供语料入库 `/ingest` 与基于向量检索的问答 `/chat_rag` 两个端点。
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.rag.ingest import ingest_corpus
from app.rag.vectorstore import get_vectorstore
from app.rag.chain import build_rag_chain

router = APIRouter()

class RAGRequest(BaseModel):
    question: str
    k: int | None = 4

def setup(llm):
    """注册 RAG 路由并返回路由对象。

    Args:
        llm: 语言模型实例，用于生成回答

    Returns:
        APIRouter: 已注册 RAG 端点的路由对象
    """
    @router.post("/ingest")
    def ingest_endpoint():
        """触发知识库入库流程。

        Returns:
            dict: {"status": "ok", "stats": Any}
        Raises:
            HTTPException: 入库失败时返回 400 与错误信息
        """
        try:
            stats = ingest_corpus()
            return {"status": "ok", "stats": stats}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/chat_rag")
    def chat_rag_endpoint(req: RAGRequest):
        """基于 RAG 的问答端点。

        Body:
            question: 用户问题
            k: 检索返回文档数量，默认 4
        Returns:
            dict: {"answer": str, "refs": list[dict]}，其中 refs 为引用来源
        """
        vs = get_vectorstore()
        retriever = vs.as_retriever(search_kwargs={"k": req.k})
        chain = build_rag_chain(retriever, llm)

        docs = retriever.get_relevant_documents(req.question)
        citations = [
            {
                "source": d.metadata.get("source"),
                "page": d.metadata.get("page"),
                "start_index": d.metadata.get("start_index")
            } for d in docs
        ]
        answer = chain.invoke(req.question)
        return {"answer": answer, "refs": citations}

    return router
