from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
import json
import math
from pathlib import Path
from typing import Optional


class WuxingElement(str, Enum):
    WOOD = "木"
    FIRE = "火"
    EARTH = "土"
    METAL = "金"
    WATER = "水"


class YinYang(str, Enum):
    YANG = "阳"
    YIN = "阴"


class DayMasterStrength(str, Enum):
    STRONG = "身强"
    WEAK = "身弱"
    NEUTRAL = "中和"
    CONG_GE = "从格"


class QuestionTemplate(str, Enum):
    A = "A"
    B = "B"
    C = "C"


HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

STEM_PROPERTIES = {
    "甲": {"element": WuxingElement.WOOD, "yin_yang": YinYang.YANG},
    "乙": {"element": WuxingElement.WOOD, "yin_yang": YinYang.YIN},
    "丙": {"element": WuxingElement.FIRE, "yin_yang": YinYang.YANG},
    "丁": {"element": WuxingElement.FIRE, "yin_yang": YinYang.YIN},
    "戊": {"element": WuxingElement.EARTH, "yin_yang": YinYang.YANG},
    "己": {"element": WuxingElement.EARTH, "yin_yang": YinYang.YIN},
    "庚": {"element": WuxingElement.METAL, "yin_yang": YinYang.YANG},
    "辛": {"element": WuxingElement.METAL, "yin_yang": YinYang.YIN},
    "壬": {"element": WuxingElement.WATER, "yin_yang": YinYang.YANG},
    "癸": {"element": WuxingElement.WATER, "yin_yang": YinYang.YIN},
}

BRANCH_PROPERTIES = {
    "子": {"element": WuxingElement.WATER, "yin_yang": YinYang.YIN},
    "丑": {"element": WuxingElement.EARTH, "yin_yang": YinYang.YIN},
    "寅": {"element": WuxingElement.WOOD, "yin_yang": YinYang.YANG},
    "卯": {"element": WuxingElement.WOOD, "yin_yang": YinYang.YIN},
    "辰": {"element": WuxingElement.EARTH, "yin_yang": YinYang.YANG},
    "巳": {"element": WuxingElement.FIRE, "yin_yang": YinYang.YIN},
    "午": {"element": WuxingElement.FIRE, "yin_yang": YinYang.YANG},
    "未": {"element": WuxingElement.EARTH, "yin_yang": YinYang.YIN},
    "申": {"element": WuxingElement.METAL, "yin_yang": YinYang.YANG},
    "酉": {"element": WuxingElement.METAL, "yin_yang": YinYang.YIN},
    "戌": {"element": WuxingElement.EARTH, "yin_yang": YinYang.YANG},
    "亥": {"element": WuxingElement.WATER, "yin_yang": YinYang.YANG},
}

BRANCH_HIDDEN_STEMS = {
    "子": [("癸", 3)],
    "丑": [("己", 3), ("癸", 1), ("辛", 2)],
    "寅": [("甲", 3), ("丙", 1), ("戊", 2)],
    "卯": [("乙", 3)],
    "辰": [("戊", 3), ("乙", 1), ("癸", 2)],
    "巳": [("丙", 3), ("庚", 2), ("戊", 1)],
    "午": [("丁", 3), ("己", 2)],
    "未": [("己", 3), ("丁", 1), ("乙", 2)],
    "申": [("庚", 3), ("壬", 2), ("戊", 1)],
    "酉": [("辛", 3)],
    "戌": [("戊", 3), ("辛", 1), ("丁", 2)],
    "亥": [("壬", 3), ("甲", 2)],
}

MONTH_STRENGTH_MULTIPLIER = {
    "寅": {WuxingElement.WOOD: 3.0, WuxingElement.FIRE: 1.5, WuxingElement.EARTH: 0.5, WuxingElement.METAL: 0.3, WuxingElement.WATER: 1.0},
    "卯": {WuxingElement.WOOD: 3.5, WuxingElement.FIRE: 1.5, WuxingElement.EARTH: 0.3, WuxingElement.METAL: 0.3, WuxingElement.WATER: 1.0},
    "辰": {WuxingElement.WOOD: 1.5, WuxingElement.FIRE: 1.0, WuxingElement.EARTH: 3.0, WuxingElement.METAL: 0.5, WuxingElement.WATER: 0.5},
    "巳": {WuxingElement.WOOD: 0.5, WuxingElement.FIRE: 3.0, WuxingElement.EARTH: 1.5, WuxingElement.METAL: 1.0, WuxingElement.WATER: 0.3},
    "午": {WuxingElement.WOOD: 0.5, WuxingElement.FIRE: 3.5, WuxingElement.EARTH: 1.5, WuxingElement.METAL: 0.3, WuxingElement.WATER: 0.3},
    "未": {WuxingElement.WOOD: 1.0, WuxingElement.FIRE: 1.5, WuxingElement.EARTH: 3.0, WuxingElement.METAL: 0.5, WuxingElement.WATER: 0.5},
    "申": {WuxingElement.WOOD: 0.3, WuxingElement.FIRE: 0.5, WuxingElement.EARTH: 1.5, WuxingElement.METAL: 3.0, WuxingElement.WATER: 1.0},
    "酉": {WuxingElement.WOOD: 0.3, WuxingElement.FIRE: 0.3, WuxingElement.EARTH: 1.0, WuxingElement.METAL: 3.5, WuxingElement.WATER: 1.5},
    "戌": {WuxingElement.WOOD: 0.5, WuxingElement.FIRE: 1.0, WuxingElement.EARTH: 3.0, WuxingElement.METAL: 1.5, WuxingElement.WATER: 0.5},
    "亥": {WuxingElement.WOOD: 1.0, WuxingElement.FIRE: 0.3, WuxingElement.EARTH: 0.3, WuxingElement.METAL: 0.5, WuxingElement.WATER: 3.0},
    "子": {WuxingElement.WOOD: 1.0, WuxingElement.FIRE: 0.3, WuxingElement.EARTH: 0.3, WuxingElement.METAL: 1.0, WuxingElement.WATER: 3.5},
    "丑": {WuxingElement.WOOD: 0.5, WuxingElement.FIRE: 0.5, WuxingElement.EARTH: 3.0, WuxingElement.METAL: 1.5, WuxingElement.WATER: 1.0},
}

