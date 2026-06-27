FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev \
    libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖（先装 CPU torch，再装其他）
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.5.1

COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

# 复制代码
COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
