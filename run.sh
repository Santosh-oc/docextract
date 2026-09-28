#!/usr/bin/env bash
# Start the Document Extraction app in the workspace. Publish it first:
#
#   d3x app create --name docextract --display-name "Document Extraction" \
#                  --description "Extract user-defined fields from PDFs with a vision model" \
#                  --icon icon.svg
#
# That writes .dkubex-app.env next to this script. Nothing supervises the app, so this is what
# actually makes the tile serve something — leave it running (tmux/nohup).
set -euo pipefail
cd "$(dirname "$0")"

set -a
. ./.dkubex-app.env
set +a

PGDATA_DIR="$(pwd)/.pgdata"
PGRUN_DIR="$(pwd)/.pgrun"
PG_BIN=/usr/lib/postgresql/18/bin

# --- local PostgreSQL (dev/standalone datastore for this app) ---
if ! "$PG_BIN"/pg_ctl -D "$PGDATA_DIR" status >/dev/null 2>&1; then
  "$PG_BIN"/pg_ctl -D "$PGDATA_DIR" -l .pglogs/postgres.log \
    -o "-p 5432 -k $PGRUN_DIR -h localhost" start
fi

# --- local S3-compatible object storage standing in for MinIO ---
# A real MinIO server is what this app is built against (see backend/app/storage), but MinIO's
# free binary/image distribution was discontinued after this environment was provisioned, so
# local development here runs against moto's S3-API-compatible mock server instead. Point
# MINIO_ENDPOINT/MINIO_ACCESS_KEY/MINIO_SECRET_KEY at a real MinIO deployment in production —
# the storage layer only speaks the generic S3 API and needs no code change to do so.
if ! curl -sf http://localhost:9000/ >/dev/null 2>&1; then
  nohup .venv/bin/python -m moto.server -H 0.0.0.0 -p 9000 > .pglogs/moto.log 2>&1 &
  sleep 1
fi

cd backend
../.venv/bin/alembic upgrade head
cd ..

cd frontend
DKUBEX_BASE_PATH="$DKUBEX_BASE_PATH" npm run build
cd ..

cd backend
# DKUBEX_BASE_PATH is read directly by app.main (see _RootPathMiddleware) rather than passed as
# uvicorn's --root-path: this workspace's nginx forwards the full, unstripped request URI, and
# --root-path would double the prefix on top of that.
exec ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
