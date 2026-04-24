# Local Development Setup

Runs the full gazeti.AFRICA stack locally using Docker Compose.

## Prerequisites

- Docker Desktop (with Rosetta emulation enabled on Apple Silicon)
- At least 4 GB RAM allocated to Docker

## Services

| Service | Port | Description |
|---|---|---|
| `web` | 8001 | Aleph API (gunicorn) |
| `ui` | 4001 | Aleph UI (React dev server) |
| `elasticsearch` | 9200 | Search index |
| `postgres` | 5433 | Database |
| `rabbitmq` | 5672 / 15672 | Task queue / management UI |
| `redis` | — | Cache |
| `convert-document` | — | Document conversion |

## Setup

**1. Configure environment**

```bash
cp aleph.env.example aleph.env
```

Edit `aleph.env` and fill in the required values (secret key, OAuth credentials, S3 credentials if using S3 storage).

**2. Build the custom Elasticsearch image**

The local stack uses Elasticsearch 6.8 with the `analysis-icu` plugin required by Aleph 3.x:

```bash
docker compose build elasticsearch
```

**3. Start all services**

```bash
docker compose up -d
```

Elasticsearch must be healthy before running the next step. The compose file includes a healthcheck so the `web` service will wait automatically.

**4. Run database migrations and create ES index**

```bash
docker compose exec web aleph upgrade
```

**5. Create an admin user**

```bash
docker compose exec web aleph createuser --admin admin@example.com
```

**6. Access the UI**

- UI: http://localhost:4001
- API: http://localhost:8001/api/2/

## S3 storage and the archive path patch

By default `aleph.env` uses `ALEPH_ARCHIVE_TYPE=file` (local disk) which is fine for development.

If you switch to `ALEPH_ARCHIVE_TYPE=s3`, the `api` and `worker` services load `patches/sitecustomize.py` at startup (via `PYTHONPATH=/opt/gazeti-patches`). This patch ensures Aleph prepends `ALEPH_ARCHIVE_PATH` to every S3 object key it builds. Without it, Aleph 3.x ignores that setting and looks for files at the wrong path in the bucket.

## Stopping

```bash
docker compose down        # keep volumes
docker compose down -v     # also delete all data
```