NAYIN_TABLE = {
    ("甲", "子"): "海中金", ("乙", "丑"): "海中金", ("丙", "寅"): "炉中火", ("丁", "卯"): "炉中火",
    ("戊", "辰"): "大林木", ("己", "巳"): "大林木", ("庚", "午"): "路旁土", ("辛", "未"): "路旁土",
    ("壬", "申"): "剑锋金", ("癸", "酉"): "剑锋金", ("甲", "戌"): "山头火", ("乙", "亥"): "山头火",
    ("丙", "子"): "涧下水", ("丁", "丑"): "涧下水", ("戊", "寅"): "城头土", ("己", "卯"): "城头土",
    ("庚", "辰"): "白蜡金", ("辛", "巳"): "白蜡金", ("壬", "午"): "杨柳木", ("癸", "未"): "杨柳木",
    ("甲", "申"): "泉中水", ("乙", "酉"): "泉中水", ("丙", "戌"): "屋上土", ("丁", "亥"): "屋上土",
    ("戊", "子"): "霹雳火", ("己", "丑"): "霹雳火", ("庚", "寅"): "松柏木", ("辛", "卯"): "松柏木",
    ("壬", "辰"): "长流水", ("癸", "巳"): "长流水", ("甲", "午"): "沙中金", ("乙", "未"): "沙中金",
    ("丙", "申"): "山下火", ("丁", "酉"): "山下火", ("戊", "戌"): "平地木", ("己", "亥"): "平地木",
    ("庚", "子"): "壁上土", ("辛", "丑"): "壁上土", ("壬", "寅"): "金箔金", ("癸", "卯"): "金箔金",
    ("甲", "辰"): "覆灯火", ("乙", "巳"): "覆灯火", ("丙", "午"): "天河水", ("丁", "未"): "天河水",
    ("戊", "申"): "大驿土", ("己", "酉"): "大驿土", ("庚", "戌"): "钗钏金", ("辛", "亥"): "钗钏金",
    ("壬", "子"): "桑柘木", ("癸", "丑"): "桑柘木", ("甲", "寅"): "大溪水", ("乙", "卯"): "大溪水",
    ("丙", "辰"): "沙中土", ("丁", "巳"): "沙中土", ("戊", "午"): "天上火", ("己", "未"): "天上火",
    ("庚", "申"): "石榴木", ("辛", "酉"): "石榴木", ("壬", "戌"): "大海水", ("癸", "亥"): "大海水",
}

SOLAR_TERMS = ["小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑", "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"]
MONTH_START_TERM_INDEX = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 0]
MONTH_BRANCHES_FROM_YIN = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]

# 1900-2099 常用节气日期近似常数，足够支撑月柱/年柱边界判断。
SOLAR_TERM_CENTURY_C = {
    20: [6.11, 20.84, 4.6295, 19.4599, 6.3826, 21.4155, 5.59, 20.888, 6.318, 21.86, 6.5, 22.20, 7.928, 23.65, 8.35, 23.95, 8.44, 23.822, 9.098, 24.218, 8.218, 23.08, 7.9, 22.60],
    21: [5.4055, 20.12, 3.87, 18.74, 5.63, 20.646, 4.81, 20.1, 5.52, 21.04, 5.678, 21.37, 7.108, 22.83, 7.5, 23.13, 7.646, 23.042, 8.318, 23.438, 7.438, 22.36, 7.18, 21.94],
}

