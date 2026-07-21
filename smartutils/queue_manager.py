"""
SmartPrint AI - Queue Manager
Background daemon:
  1. Auto-promotes Pending jobs → Queued (Demo Mode — no payment required for demo)
  2. Processes Queued jobs on Online printers via printer_service
  3. Cleans up jobs stuck in Printing > 5 minutes
"""
import sys
import os
import time
import threading
import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from smartdb.models import SessionLocal, PrintJob, Printer
from smartutils.printer_service import process_job
from smartutils.helpers import write_log

# ──────────────────────────────────────────────────────────────────────────────
# DEMO MODE: automatically promote Pending jobs to Queued so the
# full workflow (Queued → Printing → Ready) works without requiring payment.
# Set DEMO_MODE = False in production to require payment before queuing.
# ──────────────────────────────────────────────────────────────────────────────
DEMO_MODE = True


def _promote_pending_jobs(db) -> int:
    """
    Demo Mode: move all Pending jobs to Queued so the queue manager
    picks them up immediately. Returns count of jobs promoted.
    """
    if not DEMO_MODE:
        return 0

    pending_jobs = db.query(PrintJob).filter(PrintJob.status == "Pending").all()
    promoted = 0
    for job in pending_jobs:
        # Only auto-promote if printer is assigned and is Online
        if not job.printer_id:
            # Find any online printer as fallback
            online_printer = db.query(Printer).filter(Printer.status == "Online").first()
            if online_printer:
                job.printer_id = online_printer.id
                write_log("QUEUE_LOG",
                    f"[DEMO] Assigned fallback printer '{online_printer.name}' "
                    f"to Job {job.print_id} (was unassigned)")
            else:
                write_log("QUEUE_LOG",
                    f"[DEMO] Cannot promote Job {job.print_id}: no Online printers available")
                continue

        # Verify assigned printer is Online
        printer = db.query(Printer).filter(Printer.id == job.printer_id).first()
        if not printer or printer.status != "Online":
            # Try to reassign to any online printer
            online_printer = db.query(Printer).filter(Printer.status == "Online").first()
            if online_printer:
                old = printer.name if printer else "unknown"
                job.printer_id = online_printer.id
                write_log("QUEUE_LOG",
                    f"[DEMO] Reassigned Job {job.print_id} from '{old}' "
                    f"(not Online) to '{online_printer.name}'")
            else:
                write_log("QUEUE_LOG",
                    f"[DEMO] Cannot promote Job {job.print_id}: "
                    f"assigned printer not Online and no fallback available")
                continue

        job.status = "Queued"
        promoted += 1
        write_log("QUEUE_LOG",
            f"[DEMO] Promoted Job {job.print_id} Pending → Queued "
            f"(printer_id={job.printer_id})")

    if promoted:
        db.commit()
        write_log("QUEUE_LOG", f"[DEMO] {promoted} job(s) auto-promoted to Queued")

    return promoted


def _free_stuck_printing_jobs(db) -> int:
    """
    Find jobs stuck in 'Printing' for > 5 minutes and advance them to 'Ready'.
    Returns count of jobs freed.
    """
    stuck_jobs = db.query(PrintJob).filter(PrintJob.status == "Printing").all()
    freed = 0
    for job in stuck_jobs:
        ref_time = job.submitted_at or datetime.datetime.utcnow()
        elapsed = (datetime.datetime.utcnow() - ref_time).total_seconds()
        if elapsed > 300:  # 5 minutes
            job.status = "Ready"
            freed += 1
            write_log("QUEUE_LOG",
                f"Freed stuck Job {job.print_id}: was Printing for "
                f"{elapsed:.0f}s — advanced to Ready")
    if freed:
        db.commit()
    return freed


def run_queue_manager():
    """Continuously poll for jobs and process them."""
    write_log("QUEUE_LOG", "=" * 60)
    write_log("QUEUE_LOG", "Queue Manager daemon thread started.")
    write_log("QUEUE_LOG", f"DEMO_MODE = {DEMO_MODE}")
    write_log("QUEUE_LOG", "=" * 60)

    cycle = 0
    while True:
        cycle += 1
        db = SessionLocal()
        try:
            # ── Step 1: Free stuck Printing jobs ──────────────────────────
            freed = _free_stuck_printing_jobs(db)

            # ── Step 2: Demo Mode — promote Pending → Queued ───────────────
            promoted = _promote_pending_jobs(db)

            # ── Step 3: Process next Queued job per Online printer ─────────
            online_printers = db.query(Printer).filter(Printer.status == "Online").all()

            if cycle % 10 == 1:  # Log every ~30s to avoid log spam
                write_log("QUEUE_LOG",
                    f"Cycle {cycle}: {len(online_printers)} online printers, "
                    f"{promoted} promoted, {freed} freed")

            for printer in online_printers:
                # Skip if printer is busy
                active = db.query(PrintJob).filter(
                    PrintJob.printer_id == printer.id,
                    PrintJob.status == "Printing"
                ).first()

                if active:
                    elapsed = 0
                    if active.submitted_at:
                        elapsed = (datetime.datetime.utcnow() - active.submitted_at).total_seconds()
                    write_log("QUEUE_LOG",
                        f"Printer '{printer.name}' busy with Job "
                        f"{active.print_id} ({elapsed:.0f}s elapsed) — skipping")
                    continue

                # Pick next Queued job (high priority first, then FIFO)
                next_job = (
                    db.query(PrintJob)
                    .filter(
                        PrintJob.printer_id == printer.id,
                        PrintJob.status == "Queued"
                    )
                    .order_by(
                        PrintJob.priority.desc(),
                        PrintJob.submitted_at.asc()
                    )
                    .first()
                )

                if next_job:
                    write_log("QUEUE_LOG",
                        f"Dispatching Job {next_job.print_id} "
                        f"(priority={next_job.priority}) to '{printer.name}'")
                    # Close DB before process_job (it opens its own session)
                    db.close()
                    db = None
                    success = process_job(next_job.id)
                    write_log("QUEUE_LOG",
                        f"Job {next_job.print_id} process result: "
                        f"{'SUCCESS' if success else 'FAILED'}")
                    break  # One job per cycle per printer to avoid blocking

        except Exception as e:
            write_log("QUEUE_LOG", "Exception in Queue Manager cycle", e)
        finally:
            if db is not None:
                db.close()

        time.sleep(3)  # Poll every 3 seconds


def start_queue_manager_thread():
    """Spawn the queue manager as a named daemon thread (idempotent)."""
    for t in threading.enumerate():
        if t.name == "QueueManagerThread":
            return  # Already running

    thread = threading.Thread(
        target=run_queue_manager,
        name="QueueManagerThread",
        daemon=True
    )
    thread.start()
    write_log("QUEUE_LOG", "QueueManagerThread spawned successfully")


if __name__ == "__main__":
    run_queue_manager()
