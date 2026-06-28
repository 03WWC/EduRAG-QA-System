<p align="center">
  <img src="https://img.shields.io/badge/EduRAG-智能问答系统-6366f1?style=for-the-badge&logo=robot&logoColor=white" alt="EduRAG">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue-3.4-4FC08D?style=flat-square&logo=vuedotjs&logoColor=white" alt="Vue">
  <img src="https://img.shields.io/badge/LangChain-0.3-1C3C3C?style=flat-square&logo=langchain&logoColor=white" alt="LangChain">
  <img src="https://img.shields.io/badge/Milvus-2.5-00A3E0?style=flat-square&logo=milvus&logoColor=white" alt="Milvus">
  <img src="https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql&logoColor=white" alt="MySQL">
  <img src="https://img.shields.io/badge/Redis-7.0-DC382D?style=flat-square&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Docker-24-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/WebSocket-SSE-000000?style=flat-square&logo=socketdotio&logoColor=white" alt="WebSocket">
  <img src="https://img.shields.io/badge/JWT-认证-000000?style=flat-square&logo=jsonwebtokens&logoColor=white" alt="JWT">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License">
</p>

---

## 📖 项目简介

EduRAG 是一套面向教育领域的智能问答系统，融合 **BM25 结构化检索** + **RAG 混合检索** 两级策略。系统优先通过 BM25 快速匹配高频问题，未命中时回退至 Milvus 向量库进行稠密+稀疏混合检索，结合 CrossEncoder 重排序，最终由大模型生成自然语言回答。

支持多用户会话隔离、管理员知识库上传管理、流式对话，Docker 一键部署。

## 🏗️ 架构

```
用户 → Vue 3 前端 → Nginx → FastAPI
                              ├─ /api/auth/*     认证 (JWT)
                              ├─ /api/query      非流式问答
                              ├─ /api/stream     WebSocket 流式问答
                              ├─ /api/admin/*    管理员（上传/文档/用户）
                              ├─ BM25 Search ──── MySQL + Redis
                              └─ RAG Pipeline ─── Milvus + BGE-M3 + DashScope
```

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Markdown 渲染 |
| 后端 | FastAPI + WebSocket + JWT |
| 检索 | BM25 (rank-bm25) + 稠密稀疏混合 (BGE-M3) + CrossEncoder 重排序 |
| 向量库 | Milvus 2.5 |
| 大模型 | DashScope Qwen-Plus（流式 SSE） |
| 存储 | MySQL（会话历史/用户/上传记录）+ Redis（BM25 缓存） |
| 部署 | Docker Compose / 宝塔面板 |

## 🚀 快速开始

### 本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 config.ini（MySQL / Redis / Milvus / DashScope）
cp config-server.ini config.ini
vim config.ini

# 3. 启动后端
python app.py                 # http://localhost:8000

# 4. 启动前端（新终端）
cd frontend && npm install && npm run dev   # http://localhost:5173
```

### Docker 部署

```bash
docker compose up -d --build
```

详见 [部署文档](#-部署)

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 💬 流式问答 | WebSocket 逐字输出，多轮对话历史感知 |
| 🔍 两级检索 | BM25 快速匹配（≥0.85 阈值）→ RAG 混合检索 |
| 🧠 智能策略 | 直接检索 / HyDE / 子查询分解 / 回溯检索，LLM 自动选优 |
| 👥 多用户隔离 | JWT 认证，会话列表/对话历史按用户隔离 |
| 📄 知识库管理 | 管理员上传 PDF/Word/PPT/Markdown，自动分块入库 |
| 🎨 暗色模式 | 亮/暗主题切换，响应式布局 |
| 🔄 断线重连 | WebSocket 指数退避自动重连 |
| 📋 会话管理 | 新建/切换/重命名/删除会话，历史记录持久化 |

## 📁 项目结构

```
EduRAG-QA-System/
├── app.py                     # FastAPI 主入口
├── new_main.py                # 集成问答系统（BM25 + RAG）
├── admin_service.py           # 管理员服务（上传/文档管理）
├── auth/                      # JWT 认证模块
│   ├── jwt_handler.py         # Token 签发/验证中间件
│   ├── user_service.py        # 用户 CRUD
│   └── models.py              # Pydantic 模型
├── mysql_qa/                  # MySQL 问答模块
│   ├── db/mysql_client.py     # MySQL 连接
│   ├── cache/redis_client.py  # Redis 缓存
│   ├── retrieval/bm25_search.py # BM25 检索
│   └── data/                  # 结构化问答数据
├── rag_qa/                    # RAG 模块
│   ├── core/
│   │   ├── vector_store.py    # Milvus 向量存储
│   │   ├── new_rag_system.py  # RAG 生成流水线
│   │   ├── query_classifier.py # BERT 意图分类
│   │   ├── strategy_selector.py # LLM 策略选择
│   │   ├── prompts.py         # Prompt 模板
│   │   └── document_processor.py # 文档加载/分块
│   ├── edu_document_loaders/  # PDF/PPT/DOCX/IMG 加载器
│   ├── edu_text_spliter/      # 中文文本分割器
│   └── model/                 # BGE-M3 / BGE-Reranker 模型
├── frontend/                  # Vue 3 前端
│   └── src/
│       ├── components/        # Vue 组件
│       ├── composables/       # 核心逻辑（WS/Chat/Session）
│       └── utils/             # Markdown 渲染
├── Dockerfile
├── docker-compose.yml
└── config-server.ini          # 服务器配置模板
```

## 🔧 配置

`config.ini` 说明：

```ini
[mysql]        # MySQL 连接（host/port/user/password/database）
[redis]        # Redis 连接（host/port/password）
[milvus]       # Milvus 连接（host/port/database/collection）
[llm]          # LLM 配置（model/api_key/base_url）
[retrieval]    # 检索参数（分块大小/K值/重叠度）
[local]        # 本地模型路径（rerank/bge-m3）
[app]          # 应用配置（客服电话/学科列表）
```

首次启动自动创建数据库表，默认管理员 `admin / admin123`。

## 🐳 部署

```bash
# 1. 拉代码
git clone https://github.com/03WWC/EduRAG-QA-System.git
cd EduRAG-QA-System

# 2. 配置
cp config-server.ini config.ini
vim config.ini   # 填 dashscope_api_key

# 3. 拷贝模型文件（从本地，约 7GB）
# scp -r rag_qa/model/* root@server:/data/EduRAG-QA-System/rag_qa/model/

# 4. 构建前端
cd frontend && npm install && npm run build && cd ..

# 5. 启动
docker compose up -d --build
```

访问 `http://你的IP:8000`，默认管理员 `admin / admin123`。

### 宝塔面板部署

1. 软件商店安装 Nginx
2. 网站 → 添加站点 → 配置反向代理到 `127.0.0.1:8000`
3. Python 项目 → 添加 → 路径 `/data/EduRAG-QA-System`，启动命令 `app`

## 📄 License

MIT
