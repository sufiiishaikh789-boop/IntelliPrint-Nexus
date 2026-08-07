"""
IntelliPrint Nexus — AI Cost Optimizer (Enterprise Edition)
=======================================================
Analyzes a print job and recommends cheaper alternatives with environmental
impact metrics (CO₂ saved, paper sheets saved, tree equivalent).

All functions are pure (no side effects) and fully deterministic.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def analyze_cost_options(
    total_pages: int,
    copies: int,
    color_mode: str,
    duplex: bool,
    cost_per_page: float = 2.0,
    color_surcharge: float = 3.0,
) -> Dict[str, Any]:
    """
    Calculate current cost and alternative options.

    Args:
        total_pages:    Total pages in document
        copies:         Number of copies
        color_mode:     "Color" or "BW"
        duplex:         True if double-sided
        cost_per_page:  Base cost per side (BW)
        color_surcharge: Additional cost per page for color

    Returns dict with current cost, options, recommendation.
    """
    sheets = total_pages * copies
    is_color = (color_mode == "Color")

    def _cost(pages: int, color: bool, dup: bool) -> float:
        """Compute total print cost for given configuration."""
        base: float = pages * cost_per_page
        color_add: float = pages * color_surcharge if color else 0.0
        duplex_disc: float = base * 0.35 if dup else 0.0
        return max(1.0, base + color_add - duplex_disc)

    current_cost = _cost(sheets, is_color, duplex)

    options: List[Dict[str, Any]] = []

    # Option 1: Switch to BW (if currently color)
    if is_color:
        bw_cost = _cost(sheets, False, duplex)
        saving = round(current_cost - bw_cost, 2)
        if saving > 0:
            options.append({
                "label":   "Black & White",
                "desc":    "Print in grayscale",
                "cost":    round(bw_cost, 2),
                "saving":  saving,
                "icon":    "🖤",
                "settings": {"color_mode": "BW"},
            })

    # Option 2: Switch to Duplex (if currently simplex)
    if not duplex:
        dup_cost = _cost(sheets, is_color, True)
        saving = round(current_cost - dup_cost, 2)
        if saving > 0:
            options.append({
                "label":   "Double-Sided",
                "desc":    "Print on both sides",
                "cost":    round(dup_cost, 2),
                "saving":  saving,
                "icon":    "📄",
                "settings": {"duplex": True},
            })

    # Option 3: BW + Duplex (best combo)
    if is_color or not duplex:
        best_cost = _cost(sheets, False, True)
        saving = round(current_cost - best_cost, 2)
        if saving > 0:
            options.append({
                "label":   "B&W + Double-Sided",
                "desc":    "Best value combination",
                "cost":    round(best_cost, 2),
                "saving":  saving,
                "icon":    "💡",
                "settings": {"color_mode": "BW", "duplex": True},
                "recommended": True,
            })

    best_option = max(options, key=lambda o: o["saving"]) if options else None

    return {
        "current_cost":   round(current_cost, 2),
        "options":        options,
        "best_option":    best_option,
        "max_saving":     best_option["saving"] if best_option else 0,
        "sheets":         sheets,
    }


def get_paper_saving_estimate(
    total_pages: int,
    copies: int,
    duplex: bool,
    paper_weight_g: float = 5.0,  # grams per sheet
) -> Dict[str, Any]:
    """
    Calculate paper savings and environmental impact.

    Returns dict with sheets, saved, CO₂ reduction, trees impact.
    """
    total_sides = total_pages * copies
    sheets_simplex = total_sides                           # 1 side per sheet
    sheets_duplex  = (total_sides + 1) // 2               # 2 sides per sheet
    current_sheets = sheets_duplex if duplex else sheets_simplex
    recommended_sheets = sheets_duplex
    sheets_saved = max(0, sheets_simplex - recommended_sheets)

    # Environmental estimates
    # 1 tree ≈ 8,333 sheets (A4 80gsm), 1 sheet ≈ 10g CO₂
    co2_g        = sheets_saved * 10
    co2_kg       = round(co2_g / 1000, 3)
    trees_saved  = round(sheets_saved / 8333, 4)

    return {
        "current_sheets":     current_sheets,
        "recommended_sheets": recommended_sheets,
        "sheets_saved":       sheets_saved,
        "co2_kg":             co2_kg,
        "co2_g":              co2_g,
        "trees_saved":        trees_saved,
        "already_duplex":     duplex,
    }
