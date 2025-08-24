#!/bin/sh
set -e

# デバッグ用ログ出力
echo "=== Webhook Deploy Script Started ==="
echo "Current time: $(date)"
echo "Working directory: $(pwd)"
echo "Environment variables:"
echo "REPO_URL: ${REPO_URL:-'NOT SET'}"
echo "BRANCH_NAME: ${BRANCH_NAME:-'NOT SET'}"
echo "REPO_FULL_NAME: ${REPO_FULL_NAME:-'NOT SET'}"
echo "PUSHER_NAME: ${PUSHER_NAME:-'NOT SET'}"

# リポジトリURLの取得（Webhookペイロード優先）
if [ -z "$REPO_URL" ]; then
  echo "Error: REPO_URL is not set"
  exit 1
fi

# ブランチ名の取得と処理（refs/heads/branch-name → branch-name）
if [ -n "$BRANCH_NAME" ]; then
  DEPLOY_BRANCH=$(echo "$BRANCH_NAME" | sed 's|^refs/heads/||')
else
  DEPLOY_BRANCH="static-pages"
fi

echo "Deploying repository: $REPO_URL"
echo "Target branch: $DEPLOY_BRANCH"

# FORGEJO_ACCESS_TOKENが設定されている場合のみ認証URLを作成
if [ -n "$FORGEJO_ACCESS_TOKEN" ]; then
  # URLにアクセストークンを埋め込む (例: http://oauth2:TOKEN@... )
  AUTH_REPO_URL=$(echo "$REPO_URL" | sed "s|://|://oauth2:${FORGEJO_ACCESS_TOKEN}@|")
  echo "Using authenticated URL for clone/pull"
else
  AUTH_REPO_URL="$REPO_URL"
  echo "Warning: FORGEJO_ACCESS_TOKEN not set, using public access"
fi

# リポジトリ名をディレクトリ名として使用
if [ -n "$REPO_FULL_NAME" ]; then
  # full_name が使用可能な場合（user/repo形式）
  REPO_NAME=$(echo "$REPO_FULL_NAME" | sed 's|/|_|g')
else
  # URLからリポジトリ名を抽出
  REPO_NAME=$(echo "$REPO_URL" | sed 's|.*://.*/||; s|/|_|g; s|\.git$||')
fi

TARGET_DIR="/var/www/html/$REPO_NAME"
echo "Target directory: $TARGET_DIR"

# ターゲットディレクトリの作成
mkdir -p "$TARGET_DIR"

# Gitが安全なディレクトリとして認識するように設定
git config --global --add safe.directory "$TARGET_DIR" || true

if [ -d "$TARGET_DIR/.git" ]; then
  # 既存: git pullで更新
  echo "Pulling latest changes..."
  cd "$TARGET_DIR"
  
  # リモートURLを更新（認証トークンが変更された場合に対応）
  git remote set-url origin "$AUTH_REPO_URL"
  
  # 指定されたブランチが存在するかチェック
  if git ls-remote --heads origin "$DEPLOY_BRANCH" | grep -q "$DEPLOY_BRANCH"; then
    git fetch origin "$DEPLOY_BRANCH"
    git reset --hard "origin/$DEPLOY_BRANCH"
    git clean -fd
    echo "Successfully updated to branch: $DEPLOY_BRANCH"
  else
    echo "Error: Branch '$DEPLOY_BRANCH' does not exist in remote repository"
    exit 1
  fi
else
  # 新規: git clone
  echo "Cloning repository..."
  rm -rf "$TARGET_DIR"/* "$TARGET_DIR"/.??* 2>/dev/null || true
  
  # 指定されたブランチでクローン
  if git clone --branch "$DEPLOY_BRANCH" --single-branch "$AUTH_REPO_URL" "$TARGET_DIR"; then
    echo "Successfully cloned branch: $DEPLOY_BRANCH"
  else
    echo "Error: Failed to clone branch '$DEPLOY_BRANCH'. Trying default branch..."
    git clone "$AUTH_REPO_URL" "$TARGET_DIR" || exit 1
  fi
fi

echo "Deployment finished for $REPO_NAME"
echo "Site available at: http://localhost:8181/$REPO_NAME/"
echo "=== Webhook Deploy Script Completed ==="
