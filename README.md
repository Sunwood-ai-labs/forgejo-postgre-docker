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

3. サービスを起動
   ```bash
   docker-compose up -d
   ```

詳細な手順は[インストールガイド](docs/INSTALL.md)を参照してください。

---

## 🧑‍💻 使い方

### Forgejo Runnerの登録例

```bash
docker-compose exec runner forgejo-runner register \
  --no-interactive \
  --token <YOUR_TOKEN> \
  --name <RUNNER_NAME> \
  --instance http://server:3000 \
  --labels docker:docker://ghcr.io/catthehacker/ubuntu:act-22.04
```

### Forgejo Runnerデーモンの実行

```bash
docker-compose exec runner forgejo-runner daemon
```

---

## 📂 ディレクトリ構成

```
forgejo-postgre-docker/
├── certs/           # SSL証明書等を格納
├── .env.example     # 環境変数サンプル
├── docker-compose.yml
├── README.md
└── ...
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
