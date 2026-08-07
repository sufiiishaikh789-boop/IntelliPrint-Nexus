"""
IntelliPrint Nexus — SQLAlchemy Database Models
==========================================
Complete data model for the intelligent printing management system.

Enterprise upgrades in this version:
- Composite indexes on hot query patterns (user_id+status, printer_id+status)
- PRAGMA tuning: WAL, cache_size, temp_store, mmap_size, foreign_keys ON
- ``updated_at`` timestamps on User and PrintJob for audit trails
- Connection pool settings configured from smartcore.config
- Thread-safe check_same_thread=False with WAL journal mode
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Index, Integer, String, Text, event, text,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from sqlalchemy import create_engine

# ── Configuration (imported lazily to avoid circular deps at startup) ──────
try:
    from smartcore.config import cfg as _cfg
    _DB_URL = _cfg.DB.URL
    _TIMEOUT = _cfg.DB.TIMEOUT
    _ECHO = _cfg.DB.ECHO
    _POOL_RECYCLE = _cfg.DB.POOL_RECYCLE
    _POOL_PRE_PING = _cfg.DB.POOL_PRE_PING
    _CACHE_KB = _cfg.DB.CACHE_SIZE_KB
    _TEMP_STORE = _cfg.DB.TEMP_STORE
    _MMAP = _cfg.DB.MMAP_SIZE
except ImportError:
    _DB_URL = "sqlite:///smartprint.db"
    _TIMEOUT = 30
    _ECHO = False
    _POOL_RECYCLE = 3600
    _POOL_PRE_PING = True
    _CACHE_KB = 65536
    _TEMP_STORE = 2
    _MMAP = 268435456

# ---------------------------------------------------------------------------
# Engine — SQLite WAL with full PRAGMA tuning
# ---------------------------------------------------------------------------

engine = create_engine(
    _DB_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": _TIMEOUT,
    },
    echo=_ECHO,
    pool_recycle=_POOL_RECYCLE,
    pool_pre_ping=_POOL_PRE_PING,
)


@event.listens_for(engine, "connect")
def _configure_sqlite(dbapi_connection, connection_record) -> None:
    """Apply all SQLite PRAGMAs on every new connection."""
    cursor = dbapi_connection.cursor()
    pragmas = [
        ("journal_mode",  "WAL"),           # concurrent reads + writes
        ("synchronous",   "NORMAL"),         # fsync on checkpoints only
        ("foreign_keys",  "ON"),             # enforce FK constraints
        ("cache_size",    f"-{_CACHE_KB}"), # negative = kibibytes
        ("temp_store",    str(_TEMP_STORE)), # 2 = MEMORY
        ("mmap_size",     str(_MMAP)),       # memory-mapped I/O
        ("busy_timeout",  "5000"),           # wait up to 5 s on lock
    ]
    for pragma, value in pragmas:
        try:
            cursor.execute(f"PRAGMA {pragma}={value}")
        except Exception:
            pass
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# ORM Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(Base):
    """Platform user — Student or Admin."""

    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    username      = Column(String(50),  unique=True, nullable=False)
    email         = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role          = Column(String(20),  nullable=False, default="Student")  # Student / Admin
    status        = Column(String(20),  nullable=False, default="Active")   # Active / Suspended
    avatar_url    = Column(String(512), nullable=True)
    # Extended student profile
    student_id    = Column(String(30),  nullable=True)
    department    = Column(String(100), nullable=True)
    course        = Column(String(100), nullable=True)
    phone         = Column(String(20),  nullable=True)
    # Preferences JSON blob
    preferences   = Column(Text,        nullable=True)
    created_at    = Column(DateTime,    default=datetime.utcnow, nullable=False)
    updated_at    = Column(DateTime,    default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    last_login    = Column(DateTime,    nullable=True)

    # Relationships
    print_jobs    = relationship("PrintJob",    back_populates="user", cascade="all, delete-orphan", lazy="select")
    payments      = relationship("Payment",     back_populates="user", cascade="all, delete-orphan", lazy="select")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan", lazy="select")
    chat_messages = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan", lazy="select")

    # Indexes
    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_email",    "email"),
        Index("ix_users_role",     "role"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class PrintJob(Base):
    """A single document print request."""

    __tablename__ = "print_jobs"

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    user_id              = Column(Integer, ForeignKey("users.id",    ondelete="CASCADE"), nullable=False)
    document_name        = Column(String(256), nullable=False)
    file_path            = Column(String(512), nullable=False)
    status               = Column(String(20),  nullable=False, default="Pending")
    # Pending / Queued / Preparing / Printing / Completed / Ready / Collected / Cancelled / Failed
    copies               = Column(Integer, nullable=False, default=1)
    color_mode           = Column(String(10),  nullable=False, default="BW")     # Color / BW
    duplex               = Column(Boolean, nullable=False, default=False)
    page_range           = Column(String(50),  nullable=True)
    paper_size           = Column(String(10),  nullable=False, default="A4")
    priority             = Column(String(10),  nullable=False, default="Normal") # Normal / High / Urgent
    total_pages          = Column(Integer, nullable=False, default=1)
    cost_per_page        = Column(Float,   nullable=False, default=2.0)
    total_cost           = Column(Float,   nullable=False, default=0.0)
    quality_score        = Column(Float,   nullable=True)
    printer_id           = Column(Integer, ForeignKey("printers.id", ondelete="SET NULL"), nullable=True)
    print_id             = Column(String(20),  unique=True, nullable=False)
    qr_code_path         = Column(String(512), nullable=True)
    pickup_id            = Column(String(30),  nullable=True)
    preview_pdf_path     = Column(String(512), nullable=True)
    estimated_wait_time  = Column(Integer, nullable=True)          # minutes
    print_started_at     = Column(DateTime, nullable=True)
    job_timeline         = Column(Text,    nullable=True)          # JSON list
    document_fingerprint = Column(String(64), nullable=True)       # SHA-256
    is_bookmarked        = Column(Boolean, nullable=False, default=False)
    reprint_count        = Column(Integer, nullable=False, default=0)
    submitted_at         = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at           = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    completed_at         = Column(DateTime, nullable=True)

    # Relationships
    user       = relationship("User",        back_populates="print_jobs")
    printer    = relationship("Printer",     back_populates="print_jobs")
    payments   = relationship("Payment",     back_populates="job",        cascade="all, delete-orphan")
    ai_analysis = relationship("AIAnalysis", back_populates="job",        uselist=False, cascade="all, delete-orphan")

    # Composite indexes on the most frequent filter patterns
    __table_args__ = (
        Index("ix_pj_user_status",    "user_id",    "status"),
        Index("ix_pj_printer_status", "printer_id", "status"),
        Index("ix_pj_submitted_at",   "submitted_at"),
        Index("ix_pj_print_id",       "print_id"),
        Index("ix_pj_fingerprint",    "document_fingerprint"),
        Index("ix_pj_user_bookmark",  "user_id", "is_bookmarked"),
    )

    def __repr__(self) -> str:
        return f"<PrintJob(id={self.id}, print_id='{self.print_id}', status='{self.status}')>"


class Payment(Base):
    """Payment record linked to a print job."""

    __tablename__ = "payments"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    job_id         = Column(Integer, ForeignKey("print_jobs.id", ondelete="CASCADE"), nullable=False)
    user_id        = Column(Integer, ForeignKey("users.id",      ondelete="CASCADE"), nullable=False)
    amount         = Column(Float,  nullable=False)
    method         = Column(String(20), nullable=False, default="UPI")  # UPI / Card / NetBanking
    transaction_id = Column(String(100), unique=True, nullable=False)
    status         = Column(String(20),  nullable=False, default="Pending")
    # Pending / Success / Failed / Refunded
    notes          = Column(Text, nullable=True)   # refund reason, webhook payload, etc.
    created_at     = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    # Relationships
    job  = relationship("PrintJob", back_populates="payments")
    user = relationship("User",     back_populates="payments")

    __table_args__ = (
        Index("ix_pay_job_id",        "job_id"),
        Index("ix_pay_user_id",       "user_id"),
        Index("ix_pay_transaction_id","transaction_id"),
        Index("ix_pay_status",        "status"),
    )

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, amount={self.amount}, status='{self.status}')>"


class Printer(Base):
    """Physical or virtual printer registered in the system."""

    __tablename__ = "printers"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    name             = Column(String(100), unique=True, nullable=False)
    status           = Column(String(20),  nullable=False, default="Online")
    # Online / Offline / Maintenance / Idle / Busy
    location         = Column(String(200), nullable=False)
    printer_type     = Column(String(50),  nullable=False, default="LaserJet")
    total_prints     = Column(Integer, nullable=False, default=0)
    toner_level      = Column(Float,   nullable=False, default=100.0)
    error_count      = Column(Integer, nullable=False, default=0)
    temperature      = Column(Float,   nullable=False, default=35.0)
    pages_per_minute = Column(Integer, nullable=False, default=20)
    last_maintenance = Column(DateTime, nullable=True)
    last_seen_at     = Column(DateTime, nullable=True)    # heartbeat timestamp
    # True when an admin has manually set this printer's status.
    # The PrinterHeartbeatWorker must NEVER override a manual setting.
    manual_override  = Column(Boolean, nullable=False, default=False, server_default="0")

    # Relationships
    print_jobs       = relationship("PrintJob",       back_populates="printer")
    maintenance_logs = relationship("MaintenanceLog", back_populates="printer", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_printer_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Printer(id={self.id}, name='{self.name}', status='{self.status}')>"


class Notification(Base):
    """User notification message."""

    __tablename__ = "notifications"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    user_id           = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title             = Column(String(200), nullable=False)
    message           = Column(Text,        nullable=False)
    notification_type = Column(String(30),  nullable=True, default="info")
    # info / success / warning / error
    is_read           = Column(Boolean, nullable=False, default=False)
    created_at        = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("ix_notif_user_read", "user_id", "is_read"),
        Index("ix_notif_created",   "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, title='{self.title}', read={self.is_read})>"


class AIAnalysis(Base):
    """AI quality analysis result for a print job."""

    __tablename__ = "ai_analyses"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    job_id           = Column(Integer, ForeignKey("print_jobs.id", ondelete="CASCADE"), nullable=False, unique=True)
    quality_score    = Column(Float,   nullable=False, default=0.0)
    is_blurry        = Column(Boolean, nullable=False, default=False)
    is_skewed        = Column(Boolean, nullable=False, default=False)
    is_low_quality   = Column(Boolean, nullable=False, default=False)
    recommendations  = Column(Text,    nullable=True)
    analyzed_at      = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("PrintJob", back_populates="ai_analysis")

    def __repr__(self) -> str:
        return f"<AIAnalysis(id={self.id}, job_id={self.job_id}, score={self.quality_score})>"


class MaintenanceLog(Base):
    """Printer maintenance and fault record."""

    __tablename__ = "maintenance_logs"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    printer_id       = Column(Integer, ForeignKey("printers.id", ondelete="CASCADE"), nullable=False)
    issue            = Column(Text,    nullable=False)
    severity         = Column(String(20), nullable=False, default="Low")
    # Low / Medium / High / Critical
    predicted_failure = Column(Boolean, nullable=False, default=False)
    resolved         = Column(Boolean, nullable=False, default=False)
    created_at       = Column(DateTime, default=datetime.utcnow)

    # Relationships
    printer = relationship("Printer", back_populates="maintenance_logs")

    __table_args__ = (
        Index("ix_mlog_printer", "printer_id"),
        Index("ix_mlog_severity", "severity"),
    )

    def __repr__(self) -> str:
        return f"<MaintenanceLog(id={self.id}, printer_id={self.printer_id}, severity='{self.severity}')>"


class ChatHistory(Base):
    """AI assistant chat message history."""

    __tablename__ = "chat_history"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role       = Column(String(20), nullable=False)    # user / assistant
    message    = Column(Text,       nullable=False)
    created_at = Column(DateTime,   default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="chat_messages")

    __table_args__ = (
        Index("ix_chat_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ChatHistory(id={self.id}, user_id={self.user_id}, role='{self.role}')>"


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create all tables and apply safe column migrations."""
    Base.metadata.create_all(bind=engine)
    _safe_add_columns()


