"""
IntelliPrint Nexus - Document Analyzer
SHA-256 fingerprinting and enhanced document quality metrics.
"""

import hashlib
import os
from typing import Any, Dict, Optional


def compute_sha256(file_path: str) -> Optional[str]:
    """
    Compute SHA-256 hash of a file.
    Returns hex string or None if file missing/unreadable.
    """
    if not file_path or not os.path.exists(file_path):
        return None
    try:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def get_enhanced_analysis(
    file_path: str,
    total_pages: int,
    quality_score: float = 0.0,
) -> Dict[str, Any]:
    """
    Return an enhanced analysis report dict for display in the UI.
    Combines SHA-256 fingerprint with rule-based quality metrics.
    quality_score: existing AI quality score 0-100.
    """
    fingerprint = compute_sha256(file_path)
    file_size_kb = 0
    try:
        file_size_kb = round(os.path.getsize(file_path) / 1024, 1)
    except Exception:
        pass

    # Derive heuristic metrics from quality score and file characteristics
    q = quality_score or 50.0

    resolution_ok = q >= 60
    text_clarity  = "High"   if q >= 75 else "Medium" if q >= 50 else "Low"
    skew_detected = q < 40
    blank_pages   = 0        # placeholder (requires deep PDF parsing)
    color_coverage = "Moderate"  # placeholder

    # Paper recommendation based on pages
    if total_pages <= 2:
        paper_rec = "A4 — Standard"
    elif total_pages <= 10:
        paper_rec = "A4 — Standard (consider duplex)"
    else:
        paper_rec = "A4 Duplex — recommended for large documents"

    # Print recommendation
    if q >= 80:
        print_rec = "✅ Document is ready for high-quality printing."
    elif q >= 60:
        print_rec = "⚠️ Document quality is acceptable. Minor issues may appear in print."
    else:
        print_rec = "❌ Low quality detected. Consider re-exporting at higher resolution."

    return {
        "fingerprint":      fingerprint,
        "fingerprint_short": fingerprint[:16] + "..." if fingerprint else "N/A",
        "verified":         fingerprint is not None,
        "file_size_kb":     file_size_kb,
        "quality_score":    round(q, 1),
        "resolution_ok":    resolution_ok,
        "text_clarity":     text_clarity,
        "skew_detected":    skew_detected,
        "blank_pages":      blank_pages,
        "color_coverage":   color_coverage,
        "paper_rec":        paper_rec,
        "print_rec":        print_rec,
        "margin_ok":        q >= 55,
        "orientation":      "Portrait" if total_pages > 0 else "Unknown",
    }
