#!/bin/bash
# EduRAG 一键部署脚本
# 在服务器上以 root 执行: bash deploy.sh

set -e

echo "======================================"
echo "  EduRAG 自动部署"
echo "======================================"

# 0. 检查 Docker
if ! command -v docker &>/dev/null; then
    echo "[1/7] 安装 Docker..."
    curl -fsSL https://get.docker.com | bash
    systemctl enable docker
    systemctl start docker
else
    echo "[1/7] Docker 已安装 ✓"
fi

# 1. 创建目录
echo "[2/7] 创建项目目录..."
mkdir -p /data/EduRAG-QA-System/rag_qa/model
mkdir -p /data/EduRAG-QA-System/rag_qa/core/bert_query_classifier
mkdir -p /data/EduRAG-QA-System/rag_qa/data
mkdir -p /data/EduRAG-QA-System/frontend/dist
mkdir -p /data/EduRAG-QA-System/logs

# 2. 拉代码（如果已经有就跳过）
if [ ! -f /data/EduRAG-QA-System/app.py ]; then
    echo "[3/7] 拉取代码..."
    cd /data/EduRAG-QA-System
    git clone https://github.com/03WWC/EduRAG-QA-System.git /data/EduRAG-QA-System/.tmp
    cp -r /data/EduRAG-QA-System/.tmp/* /data/EduRAG-QA-System/
    cp -r /data/EduRAG-QA-System/.tmp/.gitignore /data/EduRAG-QA-System/ 2>/dev/null || true
    rm -rf /data/EduRAG-QA-System/.tmp
else
    echo "[3/7] 代码已存在，跳过 ✓"
fi

# 3. 配置文件
if [ ! -f /data/EduRAG-QA-System/config.ini ]; then
    echo "[4/7] 创建配置文件..."
    cp /data/EduRAG-QA-System/config-server.ini /data/EduRAG-QA-System/config.ini
    echo "    ⚠ 请编辑 /data/EduRAG-QA-System/config.ini 填入 dashscope_api_key"
else
    echo "[4/7] config.ini 已存在 ✓"
fi

# 4-5. 模型文件（需手动从本地传）
echo "[5/7] 模型文件检查..."
if [ -d /data/EduRAG-QA-System/rag_qa/model/bge-m3 ] && [ "$(ls -A /data/EduRAG-QA-System/rag_qa/model/bge-m3 2>/dev/null)" ]; then
    echo "    bge-m3 ✓"
else
    echo "    ✗ bge-m3 缺失，请在本地执行："
    echo "      scp -r rag_qa/model/bge-m3 root@47.120.66.230:/data/EduRAG-QA-System/rag_qa/model/bge-m3"
fi

if [ -d /data/EduRAG-QA-System/rag_qa/model/bge-reranker-large ] && [ "$(ls -A /data/EduRAG-QA-System/rag_qa/model/bge-reranker-large 2>/dev/null)" ]; then
    echo "    bge-reranker-large ✓"
else
    echo "    ✗ bge-reranker-large 缺失，请在本地执行："
    echo "      scp -r rag_qa/model/bge-reranker-large root@47.120.66.230:/data/EduRAG-QA-System/rag_qa/model/bge-reranker-large"
fi

if [ -f /data/EduRAG-QA-System/rag_qa/core/bert_query_classifier/model.safetensors ]; then
    echo "    bert_query_classifier ✓"
else
    echo "    ✗ bert_query_classifier 缺失，请在本地执行："
    echo "      scp -r rag_qa/core/bert_query_classifier root@47.120.66.230:/data/EduRAG-QA-System/rag_qa/core/bert_query_classifier"
fi

# 6. 构建前端（在本地构建后传）
echo "[6/7] 前端文件检查..."
if [ -f /data/EduRAG-QA-System/frontend/dist/index.html ]; then
    echo "    frontend/dist ✓"
else
    echo "    ✗ frontend/dist 缺失，请在本地执行："
    echo "      cd frontend && npm install && npm run build"
    echo "      scp -r frontend/dist root@47.120.66.230:/data/EduRAG-QA-System/frontend/dist"
fi

# 7. 启动
echo "[7/7] 启动 Docker 服务..."
cd /data/EduRAG-QA-System
docker compose up -d --build

echo ""
echo "======================================"
echo "  等待服务启动（约30秒）..."
echo "======================================"
sleep 30
docker compose ps
echo ""
echo "健康检查:"
curl -s http://localhost:8000/health 2>/dev/null && echo "" || echo "  还在启动中，稍等..."
echo ""
echo "======================================"
echo "  部署完成！访问: http://47.120.66.230:8000"
echo "  默认管理员: admin / admin123"
echo "======================================"
