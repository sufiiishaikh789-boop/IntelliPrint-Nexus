"""
SmartPrint AI - Security & Password Management
bcrypt-based password hashing, verification, registration, and authentication.
"""

from datetime import datetime
from typing import Optional

import bcrypt

from smartdb.models import SessionLocal, User


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with auto-generated salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def register_new_user(
    username: str,
    email: str,
    password: str,
    role: str = "Student",
) -> dict:
    """
    Register a new user in the database.

    Returns a dict with keys:
        success (bool), message (str), user_id (int | None)
    """
    session = SessionLocal()
    try:
        # Check for existing username
        existing_user = session.query(User).filter(User.username == username).first()
        if existing_user:
            return {"success": False, "message": "Username already exists.", "user_id": None}

        # Check for existing email
        existing_email = session.query(User).filter(User.email == email).first()
        if existing_email:
            return {"success": False, "message": "Email already registered.", "user_id": None}

        # Validate inputs
        if len(username) < 3:
            return {"success": False, "message": "Username must be at least 3 characters.", "user_id": None}
        if len(password) < 6:
            return {"success": False, "message": "Password must be at least 6 characters.", "user_id": None}
        if "@" not in email or "." not in email:
            return {"success": False, "message": "Invalid email address.", "user_id": None}

        new_user = User(
            username=username.strip(),
            email=email.strip().lower(),
            password_hash=hash_password(password),
            role=role,
            status="Active",
            created_at=datetime.utcnow(),
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return {"success": True, "message": "Registration successful!", "user_id": new_user.id}
    except Exception as exc:
        session.rollback()
        return {"success": False, "message": f"Registration failed: {exc}", "user_id": None}
    finally:
        session.close()


def authenticate_user(username: str, password: str) -> dict:
    """
    Authenticate a user by username and password.

    Returns a dict with keys:
        success (bool), message (str), user (dict | None)
    """
    session = SessionLocal()
    try:
        user: Optional[User] = (
            session.query(User).filter(User.username == username).first()
        )
        if not user:
            return {"success": False, "message": "User not found.", "user": None}

        if user.status != "Active":
            return {"success": False, "message": "Account is suspended.", "user": None}

        if not verify_password(password, user.password_hash):
            return {"success": False, "message": "Invalid password.", "user": None}

        # Update last login timestamp
        user.last_login = datetime.utcnow()
        session.commit()

        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "status": user.status,
            "avatar_url": user.avatar_url,
            "created_at": str(user.created_at),
            "last_login": str(user.last_login),
        }

        return {"success": True, "message": "Login successful!", "user": user_data}
    except Exception as exc:
        session.rollback()
        return {"success": False, "message": f"Authentication error: {exc}", "user": None}
    finally:
        session.close()
