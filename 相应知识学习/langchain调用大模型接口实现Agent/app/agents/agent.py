# agent.py
from langchain.agents import initialize_agent, AgentType, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_core.messages import SystemMessage
from app.tools import get_available_tools, get_tool_info
from app.config import SEARCH_ENGINE

def make_agent(llm, memory):
    """创建Agent实例，根据配置动态加载可用工具
    
    Args:
        llm: 语言模型实例
        memory: 记忆管理器实例
        
    Returns:
        Agent: 配置好的Agent实例
    """
    # 获取所有可用工具
    tools = get_available_tools()
    tool_info = get_tool_info()
    
    # 打印工具配置信息
    print(f"🔧 已加载 {tool_info['total_tools']} 个工具: {', '.join(tool_info['available_tools'])}")
    if tool_info['web_search_enabled']:
        print(f"✅ 网络搜索工具已启用 (搜索引擎: {SEARCH_ENGINE})")
    else:
        print("ℹ️  网络搜索工具已禁用")
    
    # 创建自定义的系统消息prompt
    system_message = """你是一个智能助手，拥有网络搜索能力。

CRITICAL RULE: 当用户询问天气、新闻、实时信息、最新数据时，你必须使用web_search工具。

必须使用搜索工具的情况：
1. 任何包含"天气"、"weather"的查询
2. 任何包含"新闻"、"news"的查询  
3. 任何包含"最新"、"latest"的查询
4. 任何包含"实时"、"real-time"的查询
5. 任何包含"时间"、"time"、"几点"的查询
6. 任何需要最新数据的查询

MANDATORY ACTION FORMAT:
当遇到上述查询时，必须按以下格式执行：
Action: web_search
Action Input: [具体的搜索查询]

DO NOT: 基于训练数据回答天气、新闻等实时信息问题
DO: 必须使用web_search工具获取最新信息

对于其他一般性问题，可以直接回答。"""
    
    # 创建自定义的prompt模板，包含系统消息
    custom_prompt = PromptTemplate(
        template=f"{system_message}\n\n{{input}}\n\n{{agent_scratchpad}}",
        input_variables=["input", "agent_scratchpad"]
    )
    
    # 使用ZERO_SHOT_REACT_DESCRIPTION，这是最适合工具调用的Agent类型
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=3,
        return_intermediate_steps=True,
        agent_kwargs={"prompt": custom_prompt}
    )
    return agent

