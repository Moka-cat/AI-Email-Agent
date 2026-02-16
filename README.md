# 📧 Enterprise RAG Email Agent (企业级智能邮件助理)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangChain](https://img.shields.io/badge/LangChain-0.1-green)
![RAG](https://img.shields.io/badge/RAG-Enabled-orange)

## 📖 项目简介
这是一个基于 **LLM (大语言模型)** 和 **RAG (检索增强生成)** 技术的智能邮件代理系统。它能够模拟人类员工的行为：
1.  **自动监控**：通过 IMAP 协议实时监听企业邮箱。
2.  **智能决策**：利用 LangGraph 状态机判断邮件意图（通知/需回复/垃圾邮件）。
3.  **知识检索**：基于本地向量库 (ChromaDB) 检索私有项目文档 (PDF/TXT)。
4.  **自动回复**：根据检索结果生成精准回复，并自动存入草稿箱。

## 🏗️ 系统架构
```mermaid
graph LR
    A[Email Server] -->|IMAP| B(Email Agent)
    B --> C{Intent Analysis}
    C -->|Reply Needed| D[RAG Engine]
    D -->|Query| E[(ChromaDB)]
    E -->|Context| D
    D -->|Context + Prompt| F[LLM]
    F -->|Draft| B
    B -->|SMTP/Append| A

<img width="814" height="1096" alt="image" src="https://github.com/user-attachments/assets/7f95ebc8-453d-4590-9d52-8abc56a9feeb" />
