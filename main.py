from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent.graph import app as agent_app  # 导入我们编译好的 LangGraph 应用

# 1. 初始化 FastAPI
app = FastAPI(
    title="SmartMail Agent API",
    description="An AI Agent service to classify and draft email replies.",
    version="1.0.0"
)

# 2. 定义请求的数据模型 (DTO)
class EmailRequest(BaseModel):
    id: str
    subject: str
    sender: str
    body: str

class AgentResponse(BaseModel):
    email_id: str
    classification: str
    reason: str
    draft: str | None = None

# 3. 定义 API 路由
@app.post("/api/v1/process_email", response_model=AgentResponse)
async def process_email(request: EmailRequest):
    """
    接收一封邮件，触发 AI Agent 工作流：
    分类 -> (检索) -> (拟稿)
    """
    print(f"📨 Received email: {request.subject} from {request.sender}")

    try:
        # 4. 构造初始状态
        initial_state = {
            "email_content": request.body,
            "sender": request.sender,
            # 其他字段会在 Agent 运行中填充
        }

        # 5. 调用 LangGraph (invoke 是同步的，如果需要异步可以使用 ainvoke)
        # 注意：在生产环境中，大模型调用耗时较长，建议使用 Celery 或 ainvoke
        result = await agent_app.ainvoke(initial_state)

        # 6. 返回结果
        return AgentResponse(
            email_id=request.id,
            classification=result.get("classification", "unknown"),
            reason=result.get("reason", "No reason provided"),
            draft=result.get("draft_reply")  # 可能为 None
        )

    except Exception as e:
        print(f"❌ Error processing email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 7. 健康检查 (K8s 部署常用)
@app.get("/health")
def health_check():
    return {"status": "ok"}

# 启动命令说明
if __name__ == "__main__":
    import uvicorn
    # reload=True 方便开发时热更新
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)