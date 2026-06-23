from __future__ import annotations

from datetime import datetime
from typing import Any


STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

STEM_ELEMENT = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}

BRANCH_ELEMENT = {
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}

GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}


def get_year_ganzhi(year: int) -> dict[str, Any]:
    offset = (year - 1984) % 60
    stem = STEMS[offset % 10]
    branch = BRANCHES[offset % 12]
    return {
        "year": year,
        "stem": stem,
        "branch": branch,
        "stem_element": STEM_ELEMENT[stem],
        "branch_element": BRANCH_ELEMENT[branch],
        "ganzhi": f"{stem}{branch}",
    }


def compute_past_years(bazi_chart: dict[str, Any], count: int = 20, current_year: int | None = None) -> list[dict[str, Any]]:
    year = current_year or datetime.now().year
    dm_element = bazi_chart["day_master"]["element"]
    strength = bazi_chart["preliminary"]["strength"]
    result = []

    for item_year in range(year - count, year):
        gz = get_year_ganzhi(item_year)
        stem_score = _element_score_for_dm(gz["stem_element"], dm_element, strength)
        branch_score = _element_score_for_dm(gz["branch_element"], dm_element, strength)
        total_score = stem_score * 0.6 + branch_score * 0.4
        result.append(
            {
                **gz,
                "stem_score": stem_score,
                "branch_score": branch_score,
                "total_score": round(total_score, 2),
                "tendency": _score_to_tendency(total_score),
            }
        )
    return result


def _element_score_for_dm(element: str, dm_element: str, strength: str) -> float:
    if strength in {"身弱", "中和"}:
        if element == dm_element:
            return 2.0
        if GENERATES.get(element) == dm_element:
            return 2.0
        if CONTROLS.get(element) == dm_element:
            return -2.0
        if GENERATES.get(dm_element) == element:
            return -1.5
        if CONTROLS.get(dm_element) == element:
            return -1.0
    else:
        if CONTROLS.get(element) == dm_element:
            return 2.0
        if GENERATES.get(dm_element) == element:
            return 1.5
        if CONTROLS.get(dm_element) == element:
            return 1.0
        if element == dm_element:
            return -1.5
        if GENERATES.get(element) == dm_element:
            return -2.0
    return 0.0


def _score_to_tendency(score: float) -> str:
    if score >= 1.0:
        return "喜用"
    if score >= 0.3:
        return "小喜"
    if score <= -1.0:
        return "忌神"
    if score <= -0.3:
        return "小忌"
    return "中性"


def find_best_contrast_years(past_years: list[dict[str, Any]], count: int = 2) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sorted_by_score = sorted(past_years, key=lambda item: item["total_score"])
    return sorted_by_score[-count:], sorted_by_score[:count]
