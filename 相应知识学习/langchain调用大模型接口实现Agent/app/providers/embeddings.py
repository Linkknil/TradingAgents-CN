from app.config import (
    PROVIDER, DASHSCOPE_API_KEY,
    EMBEDDING_API_KEY, EMBEDDING_BASE_URL, EMBEDDING_MODEL
)

def make_embeddings():
    if PROVIDER == "qwen":
        try:
            from langchain_community.embeddings import DashScopeEmbeddings
            if not DASHSCOPE_API_KEY:
                raise RuntimeError("缺少 DASHSCOPE_API_KEY（Embedding）")
            return DashScopeEmbeddings(dashscope_api_key=DASHSCOPE_API_KEY, model="text-embedding-v3")
        except Exception as e:
            print(f"[warn] DashScopeEmbeddings 不可用，fallback 到 OpenAIEmbeddings：{e}")

    if not EMBEDDING_API_KEY:
        raise RuntimeError("缺少 Embedding API Key：EMBEDDING_API_KEY / DEEPSEEK_API_KEY / OPENAI_API_KEY")

    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=EMBEDDING_API_KEY,
        base_url=EMBEDDING_BASE_URL,
    )
