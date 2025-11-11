"""对话相关 API 路由

提供基础对话接口 `/chat`，接收用户输入并通过 Agent 调用 LLM 返回回复。
同时提供记忆管理相关的接口。
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import Iterator
import json
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from app.memory.convo import get_memory_info, clear_memory
from app.config import STREAM_DEFAULT

router = APIRouter()

class ChatRequest(BaseModel):
    input: str
    stream: bool | None = False

class MemoryInfoResponse(BaseModel):
    memory_info: dict
    status: str

def setup(llm, memory, agent):
    """注册聊天路由并返回路由对象。

    Args:
        llm: 语言模型实例
        memory: 对话记忆组件
        agent: 负责链式调用与工具/记忆的 Agent

    Returns:
        APIRouter: 已注册聊天端点的路由对象
    """
    @router.post("/chat")
    def chat_endpoint(body: ChatRequest):
        """对话端点：支持流式与非流式（通过 stream 开关）。

        Body:
            input: 用户问题/消息。
            stream: 是否启用流式（SSE）。
        Returns:
            - 当 stream=false：{"output": str}
            - 当 stream=true：text/event-stream
        """
        use_stream = body.stream if body.stream is not None else STREAM_DEFAULT
        if use_stream:
            def event_stream():
                full_text = ""
                try:
                    # 立即开始流式输出，不等待
                    yield f"data: {json.dumps({'delta': '🤔 '})}\n\n"
                    
                    # 检查是否需要工具调用
                    needs_tools = any(keyword in body.input.lower() for keyword in 
                                    ['天气', 'weather', '新闻', 'news', '最新', 'latest', '实时', 'real-time', '时间', 'time', '几点'])
                    
                    if needs_tools:
                        # 需要工具调用时，先显示提示
                        yield f"data: {json.dumps({'delta': '🔍 正在搜索实时信息...'})}\n\n"
                        
                        # 使用Agent调用工具
                        result = agent.invoke({"input": body.input})
                        output = result.get("output", result) if isinstance(result, dict) else str(result)
                        full_text = output
                        
                        # 发送清除信号，让前端清除提示
                        yield f"data: {json.dumps({'clear': True})}\n\n"
                        
                        # 清理输出，移除可能包含的emoji和提示文本
                        cleaned_output = output
                        # 移除常见的emoji和提示文本
                        import re
                        cleaned_output = re.sub(r'^[🤔🔍💭]+\s*', '', cleaned_output)  # 移除开头的emoji
                        cleaned_output = re.sub(r'正在搜索实时信息\.\.\.', '', cleaned_output)  # 移除搜索提示
                        cleaned_output = re.sub(r'正在思考\.\.\.', '', cleaned_output)  # 移除思考提示
                        cleaned_output = cleaned_output.strip()
                        
                        # 快速流式输出结果
                        import time
                        for char in cleaned_output:
                            yield f"data: {json.dumps({'delta': char})}\n\n"
                            time.sleep(0.01)  # 10ms延迟，快速打字效果
                    else:
                        # 不需要工具时，直接使用LLM流式调用
                        yield f"data: {json.dumps({'delta': '💭 正在思考...'})}\n\n"
                        
                        # 载入历史消息
                        history = memory.load_memory_variables({}).get("chat_history", [])
                        messages = list(history) + [HumanMessage(content=body.input)]
                        
                        # 发送清除信号，清除思考提示
                        yield f"data: {json.dumps({'clear': True})}\n\n"
                        
                        # 使用LLM流式调用
                        for chunk in llm.stream(messages):
                            delta = getattr(chunk, "content", None) or ""
                            if not delta:
                                continue
                            
                            # 清理输出，移除可能包含的emoji和提示文本
                            import re
                            cleaned_delta = re.sub(r'^[🤔🔍💭]+\s*', '', delta)  # 移除开头的emoji
                            cleaned_delta = re.sub(r'正在搜索实时信息\.\.\.', '', cleaned_delta)  # 移除搜索提示
                            cleaned_delta = re.sub(r'正在思考\.\.\.', '', cleaned_delta)  # 移除思考提示
                            
                            if cleaned_delta.strip():  # 只发送非空的清理后内容
                                full_text += cleaned_delta
                                yield f"data: {json.dumps({'delta': cleaned_delta})}\n\n"
                        
                except Exception as e:
                    error_msg = f"处理失败: {str(e)}"
                    full_text = error_msg
                    yield f"data: {json.dumps({'delta': error_msg})}\n\n"
                finally:
                    # 保存到记忆
                    try:
                        memory.save_context({"input": body.input}, {"output": full_text})
                    except Exception as e:
                        yield f"data: {json.dumps({'warn': f'memory_save_failed: {str(e)}'})}\n\n"
                    yield f"data: {json.dumps({'done': True})}\n\n"

            return StreamingResponse(event_stream(), media_type="text/event-stream")

        # 非流式：沿用 Agent 能力（含工具链与记忆）
        result = agent.invoke({"input": body.input})
        return {"output": result.get("output", result)}

    @router.post("/chat_stream")
    def chat_stream_endpoint(body: ChatRequest):
        """SSE 流式对话端点（简单版）。

        说明：直接使用 LLM 的流式接口，并在结束后把完整回复写入记忆。
        当前实现未走 Agent 工具链，仅做纯对话流式。
        """

        def event_stream() -> Iterator[str]:
            # 载入历史消息（若记忆返回 BaseMessage 列表即可直接复用）
            history = memory.load_memory_variables({}).get("chat_history", [])
            messages = list(history) + [HumanMessage(content=body.input)]

            full_text = ""
            try:
                for chunk in llm.stream(messages):
                    delta = getattr(chunk, "content", None) or ""
                    if not delta:
                        continue
                    full_text += delta
                    yield f"data: {json.dumps({'delta': delta})}\n\n"
            finally:
                # 在流结束后持久化到记忆（与非流式保持同键）
                try:
                    memory.save_context({"input": body.input}, {"output": full_text})
                except Exception as e:
                    # 将错误以事件形式告知客户端，但不抛出中断连接
                    yield f"data: {json.dumps({'warn': f'memory_save_failed: {str(e)}'})}\n\n"
                # 发送完成事件
                yield f"data: {json.dumps({'done': True})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @router.get("/memory/info")
    def get_memory_info_endpoint():
        """获取当前记忆管理器的信息。
        
        Returns:
            MemoryInfoResponse: 记忆管理器详细信息
        """
        memory_info = get_memory_info(memory)
        return MemoryInfoResponse(
            memory_info=memory_info,
            status="ok"
        )
    
    @router.post("/memory/clear")
    def clear_memory_endpoint():
        """清空当前对话记忆。
        
        Returns:
            dict: 清空结果
        """
        success = clear_memory(memory)
        return {
            "status": "ok" if success else "error",
            "message": "记忆已清空" if success else "清空记忆失败"
        }

    return router
