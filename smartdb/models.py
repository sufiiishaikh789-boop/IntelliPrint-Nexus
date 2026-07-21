"""
SmartPrint AI - SQLAlchemy Database Models
Complete data model for the smart printing management system.
"""

from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# ---------------------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------------------
DATABASE_URL = "sqlite:///smartprint.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    },
    echo=False,
)

from sqlalchemy import event

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False, default="Student")  # Student / Admin
    status = Column(String(20), nullable=False, default="Active")  # Active / Suspended
    avatar_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    print_jobs = relationship("PrintJob", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class PrintJob(Base):
    __tablename__ = "print_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    document_name = Column(String(256), nullable=False)
    file_path = Column(String(512), nullable=False)
    status = Column(
        String(20), nullable=False, default="Pending"
    )  # Pending / Queued / Printing / Completed / Ready / Collected
    copies = Column(Integer, nullable=False, default=1)
    color_mode = Column(String(10), nullable=False, default="BW")  # Color / BW
    duplex = Column(Boolean, nullable=False, default=False)
    page_range = Column(String(50), nullable=True)  # e.g. "1-5" or "All"
    paper_size = Column(String(10), nullable=False, default="A4")  # A4 / A3 / Letter
    priority = Column(String(10), nullable=False, default="Normal")  # Normal / High / Urgent
    total_pages = Column(Integer, nullable=False, default=1)
    cost_per_page = Column(Float, nullable=False, default=2.0)
    total_cost = Column(Float, nullable=False, default=0.0)
    quality_score = Column(Float, nullable=True)
    printer_id = Column(Integer, ForeignKey("printers.id", ondelete="SET NULL"), nullable=True)
    print_id = Column(String(20), unique=True, nullable=False, index=True)
    qr_code_path = Column(String(512), nullable=True)
    estimated_wait_time = Column(Integer, nullable=True)  # minutes
    submitted_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="print_jobs")
    printer = relationship("Printer", back_populates="print_jobs")
    payments = relationship("Payment", back_populates="job", cascade="all, delete-orphan")
    ai_analysis = relationship("AIAnalysis", back_populates="job", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<PrintJob(id={self.id}, print_id='{self.print_id}', status='{self.status}')>"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("print_jobs.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(String(20), nullable=False, default="UPI")  # UPI / Card / NetBanking
    transaction_id = Column(String(100), unique=True, nullable=False)
    status = Column(String(20), nullable=False, default="Pending")  # Pending / Success / Failed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("PrintJob", back_populates="payments")
    user = relationship("User", back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, amount={self.amount}, status='{self.status}')>"


class Printer(Base):
    __tablename__ = "printers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    status = Column(String(20), nullable=False, default="Online")  # Online / Offline / Maintenance
    location = Column(String(200), nullable=False)
    printer_type = Column(String(50), nullable=False, default="LaserJet")
    total_prints = Column(Integer, nullable=False, default=0)
    toner_level = Column(Float, nullable=False, default=100.0)  # percentage
    error_count = Column(Integer, nullable=False, default=0)
    temperature = Column(Float, nullable=False, default=35.0)  # Celsius
    last_maintenance = Column(DateTime, nullable=True)

    # Relationships
    print_jobs = relationship("PrintJob", back_populates="printer")
    maintenance_logs = relationship("MaintenanceLog", back_populates="printer", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Printer(id={self.id}, name='{self.name}', status='{self.status}')>"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, title='{self.title}', read={self.is_read})>"


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("print_jobs.id", ondelete="CASCADE"), nullable=False, unique=True)
    quality_score = Column(Float, nullable=False, default=0.0)
    is_blurry = Column(Boolean, nullable=False, default=False)
    is_skewed = Column(Boolean, nullable=False, default=False)
    is_low_quality = Column(Boolean, nullable=False, default=False)
    recommendations = Column(Text, nullable=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("PrintJob", back_populates="ai_analysis")

    def __repr__(self) -> str:
        return f"<AIAnalysis(id={self.id}, job_id={self.job_id}, score={self.quality_score})>"


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    printer_id = Column(Integer, ForeignKey("printers.id", ondelete="CASCADE"), nullable=False)
    issue = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="Low")  # Low / Medium / High / Critical
    predicted_failure = Column(Boolean, nullable=False, default=False)
    resolved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    printer = relationship("Printer", back_populates="maintenance_logs")

    def __repr__(self) -> str:
        return f"<MaintenanceLog(id={self.id}, printer_id={self.printer_id}, severity='{self.severity}')>"


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user / assistant
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="chat_messages")

    def __repr__(self) -> str:
        return f"<ChatHistory(id={self.id}, user_id={self.user_id}, role='{self.role}')>"


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create all tables in the database if they don't already exist."""
    Base.metadata.create_all(bind=engine)
