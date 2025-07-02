#!/bin/bash

# =============================================================================
# OpenHands専用ランナー登録スクリプト（改良版）
# =============================================================================

# 色付きメッセージ用の関数
print_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

echo "🤖 OpenHands専用ランナー登録"
echo "============================="

# .envファイルの存在確認
if [ ! -f ".env" ]; then
    print_error ".envファイルが見つかりません"
    exit 1
fi

# .envファイルから既存のトークンを読み込み
source .env

# .envファイルからトークンを取得
if [ -n "$FORGEJO_RUNNER_REGISTRATION_TOKEN" ] && [ "$FORGEJO_RUNNER_REGISTRATION_TOKEN" != "YOUR_RUNNER_TOKEN_HERE" ]; then
    print_info ".envファイルから既存のランナートークンを使用します"
    RUNNER_TOKEN="$FORGEJO_RUNNER_REGISTRATION_TOKEN"
else
    print_error ".envファイルにトークンが設定されていません"
    print_info "先に.envファイルのFORGEJO_RUNNER_REGISTRATION_TOKENを設定してください"
    print_info "管理画面でトークンを取得: http://192.168.0.131:3000/admin/actions/runners"
    exit 1
fi

# OpenHands専用ランナーのラベル定義
OPENHANDS_LABELS="openhands:docker://ghcr.io/all-hands-ai/runtime:0.9-nikolaik,ubuntu-latest:docker://ghcr.io/catthehacker/ubuntu:act-22.04,ubuntu-22.04:docker://ghcr.io/catthehacker/ubuntu:act-22.04,python:docker://python:3.11-slim,node:docker://node:18-slim,docker:docker://ghcr.io/catthehacker/ubuntu:act-22.04,selfhosted:host"

print_info "OpenHands専用ランナーを登録中..."
print_info "ランナー名: openhands-runner"
print_info "対応ラベル:"
echo "  • openhands (OpenHands専用)"
echo "  • ubuntu-latest, ubuntu-22.04"
echo "  • python (Python環境)"
echo "  • node (Node.js環境)" 
echo "  • docker (Docker環境)"
echo "  • selfhosted (セルフホスト)"
echo ""

# ランナーコンテナが起動しているか確認
if ! docker-compose ps runner | grep -q "Up"; then
    print_error "ランナーコンテナが起動していません"
    print_info "ランナーを起動中..."
    docker-compose up -d runner
    sleep 10
fi

# OpenHands専用ランナーを登録
docker-compose exec runner forgejo-runner register \
  --no-interactive \
  --token "$RUNNER_TOKEN" \
  --name "openhands-runner" \
  --instance "http://192.168.0.131:3000" \
  --labels "$OPENHANDS_LABELS"

if [ $? -eq 0 ]; then
    print_success "✅ OpenHandsランナーが正常に登録されました！"
    
    print_info "🔄 ランナーデーモンを再起動中..."
    docker-compose restart runner
    
    sleep 8
    
    print_info "📋 ランナーの状態を確認:"
    echo "────────────────────────────────────"
    docker logs forgejo_runner --tail 15
    
    echo ""
    print_success "🎉 セットアップ完了！"
    echo ""
    print_info "📊 利用可能なランナー:"
    echo "  • claude-runner (既存)"
    echo "  • openhands-runner (新規追加)"
    echo ""
    print_info "🚀 OpenHandsワークフローでの使用例:"
    echo "  runs-on: openhands"
    echo "  runs-on: docker"
    echo "  runs-on: ubuntu-latest"
    echo "  runs-on: python"
    echo ""
    print_info "🔗 管理画面で確認:"
    echo "  http://192.168.0.131:3000/admin/actions/runners"
    
else
    print_error "❌ ランナーの登録に失敗しました"
    print_info "💡 トラブルシューティング:"
    echo "  1. トークンが正しいか確認"
    echo "  2. 管理画面で新しいトークンを生成"
    echo "  3. Forgejoサーバーが起動しているか確認"
    echo ""
    print_info "🔗 ランナー管理画面:"
    echo "  http://192.168.0.131:3000/admin/actions/runners"
fi