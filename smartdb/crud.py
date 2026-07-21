"""
SmartPrint AI - CRUD Operations
Complete data-access layer for every model in the system.
"""

from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from smartdb.models import (
    AIAnalysis,
    ChatHistory,
    MaintenanceLog,
    Notification,
    Payment,
    PrintJob,
    Printer,
    SessionLocal,
    User,
)


# ---------------------------------------------------------------------------
# Session helper
# ---------------------------------------------------------------------------

@contextmanager
def get_db():
    """Yield a database session and ensure it is closed after use."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===================================================================
# USER CRUD
# ===================================================================

def create_user(
    username: str,
    email: str,
    password_hash: str,
    role: str = "Student",
) -> User:
    """Create and persist a new User row."""
    with get_db() as db:
        user = User(
            username=username.strip(),
            email=email.strip().lower(),
            password_hash=password_hash,
            role=role,
            status="Active",
            created_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def get_user_by_username(username: str) -> Optional[User]:
    """Fetch a user by their username."""
    with get_db() as db:
        return db.query(User).filter(User.username == username).first()


def get_user_by_email(email: str) -> Optional[User]:
    """Fetch a user by their email address."""
    with get_db() as db:
        return db.query(User).filter(User.email == email.strip().lower()).first()


def get_all_users() -> List[Dict[str, Any]]:
    """Return all users as a list of dicts (safe for serialisation)."""
    with get_db() as db:
        users = db.query(User).order_by(User.created_at.desc()).all()
        return [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "status": u.status,
                "avatar_url": u.avatar_url,
                "created_at": u.created_at,
                "last_login": u.last_login,
            }
            for u in users
        ]


def update_user_last_login(user_id: int) -> None:
    """Set last_login to the current UTC time."""
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.last_login = datetime.utcnow()
            db.commit()


def update_user_credentials(
    user_id: int,
    email: str,
    password_hash: Optional[str] = None,
) -> bool:
    """Update a user's email and optionally their password hash in the database."""
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        user.email = email.strip().lower()
        if password_hash:
            user.password_hash = password_hash
        db.commit()
        return True



# ===================================================================
# PRINT JOB CRUD
# ===================================================================

