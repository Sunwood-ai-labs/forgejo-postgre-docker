# gradio-pages-service/Dockerfile
FROM python:3.11-slim

LABEL maintainer="Forgejo Gradio Pages"
LABEL description="Dynamic Gradio app deployment service for Forgejo"

# システムパッケージをインストール
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Docker CLI をインストール
RUN curl -fsSL https://get.docker.com | sh

# 作業ディレクトリを設定
WORKDIR /app

# Python依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY forgejo_gradio_manager.py .

# データディレクトリを作成
RUN mkdir -p /data /tmp/gradio-apps

# ポートを公開
EXPOSE 8081

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# アプリケーションを実行
CMD ["python", "forgejo_gradio_manager.py"]
