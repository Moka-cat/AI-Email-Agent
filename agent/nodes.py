from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal

from .state import AgentState
from .tools.search import search_knowledge_base

# 定义分类的输出结构 (Pydantic)
class ClassificationResult(BaseModel):
    category: Literal["spam", "info", "reply_needed"] = Field(
        ..., description="The category of the email"
    )
    reason: str = Field(..., description="Brief reason for the classification")

# 初始化 LLM 
llm = ChatOpenAI(
        model = "qwen3-max",
        api_key = "xxxxx",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

def classify_node(state: AgentState) -> AgentState:
    """节点：分析邮件意图"""
    print("--- Node: Classifying Email ---")
    
    structured_llm = llm.with_structured_output(ClassificationResult)
    
    system_prompt = """
    You are an intelligent email assistant. Classify the incoming email into one of three categories:
    1. 'spam': Unsolicited ads, phishing.
    2. 'info': Newsletters, notifications that don't need a reply.
    3. 'reply_needed': Business inquiries, questions from colleagues.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Email Content: {email_content}\nSender: {sender}")
    ])
    
    chain = prompt | structured_llm
    result = chain.invoke({"email_content": state["email_content"], "sender": state["sender"]})
    
    return {
        "classification": result.category,
        "reason": result.reason
    }

def retrieve_node(state: AgentState) -> AgentState:
    """节点：RAG 检索背景信息"""
    print("--- Node: Retrieving Context ---")
    
    # 简单提取关键词作为查询
    query = f"{state['sender']} {state['email_content'][:50]}"
    context = search_knowledge_base.invoke(query)
    
    return {"retrieved_context": context}

def draft_node(state: AgentState) -> AgentState:
    """节点：生成回复草稿"""
    print("--- Node: Drafting Reply ---")
    
    prompt = ChatPromptTemplate.from_template(
        """
        You are a helpful assistant. Draft a professional reply to the email below.
        Use the retrieved context to ensure factual accuracy.
        
        Original Email: {email_content}
        Context Info: {retrieved_context}
        
        Draft:
        """
    )
    
    chain = prompt | llm
    response = chain.invoke({
        "email_content": state["email_content"],
        "retrieved_context": state.get("retrieved_context", "No context")
    })
    
    return {"draft_reply": response.content}