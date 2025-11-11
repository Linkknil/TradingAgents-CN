"""健康检查路由

用于部署/运维层面的探活检查，返回固定 OK。
"""

from fastapi import APIRouter
from app.tools import get_tool_info

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/tools/info")
def get_tools_info():
    """获取工具配置信息
    
    Returns:
        dict: 工具配置和状态信息
    """
    return {
        "status": "ok",
        "tools": get_tool_info()
    }
