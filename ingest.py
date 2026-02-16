from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import os
import shutil

load_dotenv()

# === [关键] 设置国内镜像 ===
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 路径配置
PERSIST_DIR = "./chroma_db"
DATA_PATH = "./data"  # <--- 请确保你在项目根目录下创建了这个文件夹！

# 1. 清理旧数据库
if os.path.exists(PERSIST_DIR):
    shutil.rmtree(PERSIST_DIR)
    print(f"🧹 Cleaned up old database at {PERSIST_DIR}")

# 2. 加载数据 (Loader)
print(f"📂 Loading documents from {DATA_PATH}...")

documents = []

# 检查 data 目录是否存在
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)
    print(f"⚠️ Created missing directory: {DATA_PATH}. Please put some files in it!")
    # 创建一个测试文件，防止报错
    with open(os.path.join(DATA_PATH, "demo.txt"), "w", encoding="utf-8") as f:
        f.write("项目进度：RAG 检索模块的向量召回率已优化至 85%，目前正在调试重排序(Rerank)模型。\n")
        f.write("会议安排：周一上午的演示重点是展示 System 2 慢思考逻辑和 Multi-Agent 协作流程。")

# 加载 TXT 文件
txt_loader = DirectoryLoader(DATA_PATH, glob="**/*.txt", loader_cls=TextLoader)
documents.extend(txt_loader.load())

# 加载 PDF 文件 (如果你放入了 PDF)
pdf_loader = DirectoryLoader(DATA_PATH, glob="**/*.pdf", loader_cls=PyPDFLoader)
documents.extend(pdf_loader.load())

print(f"📄 Loaded {len(documents)} source files.")

# 3. 文本切分 (Splitter) - ⭐️ 这是 RAG 的核心技术点
# 为什么切分？因为 Embedding 模型一次只能处理有限长度（比如512个字），
# 而且切短一点，搜索会更精准。
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # 每个切片约 500 字符
    chunk_overlap=50,    # 切片之间重叠 50 字符（防止上下文断裂）
    separators=["\n\n", "\n", "。", "！", "？", " ", ""]
)

split_docs = text_splitter.split_documents(documents)
print(f"✂️  Split into {len(split_docs)} chunks.")

# 4. 初始化模型 (Embedding)
print(f"🚀 Loading Embedding Model (Local BGE)...")
model_name = "BAAI/bge-small-zh-v1.5"
model_kwargs = {'device': 'cpu', 'trust_remote_code': True}
encode_kwargs = {'normalize_embeddings': True}

embedding_model = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

# 5. 向量化并存储 (Vector Store)
print(f"🚀 Vectorizing & Saving...")

vector_db = Chroma.from_documents(
    documents=split_docs, # 注意：这里存入的是切分后的 split_docs
    embedding=embedding_model, 
    persist_directory=PERSIST_DIR,
    collection_name="project_knowledge"
)

print(f"✅ Knowledge Base Updated! Saved to {PERSIST_DIR}")