"""Tests for register / login / tokens."""
import pytest

from app import config, database
from app.errors import AuthError, ConflictError, ForbiddenError, ValidationError
from app.services import app_user_service, auth_service


@pytest.fixture(autouse=True)
def fast_hashing(monkeypatch):
    monkeypatch.setattr(config, "PASSWORD_ITERATIONS", 1_000)


def test_register_and_login():
    user = auth_service.register("a@example.com", "Asha", "secret123")
    result = auth_service.login("a@example.com", "secret123")
    assert result["token_type"] == "bearer"
    assert result["user"]["id"] == user.id


def test_login_is_case_insensitive_on_email():
    auth_service.register("Case@Example.com", "Case", "secret123")
    assert auth_service.login("CASE@example.com", "secret123")["access_token"]


def test_wrong_password_rejected():
    auth_service.register("b@example.com", "Bala", "secret123")
    with pytest.raises(AuthError):
        auth_service.login("b@example.com", "wrong-pass1")


def test_unknown_email_rejected():
    with pytest.raises(AuthError):
        auth_service.login("nobody@example.com", "secret123")


def test_weak_passwords_rejected():
    for weak in ["short1", "12345678", "abcdefgh"]:
        with pytest.raises(ValidationError):
            auth_service.register(f"{weak}@example.com", "Weak", weak)


def test_duplicate_email_rejected():
    auth_service.register("c@example.com", "Chetan", "secret123")
    with pytest.raises(ConflictError):
        auth_service.register("c@example.com", "Chetan Again", "secret123")


def test_token_resolves_to_user():
    user = auth_service.register("d@example.com", "Divya", "secret123")
    token = auth_service.login("d@example.com", "secret123")["access_token"]
    assert auth_service.current_user(token).id == user.id


def test_invalid_token_rejected():
    with pytest.raises(AuthError):
        auth_service.current_user("not-a-real-token")


def test_expired_token_rejected():
    auth_service.register("e@example.com", "Esha", "secret123")
    token = auth_service.login("e@example.com", "secret123")["access_token"]
    with database.session() as conn:
        conn.execute("UPDATE auth_tokens SET expires_at = '2000-01-01T00:00:00' WHERE token = ?", (token,))
    with pytest.raises(AuthError):
        auth_service.current_user(token)


def test_logout_invalidates_token():
    auth_service.register("f@example.com", "Farhan", "secret123")
    token = auth_service.login("f@example.com", "secret123")["access_token"]
    auth_service.logout(token)
    with pytest.raises(AuthError):
        auth_service.current_user(token)


def test_disabled_user_cannot_login():
    user = auth_service.register("g@example.com", "Gita", "secret123")
    app_user_service.update(user.id, {"is_active": False})
    with pytest.raises(AuthError):
        auth_service.login("g@example.com", "secret123")


def test_change_password():
    user = auth_service.register("h@example.com", "Hari", "secret123")
    auth_service.change_password(user.id, "secret123", "newsecret456")
    with pytest.raises(AuthError):
        auth_service.login("h@example.com", "secret123")
    assert auth_service.login("h@example.com", "newsecret456")["access_token"]


def test_change_password_needs_old_password():
    user = auth_service.register("i@example.com", "Indu", "secret123")
    with pytest.raises(AuthError):
        auth_service.change_password(user.id, "wrong-old1", "newsecret456")


def test_require_role():
    user = auth_service.register("j@example.com", "Jai", "secret123")
    auth_service.require_role(user, "commuter")
    with pytest.raises(ForbiddenError):
        auth_service.require_role(user, "admin")