SOLAR_TERM_MONTH = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12]
SOLAR_TERM_HOUR = {
    0: 6, 1: 6, 2: 5, 3: 12, 4: 6, 5: 12, 6: 6, 7: 12, 8: 6, 9: 12, 10: 6, 11: 12,
    12: 6, 13: 12, 14: 6, 15: 12, 16: 6, 17: 12, 18: 6, 19: 12, 20: 6, 21: 12, 22: 6, 23: 12,
}
SOLAR_TERM_DAY_ADJUSTMENTS = {
    (1982, 0): 1, (2019, 0): -1, (2082, 0): 1,
    (2026, 1): -1,
    (2084, 2): 1, (2000, 2): 1,
    (2021, 3): -1,
    (2008, 6): 1,
    (2008, 7): 1,
    (2002, 8): 1,
    (1928, 9): 1,
    (1922, 11): 1,
    (1925, 12): 1, (2016, 12): 1,
    (1922, 13): 1,
    (2002, 14): 1,
    (1927, 15): 1,
    (1942, 17): 1,
    (2089, 18): 1,
    (2089, 19): 1,
    (1978, 20): 1,
    (1954, 21): 1,
    (1918, 22): -1, (2021, 22): 1,
    (1918, 23): -1, (2021, 23): 1,
}


@dataclass
class Pillar:
    stem: str
    branch: str
    stem_element: WuxingElement
    branch_element: WuxingElement
    hidden_stems: list[tuple[str, int]]
    nayin: str
    yin_yang: YinYang


@dataclass
class WuxingScore:
    wood: float = 0.0
    fire: float = 0.0
    earth: float = 0.0
    metal: float = 0.0
    water: float = 0.0
    yin_star: float = 0.0
    bijie: float = 0.0
    shi_shang: float = 0.0
    cai_star: float = 0.0
    guan_sha: float = 0.0

    def to_percentage(self) -> dict:
        total = self.wood + self.fire + self.earth + self.metal + self.water
        if total == 0:
            return {}
        return {
            "wood": round(self.wood / total * 100, 1),
            "fire": round(self.fire / total * 100, 1),
            "earth": round(self.earth / total * 100, 1),
            "metal": round(self.metal / total * 100, 1),
            "water": round(self.water / total * 100, 1),
        }

    def ten_gods_percentage(self) -> dict:
        total = self.yin_star + self.bijie + self.shi_shang + self.cai_star + self.guan_sha
        if total == 0:
            return {}
        return {
            "yin_star": round(self.yin_star / total * 100, 1),
            "bijie": round(self.bijie / total * 100, 1),
            "shi_shang": round(self.shi_shang / total * 100, 1),
            "cai_star": round(self.cai_star / total * 100, 1),
            "guan_sha": round(self.guan_sha / total * 100, 1),
        }


@dataclass
class DaYun:
    index: int
    stem: str
    branch: str
    element: WuxingElement
    ten_god: str
    start_age: int
    end_age: int
    start_year: int
    end_year: int


@dataclass
class PreliminaryAnalysis:
    strength: DayMasterStrength
    confidence: str
    key_factors: list[str]
    question_template: QuestionTemplate
    supporting_ratio: float
    opposing_ratio: float


CITY_COORDINATES = {
    "北京": {"longitude": 116.4074, "latitude": 39.9042},
    "上海": {"longitude": 121.4737, "latitude": 31.2304},
    "天津": {"longitude": 117.3616, "latitude": 39.3434},
    "重庆": {"longitude": 106.5516, "latitude": 29.5630},
    "哈尔滨": {"longitude": 126.6424, "latitude": 45.7569},
    "长春": {"longitude": 125.3245, "latitude": 43.8868},
    "沈阳": {"longitude": 123.4315, "latitude": 41.8057},
    "呼和浩特": {"longitude": 111.7517, "latitude": 40.8420},
    "石家庄": {"longitude": 114.5149, "latitude": 38.0428},
    "太原": {"longitude": 112.5489, "latitude": 37.8706},
    "济南": {"longitude": 117.0009, "latitude": 36.6758},
    "郑州": {"longitude": 113.6254, "latitude": 34.7466},
    "西安": {"longitude": 108.9480, "latitude": 34.2658},
    "兰州": {"longitude": 103.8343, "latitude": 36.0611},
    "西宁": {"longitude": 101.7782, "latitude": 36.6171},
    "银川": {"longitude": 106.2782, "latitude": 38.4664},
    "乌鲁木齐": {"longitude": 87.6177, "latitude": 43.8256},
    "拉萨": {"longitude": 91.1322, "latitude": 29.6625},
    "成都": {"longitude": 104.0665, "latitude": 30.5723},
    "南充": {"longitude": 106.1110, "latitude": 30.8370},
    "贵阳": {"longitude": 106.7135, "latitude": 26.5783},
    "昆明": {"longitude": 102.8329, "latitude": 24.8801},
    "南宁": {"longitude": 108.3665, "latitude": 22.8170},
    "海口": {"longitude": 110.1999, "latitude": 20.0444},
    "武汉": {"longitude": 114.3054, "latitude": 30.5931},
    "长沙": {"longitude": 112.9388, "latitude": 28.2278},
    "南昌": {"longitude": 115.8579, "latitude": 28.6820},
    "合肥": {"longitude": 117.2272, "latitude": 31.8206},
    "南京": {"longitude": 118.7969, "latitude": 32.0603},
    "杭州": {"longitude": 120.1551, "latitude": 30.2741},
    "福州": {"longitude": 119.2965, "latitude": 26.0745},
    "广州": {"longitude": 113.2644, "latitude": 23.1291},
    "深圳": {"longitude": 114.0579, "latitude": 22.5431},
    "香港": {"longitude": 114.1694, "latitude": 22.3193},
    "澳门": {"longitude": 113.5439, "latitude": 22.1987},
    "台北": {"longitude": 121.5654, "latitude": 25.0330},
}


