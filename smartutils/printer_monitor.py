"""
IntelliPrint Nexus — Printer Monitor (Enterprise Edition)
=====================================================
Syncs local OS printers to the SmartPrint SQLite Database.

Enterprise improvements:
- Lazy import of win32print (no crash on Linux/Mac)
- Delegates to smartcore.printer_manager for cross-platform abstraction
- Backward-compatible sync_os_printers() function preserved
"""

from __future__ import annotations

import os
import sys

# Add project root to sys.path only if not already importable
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── Platform guard — no unconditional win32print import ────────────────────
try:
    import win32print
    _PYWIN32 = True
except ImportError:
    _PYWIN32 = False


def sync_os_printers() -> int:
    """
    Detect installed Windows printers and add them to the database.

    Cross-platform safe: silently does nothing on Linux/Mac.
    Returns the count of newly added printers.
    """
    try:
        from smartcore.printer_manager import printer_manager
        count = printer_manager.sync_os_printers()
        print(f"Printers synced: {count} new printer(s) added.")
        return count
    except Exception as exc:
        print(f"Failed to sync printers: {exc}")
        return 0


if __name__ == "__main__":
    sync_os_printers()
