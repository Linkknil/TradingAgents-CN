from langchain_openai import ChatOpenAI
from app.config import (
    PROVIDER, TEMPERATURE, TIMEOUT_S, MAX_TOKENS,
    QWEN_MODEL, QWEN_BASE_URL, DASHSCOPE_API_KEY,
    DEEPSEEK_MODEL, DEEPSEEK_BASE_URL, DEEPSEEK_API_KEY
)

def make_llm() -> ChatOpenAI:
    if PROVIDER == "qwen":
        if not DASHSCOPE_API_KEY:
            raise RuntimeError("缺少通义千问 API Key：请设置 DASHSCOPE_API_KEY 或 QWEN_API_KEY")
        llm = ChatOpenAI(
            model=QWEN_MODEL,
            api_key=DASHSCOPE_API_KEY,
            base_url=QWEN_BASE_URL,
            temperature=TEMPERATURE,
            timeout=TIMEOUT_S,
            max_tokens=MAX_TOKENS,
        )
    elif PROVIDER == "deepseek":
        if not DEEPSEEK_API_KEY:
            raise RuntimeError("缺少 DeepSeek API Key：请设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY")
        llm = ChatOpenAI(
            model=DEEPSEEK_MODEL,
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            temperature=TEMPERATURE,
            timeout=TIMEOUT_S,
            max_tokens=MAX_TOKENS,
        )
    else:
        raise ValueError(f"不支持的 PROVIDER：{PROVIDER}（仅 deepseek / qwen）")
    
    # 注意：系统消息将在Agent的prompt中处理，而不是通过bind方法
    # 因为ChatOpenAI的bind方法不支持system_message参数
    return llm
