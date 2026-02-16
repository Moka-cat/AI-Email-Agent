from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import classify_node, retrieve_node, draft_node

def route_email(state: AgentState):
    """
    条件边逻辑：根据分类结果决定下一步
    """
    category = state["classification"]
    if category == "reply_needed":
        return "retrieve"
    else:
        # 如果是垃圾邮件或通知，直接结束
        return END

# 1. 初始化图
workflow = StateGraph(AgentState)

# 2. 添加节点
workflow.add_node("classify", classify_node)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("draft", draft_node)

# 3. 设置入口
workflow.set_entry_point("classify")

# 4. 添加边 (Edges)
# 从 classify 出发，根据 route_email 的返回值跳转
workflow.add_conditional_edges(
    "classify",
    route_email,
    {
        "retrieve": "retrieve",
        END: END
    }
)

# 正常的线性边
workflow.add_edge("retrieve", "draft")
workflow.add_edge("draft", END)

# 5. 编译成可运行的 Application
app = workflow.compile()