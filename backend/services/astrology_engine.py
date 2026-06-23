from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import swisseph as swe


SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

SIGN_LABELS_ZH = {
    "Aries": "白羊",
    "Taurus": "金牛",
    "Gemini": "双子",
    "Cancer": "巨蟹",
    "Leo": "狮子",
    "Virgo": "处女",
    "Libra": "天秤",
    "Scorpio": "天蝎",
    "Sagittarius": "射手",
    "Capricorn": "摩羯",
    "Aquarius": "水瓶",
    "Pisces": "双鱼",
}

PLANETS = {
    "sun": ("Sun", swe.SUN),
    "moon": ("Moon", swe.MOON),
    "mercury": ("Mercury", swe.MERCURY),
    "venus": ("Venus", swe.VENUS),
    "mars": ("Mars", swe.MARS),
    "jupiter": ("Jupiter", swe.JUPITER),
    "saturn": ("Saturn", swe.SATURN),
    "uranus": ("Uranus", swe.URANUS),
    "neptune": ("Neptune", swe.NEPTUNE),
    "pluto": ("Pluto", swe.PLUTO),
    "northNode": ("North Node", swe.TRUE_NODE),
}

MAJOR_ASPECTS = [
    ("conjunction", 0, 8),
    ("opposition", 180, 8),
    ("trine", 120, 7),
    ("square", 90, 7),
    ("sextile", 60, 5),
]

ESSENTIAL_DIGNITIES = {
    "sun": {
        "domicile": ["Leo"],
        "exaltation": ["Aries"],
        "detriment": ["Aquarius"],
        "fall": ["Libra"],
    },
    "moon": {
        "domicile": ["Cancer"],
        "exaltation": ["Taurus"],
        "detriment": ["Capricorn"],
        "fall": ["Scorpio"],
    },
    "mercury": {
        "domicile": ["Gemini", "Virgo"],
        "exaltation": ["Virgo"],
        "detriment": ["Sagittarius", "Pisces"],
        "fall": ["Pisces"],
    },
    "venus": {
        "domicile": ["Taurus", "Libra"],
        "exaltation": ["Pisces"],
        "detriment": ["Scorpio", "Aries"],
        "fall": ["Virgo"],
    },
    "mars": {
        "domicile": ["Aries", "Scorpio"],
        "exaltation": ["Capricorn"],
        "detriment": ["Libra", "Taurus"],
        "fall": ["Cancer"],
    },
    "jupiter": {
        "domicile": ["Sagittarius", "Pisces"],
        "exaltation": ["Cancer"],
        "detriment": ["Gemini", "Virgo"],
        "fall": ["Capricorn"],
    },
    "saturn": {
        "domicile": ["Capricorn", "Aquarius"],
        "exaltation": ["Libra"],
        "detriment": ["Cancer", "Leo"],
        "fall": ["Aries"],
    },
}

DIGNITY_LABELS = {
    "domicile": ("入庙", "行星处在自己掌管的星座，表达较自然、有主导感。"),
    "exaltation": ("擢升", "行星处在被提升的位置，优势更容易被放大与发挥。"),
    "detriment": ("失势", "行星处在对宫位置，表达方式需要更多调整与学习。"),
    "fall": ("落陷", "行星处在较不舒适的位置，相关主题常需要刻意练习。"),
    "peregrine": ("常态", "行星不处于主要庙旺陷弱位置，需结合宫位和相位综合判断。"),
    "point": ("轴点", "这是星盘关键轴点，不使用传统行星庙旺陷弱判断。"),
}

