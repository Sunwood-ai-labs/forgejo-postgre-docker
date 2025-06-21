#!/bin/bash
set -e

# カスタムテンプレート設置先
TARGET_DIR="./forgejo/gitea/templates/custom"
TARGET_FILE="$TARGET_DIR/header.tmpl"
SOURCE_FILE="./assets/header.tmpl"

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${CYAN}${BOLD}== Forgejo カスタムテーマセットアップ ==${RESET}"

# ディレクトリ作成
mkdir -p "$TARGET_DIR"

# ファイルコピー
cp "$SOURCE_FILE" "$TARGET_FILE"
echo -e "${GREEN}✔ カスタム header.tmpl を $TARGET_FILE にコピーしました。${RESET}"

# assets/public を forgejo/gitea/public にコピー
mkdir -p ./forgejo/gitea/public/assets/img
cp -r ./assets/public/assets/img/* ./forgejo/gitea/public/assets/img/
echo -e "${GREEN}✔ assets/img 配下を ./forgejo/gitea/public/assets/img/ にコピーしました。${RESET}"

# Forgejo再起動
echo -e "${YELLOW}→ Forgejoサーバーを再起動します...${RESET}"
docker compose restart server

echo -e "${BOLD}${CYAN}🎉 セットアップ完了！Forgejoをリロードしてテーマ切り替えUIを確認してください。${RESET}"