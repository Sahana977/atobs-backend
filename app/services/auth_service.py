"""
Simple email + password auth with bearer tokens.

Passwords are hashed with PBKDF2-SHA256 (Python standard library, no extra packages).
Tokens are random strings stored in SQLite with an expiry time.
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from app import config, database
from app.errors import AuthError, ForbiddenError, ValidationError
from app.models.app_user import AppUser
from app.repositories import app_user_repo
from app.services import app_user_service

MIN_PASSWORD_LENGTH = 8


def _hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), config.PASSWORD_ITERATIONS)
    return digest.hex()


def _check_password_strength(password: str) -> None:
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError({"password": f"must be at least {MIN_PASSWORD_LENGTH} characters"})
    if password.isdigit() or password.isalpha():
        raise ValidationError({"password": "must contain both letters and numbers"})


def register(email: str, full_name: str, password: str, role: str = "commuter") -> AppUser:
    _check_password_strength(password)
    user = app_user_service.create({"email": email, "full_name": full_name, "role": role})
    salt = secrets.token_hex(16)
    with database.session() as conn:
        conn.execute(
            "INSERT INTO user_credentials (user_id, salt, password_hash) VALUES (?, ?, ?)",
            (user.id, salt, _hash_password(password, salt)),
        )
    return user


def login(email: str, password: str) -> dict:
    with database.session() as conn:
        user = app_user_repo.get_by_email(conn, (email or "").strip().lower())
        creds = conn.execute(
            "SELECT salt, password_hash FROM user_credentials WHERE user_id = ?",
            (user.id if user else -1,),
        ).fetchone()
        if user is None or creds is None:
            raise AuthError("invalid email or password")
        if not hmac.compare_digest(_hash_password(password, creds["salt"]), creds["password_hash"]):
            raise AuthError("invalid email or password")
        if not user.is_active:
            raise AuthError("account is disabled")

        token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(hours=config.TOKEN_TTL_HOURS)
        conn.execute(
            "INSERT INTO auth_tokens (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user.id, expires.isoformat(timespec="seconds")),
        )
    return {"access_token": token, "token_type": "bearer",
            "expires_at": expires.isoformat(timespec="seconds"), "user": user.to_dict()}


def current_user(token: str) -> AppUser:
    if not token:
        raise AuthError("missing token")
    with database.session() as conn:
        row = conn.execute("SELECT user_id, expires_at FROM auth_tokens WHERE token = ?", (token,)).fetchone()
        if row is None:
            raise AuthError("invalid token")
        if datetime.fromisoformat(row["expires_at"]) < datetime.now():
            conn.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
            raise AuthError("token expired")
        user = app_user_repo.get(conn, row["user_id"])
    if user is None or not user.is_active:
        raise AuthError("account not available")
    return user


def logout(token: str) -> None:
    with database.session() as conn:
        conn.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))


def change_password(user_id: int, old_password: str, new_password: str) -> None:
    _check_password_strength(new_password)
    with database.session() as conn:
        creds = conn.execute(
            "SELECT salt, password_hash FROM user_credentials WHERE user_id = ?", (user_id,)).fetchone()
        if creds is None or not hmac.compare_digest(
                _hash_password(old_password, creds["salt"]), creds["password_hash"]):
            raise AuthError("current password is incorrect")
        salt = secrets.token_hex(16)
        conn.execute(
            "UPDATE user_credentials SET salt = ?, password_hash = ? WHERE user_id = ?",
            (salt, _hash_password(new_password, salt), user_id),
        )
        conn.execute("DELETE FROM auth_tokens WHERE user_id = ?", (user_id,))


def require_role(user: AppUser, *roles: str) -> None:
    if user.role not in roles:
        raise ForbiddenError(f"requires role: {' or '.join(roles)}")