PLANET_INTERPRETATION_META = {
    "sun": {
        "name": "太阳",
        "theme": "核心自我与生命意志",
        "keywords": ["自我", "生命力", "目标感", "创造力"],
        "meaning": "太阳描述一个人最核心的身份感、生命驱动力，以及希望被世界看见的方式。",
        "advice": "把精力放在能让你持续发光的长期目标上，避免只为外界认可而消耗自己。",
    },
    "moon": {
        "name": "月亮",
        "theme": "情绪需求与安全感",
        "keywords": ["情绪", "本能", "安全感", "亲密"],
        "meaning": "月亮描述你的情绪反应、内在需求、依恋模式，以及最需要被照顾的心理区域。",
        "advice": "尊重自己的情绪节律，用稳定的生活习惯和亲密支持系统滋养内在安全感。",
    },
    "mercury": {
        "name": "水星",
        "theme": "思维方式与表达",
        "keywords": ["思考", "沟通", "学习", "判断"],
        "meaning": "水星描述你的学习方式、语言表达、信息处理速度，以及如何理解复杂问题。",
        "advice": "建立清晰的信息筛选和表达结构，重要沟通尽量先整理逻辑再输出。",
    },
    "venus": {
        "name": "金星",
        "theme": "关系审美与价值选择",
        "keywords": ["关系", "审美", "吸引力", "价值"],
        "meaning": "金星描述你如何建立好感、体验愉悦、表达爱意，以及对美与价值的偏好。",
        "advice": "把关系中的真实需求说清楚，也让审美和价值感成为选择的重要标准。",
    },
    "mars": {
        "name": "火星",
        "theme": "行动力与欲望驱动",
        "keywords": ["行动", "竞争", "勇气", "欲望"],
        "meaning": "火星描述你的行动模式、冲突反应、竞争方式，以及推进目标时的原始动力。",
        "advice": "把冲劲导入可执行计划，避免在压力下用过度对抗或急躁来解决问题。",
    },
    "jupiter": {
        "name": "木星",
        "theme": "成长机会与信念扩张",
        "keywords": ["成长", "机会", "信念", "视野"],
        "meaning": "木星描述你容易获得增长、贵人、机会与信心的领域，也代表世界观的扩张。",
        "advice": "在有潜力的方向上保持开放，但要用现实边界过滤过度乐观。",
    },
    "saturn": {
        "name": "土星",
        "theme": "责任边界与长期功课",
        "keywords": ["责任", "边界", "纪律", "成熟"],
        "meaning": "土星描述你需要长期修炼的课题、压力来源、责任结构，以及成熟后的稳定能力。",
        "advice": "用制度、节奏和耐心处理压力，把限制转化成可以积累的专业能力。",
    },
    "northNode": {
        "name": "北交",
        "theme": "灵魂成长方向",
        "keywords": ["成长", "课题", "方向", "突破"],
        "meaning": "北交点描述人生需要逐渐发展出的新能力，以及走出惯性舒适区的成长方向。",
        "advice": "不要只重复熟悉模式，主动练习北交所在领域的选择和能力。",
    },
    "ascendant": {
        "name": "ASC 上升",
        "theme": "人格面具与生命入口",
        "keywords": ["外在气质", "第一反应", "自我呈现", "人生入口"],
        "meaning": "上升点描述你进入世界的方式、别人最先感受到的气质，以及人生展开的入口。",
        "advice": "善用你的外在风格与第一反应，但不要让表层防御掩盖真正需求。",
    },
    "mc": {
        "name": "MC 天顶",
        "theme": "事业方向与社会形象",
        "keywords": ["事业", "声望", "目标", "社会角色"],
        "meaning": "天顶描述职业发展、公共形象、社会成就感，以及你希望被外界认可的方向。",
        "advice": "把事业目标拆成长期路径，让社会角色和内在价值保持一致。",
    },
}


@dataclass(frozen=True)
class BirthData:
    local_date: str
    local_time: str
    timezone: str
    latitude: float
    longitude: float
    place: str = ""
    house_system: str = "P"
    zodiac: str = "tropical"


