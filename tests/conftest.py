"""Every test gets its own fresh, empty SQLite database."""
import pytest

from app import config, database


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    yield
