#!/bin/bash
set -e

# カスタムテンプレート設置先
TARGET_DIR="./forgejo/gitea/templates/custom"
TARGET_FILE="$TARGET_DIR/header.tmpl"
SOURCE_FILE="./assets/header.tmpl"

echo "== Forgejo カスタムテーマセットアップ =="

# ディレクトリ作成
mkdir -p "$TARGET_DIR"

# ファイルコピー
cp "$SOURCE_FILE" "$TARGET_FILE"
echo "カスタム header.tmpl を $TARGET_FILE にコピーしました。"

# Forgejo再起動
docker compose restart server

echo "セットアップ完了！Forgejoをリロードしてテーマ切り替えUIを確認してください。"