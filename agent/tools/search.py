from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings  # <--- 变动 1: 引入本地模型库
from langchain_core.tools import tool
from dotenv import load_dotenv
import os

load_dotenv()

# 设置国内镜像，防止第一次运行时下载模型卡住
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

PERSIST_DIR = "./chroma_db"

@tool
def search_knowledge_base(query: str) -> str:
    """Search project documents via Local BGE Embedding."""
    print(f"--- [RAG] Searching ChromaDB for: {query} ---")
    
    # <--- 变动 2: 使用 BGE 小模型 (BAAI/bge-small-zh-v1.5)
    # 必须和你 ingest.py 里用的模型完全一致！
    embedding_model = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-zh-v1.5",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # 连接本地数据库
    vector_db = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embedding_model,  # <--- 变动 3: 传入本地模型
        collection_name="project_knowledge",
    )
    
    # 搜索
    results = vector_db.similarity_search(query, k=2)
    
    if not results:
        return "No info found."
        
    context = "\n".join([f"- {doc.page_content}" for doc in results])
    print(f"--- [RAG] Found context:\n{context}\n---")
    return context