# The base path is fixed at "/docextract", matching how the Helm chart derives
# DKUBEX_BASE_PATH ("/" + the chart name) for the common case (no nameOverride). Vite needs the
# base path at build time, so it is baked in here rather than at container start.
ARG DKUBEX_BASE_PATH=/docextract

FROM node:22-slim AS frontend-build
ARG DKUBEX_BASE_PATH
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN DKUBEX_BASE_PATH=${DKUBEX_BASE_PATH} npm run build

FROM python:3.12-slim AS backend
WORKDIR /app/backend

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./
COPY --from=frontend-build /src/frontend/dist /app/frontend/dist
COPY docker-entrypoint.sh /app/docker-entrypoint.sh

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/backend/.data \
    && chmod +x /app/docker-entrypoint.sh \
    && chown -R appuser:appuser /app
USER appuser

ENV PORT=8080
EXPOSE 8080

ENTRYPOINT ["/app/docker-entrypoint.sh"]