def calculate_western_chart(birth: BirthData | dict[str, Any]) -> dict[str, Any]:
    """Return a modern Western natal chart using Swiss Ephemeris.

    Defaults are tropical zodiac and Placidus houses. The input time is treated
    as the user's local civil birth time and converted to UTC through zoneinfo.
    """
    data = _coerce_birth_data(birth)
    if data.zodiac.lower() != "tropical":
        raise ValueError("Only tropical zodiac is currently supported.")

    local_dt = _local_datetime(data.local_date, data.local_time, data.timezone)
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    jd_ut = swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600,
    )

    house_system = data.house_system.encode("ascii")
    cusps, ascmc = swe.houses_ex(jd_ut, data.latitude, data.longitude, house_system)
    cusp_values = [_normalize(cusp) for cusp in cusps[:12]]

    planets: dict[str, Any] = {}
    for key, (name, swe_id) in PLANETS.items():
        position, flags = swe.calc_ut(jd_ut, swe_id, swe.FLG_SWIEPH | swe.FLG_SPEED)
        longitude = _normalize(position[0])
        planets[key] = {
            **_degree_payload(longitude),
            "name": name,
            "house": _house_from_longitude(longitude, cusp_values),
            "speed": round(float(position[3]), 6),
            "retrograde": bool(position[3] < 0),
            "flags": int(flags),
        }

    south_node_longitude = _normalize(planets["northNode"]["longitude"] + 180)
    planets["southNode"] = {
        **_degree_payload(south_node_longitude),
        "name": "South Node",
        "house": _house_from_longitude(south_node_longitude, cusp_values),
        "speed": planets["northNode"]["speed"],
        "retrograde": planets["northNode"]["retrograde"],
        "flags": planets["northNode"]["flags"],
    }

    houses = [
        {"house": index + 1, **_degree_payload(cusp)}
        for index, cusp in enumerate(cusp_values)
    ]
    ascendant = {**_degree_payload(ascmc[0]), "name": "Ascendant"}
    mc = {**_degree_payload(ascmc[1]), "name": "Midheaven"}
    point_bodies = {**planets, "ascendant": ascendant, "mc": mc}
    astrology_interpretation = {
        "summary": _build_summary(point_bodies),
        "planet_interpretations": _build_planet_interpretations(point_bodies),
    }

    chart = {
        "schema": "western_natal_chart.v1",
        "settings": {
            "astrology_type": "Western astrology",
            "zodiac": "Tropical",
            "house_system": "Placidus" if data.house_system.upper() == "P" else data.house_system,
            "house_system_code": data.house_system.upper(),
            "ephemeris": "Swiss Ephemeris via pyswisseph",
        },
        "input": {
            "date": data.local_date,
            "time": data.local_time,
            "timezone": data.timezone,
            "place": data.place,
            "latitude": data.latitude,
            "longitude": data.longitude,
        },
        "time": {
            "local_iso": local_dt.isoformat(),
            "utc_iso": utc_dt.isoformat(),
            "julian_day_ut": round(jd_ut, 8),
        },
        "sun": planets["sun"],
        "moon": planets["moon"],
        "ascendant": ascendant,
        "mc": mc,
        "planets": planets,
        "houses": houses,
        "aspects": _build_aspects(point_bodies),
        "astrology_interpretation": astrology_interpretation,
        "_meta": {
            "status": "ready",
            "provider": "pyswisseph",
            "message": "当前排盘：现代西占 · Tropical 回归黄道 · Placidus/P制",
        },
    }

    # Backward-compatible top-level aliases used by the current frontend.
    chart.update({key: planets[key] for key in planets})
    return chart


def _coerce_birth_data(birth: BirthData | dict[str, Any]) -> BirthData:
    if isinstance(birth, BirthData):
        return birth
    true_solar = birth.get("true_solar") or {}
    return BirthData(
        local_date=str(birth.get("solar_date") or true_solar.get("date") or "1990-01-01"),
        local_time=str(birth.get("solar_time") or true_solar.get("time") or "12:00"),
        timezone=str(birth.get("timezone") or "Asia/Shanghai"),
        latitude=float(birth.get("latitude", 30.0)),
        longitude=float(birth.get("longitude", 120.0)),
        place=str(birth.get("city") or birth.get("place") or ""),
        house_system=str(birth.get("house_system") or "P"),
        zodiac=str(birth.get("zodiac") or "tropical"),
    )


def _local_datetime(local_date: str, local_time: str, timezone: str) -> datetime:
    naive = datetime.strptime(f"{local_date} {local_time}", "%Y-%m-%d %H:%M")
    return naive.replace(tzinfo=ZoneInfo(timezone))


