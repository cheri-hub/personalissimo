import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-123")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db import Base, get_db
from app.main import create_app
from app.security import login_ip_limiter, login_limiter
from tests.helpers import registrar_e_logar


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(engine):
    application = create_app()

    def _get_db():
        with Session(engine) as session:
            yield session

    application.dependency_overrides[get_db] = _get_db
    login_limiter.reset()
    login_ip_limiter.reset()
    return TestClient(application)


@pytest.fixture
def auth(client):
    return registrar_e_logar(client)