def _safe_add_columns() -> None:
    """
    Add new columns to existing tables without data loss (SQLite safe).
    Each migration is wrapped individually so one failure does not
    prevent subsequent migrations from running.
    """
    migrations = [
        # print_jobs additions
        ("print_jobs", "pickup_id",             "VARCHAR(30)"),
        ("print_jobs", "preview_pdf_path",      "VARCHAR(512)"),
        ("print_jobs", "print_started_at",      "DATETIME"),
        ("print_jobs", "job_timeline",          "TEXT"),
        ("print_jobs", "document_fingerprint",  "VARCHAR(64)"),
        ("print_jobs", "is_bookmarked",         "BOOLEAN DEFAULT 0"),
        ("print_jobs", "reprint_count",         "INTEGER DEFAULT 0"),
        ("print_jobs", "updated_at",            "DATETIME"),
        # printers additions
        ("printers",   "pages_per_minute",      "INTEGER DEFAULT 20"),
        ("printers",   "last_seen_at",          "DATETIME"),
        # users additions
        ("users",      "student_id",            "VARCHAR(30)"),
        ("users",      "department",            "VARCHAR(100)"),
        ("users",      "course",                "VARCHAR(100)"),
        ("users",      "phone",                 "VARCHAR(20)"),
        ("users",      "preferences",           "TEXT"),
        ("users",      "updated_at",            "DATETIME"),
        # notifications additions
        ("notifications", "notification_type",  "VARCHAR(30) DEFAULT 'info'"),
        # payments additions
        ("payments",   "notes",                 "TEXT"),
        ("payments",   "updated_at",            "DATETIME"),
    ]
    try:
        with engine.connect() as conn:
            for table, col, col_type in migrations:
                try:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                    conn.commit()
                except Exception:
                    # Column already exists — safe to ignore
                    pass
    except Exception:
        pass
