from typing import TypedDict, Optional, List

class AgentState(TypedDict):
    """
    定义 Agent 在工作流中传递的状态。
    """
    email_content: str      # 原始邮件内容
    sender: str             # 发件人
    
    classification: str     # 分类结果: "spam", "info", "reply_needed"
    reason: str             # 分类理由 (用于可观测性/调试)
    
    retrieved_context: Optional[str] # RAG 检索到的背景知识
    draft_reply: Optional[str]       # 最终生成的草稿