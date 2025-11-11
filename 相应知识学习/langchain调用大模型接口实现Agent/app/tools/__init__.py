"""工具模块初始化

统一管理所有可用的工具，根据配置动态加载
"""

from langchain.tools import Tool
from app.tools.argue import ARGUE_TOOL
from app.tools.search import WEB_SEARCH_TOOL
from app.config import ENABLE_WEB_SEARCH

def get_available_tools() -> list[Tool]:
    """获取所有可用的工具列表
    
    Returns:
        list[Tool]: 根据配置启用的工具列表
    """
    tools = [ARGUE_TOOL]  # 基础工具
    
    # 根据配置添加可选工具
    if ENABLE_WEB_SEARCH:
        tools.append(WEB_SEARCH_TOOL)
    
    return tools

def get_tool_info() -> dict:
    """获取工具信息
    
    Returns:
        dict: 工具配置信息
    """
    return {
        "total_tools": len(get_available_tools()),
        "web_search_enabled": ENABLE_WEB_SEARCH,
        "available_tools": [tool.name for tool in get_available_tools()]
    }