def _load_city_data() -> tuple[dict, list[dict], list[dict]]:
    fallback_options = [{"value": name, "label": name} for name in sorted(CITY_COORDINATES)]
    path = Path(__file__).resolve().parents[1] / "data" / "cities.json"
    if not path.exists():
        return CITY_COORDINATES, fallback_options, []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return CITY_COORDINATES, fallback_options, []

    coordinates = dict(CITY_COORDINATES)
    coordinates.update(data.get("coordinates", {}))
    options = data.get("options") or fallback_options
    hierarchy = data.get("hierarchy") or []
    return coordinates, options, hierarchy


CITY_COORDINATES, CITY_OPTIONS, CITY_HIERARCHY = _load_city_data()


def list_city_options() -> list[dict]:
    return CITY_OPTIONS


def list_region_hierarchy() -> list[dict]:
    return CITY_HIERARCHY

BEIJING_LONGITUDE = 120.0
POSITION_BASE_WEIGHT = {"year_stem": 1.0, "month_stem": 1.5, "day_stem": 1.5, "hour_stem": 1.0, "year_branch": 1.0, "month_branch": 2.0, "day_branch": 1.5, "hour_branch": 1.0}
HIDDEN_STEM_WEIGHT = {3: 1.0, 2: 0.6, 1: 0.3}


def calculate_true_solar_time(dt: datetime, longitude: float) -> tuple[datetime, int]:
    if longitude >= BEIJING_LONGITUDE:
        local_mean_time_correction = (BEIJING_LONGITUDE - longitude) * 4
    elif longitude < 110:
        local_mean_time_correction = (longitude - BEIJING_LONGITUDE) * 4
    else:
        local_mean_time_correction = (longitude - CITY_COORDINATES["北京"]["longitude"]) * 4
    equation_of_time = _calculate_equation_of_time(dt.timetuple().tm_yday)
    total_correction_minutes = round(local_mean_time_correction - equation_of_time)
    return dt + timedelta(minutes=total_correction_minutes), total_correction_minutes


def _calculate_equation_of_time(day_of_year: int) -> float:
    b = math.radians((360 / 365.0) * (day_of_year - 81))
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def get_city_coordinates(city: str) -> Optional[dict]:
    if city in CITY_COORDINATES:
        return CITY_COORDINATES[city]
    clean_city = city.replace("市", "").replace("省", "").replace("自治区", "")
    if clean_city in CITY_COORDINATES:
        return CITY_COORDINATES[clean_city]
    for key, value in CITY_COORDINATES.items():
        if key in city or city in key:
            return value
    return None


def solar_to_lunar(year: int, month: int, day: int) -> dict:
    try:
        from lunardate import LunarDate

        lunar = LunarDate.fromSolarDate(year, month, day)
        return {"year": lunar.year, "month": lunar.month, "day": lunar.day, "is_leap_month": lunar.isLeapMonth, "gz_year": _get_gz_year(lunar.year)}
    except ImportError:
        return {"year": year, "month": month, "day": day, "is_leap_month": False, "gz_year": "未知", "note": "需安装 lunardate 库获取精确农历"}


def _get_gz_year(lunar_year: int) -> str:
    offset = (lunar_year - 1984) % 60
    return f"{HEAVENLY_STEMS[offset % 10]}{EARTHLY_BRANCHES[offset % 12]}"


def _get_solar_term(year: int, term_index: int) -> datetime:
    century = 20 if year < 2000 else 21
    c = SOLAR_TERM_CENTURY_C[century][term_index]
    y = year % 100
    day = int(y * 0.2422 + c) - int((y - 1) / 4)
    day += SOLAR_TERM_DAY_ADJUSTMENTS.get((year, term_index), 0)
    month = SOLAR_TERM_MONTH[term_index]
    return datetime(year, month, day, SOLAR_TERM_HOUR.get(term_index, 6), 0)


def calculate_year_pillar(solar_dt: datetime) -> Pillar:
    year = solar_dt.year
    if solar_dt < _get_solar_term(year, 2):
        year -= 1
    offset = (year - 1984) % 60
    return _build_pillar(HEAVENLY_STEMS[offset % 10], EARTHLY_BRANCHES[offset % 12])


