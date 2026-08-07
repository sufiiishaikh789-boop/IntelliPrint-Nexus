"""
IntelliPrint Nexus — AI Queue Recommender (Enterprise Edition)
=========================================================
Analyzes available printers and recommends the best one for a job.
All scoring is deterministic and reproducible.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def recommend_best_printer(
    printers: List[Dict[str, Any]],
    all_jobs: List[Dict[str, Any]],
    color_mode: str = "BW",
    preferred_location: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze printers and return a ranked recommendation.

    Scoring factors:
    - Queue length (fewer = better)
    - Status (Online/Idle best, others penalised)
    - PPM speed (higher = better)
    - Toner level (low toner = penalised)
    - Location match bonus
    """
    ONLINE_STATUSES = {"online", "idle"}
    scored: List[Dict[str, Any]] = []

    for p in printers:
        status = (p.get("status") or "").lower()
        if status in ("offline", "maintenance", "paper jam", "error"):
            continue  # Skip unavailable printers

        pid = p.get("id")
        toner = p.get("toner_level") or 100
        ppm   = p.get("pages_per_minute") or 20
        name  = p.get("name", "Unknown Printer")
        loc   = p.get("location", "")

        # Count active jobs in queue for this printer
        queue_len = sum(
            1 for j in all_jobs
            if j.get("printer_id") == pid
            and (j.get("status") or "").lower() in ("queued", "printing", "preparing")
        )

        # Score calculation (higher = better)
        score = 100
        score -= queue_len * 15           # Penalise long queues
        score += min(ppm, 60)             # Reward speed (capped)
        if status in ONLINE_STATUSES:
            score += 20
        if toner < 15:
            score -= 40
        elif toner < 30:
            score -= 20
        if preferred_location and preferred_location.lower() in loc.lower():
            score += 30                   # Location preference bonus

        # Estimated wait (minutes) based on queue depth + PPM
        est_wait = round((queue_len * 5) + (30 / max(ppm, 1)), 1)

        scored.append({
            "printer_id":   pid,
            "name":         name,
            "location":     loc,
            "status":       p.get("status", "Unknown"),
            "ppm":          ppm,
            "toner":        toner,
            "queue_len":    queue_len,
            "est_wait_min": est_wait,
            "score":        score,
        })

    if not scored:
        return {"available": False, "message": "No printers currently available."}

    scored.sort(key=lambda x: x["score"], reverse=True)
    best = scored[0]

    # Build reason string
    reasons = []
    if best["queue_len"] == 0:
        reasons.append("No jobs in queue")
    else:
        reasons.append(f"Only {best['queue_len']} job(s) ahead")
    reasons.append(f"{best['ppm']} PPM speed")
    if best["toner"] >= 70:
        reasons.append(f"{best['toner']:.0f}% toner remaining")

    # Category badges
    fastest  = max(scored, key=lambda x: x["ppm"])
    shortest = min(scored, key=lambda x: x["queue_len"])

    return {
        "available":      True,
        "recommended":    best,
        "fastest":        fastest,
        "shortest_queue": shortest,
        "all_scored":     scored,
        "reason":         " · ".join(reasons),
        "estimated_wait": f"{best['est_wait_min']} min",
    }


def get_printer_recommendation_summary(rec: Dict[str, Any]) -> str:
    """Return a human-readable summary string from a recommendation dict."""
    if not rec.get("available"):
        return "⚠️ No printers available right now."
    best = rec["recommended"]
    return (
        f"✅ **{best['name']}** ({best['location']}) — "
        f"Queue: {best['queue_len']} job(s) · "
        f"Est. wait: {rec['estimated_wait']} · "
        f"{rec['reason']}"
    )
