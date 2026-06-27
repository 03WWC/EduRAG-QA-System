FROM python:3.11-slim

WORKDIR /app

# 换阿里云镜像源（Debian）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0t64 libsm6 libxext6 libxrender-dev libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

# pip 全部走清华源（清华同步了 PyTorch 的包）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir torch>=2.6

COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

COPY . .

EXPOSE 8000

ENV OMP_NUM_THREADS=2 MKL_NUM_THREADS=2

CMD ["python", "app.py"]
