from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.astrology_engine import BirthData, calculate_western_chart


TEST_BIRTH = BirthData(
    local_date="2001-11-16",
    local_time="07:30",
    timezone="Asia/Shanghai",
    latitude=30.837,
    longitude=106.111,
    place="四川省南充市",
    house_system="P",
    zodiac="tropical",
)


def summarize_engine_chart(chart: dict[str, Any]) -> dict[str, Any]:
    planets = chart["planets"]
    return {
        "sun": summarize_body(planets["sun"]),
        "moon": summarize_body(planets["moon"]),
        "asc": summarize_body(chart["ascendant"]),
        "mc": summarize_body(chart["mc"]),
        "houses": [
            {
                "house": item["house"],
                "longitude": item["longitude"],
                "sign": item["sign"],
                "degree": item["degree_display"],
            }
            for item in chart["houses"]
        ],
        "planet_houses": {
            key: value["house"]
            for key, value in planets.items()
            if key != "southNode"
        },
        "aspects": chart["aspects"],
        "meta": chart["_meta"],
    }


def summarize_body(body: dict[str, Any]) -> dict[str, Any]:
    return {
        "longitude": body["longitude"],
        "sign": body["sign"],
        "sign_zh": body["sign_zh"],
        "degree": body["degree_display"],
        "house": body.get("house"),
    }


def try_kerykeion() -> dict[str, Any]:
    try:
        kerykeion = importlib.import_module("kerykeion")
    except Exception as exc:
        return {"status": "unavailable", "reason": repr(exc)}

    try:
        subject_cls = getattr(kerykeion, "AstrologicalSubject")
        subject = subject_cls(
            name="Nanchong Test",
            year=2001,
            month=11,
            day=16,
            hour=7,
            minute=30,
            city="Nanchong",
            nation="CN",
            lng=106.111,
            lat=30.837,
            tz_str="Asia/Shanghai",
            zodiac_type="Tropic",
        )
        fields = [
            "sun",
            "moon",
            "first_house",
            "tenth_house",
            "mercury",
            "venus",
            "mars",
            "jupiter",
            "saturn",
            "uranus",
            "neptune",
            "pluto",
        ]
        payload = {}
        for field in fields:
            item = getattr(subject, field, None)
            if item is None:
                continue
            payload[field] = {
                "longitude": getattr(item, "abs_pos", None),
                "sign": getattr(item, "sign", None),
                "degree": getattr(item, "position", None),
                "house": getattr(item, "house", None),
            }
        return {"status": "ready", "version": getattr(kerykeion, "__version__", None), "chart": payload}
    except Exception as exc:
        return {"status": "error", "reason": repr(exc)}


def try_immanuel() -> dict[str, Any]:
    try:
        immanuel = importlib.import_module("immanuel")
    except Exception as exc:
        return {"status": "unavailable", "reason": repr(exc)}

    # immanuel has changed its public API across releases, so this evaluator is
    # intentionally defensive and reports the installed package metadata if a
    # local adapter needs to be filled in for that version.
    return {
        "status": "installed_adapter_needed",
        "version": getattr(immanuel, "__version__", None),
        "module": getattr(immanuel, "__file__", None),
        "reason": "immanuel is installed, but no stable local adapter was configured for this version.",
    }


def main() -> None:
    swiss_chart = calculate_western_chart(TEST_BIRTH)
    report = {
        "test_birth": TEST_BIRTH.__dict__,
        "pyswisseph": {
            "status": "ready",
            "summary": summarize_engine_chart(swiss_chart),
        },
        "kerykeion": try_kerykeion(),
        "immanuel": try_immanuel(),
        "manual_reference": {
            "status": "pending",
            "note": "请用 Astro.com / Astro-Seek / 测测以同一出生信息人工核对；本脚本输出字段已对齐核对项。",
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
