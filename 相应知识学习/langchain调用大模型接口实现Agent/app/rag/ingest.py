"""知识入库流程

负责将原始文档加载、切分并写入向量库（Chroma）。
"""

from app.rag.loaders import load_documents
from app.rag.splitter import split_documents
from app.rag.vectorstore import get_vectorstore
from app.config import DATA_DIR

def ingest_corpus():
    """执行数据入库。

    Raises:
        RuntimeError: 当数据目录为空时抛出。
    Returns:
        dict: 入库统计数据（原始文档数、切分片段数）。
    """
    documents = load_documents(DATA_DIR)
    if not documents:
        raise RuntimeError(f"数据目录为空：{DATA_DIR}（放入 .txt/.md/.pdf 后再试）")
    chunks = split_documents(documents)
    vs = get_vectorstore()
    vs.add_documents(chunks)
    #vs.persist()
    return {"docs": len(documents), "chunks": len(chunks)}
