"""文档加载器

从数据目录递归加载 .txt/.md（使用 TextLoader）与 .pdf（使用 PyPDFLoader）。
当目录不存在时返回空列表。
"""

import os
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader

def load_documents(data_dir: str):
    """加载指定目录中的文本/PDF 文档。

    Args:
        data_dir: 数据目录路径
    Returns:
        list[Document]: LangChain 文档对象列表
    """
    if not os.path.exists(data_dir):
        return []

    docs = []
    # 文本类
    txt_loader = DirectoryLoader(data_dir, glob="**/*.txt", loader_cls=TextLoader, show_progress=True)
    md_loader  = DirectoryLoader(data_dir, glob="**/*.md",  loader_cls=TextLoader, show_progress=True)
    docs.extend(txt_loader.load())
    docs.extend(md_loader.load())

    # PDF 单独处理
    for root, _, files in os.walk(data_dir):
        for f in files:
            if f.lower().endswith(".pdf"):
                path = os.path.join(root, f)
                try:
                    docs.extend(PyPDFLoader(path).load())
                except Exception as e:
                    print(f"[warn] 读取 PDF 失败：{path} -> {e}")

    return docs
