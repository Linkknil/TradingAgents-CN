from langchain_core.prompts import ChatPromptTemplate

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是可靠的中文助理。只根据【检索片段】回答；资料不足就说“我无法从资料中确定”。用要点作答。"),
    ("human", "用户问题：{question}\n\n【检索片段】\n{context}"),
])
