"""配置模块

从环境变量加载 LLM、Embedding 与 RAG 相关的配置项。
优先级：环境变量 > 默认值。支持 DeepSeek 与 Qwen（DashScope 兼容）两类提供商。
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Provider: deepseek / qwen
PROVIDER = os.getenv("PROVIDER", "deepseek").lower()

# LLM 基参
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.8))
TIMEOUT_S = float(os.getenv("TIMEOUT_S", 60))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 2048))

# DeepSeek
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")

# Qwen（DashScope 兼容）
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")

# Embedding（OpenAI 兼容通道）
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY") or DEEPSEEK_API_KEY or os.getenv("OPENAI_API_KEY")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", DEEPSEEK_BASE_URL)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")

# RAG 相关
DATA_DIR = os.getenv("DATA_DIR", "data")
CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "kb-main")

# 记忆管理相关
MEMORY_TYPE = os.getenv("MEMORY_TYPE", "buffer")  # buffer/summary/summary_buffer/vector
MEMORY_MAX_TOKEN_LIMIT = int(os.getenv("MEMORY_MAX_TOKEN_LIMIT", "1000"))
MEMORY_RETRIEVER_K = int(os.getenv("MEMORY_RETRIEVER_K", "5"))

# 流式默认开关（当请求未显式传 stream 时使用）
STREAM_DEFAULT = os.getenv("STREAM_DEFAULT", "false").strip().lower() in {"1", "true", "yes", "on"}

# 网络搜索工具相关配置
ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "false").strip().lower() in {"1", "true", "yes", "on"}
SEARCH_ENGINE = os.getenv("SEARCH_ENGINE", "duckduckgo")  # duckduckgo / serpapi / google
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
SEARCH_MAX_RESULTS = int(os.getenv("SEARCH_MAX_RESULTS", "5"))
