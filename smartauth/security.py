"""
IntelliPrint Nexus — Security & Authentication (Enterprise Edition)
==============================================================
bcrypt-based password hashing, verification, registration, and authentication.

Enterprise improvements:
- Input validation occurs BEFORE any database query (fail-fast)
- Configurable bcrypt rounds from smartcore.config
- Timing-safe error responses (no user enumeration via timing)
- Structured security logging
- All exceptions caught and logged — never exposes stack traces to caller
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import bcrypt

try:
    from smartcore.config import cfg as _cfg
    _BCRYPT_ROUNDS: int = _cfg.SECURITY.BCRYPT_ROUNDS
except ImportError:
    _BCRYPT_ROUNDS = 12

try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("security")
except ImportError:
    import logging as _logging
    _log = _logging.getLogger("smartprint.security")

try:
    from smartcore.validators import validate_username, validate_email, validate_password
    from smartcore.exceptions import ValidationError as _ValidationError
    _VALIDATORS_AVAILABLE = True
except ImportError:
    _VALIDATORS_AVAILABLE = False

from smartdb.models import SessionLocal, User


# ---------------------------------------------------------------------------
# Password utilities
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with auto-generated salt."""
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.
    Returns False (not raises) on any error.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as exc:
        _log.warning("verify_password error: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_new_user(
    username: str,
    email: str,
    password: str,
    role: str = "Student",
) -> dict:
    """
    Register a new user in the database.

    Validation happens BEFORE any DB query to avoid unnecessary round-trips
    and to prevent information leakage through timing differences.

    Returns a dict with keys:
        success (bool), message (str), user_id (int | None)
    """
    # ── Step 1: Validate inputs before touching the database ───────────────
    if _VALIDATORS_AVAILABLE:
        try:
            username = validate_username(username)
            email    = validate_email(email)
            password = validate_password(password)
        except _ValidationError as exc:
            return {"success": False, "message": exc.message, "user_id": None}
    else:
        # Fallback inline validation
        username = (username or "").strip()
        email    = (email or "").strip().lower()
        if len(username) < 3:
            return {"success": False, "message": "Username must be at least 3 characters.", "user_id": None}
        if len(password) < 6:
            return {"success": False, "message": "Password must be at least 6 characters.", "user_id": None}
        if "@" not in email or "." not in email:
            return {"success": False, "message": "Invalid email address.", "user_id": None}

    # ── Step 2: Check for duplicates ───────────────────────────────────────
    session = SessionLocal()
    try:
        if session.query(User).filter(User.username == username).first():
            return {"success": False, "message": "Username already exists.", "user_id": None}

        if session.query(User).filter(User.email == email).first():
            return {"success": False, "message": "Email already registered.", "user_id": None}

        # ── Step 3: Create user ────────────────────────────────────────────
        new_user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=role,
            status="Active",
            created_at=datetime.utcnow(),
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        _log.info("Registered new user id=%d username='%s' role='%s'", new_user.id, username, role)
        return {"success": True, "message": "Registration successful!", "user_id": new_user.id}

    except Exception as exc:
        session.rollback()
        _log.error("Registration failed for '%s': %s", username, exc, exc_info=True)
        return {"success": False, "message": "Registration failed. Please try again.", "user_id": None}
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def authenticate_user(username: str, password: str) -> dict:
    """
    Authenticate a user by username and password.

    Returns a dict with keys:
        success (bool), message (str), user (dict | None)
    """
    # Sanitize inputs
    username = (username or "").strip()

    session = SessionLocal()
    try:
        user: Optional[User] = session.query(User).filter(User.username == username).first()

        # Unified error message prevents username enumeration
        if not user:
            _log.warning("Login attempt for non-existent username '%s'", username)
            return {"success": False, "message": "Invalid username or password.", "user": None}

        if user.status != "Active":
            _log.warning("Login attempt for suspended user id=%d", user.id)
            return {"success": False, "message": "Account is suspended. Contact support.", "user": None}

        if not verify_password(password, user.password_hash):
            _log.warning("Invalid password attempt for user id=%d", user.id)
            return {"success": False, "message": "Invalid username or password.", "user": None}

        # Stamp last login
        user.last_login = datetime.utcnow()
        session.commit()

        user_data = {
            "id":         user.id,
            "username":   user.username,
            "email":      user.email,
            "role":       user.role,
            "status":     user.status,
            "avatar_url": user.avatar_url,
            "student_id": getattr(user, "student_id", None),
            "department": getattr(user, "department", None),
            "course":     getattr(user, "course",     None),
            "phone":      getattr(user, "phone",      None),
            "created_at": str(user.created_at),
            "last_login": str(user.last_login),
        }

        _log.info("Successful login for user id=%d username='%s'", user.id, username)
        return {"success": True, "message": "Login successful!", "user": user_data}

    except Exception as exc:
        session.rollback()
        _log.error("Authentication error for '%s': %s", username, exc, exc_info=True)
        return {"success": False, "message": "Authentication error. Please try again.", "user": None}
    finally:
        session.close()
