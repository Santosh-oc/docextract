import os
import tempfile

_tmp_settings_dir = tempfile.mkdtemp(prefix="docextract_settings_")

os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://document_extractor:document_extractor@localhost:5432/document_extractor_test"
)
os.environ["MINIO_ENDPOINT"] = "localhost:9000"
os.environ["MINIO_ACCESS_KEY"] = "minioadmin"
os.environ["MINIO_SECRET_KEY"] = "minioadmin"
os.environ["MINIO_SECURE"] = "false"
os.environ["MINIO_BUCKET_DOCUMENTS"] = "documents-test"
os.environ["SETTINGS_FILE"] = os.path.join(_tmp_settings_dir, "model_settings.json")
os.environ["MODEL_BASE_URL"] = "http://mock-vision.test/v1"
os.environ["MODEL_NAME"] = "mock-vision-model"
os.environ["MODEL_API_KEY"] = "test-key"

import pytest
import pytest_asyncio
from alembic.config import Config as AlembicConfig
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from alembic import command

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run_migrations():
    cfg = AlembicConfig(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    command.upgrade(cfg, "head")


_run_migrations()

from app.db import SessionLocal, engine
from app.main import app
from app.storage.minio_storage import get_object_storage


@pytest.fixture(scope="session", autouse=True)
def _ensure_test_bucket():
    storage = get_object_storage()
    yield storage


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables():
    yield
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE TABLE extraction_results, extraction_fields, extractions, "
                "document_sections, documents RESTART IDENTITY CASCADE"
            )
        )


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
def db_session_factory():
    return SessionLocal