def create_print_job(
    user_id: int,
    document_name: str,
    file_path: str,
    print_id: str,
    copies: int = 1,
    color_mode: str = "BW",
    duplex: bool = False,
    page_range: Optional[str] = None,
    paper_size: str = "A4",
    priority: str = "Normal",
    total_pages: int = 1,
    cost_per_page: float = 2.0,
    total_cost: float = 0.0,
    quality_score: Optional[float] = None,
    printer_id: Optional[int] = None,
    qr_code_path: Optional[str] = None,
    estimated_wait_time: Optional[int] = None,
) -> Dict[str, Any]:
    """Create a new print job and return its data as a dict."""
    with get_db() as db:
        job = PrintJob(
            user_id=user_id,
            document_name=document_name,
            file_path=file_path,
            print_id=print_id,
            status="Pending",
            copies=copies,
            color_mode=color_mode,
            duplex=duplex,
            page_range=page_range,
            paper_size=paper_size,
            priority=priority,
            total_pages=total_pages,
            cost_per_page=cost_per_page,
            total_cost=total_cost,
            quality_score=quality_score,
            printer_id=printer_id,
            qr_code_path=qr_code_path,
            estimated_wait_time=estimated_wait_time,
            submitted_at=datetime.utcnow(),
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return _job_to_dict(job)


def get_user_jobs(user_id: int) -> List[Dict[str, Any]]:
    """Return all print jobs for a given user, newest first."""
    with get_db() as db:
        jobs = (
            db.query(PrintJob)
            .filter(PrintJob.user_id == user_id)
            .order_by(PrintJob.submitted_at.desc())
            .all()
        )
        return [_job_to_dict(j) for j in jobs]


def get_all_jobs() -> List[Dict[str, Any]]:
    """Return every print job (admin view), newest first."""
    with get_db() as db:
        jobs = db.query(PrintJob).order_by(PrintJob.submitted_at.desc()).all()
        return [_job_to_dict(j) for j in jobs]


def update_job_status(job_id: int, new_status: str) -> bool:
    """Update the status of a print job. Returns True on success."""
    with get_db() as db:
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if not job:
            return False
        job.status = new_status
        if new_status in ("Completed", "Ready", "Collected"):
            job.completed_at = datetime.utcnow()
        db.commit()
        return True


def get_job_by_id(job_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single print job by its primary key."""
    with get_db() as db:
        job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
        return _job_to_dict(job) if job else None


def get_job_by_print_id(print_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single print job by its human-readable print_id (e.g. SP2026-AB12)."""
    with get_db() as db:
        job = db.query(PrintJob).filter(PrintJob.print_id == print_id).first()
        return _job_to_dict(job) if job else None


def _job_to_dict(job: PrintJob) -> Dict[str, Any]:
    """Serialise a PrintJob ORM object to a plain dict."""
    return {
        "id": job.id,
        "user_id": job.user_id,
        "document_name": job.document_name,
        "file_path": job.file_path,
        "status": job.status,
        "copies": job.copies,
        "color_mode": job.color_mode,
        "duplex": job.duplex,
        "page_range": job.page_range,
        "paper_size": job.paper_size,
        "priority": job.priority,
        "total_pages": job.total_pages,
        "pages": job.total_pages,
        "cost_per_page": job.cost_per_page,
        "total_cost": job.total_cost,
        "cost": job.total_cost,
        "quality_score": job.quality_score,
        "printer_id": job.printer_id,
        "print_id": job.print_id,
        "qr_code_path": job.qr_code_path,
        "estimated_wait_time": job.estimated_wait_time,
        "submitted_at": job.submitted_at,
        "created_at": str(job.submitted_at),
        "completed_at": job.completed_at,
    }


# ===================================================================
# PAYMENT CRUD
# ===================================================================

def create_payment(
    job_id: int,
    user_id: int,
    amount: float,
    method: str,
    transaction_id: str,
    status: str = "Pending",
) -> Dict[str, Any]:
    """Create a payment record and return it as a dict."""
    with get_db() as db:
        payment = Payment(
            job_id=job_id,
            user_id=user_id,
            amount=amount,
            method=method,
            transaction_id=transaction_id,
            status=status,
            created_at=datetime.utcnow(),
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return {
            "id": payment.id,
            "job_id": payment.job_id,
            "user_id": payment.user_id,
            "amount": payment.amount,
            "method": payment.method,
            "transaction_id": payment.transaction_id,
            "status": payment.status,
            "created_at": payment.created_at,
        }


def get_payment_by_job(job_id: int) -> Optional[Dict[str, Any]]:
    """Fetch the payment associated with a print job."""
    with get_db() as db:
        payment = db.query(Payment).filter(Payment.job_id == job_id).first()
        if not payment:
            return None
        return {
            "id": payment.id,
            "job_id": payment.job_id,
            "user_id": payment.user_id,
            "amount": payment.amount,
            "method": payment.method,
            "transaction_id": payment.transaction_id,
            "status": payment.status,
            "created_at": payment.created_at,
        }


# ===================================================================
# PRINTER CRUD
# ===================================================================

def get_all_printers() -> List[Dict[str, Any]]:
    """Return all printers as a list of dicts."""
    with get_db() as db:
        printers = db.query(Printer).order_by(Printer.name).all()
        return [_printer_to_dict(p) for p in printers]


def update_printer_status(printer_id: int, new_status: str) -> bool:
    """Update a printer's status. Returns True on success."""
    with get_db() as db:
        printer = db.query(Printer).filter(Printer.id == printer_id).first()
        if not printer:
            return False
        printer.status = new_status
        db.commit()
        return True


def get_best_printer() -> Optional[Dict[str, Any]]:
    """
    Select the best available printer based on:
      1. Online status
      2. Highest toner level
      3. Fewest errors
    Returns None when no printer is available.
    """
    with get_db() as db:
        printer = (
            db.query(Printer)
            .filter(Printer.status == "Online")
            .order_by(Printer.toner_level.desc(), Printer.error_count.asc())
            .first()
        )
        return _printer_to_dict(printer) if printer else None


def _printer_to_dict(printer: Printer) -> Dict[str, Any]:
    """Serialise a Printer ORM object to a plain dict."""
    return {
        "id": printer.id,
        "name": printer.name,
        "status": printer.status,
        "location": printer.location,
        "printer_type": printer.printer_type,
        "total_prints": printer.total_prints,
        "toner_level": printer.toner_level,
        "error_count": printer.error_count,
        "temperature": printer.temperature,
        "last_maintenance": printer.last_maintenance,
    }


# ===================================================================
# NOTIFICATION CRUD
# ===================================================================

def create_notification(user_id: int, title: str, message: str) -> Dict[str, Any]:
    """Create a notification for a user."""
    with get_db() as db:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            is_read=False,
            created_at=datetime.utcnow(),
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return {
            "id": notif.id,
            "user_id": notif.user_id,
            "title": notif.title,
            "message": notif.message,
            "is_read": notif.is_read,
            "created_at": notif.created_at,
        }


def get_user_notifications(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch recent notifications for a user, newest first."""
    with get_db() as db:
        notifs = (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": n.id,
                "user_id": n.user_id,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": str(n.created_at),
            }
            for n in notifs
        ]


def mark_notification_read(notification_id: int) -> bool:
    """Mark a single notification as read. Returns True on success."""
    with get_db() as db:
        notif = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notif:
            return False
        notif.is_read = True
        db.commit()
        return True


def get_unread_count(user_id: int) -> int:
    """Return the number of unread notifications for a user."""
    with get_db() as db:
        return (
            db.query(func.count(Notification.id))
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .scalar()
        ) or 0


# ===================================================================
# AI ANALYSIS CRUD
# ===================================================================

def create_ai_analysis(
    job_id: int,
    quality_score: float,
    is_blurry: bool = False,
    is_skewed: bool = False,
    is_low_quality: bool = False,
    recommendations: Optional[str] = None,
) -> Dict[str, Any]:
    """Create or update an AI analysis record for a print job (upsert)."""
    with get_db() as db:
        # Check if analysis already exists (prevent UNIQUE constraint failure)
        existing = db.query(AIAnalysis).filter(AIAnalysis.job_id == job_id).first()
        if existing:
            # Update existing record
            existing.quality_score = quality_score
            existing.is_blurry = is_blurry
            existing.is_skewed = is_skewed
            existing.is_low_quality = is_low_quality
            existing.recommendations = recommendations
            existing.analyzed_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return {
                "id": existing.id,
                "job_id": existing.job_id,
                "quality_score": existing.quality_score,
                "is_blurry": existing.is_blurry,
                "is_skewed": existing.is_skewed,
                "is_low_quality": existing.is_low_quality,
                "recommendations": existing.recommendations,
                "analyzed_at": existing.analyzed_at,
            }
        
        analysis = AIAnalysis(
            job_id=job_id,
            quality_score=quality_score,
            is_blurry=is_blurry,
            is_skewed=is_skewed,
            is_low_quality=is_low_quality,
            recommendations=recommendations,
            analyzed_at=datetime.utcnow(),
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return {
            "id": analysis.id,
            "job_id": analysis.job_id,
            "quality_score": analysis.quality_score,
            "is_blurry": analysis.is_blurry,
            "is_skewed": analysis.is_skewed,
            "is_low_quality": analysis.is_low_quality,
            "recommendations": analysis.recommendations,
            "analyzed_at": analysis.analyzed_at,
        }



def get_analysis_by_job(job_id: int) -> Optional[Dict[str, Any]]:
    """Fetch the AI analysis for a specific print job."""
    with get_db() as db:
        analysis = db.query(AIAnalysis).filter(AIAnalysis.job_id == job_id).first()
        if not analysis:
            return None
        return {
            "id": analysis.id,
            "job_id": analysis.job_id,
            "quality_score": analysis.quality_score,
            "is_blurry": analysis.is_blurry,
            "is_skewed": analysis.is_skewed,
            "is_low_quality": analysis.is_low_quality,
            "recommendations": analysis.recommendations,
            "analyzed_at": analysis.analyzed_at,
        }


# ===================================================================
# MAINTENANCE LOG CRUD
# ===================================================================

def create_maintenance_log(
    printer_id: int,
    issue: str,
    severity: str = "Low",
    predicted_failure: bool = False,
) -> Dict[str, Any]:
    """Create a maintenance log entry for a printer."""
    with get_db() as db:
        log = MaintenanceLog(
            printer_id=printer_id,
            issue=issue,
            severity=severity,
            predicted_failure=predicted_failure,
            resolved=False,
            created_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return {
            "id": log.id,
            "printer_id": log.printer_id,
            "issue": log.issue,
            "severity": log.severity,
            "predicted_failure": log.predicted_failure,
            "resolved": log.resolved,
            "created_at": log.created_at,
        }


def get_printer_maintenance(printer_id: int) -> List[Dict[str, Any]]:
    """Get maintenance history for a printer, newest first."""
    with get_db() as db:
        logs = (
            db.query(MaintenanceLog)
            .filter(MaintenanceLog.printer_id == printer_id)
            .order_by(MaintenanceLog.created_at.desc())
            .all()
        )
        return [
            {
                "id": log.id,
                "printer_id": log.printer_id,
                "issue": log.issue,
                "severity": log.severity,
                "predicted_failure": log.predicted_failure,
                "resolved": log.resolved,
                "created_at": log.created_at,
            }
            for log in logs
        ]


# ===================================================================
# CHAT HISTORY CRUD
# ===================================================================

def save_chat_message(user_id: int, role: str, message: str) -> Dict[str, Any]:
    """Persist a single chat message (role = 'user' or 'assistant')."""
    with get_db() as db:
        chat = ChatHistory(
            user_id=user_id,
            role=role,
            message=message,
            created_at=datetime.utcnow(),
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return {
            "id": chat.id,
            "user_id": chat.user_id,
            "role": chat.role,
            "message": chat.message,
            "created_at": chat.created_at,
        }


def get_chat_history(user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch chat history for a user, oldest first."""
    with get_db() as db:
        messages = (
            db.query(ChatHistory)
            .filter(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.created_at.asc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": m.id,
                "user_id": m.user_id,
                "role": m.role,
                "message": m.message,
                "created_at": m.created_at,
            }
            for m in messages
        ]


# ===================================================================
# DASHBOARD STATISTICS
# ===================================================================

def get_dashboard_stats() -> Dict[str, Any]:
    """
    Aggregate statistics for the admin dashboard.

    Returns counts and revenue figures.
    """
    with get_db() as db:
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_jobs = db.query(func.count(PrintJob.id)).scalar() or 0
        total_revenue = db.query(func.coalesce(func.sum(PrintJob.total_cost), 0.0)).scalar()

        pending_count = (
            db.query(func.count(PrintJob.id))
            .filter(PrintJob.status == "Pending")
            .scalar()
        ) or 0
        queued_count = (
            db.query(func.count(PrintJob.id))
            .filter(PrintJob.status == "Queued")
            .scalar()
        ) or 0
        printing_count = (
            db.query(func.count(PrintJob.id))
            .filter(PrintJob.status == "Printing")
            .scalar()
        ) or 0
        completed_count = (
            db.query(func.count(PrintJob.id))
            .filter(PrintJob.status.in_(["Completed", "Ready", "Collected"]))
            .scalar()
        ) or 0

        return {
            "total_users": total_users,
            "total_jobs": total_jobs,
            "total_revenue": round(float(total_revenue), 2),
            "pending_count": pending_count,
            "queued_count": queued_count,
            "printing_count": printing_count,
            "completed_count": completed_count,
            "pending": pending_count,
            "queued": queued_count,
            "printing": printing_count,
            "completed": completed_count,
        }


# ===================================================================
# SEED DATA
# ===================================================================

def seed_printers() -> None:
    """Create four sample printers if the printers table is empty."""
    with get_db() as db:
        count = db.query(func.count(Printer.id)).scalar() or 0
        if count > 0:
            return

        sample_printers = [
            Printer(
                name="HP LaserJet Pro M404",
                status="Online",
                location="Library — Ground Floor",
                printer_type="LaserJet",
                total_prints=12_450,
                toner_level=78.5,
                error_count=3,
                temperature=36.2,
                last_maintenance=datetime(2026, 5, 15),
            ),
            Printer(
                name="Canon imageCLASS MF445dw",
                status="Online",
                location="CS Lab — Block A, 2nd Floor",
                printer_type="LaserJet Multifunction",
                total_prints=8_320,
                toner_level=92.1,
                error_count=1,
                temperature=34.8,
                last_maintenance=datetime(2026, 6, 1),
            ),
            Printer(
                name="Epson EcoTank L3250",
                status="Maintenance",
                location="Admin Office — Block B",
                printer_type="InkTank",
                total_prints=5_680,
                toner_level=45.3,
                error_count=7,
                temperature=38.1,
                last_maintenance=datetime(2026, 4, 20),
            ),
            Printer(
                name="Brother HL-L2395DW",
                status="Online",
                location="Student Center — Cafeteria Building",
                printer_type="LaserJet",
                total_prints=15_900,
                toner_level=61.7,
                error_count=5,
                temperature=37.0,
                last_maintenance=datetime(2026, 5, 28),
            ),
        ]

        db.add_all(sample_printers)
        db.commit()


# ===================================================================
# ALIASES & COMPATIBILITY
# ===================================================================
get_ai_analysis = get_analysis_by_job

def get_print_jobs_for_printer(printer_id: int) -> List[Dict[str, Any]]:
    """Fetch all print jobs associated with a printer."""
    with get_db() as db:
        jobs = db.query(PrintJob).filter(PrintJob.printer_id == printer_id).all()
        return [_job_to_dict(j) for j in jobs]


