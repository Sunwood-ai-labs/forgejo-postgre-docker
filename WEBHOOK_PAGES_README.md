# 🔄 Webhook Pages 機能実装

## 📋 概要

Forgejoの静的サイトホスティング機能を、NginxとWebhookを使って再現した実装です。よりシンプルで軽量な構成となっています。

## 🏗️ 構成

* **Nginx** (ポート 8080): 静的サイトのファイルを配信
* **Webhook** (ポート 9000): Forgejoからの通知を受け取り、Gitリポジトリから最新のファイルを自動取得・配置

## 📁 ファイル構成

```
.
├── docker-compose.yml          # サービス定義（nginx, webhookサービス追加済み）
├── .env                        # 環境変数（Webhook設定追加済み）
├── nginx/
│   └── nginx.conf              # Nginx設定ファイル
├── webhook/
│   ├── hooks.json              # Webhook設定ファイル
│   └── scripts/
│       └── deploy.sh           # デプロイ用スクリプト（実行権限付与済み）
└── pages-data/                 # 静的サイトのコンテンツ置き場
```

## ⚙️ セットアップ手順

### 1. 環境変数の設定

`.env`ファイルの以下の項目を編集してください：

```env
# デフォルトのデプロイ対象ブランチ名
BRANCH_NAME=static-pages

# Forgejoで生成したアクセストークン
# アクセストークンは全リポジトリの読み取り権限(read:repository)が必要です
FORGEJO_ACCESS_TOKEN=your_forgejo_access_token_here

# Webhookのシークレットキー
WEBHOOK_SECRET=YourSuperSecretWebhookToken
```

### 2. Forgejoでの設定

#### アクセストークンの生成
1. Forgejoにログイン
2. 右上のアイコン → 「設定」 → 「アプリケーション」
3. 「トークンを生成」で `webhook-for-pages` などの名前を入力
4. 権限で `repository` の `read:repository` にチェック
5. トークンをコピーして `.env` の `FORGEJO_ACCESS_TOKEN` に貼り付け

#### Webhookの設定
1. 対象リポジトリ → 「設定」 → 「Webhook」
2. 「Webhookを追加」 → 「Forgejo」
3. 以下の通り設定：
   - **ターゲットURL**: `http://webhook:9000/hooks/deploy-pages`
   - **HTTPメソッド**: `POST`
   - **シークレットキー**: `.env`の`WEBHOOK_SECRET`と同じ値
   - **トリガー**: 「プッシュイベント」を選択

### 3. 起動と動作確認

```bash
# サービスの起動
docker-compose up -d --build

# 対象リポジトリの対象ブランチに変更をプッシュ
# → 自動的にWebhookが発火し、静的サイトが更新されます

# ブラウザで確認
# http://localhost:8080
```

## 🔧 動作フロー

1. **プッシュイベント**: `static-pages`ブランチを持つ任意のリポジトリに変更がプッシュされる
2. **Webhook通知**: ForgejoがWebhookサービスにPOSTリクエストを送信
3. **署名検証**: Webhookサービスがリクエストの署名を検証
4. **デプロイスクリプト実行**: `deploy.sh`が実行され、Webhookから渡されたリポジトリ情報を基に最新のファイルをGitから取得
5. **Nginx配信**: Nginxがリポジトリごとに個別のディレクトリに配置された静的ファイルを配信

## 🌐 アクセス方法

各リポジトリの静的サイトは以下のURLでアクセスできます：

```
http://localhost:8080/{user}_{repo}/
```

例:
- リポジトリ: `http://192.168.0.131:3000/user1/my-site.git`
- アクセスURL: `http://localhost:8080/user1_my-site/`

## 🛠️ トラブルシューティング

### デプロイが動作しない場合
- Webhook URLが正しいか確認（`localhost`ではなく実際のIPアドレス）
- アクセストークンに `read:repository` 権限があるか確認
- シークレットキーが`.env`とWebhook設定で一致するか確認

### 静的サイトが表示されない場合
- `pages-data`ディレクトリにファイルが存在するか確認
- Nginxコンテナが正常に起動しているか確認
- ポート8080が他のサービスで使用されていないか確認

## 📝 メモ

- 既存の`forgejo-pages`サービスは`nginx`と`webhook`サービスに置き換えられています
- `pages-data`ディレクトリはNginxとWebhookサービスで共有されます
- 各リポジトリは個別のサブディレクトリ（`user_repo`形式）で管理されます
- `static-pages`ブランチを持つすべてのリポジトリが自動的にpagesの対象になります
- Webhookは動的にリポジトリ情報を取得するため、固定の設定は不要です
- 初回デプロイ時はWebhookがトリガーされた時点で自動的にクローンされます
