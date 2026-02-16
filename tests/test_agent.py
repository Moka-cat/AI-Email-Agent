import pytest
from unittest.mock import MagicMock, patch
from agent.nodes import classify_node, draft_node
from agent.state import AgentState
from agent.nodes import ClassificationResult

# --- 1. 测试节点逻辑 (Unit Test) ---

@patch("agent.nodes.llm")
def test_classify_spam(mock_llm):
    """
    测试垃圾邮件分类逻辑
    """
    # 准备预期的 Pydantic 对象
    expected_result = ClassificationResult(
        category="spam",
        reason="Detected phishing keywords"
    )

    # 1. 获取 with_structured_output 生成的 mock 对象
    mock_structured_llm = mock_llm.with_structured_output.return_value
    
    # [双重保险 Mock 策略]
    # 情况 A: LangChain 调用了 .invoke() (标准 Runnable 行为)
    mock_structured_llm.invoke.return_value = expected_result
    # 情况 B: LangChain 直接调用了对象本身 (Callable 行为, 也就是报错发生的原因)
    mock_structured_llm.return_value = expected_result
    
    state = AgentState(email_content="You won $1M!", sender="scammer@bad.com")
    result = classify_node(state)
    
    assert result["classification"] == "spam"
    assert "phishing" in result["reason"]

@patch("agent.nodes.llm")
def test_draft_node(mock_llm):
    """
    测试草稿生成
    """
    # 1. 模拟 LLM 返回的消息对象
    mock_response = MagicMock()
    mock_response.content = "Dear Boss, I will adjust the budget."
    
    # [双重保险 Mock 策略]
    # 情况 A: LangChain 调用了 .invoke()
    mock_llm.invoke.return_value = mock_response
    # 情况 B: LangChain 直接调用了对象本身 (报错原因: name='llm().content')
    mock_llm.return_value = mock_response
    
    state = AgentState(
        email_content="Budget?", 
        sender="boss", 
        retrieved_context="Context info"
    )
    result = draft_node(state)
    
    assert result["draft_reply"] == "Dear Boss, I will adjust the budget."

# --- 2. 测试工作流 (Integration Test) ---

def test_workflow_logic_reply_needed():
    """
    测试：需要回复的邮件应该走完整流程 classify -> retrieve -> draft
    """
    from langgraph.graph import StateGraph, END
    
    # Mock 节点函数的行为 (不Mock LLM，直接Mock节点函数本身)
    def mock_classify(state):
        return {"classification": "reply_needed"}
    
    def mock_retrieve(state):
        return {"retrieved_context": "budget is 50k"}
        
    def mock_draft(state):
        return {"draft_reply": "Ok, noted."}
    
    # 重建测试图
    workflow = StateGraph(AgentState)
    workflow.add_node("classify", mock_classify)
    workflow.add_node("retrieve", mock_retrieve)
    workflow.add_node("draft", mock_draft)
    
    workflow.set_entry_point("classify")
    
    workflow.add_conditional_edges(
        "classify",
        lambda x: "retrieve" if x["classification"] == "reply_needed" else END,
        {"retrieve": "retrieve", END: END}
    )
    workflow.add_edge("retrieve", "draft")
    workflow.add_edge("draft", END)
    
    test_app = workflow.compile()
    
    initial_state = {"email_content": "Budget?", "sender": "boss"}
    result = test_app.invoke(initial_state)
    
    assert result["classification"] == "reply_needed"
    assert result["retrieved_context"] == "budget is 50k"
    assert result["draft_reply"] == "Ok, noted."