def calculate_month_pillar(solar_dt: datetime) -> Pillar:
    month_branch_index = _get_month_branch_index(solar_dt)
    branch = MONTH_BRANCHES_FROM_YIN[month_branch_index]
    year_stem_index = HEAVENLY_STEMS.index(calculate_year_pillar(solar_dt).stem)
    month_stem_starts = {0: 2, 5: 2, 1: 4, 6: 4, 2: 6, 7: 6, 3: 8, 8: 8, 4: 0, 9: 0}
    stem = HEAVENLY_STEMS[(month_stem_starts[year_stem_index] + month_branch_index) % 10]
    return _build_pillar(stem, branch)


def _get_month_branch_index(solar_dt: datetime) -> int:
    year = solar_dt.year
    starts = [(_get_solar_term(year, term_idx), idx) for idx, term_idx in enumerate(MONTH_START_TERM_INDEX[:-1])]
    starts.append((_get_solar_term(year, 0), 11))
    starts.append((_get_solar_term(year + 1, 0), 11))
    starts.append((_get_solar_term(year - 1, 22), 10))
    starts.sort(key=lambda item: item[0])

    current_index = 11
    for term_dt, branch_index in starts:
        if solar_dt >= term_dt:
            current_index = branch_index
        else:
            break
    return current_index


def calculate_day_pillar(solar_dt: datetime) -> Pillar:
    # Calibrated against known almanac case: 2001-11-16 is 癸未.
    base_date = date(2001, 11, 16)
    base_stem_index = HEAVENLY_STEMS.index("癸")
    base_branch_index = EARTHLY_BRANCHES.index("未")
    days = (solar_dt.date() - base_date).days
    stem = HEAVENLY_STEMS[(base_stem_index + days) % 10]
    branch = EARTHLY_BRANCHES[(base_branch_index + days) % 12]
    return _build_pillar(stem, branch)


