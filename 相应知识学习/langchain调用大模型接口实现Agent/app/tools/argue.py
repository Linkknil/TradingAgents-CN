from langchain.tools import Tool

def argue_tool(input_text: str) -> str:
    return f"反驳：{input_text} 根本不对！你这是在胡说八道。"

ARGUE_TOOL = Tool(
    name="argue_tool",
    func=argue_tool,
    description="当需要反驳对方时调用此工具，输入是对方说的话，输出是反驳内容。"
)
