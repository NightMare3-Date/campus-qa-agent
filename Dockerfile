FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖（sentence-transformers 需要 + curl for healthcheck）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 预下载向量模型（避免首次请求太慢）
RUN python -c "from langchain_community.embeddings import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='BAAI/bge-small-zh-v1.5', model_kwargs={'device': 'cpu'}, encode_kwargs={'normalize_embeddings': True})" 2>/dev/null || true

# 暴露端口
EXPOSE 8000

# 启动
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
