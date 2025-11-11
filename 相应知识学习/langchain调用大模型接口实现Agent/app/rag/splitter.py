"""文档切分器

使用递归字符切分策略，将文档切分为带重叠的片段，便于向量化与检索。
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_documents(documents):
    """将文档切分为片段。

    chunk_size=1000, chunk_overlap=150，保留 `start_index` 以便引用定位。
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        add_start_index=True,
        separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""],
    )
    return splitter.split_documents(documents)
