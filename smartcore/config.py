"""
IntelliPrint Nexus — Centralized Configuration
==========================================
Single source of truth for all application constants, thresholds,
timeouts, paths, and feature flags. Import this module anywhere you
need a configuration value — never hardcode values elsewhere.

Usage::

    from smartcore.config import cfg
    timeout = cfg.DB_TIMEOUT
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class _DatabaseConfig:
    """SQLite / SQLAlchemy database settings."""
    # Core connection
    URL: str = "sqlite:///smartprint.db"
    TIMEOUT: int = 30                       # seconds before 'database is locked' raises
    ECHO: bool = False                      # set True to log all SQL statements

    # Connection pool (used when migrating to PostgreSQL)
    POOL_SIZE: int = 10
    MAX_OVERFLOW: int = 20
    POOL_TIMEOUT: int = 30
    POOL_RECYCLE: int = 3600               # recycle connections every hour
    POOL_PRE_PING: bool = True             # detect stale connections

    # WAL / performance PRAGMAs
    JOURNAL_MODE: str = "WAL"
    SYNCHRONOUS: str = "NORMAL"
    CACHE_SIZE_KB: int = 65536             # 64 MB page cache
    TEMP_STORE: int = 2                    # 2 = MEMORY
    MMAP_SIZE: int = 268435456            # 256 MB memory-mapped I/O

    # Maintenance
    VACUUM_INTERVAL_HOURS: int = 24
    BACKUP_INTERVAL_HOURS: int = 6
    BACKUP_KEEP_COUNT: int = 5


@dataclass(frozen=True)
class _AIConfig:
    """AI / ML engine settings."""
    # Model paths
    DOCUMENT_QUALITY_MODEL: str = "models/document_quality_model.h5"
    MAINTENANCE_MODEL: str = "models/maintenance_model.pkl"
    QUEUE_MODEL: str = "models/queue_recommender.pkl"
    COST_MODEL: str = "models/cost_optimizer.pkl"

    # Inference
    IMAGE_SIZE: int = 224                  # px — MobileNetV2 input
    INFERENCE_TIMEOUT_S: float = 15.0      # give up after this long
    CONFIDENCE_THRESHOLD: float = 0.60    # below this → fallback heuristic
    MAX_BATCH_SIZE: int = 8

    # Model cache TTL
    MODEL_CACHE_TTL_S: int = 0            # 0 = cache forever (reload on startup only)
    GPU_MEMORY_FRACTION: float = 0.4      # fraction of VRAM to use (TF)

    # Quality thresholds
    QUALITY_EXCELLENT: float = 92.0
    QUALITY_VERY_GOOD: float = 80.0
    QUALITY_GOOD: float = 68.0
    QUALITY_AVERAGE: float = 55.0
    QUALITY_POOR: float = 38.0

    # Computer Vision
    BLUR_VARIANCE_THRESHOLD: float = 100.0
    SKEW_ANGLE_THRESHOLD: float = 1.5     # degrees
    SHADOW_THRESHOLD: float = 30.0

    # Caching
    CV_CACHE_SIZE: int = 128              # number of image fingerprints to cache


@dataclass(frozen=True)
class _QueueConfig:
    """Print queue engine settings."""
    POLL_INTERVAL_IDLE_S: float = 5.0     # polling interval when no jobs pending
    POLL_INTERVAL_BUSY_S: float = 1.5     # polling interval when jobs are queued
    PREPARE_SECONDS: float = 4.0          # "Preparing Printer" stage duration
    STUCK_JOB_TIMEOUT_S: int = 600        # 10 min — auto-release stuck Printing jobs
    MAX_RETRIES: int = 3                   # retries before marking as Failed
    RETRY_BACKOFF_S: float = 5.0          # base backoff between retries

    # Priorities (higher = first)
    PRIORITY_MAP: dict = field(default_factory=lambda: {
        "Urgent": 3,
        "High": 2,
        "Priority": 2,
        "Normal": 1,
    })

    # Persistence
    CHECKPOINT_FILE: str = "logs/queue_checkpoint.json"
    DEMO_MODE: bool = False               # auto-promote Pending→Queued without payment


@dataclass(frozen=True)
class _PaymentConfig:
    """Payment engine settings."""
    TRANSACTION_ID_PREFIX: str = "TXN"
    TRANSACTION_ID_LENGTH: int = 12       # random characters after prefix
    RECEIPT_DIR: str = "uploads/receipts"
    PAYMENT_LOG_FILE: str = "logs/payments.log"
    MAX_AMOUNT: float = 10_000.0          # sanity cap in rupees
    MIN_AMOUNT: float = 0.50              # minimum charge

    # Simulated processing delay
    SIMULATE_DELAY_S: float = 0.0


@dataclass(frozen=True)
class _PrintingConfig:
    """Cost rates and printing parameters."""
    # Per-page base costs (₹)
    COST_BW_PER_PAGE: float = 2.0
    COST_COLOR_PER_PAGE: float = 5.0

    # Priority multipliers
    PRIORITY_NORMAL_MULT: float = 1.0
    PRIORITY_HIGH_MULT: float = 1.5
    PRIORITY_URGENT_MULT: float = 2.0

    # Duplex discount
    DUPLEX_DISCOUNT: float = 0.10         # 10 % off when duplex enabled

    # Default print settings
    DEFAULT_COPIES: int = 1
    DEFAULT_COLOR_MODE: str = "BW"
    DEFAULT_DUPLEX: bool = False
    DEFAULT_PAPER_SIZE: str = "A4"
    DEFAULT_PRIORITY: str = "Normal"
    DEFAULT_PPM: int = 20                 # pages per minute fallback

    # Environmental
    CO2_PER_SHEET_KG: float = 0.005      # ~5 g CO₂ per sheet saved by duplex


@dataclass(frozen=True)
class _SecurityConfig:
    """Authentication and security settings."""
    BCRYPT_ROUNDS: int = 12
    SESSION_TIMEOUT_HOURS: int = 24
    MAX_LOGIN_ATTEMPTS: int = 5           # before temporary lockout
    LOCKOUT_MINUTES: int = 15

    # Input validation
    USERNAME_MIN_LEN: int = 3
    USERNAME_MAX_LEN: int = 50
    PASSWORD_MIN_LEN: int = 6
    PASSWORD_MAX_LEN: int = 128
    EMAIL_MAX_LEN: int = 120

    # Allowed characters in usernames (regex)
    USERNAME_PATTERN: str = r"^[a-zA-Z0-9_\-\.]+$"

    # File uploads
    MAX_UPLOAD_SIZE_MB: float = 50.0
    ALLOWED_EXTENSIONS: tuple = (".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp")
    UPLOADS_DIR: str = "uploads"
    QR_DIR: str = "qrcodes"
    PREVIEW_DIR: str = "uploads/previews"


@dataclass(frozen=True)
class _LoggingConfig:
    """Enterprise logging settings."""
    LEVEL: str = "INFO"                   # DEBUG / INFO / WARNING / ERROR / CRITICAL
    LOG_DIR: str = "logs"
    UNIFIED_LOG_FILE: str = "logs/smartprint.log"
    MAX_BYTES: int = 10 * 1024 * 1024    # 10 MB per log file
    BACKUP_COUNT: int = 5
    FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    JSON_FORMAT: bool = False             # set True for machine-parseable logs

    # Per-module log files
    APP_LOG: str = "logs/app.log"
    DB_LOG: str = "logs/database.log"
    QUEUE_LOG: str = "logs/queue.log"
    PRINTER_LOG: str = "logs/printer.log"
    PAYMENT_LOG: str = "logs/payment.log"
    SECURITY_LOG: str = "logs/security.log"
    AI_LOG: str = "logs/ai.log"
    UPLOAD_LOG: str = "logs/upload.log"
    MONITOR_LOG: str = "logs/monitor.log"


@dataclass(frozen=True)
class _GPUConfig:
    """GPU detection and management settings."""
    ENABLE_GPU: bool = True               # master switch
    NVIDIA_SMI_TIMEOUT_S: int = 5
    STATS_CACHE_TTL_S: int = 30          # refresh GPU stats every 30 s
    MIN_FREE_VRAM_MB: int = 512          # require at least this much free VRAM
    TF_MEMORY_GROWTH: bool = True        # grow TF GPU memory incrementally
    TF_PER_PROCESS_MEMORY_FRACTION: float = 0.4


@dataclass(frozen=True)
class _MonitoringConfig:
    """Real-time system monitoring settings."""
    METRICS_WINDOW_SIZE: int = 60         # rolling window (data points)
    REFRESH_INTERVAL_S: float = 30.0
    SLOW_QUERY_THRESHOLD_MS: float = 200.0
    HIGH_CPU_THRESHOLD: float = 85.0
    HIGH_RAM_THRESHOLD: float = 90.0
    QUEUE_DEPTH_WARNING: int = 20


@dataclass(frozen=True)
class AppConfig:
    """
    Root configuration object.  Access via the module-level ``cfg`` singleton::

        from smartcore.config import cfg
        print(cfg.DB.URL)
    """
    DB: _DatabaseConfig = field(default_factory=_DatabaseConfig)
    AI: _AIConfig = field(default_factory=_AIConfig)
    QUEUE: _QueueConfig = field(default_factory=_QueueConfig)
    PAYMENT: _PaymentConfig = field(default_factory=_PaymentConfig)
    PRINTING: _PrintingConfig = field(default_factory=_PrintingConfig)
    SECURITY: _SecurityConfig = field(default_factory=_SecurityConfig)
    LOGGING: _LoggingConfig = field(default_factory=_LoggingConfig)
    GPU: _GPUConfig = field(default_factory=_GPUConfig)
    MONITORING: _MonitoringConfig = field(default_factory=_MonitoringConfig)

    # ── Convenience shortcuts ──────────────────────────────────────────────
    @property
    def DB_TIMEOUT(self) -> int:
        return self.DB.TIMEOUT

    @property
    def LOG_DIR(self) -> str:
        return self.LOGGING.LOG_DIR

    @property
    def UPLOADS_DIR(self) -> str:
        return self.SECURITY.UPLOADS_DIR

    @property
    def QR_DIR(self) -> str:
        return self.SECURITY.QR_DIR


# ── Module-level singleton ──────────────────────────────────────────────────
cfg = AppConfig()


def ensure_directories() -> None:
    """Create all required runtime directories if they don't exist."""
    dirs = [
        cfg.LOGGING.LOG_DIR,
        cfg.SECURITY.UPLOADS_DIR,
        cfg.SECURITY.QR_DIR,
        cfg.SECURITY.PREVIEW_DIR,
        cfg.PAYMENT.RECEIPT_DIR,
        "models",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
