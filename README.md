<div align="center">

<img src="https://github.com/user-attachments/assets/219b5824-0954-4367-af27-7f05013f546c" width="100%" />

# forgejo-postgre-docker

<p>
  <img src="https://img.shields.io/badge/docker-blue?logo=docker" />
  <img src="https://img.shields.io/badge/postgresql-336791?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/forgejo-orange" />
</p>

</div>

---

## 📝 概要

このリポジトリは、ForgejoとPostgreSQLをDocker Composeで簡単に構築・運用するためのテンプレートです。  
SSL証明書管理や環境変数による柔軟な設定もサポートしています。

---

## 🛠️ 技術スタック

- Docker / Docker Compose
- Forgejo
- PostgreSQL

---

## 🚀 インストール

1. リポジトリをクローン
   ```bash
   git clone https://github.com/yourname/forgejo-postgre-docker.git
   cd forgejo-postgre-docker
   ```

2. `.env` ファイルを作成（`.env.example`をコピーして編集）
   ```bash
   cp .env.example .env
   # 必要に応じて値を編集
   ```

   > **IPアドレス設定について**:
   > デフォルトでは `192.168.0.131` が設定されていますが、以下の環境変数で変更可能です：
   > - `FORGEJO_DOMAIN`: Forgejoのドメイン/IPアドレス
   > - `FORGEJO_ROOT_URL`: ForgejoのベースURL
   >
   > ローカル環境の場合は、以下を`.env`ファイルに追加してください：
   > ```
   > FORGEJO_DOMAIN=localhost
   > FORGEJO_ROOT_URL=http://localhost:3000/
   > ```

3. サービスを起動
   ```bash
   docker-compose up -d
   ```

詳細な手順は[インストールガイド](docs/INSTALL.md)を参照してください。

4. Forgejoにアクセス
```
http://192.168.0.131:3000
```

> **重要**: `192.168.0.131` の部分は、実際のDockerホストのIPアドレスに置き換えてください。
> ローカル環境の場合は `http://localhost:3000` でもアクセス可能です。

---

## 🧑‍💻 使い方

### Forgejo Runnerの設定

#### 自動登録（推奨）
Docker Composeの起動時に自動的にランナーが登録されます。環境変数で設定を行ってください：

```bash
# .envファイルで設定
FORGEJO_RUNNER_TOKEN=your-runner-registration-token
```

ランナー登録トークンは以下のURLから取得できます：
```
http://192.168.0.131:3000/admin/actions/runners
```

#### 手動登録
必要に応じて手動でランナーを登録することも可能です：

```bash
docker-compose exec runner forgejo-runner register \
  --no-interactive \
  --token <YOUR_TOKEN> \
  --name <RUNNER_NAME> \
  --instance http://192.168.0.131:3000 \
  --labels docker:docker://ghcr.io/catthehacker/ubuntu:act-22.04
```

#### ランナー設定ファイル
ランナーの設定は [`runner/.runner.example`](runner/.runner.example) を参考にしてください：

```json
{
  "id": 3,
  "uuid": "yyyyyyyyy",
  "name": "claude-runner",
  "token": "xxxxxxxxx",
  "address": "http://192.168.0.131:3000",
  "labels": [
    "docker:docker://ghcr.io/catthehacker/ubuntu:act-22.04"
  ]
}
```

> **注意**: `192.168.0.131` は環境に応じて適切なIPアドレスに変更してください。
> 実際のForgejoサーバーのIPアドレスは、Docker ComposeでデプロイされたホストのIPアドレスを指定する必要があります。

### Forgejo Runnerデーモンの実行

```bash
docker-compose exec runner forgejo-runner daemon
```

---

## 📂 ディレクトリ構成

```
forgejo-postgre-docker/
├── certs/                    # SSL証明書等を格納
├── runner/                   # Forgejo Runner関連ファイル
│   ├── .runner              # ランナー設定ファイル（自動生成）
│   └── .runner.example      # ランナー設定のサンプル
├── gradio-pages-service/    # Gradioページサービス
├── .env.example             # 環境変数サンプル
├── docker-compose.yml       # Docker Compose設定
├── README.md
└── ...
```

---

## 🔧 トラブルシューティング

### `http://server:3000` でエラーが発生する場合

`server` ホスト名ではなく、実際のIPアドレスを使用してください：

1. **ローカル環境の場合**:
   ```
   http://localhost:3000
   ```

2. **リモート環境の場合**:
   ```
   http://<DockerホストのIPアドレス>:3000
   ```

3. **環境変数での設定**:
   `.env`ファイルで以下を設定：
   ```env
   FORGEJO_DOMAIN=localhost  # または適切なIPアドレス
   FORGEJO_ROOT_URL=http://localhost:3000/  # または適切なURL
   ```

### IPアドレスの確認方法

```bash
# ローカルIPアドレスを確認
ip addr show | grep inet
# または
hostname -I
```

---

## 🔒 セキュリティ

- 機密情報は`.env`ファイルで管理し、`.gitignore`で除外しています。
- `.env.example`に必要な環境変数例を記載しています。

---

## 📄 ライセンス

このプロジェクトは [MIT License](LICENSE) のもとで公開されています。

---

## 📝 その他

ご質問・改善提案はIssueまたはPRでお気軽にどうぞ！
