"""
IntelliPrint Nexus — Printer Recommendation Engine (Enterprise Edition)
==================================================================
ML-based recommendation system that ranks available printers for a given
print job using scored heuristics and wait-time predictions.

Enterprise improvements over the previous version:
- Removed non-deterministic ``random.uniform(-2, 2)`` score noise
  (identical inputs now produce identical, reproducible rankings)
- Added structured logger from smartcore.logger
- Full type hints throughout
- from __future__ import annotations
- Improved docstring quality
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# ── Structured logger ─────────────────────────────────────────────────────────
try:
    from smartcore.logger import get_logger as _get_logger
    _log = _get_logger("ai")
except ImportError:
    import logging as _logging
    _log = _logging.getLogger("smartprint.recommendation")


def recommend_printers(
    job_pages: int,
    job_copies: int,
    color_required: bool,
    available_printers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Recommend the best printer based on job specifications and ML-predicted
    queue wait times.

    Scoring factors (deterministic, reproducible):
    - Color capability match (hard penalty if color required but unsupported)
    - Toner level (penalty thresholds at 10 % and 30 %)
    - Printer speed (PPM) reward for large jobs
    - ML-predicted wait time penalty (XGBoost/RF via predict_wait_time)

    Parameters
    ----------
    job_pages          : Total pages in the document
    job_copies         : Number of copies requested
    color_required     : True if job requires color printing
    available_printers : List of printer dicts from the database

    Returns
    -------
    dict with keys:
        best_printer, fastest_printer, lowest_wait_time_printer,
        highest_efficiency_printer, all_scored (sorted by score desc)
        Returns {"error": str} if no suitable printers exist.
    """
    if not available_printers:
        _log.warning("recommend_printers: no printers provided")
        return {}

    from smartai.wait_time import predict_wait_time

    total_pages: int = job_pages * job_copies
    scored_printers: List[Dict[str, Any]] = []

    for p in available_printers:
        score: float = 100.0

        # Penalty: color required but printer does not support it
        if color_required and not p.get("supports_color", True):
            score -= 100.0

        # Toner-level penalties
        toner: float = float(p.get("toner_level") or 100)
        if toner < 10:
            score -= 50.0
        elif toner < 30:
            score -= 20.0

        # Speed reward for large jobs
        speed: int = int(p.get("pages_per_minute") or p.get("ppm") or 30)
        if total_pages > 50:
            score += float(speed - 30)  # positive for fast printers, negative for slow

        # ML wait-time penalty (deterministic — no random noise)
        queue_len: int = int(p.get("queue_length") or 0)
        pred: Dict[str, Any] = predict_wait_time(
            queue_length=queue_len,
            pages=job_pages,
            copies=job_copies,
            printer_speed_ppm=speed,
            priority_flag=False,
        )
        wait_time: float = float(pred["estimated_wait_minutes"])
        score -= wait_time * 4.0

        scored_printers.append({
            "printer_id":     p.get("id", "Unknown"),
            "name":           p.get("name", "Printer"),
            "score":          round(max(0.0, min(100.0, score)), 2),
            "ppm":            speed,
            "queue":          queue_len,
            "predicted_wait": wait_time,
        })

    # Sort by score descending (deterministic — no random tiebreaker)
    scored_printers.sort(key=lambda x: x["score"], reverse=True)
    valid_printers: List[Dict[str, Any]] = [p for p in scored_printers if p["score"] > 0]

    if not valid_printers:
        _log.warning("recommend_printers: no suitable printers after scoring")
        return {"error": "No suitable printers available."}

    fastest:    Dict[str, Any] = max(valid_printers, key=lambda x: x["ppm"])
    lowest_wait: Dict[str, Any] = min(valid_printers, key=lambda x: x["predicted_wait"])
    best_overall: Dict[str, Any] = valid_printers[0]

    _log.debug(
        "recommend_printers: best='%s' score=%.1f wait=%.1f min",
        best_overall["name"], best_overall["score"], best_overall["predicted_wait"],
    )

    return {
        "best_printer":                 best_overall,
        "fastest_printer":              fastest,
        "lowest_wait_time_printer":     lowest_wait,
        "highest_efficiency_printer":   best_overall,
        "all_scored":                   valid_printers,
    }


# ── Backward-compatible alias ─────────────────────────────────────────────────
recommend_printer = recommend_printers
