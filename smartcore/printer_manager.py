"""
IntelliPrint Nexus — Enterprise Printer Manager
==========================================
Centralized printer communication abstraction layer.

Features:
- Health monitoring for all registered printers
- Load balancing: distribute jobs to least-loaded printer
- Heartbeat background thread (pings printers every 60 s)
- Diagnostics report per printer
- Cross-platform: Windows uses win32print; Linux/Mac degrades gracefully
- Auto-marks offline printers; attempts reconnection
- Thread-safe state tracking
"""

from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("printer")
except ImportError:
    import logging as _logging
    _log = _logging.getLogger("smartprint.printer")

# ── Platform guard ─────────────────────────────────────────────────────────
try:
    import win32print
    import win32api
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False


class PrinterManager:
    """
    Centralised printer state manager.
    Use the module-level ``printer_manager`` singleton.
    """

    def __init__(self) -> None:
        self._lock    = threading.Lock()
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._running = False

    # ── Heartbeat ─────────────────────────────────────────────────────────

    def start_heartbeat(self, interval_s: int = 60) -> None:
        """Start the background printer heartbeat thread."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop,
                args=(interval_s,),
                name="PrinterHeartbeat",
                daemon=True,
            )
            self._heartbeat_thread.start()
            _log.info("Printer heartbeat started (interval=%ds)", interval_s)

    def stop_heartbeat(self) -> None:
        """Signal the heartbeat thread to stop."""
        self._running = False

    def _heartbeat_loop(self, interval_s: int) -> None:
        while self._running:
            try:
                self._check_all_printers()
            except Exception as exc:
                _log.error("Heartbeat cycle error: %s", exc)
            time.sleep(interval_s)

    def _check_all_printers(self) -> None:
        """Ping all printers and update DB status.

        Printers with manual_override=True are always skipped — their status
        was intentionally set by an admin via Printer Management and must not
        be reverted by connectivity checks.
        """
        from smartdb.crud import get_all_printers, update_printer_fields

        printers = get_all_printers()
        for p in printers:
            name       = p.get("name", "")
            pid        = p.get("id")
            cur_status = p.get("status", "Offline")

            # ── Respect admin-set statuses ──────────────────────────────────
            # If an admin manually set this printer's status via the Printer
            # Management page, do NOT override it based on Windows spooler
            # connectivity. The manual_override flag is cleared only when the
            # admin explicitly changes the status again.
            if p.get("manual_override"):
                # Only refresh the heartbeat timestamp so "last seen" stays
                # current for printers the admin has set as Online/Idle/Busy.
                if cur_status.lower() in ("online", "idle", "busy"):
                    try:
                        update_printer_fields(pid, last_seen_at=datetime.utcnow())
                    except Exception:
                        pass
                _log.debug(
                    "Printer '%s' skipped (manual_override=True, status='%s')",
                    name, cur_status,
                )
                continue

            # ── Auto-detect status for non-overridden printers ──────────────
            is_online  = self._check_printer_online(name)
            new_status = "Online" if is_online else "Offline"

            # Only update if status changed (avoid unnecessary DB writes)
            if cur_status != new_status:
                update_printer_fields(pid, status=new_status, last_seen_at=datetime.utcnow())
                _log.info("Printer '%s' status changed → %s", name, new_status)
            elif is_online:
                # Still online — refresh last_seen_at
                update_printer_fields(pid, last_seen_at=datetime.utcnow())

    # ── Printer connectivity ───────────────────────────────────────────────

    def _check_printer_online(self, printer_name: str) -> bool:
        """Check if a printer is responsive."""
        if not printer_name:
            return False

        # Windows: query via win32print
        if PYWIN32_AVAILABLE:
            return self._check_win32_printer(printer_name)

        # Linux/Mac fallback: virtual printers always show online
        return "Virtual" in printer_name or "PDF" in printer_name

    def _check_win32_printer(self, printer_name: str) -> bool:
        """Check printer via Windows spooler API."""
        try:
            handle = win32print.OpenPrinter(printer_name)
            info   = win32print.GetPrinter(handle, 2)
            win32print.ClosePrinter(handle)
            # STATUS_OFFLINE = 0x00000080
            status_flags = info.get("Status", 0)
            is_offline   = bool(status_flags & 0x00000080)
            return not is_offline
        except Exception:
            return False

    # ── Load balancing ─────────────────────────────────────────────────────

    def get_best_printer(self) -> Optional[Dict[str, Any]]:
        """
        Select the best available printer using a composite score:
          1. Must be Online
          2. Highest toner level (weight: 60 %)
          3. Fewest queued jobs (weight: 30 %)
          4. Fewest errors (weight: 10 %)

        Returns the printer dict or None if no printer is available.
        """
        from smartdb.crud import get_all_printers
        from smartdb.models import SessionLocal, PrintJob

        printers = [p for p in get_all_printers() if p.get("status") == "Online"]
        if not printers:
            _log.warning("No online printers available")
            return None

        if len(printers) == 1:
            return printers[0]

        # Count queued jobs per printer
        db = SessionLocal()
        try:
            queued_counts: Dict[int, int] = {}
            for p in printers:
                cnt = (
                    db.query(PrintJob)
                    .filter(PrintJob.printer_id == p["id"], PrintJob.status == "Queued")
                    .count()
                )
                queued_counts[p["id"]] = cnt
        finally:
            db.close()

        def _score(p: Dict[str, Any]) -> float:
            toner     = p.get("toner_level", 0) / 100.0
            errors    = p.get("error_count", 0)
            queue_len = queued_counts.get(p["id"], 0)
            return (toner * 0.6) - (queue_len * 0.03) - (errors * 0.01)

        return max(printers, key=_score)

    # ── Diagnostics ────────────────────────────────────────────────────────

    def get_printer_diagnostics(self, printer_id: int) -> Dict[str, Any]:
        """Return a comprehensive diagnostic report for one printer."""
        from smartdb.crud import get_printer_by_id, get_printer_maintenance
        from smartdb.models import SessionLocal, PrintJob

        printer = get_printer_by_id(printer_id)
        if not printer:
            return {"error": "Printer not found"}

        db = SessionLocal()
        try:
            job_counts: Dict[str, int] = {}
            rows = (
                db.query(PrintJob.status, __import__("sqlalchemy").func.count(PrintJob.id))
                .filter(PrintJob.printer_id == printer_id)
                .group_by(PrintJob.status)
                .all()
            )
            for status, cnt in rows:
                job_counts[status] = cnt

            total_jobs = sum(job_counts.values())
            error_rate = round(
                (printer.get("error_count", 0) / max(1, printer.get("total_prints", 1))) * 100, 2
            )
        finally:
            db.close()

        maintenance = get_printer_maintenance(printer_id)
        unresolved  = [m for m in maintenance if not m.get("resolved")]

        toner    = printer.get("toner_level", 0)
        toner_health = "Good" if toner > 50 else "Low" if toner > 20 else "Critical"

        return {
            "printer":          printer,
            "job_status_counts": job_counts,
            "total_jobs":       total_jobs,
            "error_rate_pct":   error_rate,
            "toner_health":     toner_health,
            "open_issues":      len(unresolved),
            "maintenance_logs": maintenance[:10],
            "online_check":     self._check_printer_online(printer.get("name", "")),
            "diagnostics_at":   datetime.utcnow().isoformat(),
        }

    # ── OS Printer Sync ────────────────────────────────────────────────────

    def sync_os_printers(self) -> int:
        """
        Detect installed OS printers and add missing ones to the DB.
        Returns the count of newly added printers.
        """
        if not PYWIN32_AVAILABLE:
            _log.info("sync_os_printers: win32print not available — skipping")
            return 0

        from smartdb.crud import get_all_printers, add_printer

        try:
            os_printers = win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )
        except Exception as exc:
            _log.error("EnumPrinters failed: %s", exc)
            return 0

        existing_names = {p["name"] for p in get_all_printers()}
        added = 0
        for p in os_printers:
            name = p[2]
            if name not in existing_names:
                printer_type = "Virtual" if any(k in name for k in ("PDF", "XPS", "Fax")) else "LaserJet"
                add_printer(
                    name=name,
                    location="Local / Network",
                    printer_type=printer_type,
                    status="Online",
                )
                _log.info("Added OS printer: '%s'", name)
                added += 1
        return added


# ── Module-level singleton ──────────────────────────────────────────────────
printer_manager = PrinterManager()
