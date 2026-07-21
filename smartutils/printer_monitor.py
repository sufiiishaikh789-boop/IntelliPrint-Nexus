"""
SmartPrint AI - Printer Monitor
Syncs local OS printers to the SmartPrint SQLite Database.
"""
import sys
import os

# Add the project root to sys.path so we can import smartdb from everywhere
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import win32print
from smartdb.models import SessionLocal, Printer

def sync_os_printers():
    """Detects installed Windows printers and adds them to the DB."""
    try:
        # PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS
        printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        
        db = SessionLocal()
        try:
            for p in printers:
                printer_name = p[2]
                # Check if it exists
                existing = db.query(Printer).filter(Printer.name == printer_name).first()
                if not existing:
                    new_printer = Printer(
                        name=printer_name,
                        status="Online",
                        location="Local/Network",
                        printer_type="Virtual" if "PDF" in printer_name else "LaserJet",
                        total_prints=0,
                        toner_level=100.0,
                    )
                    db.add(new_printer)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        print(f"Failed to sync printers: {e}")

if __name__ == "__main__":
    sync_os_printers()
    print("Printers synced to DB.")
