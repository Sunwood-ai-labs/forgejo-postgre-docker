FROM ghcr.io/thecatlady/webhook:latest

# git と必要なツールをインストール
RUN apk add --no-cache \
    git \
    openssh-client \
    curl \
    bash

# 作業ディレクトリを設定
WORKDIR /

# デフォルトコマンド
CMD ["webhook", "-hooks", "/config/hooks.json", "-verbose"]