def _degree_payload(longitude: float) -> dict[str, Any]:
    longitude = _normalize(longitude)
    sign = SIGNS[int(longitude // 30) % 12]
    degree_in_sign = longitude % 30
    return {
        "sign": sign,
        "sign_zh": SIGN_LABELS_ZH[sign],
        "degree": round(degree_in_sign, 6),
        "degree_display": _format_degree(degree_in_sign),
        "longitude": round(longitude, 6),
    }


def _format_degree(degree: float) -> str:
    whole = int(degree)
    minutes_float = (degree - whole) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60)
    if seconds == 60:
        seconds = 0
        minutes += 1
    if minutes == 60:
        minutes = 0
        whole += 1
    return f"{whole:02d}°{minutes:02d}'{seconds:02d}\""


def _build_summary(bodies: dict[str, Any]) -> dict[str, Any]:
    sun = bodies.get("sun", {})
    moon = bodies.get("moon", {})
    asc = bodies.get("ascendant", {})
    mc = bodies.get("mc", {})
    return {
        "title": "核心星盘摘要",
        "items": [
            f"太阳 {sun.get('sign_zh', sun.get('sign', ''))} {sun.get('degree_display', '')}",
            f"月亮 {moon.get('sign_zh', moon.get('sign', ''))} {moon.get('degree_display', '')}",
            f"上升 {asc.get('sign_zh', asc.get('sign', ''))} {asc.get('degree_display', '')}",
            f"天顶 {mc.get('sign_zh', mc.get('sign', ''))} {mc.get('degree_display', '')}",
        ],
        "description": "摘要用于快速把握人格核心、情绪需求、外在呈现与事业方向。点击星体可查看更细的星座、宫位和行动建议。",
    }


def _build_planet_interpretations(bodies: dict[str, Any]) -> dict[str, Any]:
    interpretations: dict[str, Any] = {}
    for key, meta in PLANET_INTERPRETATION_META.items():
        body = bodies.get(key)
        if not body:
            continue
        payload = _interpretation_payload(key, body, meta)
        interpretations[key] = payload
        if key == "northNode":
            interpretations["north_node"] = payload
    return interpretations


def _interpretation_payload(key: str, body: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    sign = body.get("sign_zh") or body.get("sign") or ""
    degree = body.get("degree_display") or ""
    house = body.get("house")
    house_text = f"第{house}宫" if house else "轴点"
    name = meta["name"]
    dignity = _dignity_for(key, body.get("sign"))
    return {
        "key": "north_node" if key == "northNode" else key,
        "name": name,
        "position": {
            "sign": body.get("sign"),
            "sign_zh": sign,
            "degree": degree,
            "longitude": body.get("longitude"),
            "house": house,
        },
        "dignity": dignity,
        "position_text": f"{sign} {degree}" + (f" · {house_text}" if house else ""),
        "theme": meta["theme"],
        "keywords": meta["keywords"],
        "basic_meaning": meta["meaning"],
        "personalized_interpretation": f"{name}落在{sign}，会让“{meta['theme']}”带有{sign}式的表达方式；它位于{house_text}，说明这股能量更容易在{_house_topic(house)}中被看见。",
        "house_interpretation": f"{house_text}强调{_house_topic(house)}。当{name}落入这里，相关主题会成为你理解自己和做选择时不可忽略的线索。",
        "advice": meta["advice"],
    }


def _dignity_for(key: str, sign: str | None) -> dict[str, str]:
    if key in {"northNode", "ascendant", "mc"}:
        label, description = DIGNITY_LABELS["point"]
        return {"status": "point", "label": label, "description": description}
    rules = ESSENTIAL_DIGNITIES.get(key)
    status = "peregrine"
    if rules and sign:
        for candidate in ("domicile", "exaltation", "detriment", "fall"):
            if sign in rules.get(candidate, []):
                status = candidate
                break
    label, description = DIGNITY_LABELS[status]
    return {"status": status, "label": label, "description": description}


def _house_topic(house: int | None) -> str:
    topics = {
        1: "自我呈现、身体状态和人生开场方式",
        2: "金钱价值、安全感和资源管理",
        3: "学习沟通、信息交换和近距离环境",
        4: "家庭根基、内在安全和私人生活",
        5: "创造力、恋爱表达和自我愉悦",
        6: "工作流程、健康习惯和日常秩序",
        7: "亲密关系、合作伙伴和一对一互动",
        8: "深层关系、共享资源和心理转化",
        9: "高等学习、远方经验和信念系统",
        10: "事业目标、社会身份和公众成就",
        11: "社群网络、长期愿景和团队关系",
        12: "潜意识、隐秘动力、疗愈和幕后空间",
    }
    return topics.get(house or 0, "人生关键轴线与外在定位")


def _house_from_longitude(longitude: float, cusps: list[float]) -> int:
    degree = _normalize(longitude)
    for index, start in enumerate(cusps):
        end = cusps[(index + 1) % 12]
        if start <= end:
            in_house = start <= degree < end
        else:
            in_house = degree >= start or degree < end
        if in_house:
            return index + 1
    return 12


def _build_aspects(planets: dict[str, Any]) -> list[dict[str, Any]]:
    keys = [
        "sun",
        "moon",
        "mercury",
        "venus",
        "mars",
        "jupiter",
        "saturn",
        "uranus",
        "neptune",
        "pluto",
        "northNode",
        "ascendant",
        "mc",
    ]
    aspects: list[dict[str, Any]] = []
    for left_index, left in enumerate(keys):
        for right in keys[left_index + 1 :]:
            diff = abs(planets[left]["longitude"] - planets[right]["longitude"]) % 360
            angle = min(diff, 360 - diff)
            for aspect_name, target, orb in MAJOR_ASPECTS:
                delta = abs(angle - target)
                if delta <= orb:
                    aspects.append(
                        {
                            "from": left,
                            "to": right,
                            "type": aspect_name,
                            "angle": target,
                            "orb": round(delta, 4),
                            "actual_angle": round(angle, 4),
                        }
                    )
                    break
    return sorted(aspects, key=lambda item: (item["orb"], item["angle"]))


def _normalize(degree: float) -> float:
    return float(degree) % 360
