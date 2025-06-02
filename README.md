# forgejo-postgre-docker

```bash
# 2. Runner登録
docker-compose exec runner forgejo-runner register \
  --no-interactive \
  --token ZZZZZZZZZZZ \
  --name claude-runner \
  --instance http://server:3000 \
  --labels docker:docker://ghcr.io/catthehacker/ubuntu:act-22.04

  ```