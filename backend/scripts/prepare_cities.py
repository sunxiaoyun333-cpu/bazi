from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "city_geo_raw.json"
OUT_PATH = ROOT / "data" / "cities.json"

DIRECT_CONTROLLED = {"北京市", "上海市", "天津市", "重庆市"}
SUFFIXES = ("特别行政区", "自治区", "省", "市", "地区", "盟", "自治州")


def strip_suffix(name: str) -> str:
    for suffix in SUFFIXES:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def add_alias(target: dict, name: str, entry: dict) -> None:
    if not name:
        return
    target.setdefault(name, entry)
    short = strip_suffix(name)
    if short and short != name:
        target.setdefault(short, entry)


def build() -> dict:
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    coordinates: dict[str, dict] = {}
    option_seen: set[str] = set()
    options: list[dict] = []
    provinces: dict[str, dict] = {}

    for item in raw:
        province = item.get("province", "").strip()
        city = item.get("city", "").strip()
        area = item.get("area", "").strip()
        if not province or not item.get("lng") or not item.get("lat"):
            continue

        try:
            entry = {
                "longitude": float(item["lng"]),
                "latitude": float(item["lat"]),
                "province": province,
                "city": city,
                "area": area,
            }
        except (TypeError, ValueError):
            continue

        province_short = strip_suffix(province)
        city_is_generic = city in {"市辖区", "县", "省直辖县级行政区划", "自治区直辖县级行政区划"}
        city_name = province if province in DIRECT_CONTROLLED and city_is_generic else city
        city_short = strip_suffix(city_name)

        if not area:
            value = city_short or province_short
            label = province_short if city_is_generic else f"{province_short} / {city_short}"
            add_alias(coordinates, value, entry)
            add_alias(coordinates, city_name, entry)
            add_alias(coordinates, province, entry)
        else:
            area_short = strip_suffix(area)
            value = f"{city_short}{area_short}" if city_short and city_is_generic else area_short
            if province in DIRECT_CONTROLLED:
                value = f"{province_short}{area_short}"
                label = f"{province_short} / {area_short}"
            elif city_is_generic:
                label = f"{province_short} / {area_short}"
            else:
                label = f"{province_short} / {city_short} / {area_short}"

            add_alias(coordinates, value, entry)
            add_alias(coordinates, area, entry)
            if city_short:
                add_alias(coordinates, f"{city_short}{area_short}", entry)

        if value and value not in option_seen:
            option_seen.add(value)
            options.append({"value": value, "label": label})

        province_node = provinces.setdefault(
            province_short,
            {"value": province_short, "label": province_short, "cities": {}},
        )
        city_value = province_short if province in DIRECT_CONTROLLED else city_short
        city_label = f"{province_short}市辖区" if province in DIRECT_CONTROLLED else city_short
        if not city_value:
            city_value = province_short
            city_label = province_short
        city_node = province_node["cities"].setdefault(
            city_value,
            {
                "value": city_value,
                "label": city_label,
                "coordinate": coordinates.get(city_value) or entry,
                "districts": {},
            },
        )
        if area:
            district_value = f"{province_short}{area_short}" if province in DIRECT_CONTROLLED else area_short
            city_node["districts"].setdefault(
                district_value,
                {
                    "value": district_value,
                    "label": area_short,
                    "coordinate": entry,
                },
            )
        else:
            city_node["coordinate"] = entry

    fallback = {
        "香港": {"longitude": 114.1694, "latitude": 22.3193, "province": "香港特别行政区", "city": "香港", "area": ""},
        "澳门": {"longitude": 113.5439, "latitude": 22.1987, "province": "澳门特别行政区", "city": "澳门", "area": ""},
        "台北": {"longitude": 121.5654, "latitude": 25.0330, "province": "台湾省", "city": "台北", "area": ""},
    }
    for name, entry in fallback.items():
        add_alias(coordinates, name, entry)
        if name not in option_seen:
            options.append({"value": name, "label": name})
            option_seen.add(name)
        provinces.setdefault(name, {"value": name, "label": name, "cities": {}})
        provinces[name]["cities"].setdefault(
            name,
            {"value": name, "label": name, "coordinate": entry, "districts": {}},
        )

    options.sort(key=lambda item: item["label"])
    hierarchy = []
    for province in sorted(provinces.values(), key=lambda item: item["label"]):
        cities = []
        for city in sorted(province["cities"].values(), key=lambda item: item["label"]):
            districts = sorted(city["districts"].values(), key=lambda item: item["label"])
            cities.append(
                {
                    "value": city["value"],
                    "label": city["label"],
                    "coordinate": city["coordinate"],
                    "districts": districts,
                }
            )
        hierarchy.append({"value": province["value"], "label": province["label"], "cities": cities})
    return {"coordinates": coordinates, "options": options, "hierarchy": hierarchy}


if __name__ == "__main__":
    OUT_PATH.write_text(json.dumps(build(), ensure_ascii=False, indent=2), encoding="utf-8")
    data = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    print(
        f"城市数据已生成：{len(data['coordinates'])} 个可匹配名称，"
        f"{len(data['options'])} 个下拉选项，{len(data['hierarchy'])} 个省级选项"
    )
