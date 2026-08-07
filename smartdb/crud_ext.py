"""
IntelliPrint Nexus — Phase 3 CRUD Extensions (Enterprise Edition)
=============================================================
Thin compatibility shim for any code that imports from crud_ext.
All primary implementations now live in crud.py.

Functions re-exported here are the canonical implementations from crud.py.
Any function unique to this module (get_user_profile, get_bookmarked_jobs)
delegates to crud.py counterparts to avoid code duplication.
"""

from __future__ import annotations

# Re-export everything from the primary CRUD module so that any view that
# does ``from smartdb.crud_ext import X`` continues to work unchanged.
from smartdb.crud import (
    get_student_analytics,
    get_duplicate_by_fingerprint,
    set_job_fingerprint,
    get_favorite_printer,
    bookmark_job,
    get_bookmarked_jobs,
    get_user_profile,
    update_user_profile,
    get_user_settings,
    save_user_settings,
    get_notifications_unread_count,
    create_notification,
    mark_all_notifications_read,
)

__all__ = [
    "get_student_analytics",
    "get_duplicate_by_fingerprint",
    "set_job_fingerprint",
    "get_favorite_printer",
    "bookmark_job",
    "get_bookmarked_jobs",
    "get_user_profile",
    "update_user_profile",
    "get_user_settings",
    "save_user_settings",
    "get_notifications_unread_count",
    "create_notification",
    "mark_all_notifications_read",
]
