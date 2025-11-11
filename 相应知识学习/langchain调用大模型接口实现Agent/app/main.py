"""FastAPI 应用入口

本模块负责：
- 组装 LLM、对话记忆与 Agent
- 注册对话、RAG 与健康检查路由
- 挂载静态前端资源目录（`app/static`）

对外暴露 `app` 供 ASGI 服务器（如 uvicorn）启动。
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.providers.llm import make_llm
from app.memory.convo import make_memory
from app.agents.agent import make_agent
from app.config import MEMORY_TYPE

from app.api import routes_chat, routes_rag, routes_health

def create_app() -> FastAPI:
    """创建并返回 FastAPI 应用实例。

    该函数完成以下初始化：
    1) 创建 LLM、记忆与 Agent 组件
    2) 注册聊天、RAG 与健康检查相关路由
    3) 挂载静态资源目录，以便直接访问前端页面

    Returns:
        FastAPI: 已完成组件装配与路由注册的应用实例。
    """
    llm = make_llm()
    memory = make_memory(MEMORY_TYPE)
    agent = make_agent(llm, memory)

    app = FastAPI(title="LangChain Agent Service (Modular)")

    # 路由
    app.include_router(routes_chat.setup(llm, memory, agent))
    app.include_router(routes_rag.setup(llm))
    app.include_router(routes_health.router)

    # 静态资源：使用与该文件同级目录的 package 相对路径，兼容 Docker WORKDIR
    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
    return app

app = create_app()
