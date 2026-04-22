# Deployment Guide (Dokku)

This guide covers deploying gazeti.AFRICA on a Ubuntu server using [Dokku](https://dokku.com).

## Architecture

| Dokku app | Dockerfile | Description |
|---|---|---|
| `gazeti-web` | `gazeti-api/Dockerfile` | Aleph API (gunicorn) |
| `gazeti-ui` | `gazeti-ui/Dockerfile` | Aleph UI (React, served by nginx) |
| `gazeti-worker` | `gazeti-worker/Dockerfile` | Celery task worker |
| `gazeti-beat` | `gazeti-beat/Dockerfile` | Celery beat scheduler |
| `gazeti-convert` | `gazeti-convert/Dockerfile` | Document conversion service |

Each Dockerfile uses the repo root as its build context so that `patches/sitecustomize.py` is accessible to all services that need it.

## Prerequisites

- Ubuntu 20.04+ server with Dokku installed
- Domain names pointing to the server (`gazeti.africa`, `api.gazeti.africa`)
- AWS OpenSearch domain (Elasticsearch 6.8 compatible)
- PostgreSQL 11 (Aleph 3.0.3 requires PG11 — PG12+ removed the `pg_catalog.pg_constraints.consrc` column that SQLAlchemy queries)

## 1. Install Dokku plugins

```bash
sudo dokku plugin:install https://github.com/dokku/dokku-postgres.git --name postgres
sudo dokku plugin:install https://github.com/dokku/dokku-redis.git redis
sudo dokku plugin:install https://github.com/dokku/dokku-rabbitmq.git rabbitmq
sudo dokku plugin:install https://github.com/dokku/dokku-letsencrypt.git
```

> Do **not** install an Elasticsearch plugin — use AWS OpenSearch instead to avoid OOM on small instances.

## 2. Provision backing services

```bash
# PostgreSQL 11 (required — do not use PG12+)
dokku postgres:create gazeti-db --image-version 11

# Redis and RabbitMQ
dokku redis:create gazeti-cache
dokku rabbitmq:create gazeti-mq
```

## 3. Create Dokku apps

```bash
for app in gazeti-web gazeti-ui gazeti-worker gazeti-beat gazeti-convert; do
  dokku apps:create $app
done
```

## 4. Link backing services

```bash
dokku postgres:link gazeti-db gazeti-web
dokku postgres:link gazeti-db gazeti-worker
dokku postgres:link gazeti-db gazeti-beat

dokku redis:link gazeti-cache gazeti-web
dokku redis:link gazeti-cache gazeti-worker

dokku rabbitmq:link gazeti-mq gazeti-web
dokku rabbitmq:link gazeti-mq gazeti-worker
dokku rabbitmq:link gazeti-mq gazeti-beat
```

## 5. Point each app to its Dockerfile

Dokku looks for `Dockerfile` in the repo root by default. Override this for each app:

```bash
dokku builder-dockerfile:set gazeti-web dockerfile-path gazeti-api/Dockerfile
dokku builder-dockerfile:set gazeti-ui dockerfile-path gazeti-ui/Dockerfile
dokku builder-dockerfile:set gazeti-worker dockerfile-path gazeti-worker/Dockerfile
dokku builder-dockerfile:set gazeti-beat dockerfile-path gazeti-beat/Dockerfile
dokku builder-dockerfile:set gazeti-convert dockerfile-path gazeti-convert/Dockerfile
```

## 6. Configure environment variables

Set the following on `gazeti-web`, `gazeti-worker`, and `gazeti-beat` (replace placeholders):

```bash
dokku config:set gazeti-web \
  ALEPH_SECRET_KEY=<random-secret> \
  ALEPH_APP_NAME=opengazettes_ke \
  ALEPH_APP_TITLE="gazeti.AFRICA" \
  ALEPH_APP_URL=https://api.gazeti.africa \
  ALEPH_URL_SCHEME=https \
  ALEPH_LOGO=https://raw.githubusercontent.com/gazeti/gazeti.AFRICA/e361fa9daf71a05a25b7f715c3cbda7e7719ce21/img/logo.png \
  ALEPH_FAVICON=https://gazeti.africa/favicon.ico \
  ALEPH_PASSWORD_LOGIN=true \
  ALEPH_CORS_ORIGINS=https://gazeti.africa \
  ALEPH_ELASTICSEARCH_URI=<aws-opensearch-endpoint> \
  ALEPH_ARCHIVE_TYPE=s3 \
  ALEPH_ARCHIVE_BUCKET=<s3-bucket> \
  ALEPH_ARCHIVE_PATH=aleph \
  AWS_ACCESS_KEY_ID=<key> \
  AWS_SECRET_ACCESS_KEY=<secret> \
  AWS_REGION=eu-west-1 \
  ALEPH_DEFAULT_LANGUAGE=en \
  ALEPH_CACHE=true \
  ALEPH_QUEUE=true \
  C_FORCE_ROOT=true
```

Copy the same config to worker and beat:

```bash
dokku config:set gazeti-worker $(dokku config:export --format shell gazeti-web | grep -v DATABASE_URL | grep -v REDIS_URL | grep -v RABBITMQ_URL)
dokku config:set gazeti-beat $(dokku config:export --format shell gazeti-web | grep -v DATABASE_URL | grep -v RABBITMQ_URL)
```

For `gazeti-ui`, set only:

```bash
dokku config:set gazeti-ui \
  REACT_APP_API_ENDPOINT=https://api.gazeti.africa/api/2/
```

## 7. Configure domains and ports

```bash
dokku domains:set gazeti-web api.gazeti.africa
dokku domains:set gazeti-ui gazeti.africa

dokku proxy:ports-set gazeti-web http:80:5000
dokku proxy:ports-set gazeti-ui http:80:4001
dokku proxy:ports-set gazeti-convert http:80:3000
```

## 8. Deploy

Images are built and pushed to DockerHub by CI. Deploy each app by pulling the image directly:

```bash
dokku git:from-image gazeti-web codeforafrica/gazeti-web:3.0.3
dokku git:from-image gazeti-ui codeforafrica/gazeti-ui:3.0.3
dokku git:from-image gazeti-worker codeforafrica/gazeti-worker:3.0.3
dokku git:from-image gazeti-beat codeforafrica/gazeti-beat:3.0.3
dokku git:from-image gazeti-convert codeforafrica/gazeti-convert:3.0.3
```

To deploy a newer image, update the tag and re-run the relevant `git:from-image` command.

## 9. Run database migrations

Run once after the first deploy:

```bash
dokku run gazeti-web aleph upgrade
```

## 10. Enable HTTPS (Let's Encrypt)

```bash
dokku letsencrypt:set --global email support@codeforafrica.org
dokku letsencrypt:enable gazeti-web
dokku letsencrypt:enable gazeti-ui
dokku letsencrypt:cron-job --add
```

## S3 storage and the archive path patch

The `gazeti-api` and `gazeti-worker` images include `patches/sitecustomize.py`, loaded automatically at Python startup via `PYTHONPATH=/opt/gazeti-patches`.

This patch prepends `ALEPH_ARCHIVE_PATH` (e.g. `aleph`) to every S3 object key that Aleph builds. Aleph 3.x ignores this setting natively, which means without the patch it would read and write files at the wrong path in the S3 bucket. The patch is a no-op when `ALEPH_ARCHIVE_TYPE=file`.

## Scaling

```bash
dokku ps:scale gazeti-worker worker=2
dokku ps:scale gazeti-web web=4
```