def calculate_hour_pillar(true_solar_dt: datetime, day_stem: str) -> Pillar:
    total_minutes = true_solar_dt.hour * 60 + true_solar_dt.minute
    if total_minutes >= 23 * 60 or total_minutes < 1 * 60:
        branch_index = 0
    else:
        branch_index = int((total_minutes - 60) // 120) + 1
        if total_minutes >= 14 * 60:
            branch_index += 1
        branch_index = min(branch_index, 11)

    day_stem_index = HEAVENLY_STEMS.index(day_stem)
    hour_stem_starts = {0: 0, 5: 0, 1: 2, 6: 2, 2: 4, 7: 4, 3: 6, 8: 6, 4: 8, 9: 8}
    stem = HEAVENLY_STEMS[(hour_stem_starts[day_stem_index] + branch_index) % 10]
    return _build_pillar(stem, EARTHLY_BRANCHES[branch_index])


def _build_pillar(stem: str, branch: str) -> Pillar:
    stem_prop = STEM_PROPERTIES[stem]
    branch_prop = BRANCH_PROPERTIES[branch]
    return Pillar(stem, branch, stem_prop["element"], branch_prop["element"], BRANCH_HIDDEN_STEMS[branch], NAYIN_TABLE.get((stem, branch), "未知"), stem_prop["yin_yang"])


def calculate_ten_god(day_master_stem: str, target_stem: str) -> str:
    dm_element = STEM_PROPERTIES[day_master_stem]["element"]
    dm_yy = STEM_PROPERTIES[day_master_stem]["yin_yang"]
    tgt_element = STEM_PROPERTIES[target_stem]["element"]
    tgt_yy = STEM_PROPERTIES[target_stem]["yin_yang"]
    same_yin_yang = dm_yy == tgt_yy
    relation = _get_wuxing_relation(dm_element, tgt_element)
    return {
        ("same", True): "比肩",
        ("same", False): "劫财",
        ("generate_out", True): "食神",
        ("generate_out", False): "伤官",
        ("generate_in", True): "偏印",
        ("generate_in", False): "正印",
        ("control_out", True): "偏财",
        ("control_out", False): "正财",
        ("control_in", True): "七杀",
        ("control_in", False): "正官",
    }.get((relation, same_yin_yang), "未知")


def _get_wuxing_relation(dm: WuxingElement, target: WuxingElement) -> str:
    if dm == target:
        return "same"
    generates = {WuxingElement.WOOD: WuxingElement.FIRE, WuxingElement.FIRE: WuxingElement.EARTH, WuxingElement.EARTH: WuxingElement.METAL, WuxingElement.METAL: WuxingElement.WATER, WuxingElement.WATER: WuxingElement.WOOD}
    controls = {WuxingElement.WOOD: WuxingElement.EARTH, WuxingElement.FIRE: WuxingElement.METAL, WuxingElement.EARTH: WuxingElement.WATER, WuxingElement.METAL: WuxingElement.WOOD, WuxingElement.WATER: WuxingElement.FIRE}
    if generates[dm] == target:
        return "generate_out"
    if generates[target] == dm:
        return "generate_in"
    if controls[dm] == target:
        return "control_out"
    if controls[target] == dm:
        return "control_in"
    return "unknown"


def calculate_all_ten_gods(pillars: dict[str, Pillar], day_master_stem: str) -> dict[str, str]:
    positions = {
        "year_stem": pillars["year"].stem,
        "month_stem": pillars["month"].stem,
        "hour_stem": pillars["hour"].stem,
        "year_branch_main": pillars["year"].hidden_stems[0][0],
        "month_branch_main": pillars["month"].hidden_stems[0][0],
        "day_branch_main": pillars["day"].hidden_stems[0][0],
        "hour_branch_main": pillars["hour"].hidden_stems[0][0],
    }
    return {pos: calculate_ten_god(day_master_stem, stem) for pos, stem in positions.items()}


def calculate_wuxing_score(pillars: dict[str, Pillar], day_master_stem: str) -> WuxingScore:
    score = WuxingScore()
    month_branch = pillars["month"].branch

    def add_score(element: WuxingElement, raw_weight: float) -> None:
        weighted = raw_weight * MONTH_STRENGTH_MULTIPLIER[month_branch][element]
        if element == WuxingElement.WOOD:
            score.wood += weighted
        elif element == WuxingElement.FIRE:
            score.fire += weighted
        elif element == WuxingElement.EARTH:
            score.earth += weighted
        elif element == WuxingElement.METAL:
            score.metal += weighted
        elif element == WuxingElement.WATER:
            score.water += weighted

    for pillar_name, weight_key in [("year", "year_stem"), ("month", "month_stem"), ("hour", "hour_stem")]:
        add_score(pillars[pillar_name].stem_element, POSITION_BASE_WEIGHT[weight_key])
    add_score(STEM_PROPERTIES[day_master_stem]["element"], POSITION_BASE_WEIGHT["day_stem"])

    for pillar_name, weight_key in [("year", "year_branch"), ("month", "month_branch"), ("day", "day_branch"), ("hour", "hour_branch")]:
        for hidden_stem, hidden_weight in pillars[pillar_name].hidden_stems:
            total_weight = POSITION_BASE_WEIGHT[weight_key] * HIDDEN_STEM_WEIGHT[hidden_weight]
            add_score(STEM_PROPERTIES[hidden_stem]["element"], total_weight)

    _calculate_ten_gods_score(score, pillars, day_master_stem, month_branch)
    return score


def _calculate_ten_gods_score(score: WuxingScore, pillars: dict[str, Pillar], day_master_stem: str, month_branch: str) -> None:
    categories = {
        "正印": "yin_star", "偏印": "yin_star",
        "比肩": "bijie", "劫财": "bijie",
        "食神": "shi_shang", "伤官": "shi_shang",
        "正财": "cai_star", "偏财": "cai_star",
        "正官": "guan_sha", "七杀": "guan_sha",
    }

    def add_ten_god_score(stem: str, base_weight: float) -> None:
        ten_god = calculate_ten_god(day_master_stem, stem)
        category = categories.get(ten_god)
        if not category:
            return
        element = STEM_PROPERTIES[stem]["element"]
        weighted = base_weight * MONTH_STRENGTH_MULTIPLIER[month_branch][element]
        setattr(score, category, getattr(score, category) + weighted)

    for pillar_name, weight_key in [("year", "year_stem"), ("month", "month_stem"), ("hour", "hour_stem")]:
        add_ten_god_score(pillars[pillar_name].stem, POSITION_BASE_WEIGHT[weight_key])
    add_ten_god_score(day_master_stem, POSITION_BASE_WEIGHT["day_stem"])

    for pillar_name, weight_key in [("year", "year_branch"), ("month", "month_branch"), ("day", "day_branch"), ("hour", "hour_branch")]:
        for hidden_stem, hidden_weight in pillars[pillar_name].hidden_stems:
            add_ten_god_score(hidden_stem, POSITION_BASE_WEIGHT[weight_key] * HIDDEN_STEM_WEIGHT[hidden_weight])


def calculate_dayun(pillars: dict[str, Pillar], birth_dt: datetime, gender: str, birth_year: int) -> tuple[list[DaYun], bool, int]:
    year_yin_yang = STEM_PROPERTIES[pillars["year"].stem]["yin_yang"]
    forward = (year_yin_yang == YinYang.YANG and gender == "male") or (year_yin_yang == YinYang.YIN and gender == "female")
    start_age = _calculate_dayun_start_age(birth_dt, forward)
    month_stem_index = HEAVENLY_STEMS.index(pillars["month"].stem)
    month_branch_index = EARTHLY_BRANCHES.index(pillars["month"].branch)
    dayuns = []

    for i in range(8):
        step = i + 1
        stem = HEAVENLY_STEMS[(month_stem_index + step if forward else month_stem_index - step) % 10]
        branch = EARTHLY_BRANCHES[(month_branch_index + step if forward else month_branch_index - step) % 12]
        start_age_i = start_age + i * 10
        dayuns.append(DaYun(i, stem, branch, STEM_PROPERTIES[stem]["element"], calculate_ten_god(pillars["day"].stem, stem), start_age_i, start_age_i + 9, birth_year + start_age_i, birth_year + start_age_i + 9))
    return dayuns, forward, start_age


def _calculate_dayun_start_age(birth_dt: datetime, forward: bool) -> int:
    days = _days_to_next_jie(birth_dt) if forward else _days_to_prev_jie(birth_dt)
    return max(1, round(days / 3))


def _jie_dates_for_years(*years: int) -> list[datetime]:
    terms = []
    for year in years:
        for term_idx in MONTH_START_TERM_INDEX:
            terms.append(_get_solar_term(year + 1, 0) if term_idx == 0 else _get_solar_term(year, term_idx))
    return sorted(set(terms))


def _days_to_next_jie(dt: datetime) -> int:
    for jie_dt in _jie_dates_for_years(dt.year, dt.year + 1):
        if jie_dt > dt:
            return max(1, (jie_dt.date() - dt.date()).days)
    return 90


def _days_to_prev_jie(dt: datetime) -> int:
    for jie_dt in reversed(_jie_dates_for_years(dt.year - 1, dt.year)):
        if jie_dt < dt:
            return max(1, (dt.date() - jie_dt.date()).days)
    return 90


def preliminary_strength_analysis(wuxing_score: WuxingScore, pillars: dict[str, Pillar], day_master_stem: str) -> PreliminaryAnalysis:
    tg_pct = wuxing_score.ten_gods_percentage()
    supporting = tg_pct.get("yin_star", 0) + tg_pct.get("bijie", 0)
    opposing = tg_pct.get("guan_sha", 0) + tg_pct.get("cai_star", 0) + tg_pct.get("shi_shang", 0)
    month_main_stem = pillars["month"].hidden_stems[0][0]
    month_ten_god = calculate_ten_god(day_master_stem, month_main_stem)
    month_supports = month_ten_god in ["正印", "偏印", "比肩", "劫财"]
    key_factors = ["月令生扶日主，得令" if month_supports else "月令不生日主，失令"]

    max_ten_god_pct = max(tg_pct.values()) if tg_pct else 0
    if max_ten_god_pct > 80 and supporting < 15 and not month_supports:
        return PreliminaryAnalysis(DayMasterStrength.CONG_GE, "medium", ["八字中一种十神力量极度集中，日主势孤，疑似从格"], QuestionTemplate.C, supporting, opposing)

    if supporting >= 50:
        key_factors.append(f"印比合计 {supporting:.0f}%，生扶有力")
        strength = DayMasterStrength.STRONG
        template = QuestionTemplate.A
        confidence = "high" if supporting >= 65 else "medium"
    elif supporting <= 35:
        key_factors.append(f"官杀财食伤合计 {opposing:.0f}%，克泄过重")
        strength = DayMasterStrength.WEAK
        template = QuestionTemplate.B
        confidence = "high" if opposing >= 65 else "medium"
    else:
        key_factors.append(f"印比 {supporting:.0f}% vs 官杀财食 {opposing:.0f}%，力量接近")
        strength = DayMasterStrength.NEUTRAL
        template = QuestionTemplate.B
        confidence = "low"

    if not month_supports and strength == DayMasterStrength.STRONG:
        key_factors.append("虽印比占优，但月令失令，置信度降低")
        confidence = "medium"
    if month_supports and strength == DayMasterStrength.WEAK:
        key_factors.append("虽克泄过重，但月令得助，置信度降低")
        confidence = "medium"
    return PreliminaryAnalysis(strength, confidence, key_factors, template, supporting, opposing)


def calculate_palaces(pillars: dict[str, Pillar], day_master_stem: str, gender: str) -> dict[str, str]:
    is_male = gender == "male"
    return {
        "spouse": pillars["day"].branch,
        "parents": _find_ten_god_in_chart(pillars, day_master_stem, ["正印"]),
        "children": _find_ten_god_in_chart(pillars, day_master_stem, ["食神", "伤官"] if is_male else ["正官", "七杀"]),
        "wealth": _find_ten_god_in_chart(pillars, day_master_stem, ["正财", "偏财"]),
    }


def _find_ten_god_in_chart(pillars: dict[str, Pillar], day_master_stem: str, target_gods: list[str]) -> str:
    for pillar_name, pos in zip(["year", "month", "day", "hour"], ["年", "月", "日", "时"]):
        pillar = pillars[pillar_name]
        if calculate_ten_god(day_master_stem, pillar.stem) in target_gods:
            return f"{pos}柱天干（{pillar.stem}）"
        for hidden_stem, _ in pillar.hidden_stems:
            if calculate_ten_god(day_master_stem, hidden_stem) in target_gods:
                return f"{pos}柱地支（{pillar.branch}中{hidden_stem}）"
    return "命中未见"


def calculate_bazi(
    solar_year: int,
    solar_month: int,
    solar_day: int,
    solar_hour: int,
    solar_minute: int,
    city: str,
    gender: str,
    unknown_time: bool = False,
) -> dict:
    coords = get_city_coordinates(city)
    if not coords:
        raise ValueError(f"未找到城市：{city}")
    if gender not in {"male", "female"}:
        raise ValueError("gender 必须为 male 或 female")

    if unknown_time:
        solar_hour = 23
        solar_minute = 0

    birth_dt_beijing = datetime(solar_year, solar_month, solar_day, solar_hour, solar_minute)
    true_solar_dt, correction_minutes = calculate_true_solar_time(birth_dt_beijing, coords["longitude"])
    chart_dt = birth_dt_beijing if unknown_time else true_solar_dt
    lunar = solar_to_lunar(solar_year, solar_month, solar_day)

    year_pillar = calculate_year_pillar(chart_dt)
    month_pillar = calculate_month_pillar(chart_dt)
    day_pillar = calculate_day_pillar(chart_dt)
    hour_pillar = calculate_hour_pillar(chart_dt, day_pillar.stem)
    pillars = {"year": year_pillar, "month": month_pillar, "day": day_pillar, "hour": hour_pillar}
    day_master_stem = day_pillar.stem

    ten_gods = calculate_all_ten_gods(pillars, day_master_stem)
    wuxing_score = calculate_wuxing_score(pillars, day_master_stem)
    dayuns, forward, start_age = calculate_dayun(pillars, chart_dt, gender, solar_year)
    preliminary = preliminary_strength_analysis(wuxing_score, pillars, day_master_stem)
    palaces = calculate_palaces(pillars, day_master_stem, gender)

    return {
        "birth_info": {
            "solar_date": f"{solar_year}-{solar_month:02d}-{solar_day:02d}",
            "solar_time": f"{solar_hour:02d}:{solar_minute:02d}",
            "city": city,
            "longitude": coords["longitude"],
            "latitude": coords["latitude"],
            "timezone": "Asia/Shanghai",
            "unknown_time": unknown_time,
            "true_solar": {"date": true_solar_dt.strftime("%Y-%m-%d"), "time": true_solar_dt.strftime("%H:%M"), "adjust_minutes": correction_minutes},
            "lunar": lunar,
        },
        "bazi_chart": {
            "pillars": {
                name: {
                    "stem": p.stem,
                    "branch": p.branch,
                    "stem_element": p.stem_element.value,
                    "branch_element": p.branch_element.value,
                    "hidden_stems": [{"stem": s, "weight": w} for s, w in p.hidden_stems],
                    "nayin": p.nayin,
                    "yin_yang": p.yin_yang.value,
                }
                for name, p in pillars.items()
            },
            "day_master": {"stem": day_master_stem, "element": STEM_PROPERTIES[day_master_stem]["element"].value, "yin_yang": STEM_PROPERTIES[day_master_stem]["yin_yang"].value},
            "ten_gods": ten_gods,
            "wuxing_score": {
                "raw": {"wood": round(wuxing_score.wood, 2), "fire": round(wuxing_score.fire, 2), "earth": round(wuxing_score.earth, 2), "metal": round(wuxing_score.metal, 2), "water": round(wuxing_score.water, 2)},
                "percentage": wuxing_score.to_percentage(),
                "ten_gods_percentage": wuxing_score.ten_gods_percentage(),
            },
            "palaces": palaces,
            "dayun": {
                "forward": forward,
                "start_age": start_age,
                "list": [
                    {"index": d.index, "stem": d.stem, "branch": d.branch, "element": d.element.value, "ten_god": d.ten_god, "start_age": d.start_age, "end_age": d.end_age, "start_year": d.start_year, "end_year": d.end_year}
                    for d in dayuns
                ],
            },
            "preliminary": {"strength": preliminary.strength.value, "confidence": preliminary.confidence, "key_factors": preliminary.key_factors, "question_template": preliminary.question_template.value, "supporting_ratio": round(preliminary.supporting_ratio, 1), "opposing_ratio": round(preliminary.opposing_ratio, 1)},
            "unknown_time_note": "出生时间不详，时柱以子时代替，时柱相关分析仅供参考" if unknown_time else None,
        },
    }


if __name__ == "__main__":
    result = calculate_bazi(1990, 5, 15, 14, 30, "上海", "female")
    chart = result["bazi_chart"]
    print("=" * 40)
    print("八字排盘结果")
    print("=" * 40)
    print(f"真太阳时修正：{result['birth_info']['true_solar']['adjust_minutes']}分钟")
    print(f"真太阳时：{result['birth_info']['true_solar']['time']}")
    print("四柱：")
    for name, cn in [("year", "年"), ("month", "月"), ("day", "日"), ("hour", "时")]:
        pillar = chart["pillars"][name]
        print(f"  {cn}柱：{pillar['stem']}{pillar['branch']}  纳音：{pillar['nayin']}")
    print(f"日主：{chart['day_master']['stem']} ({chart['day_master']['element']})")
    print(f"初判：{chart['preliminary']['strength']}")
