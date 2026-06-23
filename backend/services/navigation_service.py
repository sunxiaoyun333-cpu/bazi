from __future__ import annotations

from typing import Any


MODULE_TITLES = {
    "talent": "人生天赋",
    "career": "职业方向",
    "city": "适合发展的城市",
    "life_lesson": "人生课题",
}

CANDIDATE_CITIES = [
    "北京",
    "上海",
    "深圳",
    "广州",
    "杭州",
    "成都",
    "重庆",
    "武汉",
    "南京",
    "苏州",
    "厦门",
    "香港",
    "新加坡",
    "东京",
]

CITY_PROFILES = {
    "北京": {"elements": ["金", "水"], "tags": ["资源密集", "平台", "政策", "学术"]},
    "上海": {"elements": ["金", "水"], "tags": ["国际化", "平台", "金融", "品牌"]},
    "深圳": {"elements": ["火", "木"], "tags": ["创新", "科技", "速度", "创业"]},
    "广州": {"elements": ["火", "土"], "tags": ["商业", "供应链", "务实", "生活"]},
    "杭州": {"elements": ["木", "火"], "tags": ["互联网", "内容", "AI", "产品"]},
    "成都": {"elements": ["土", "木"], "tags": ["生活", "创意", "稳定", "消费"]},
    "重庆": {"elements": ["火", "土"], "tags": ["韧性", "增长", "商业", "执行"]},
    "武汉": {"elements": ["水", "木"], "tags": ["教育", "交通", "技术", "连接"]},
    "南京": {"elements": ["木", "金"], "tags": ["教育", "稳定", "文化", "组织"]},
    "苏州": {"elements": ["金", "木"], "tags": ["制造", "外企", "精细", "产业"]},
    "厦门": {"elements": ["水", "木"], "tags": ["内容", "贸易", "生活", "审美"]},
    "香港": {"elements": ["金", "水"], "tags": ["金融", "国际", "流动", "资源"]},
    "新加坡": {"elements": ["金", "水"], "tags": ["国际", "规则", "平台", "跳板"]},
    "东京": {"elements": ["金", "木"], "tags": ["设计", "秩序", "科技", "专业"]},
}


def generate_navigation_report(
    modules: list[str],
    bazi_chart: dict[str, Any],
    birth_info: dict[str, Any],
    astrology: dict[str, Any] | None,
    analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    selected = _normalize_modules(modules)
    context = _build_context(bazi_chart, birth_info, astrology, analysis)
    cards = []
    for module in selected:
        if module == "talent":
            cards.append(_talent_card(context))
        elif module == "career":
            cards.append(_career_card(context))
        elif module == "city":
            cards.append(_city_card(context))
        elif module == "life_lesson":
            cards.append(_life_lesson_card(context))

    return {
        "summary": _summary(cards, context),
        "selected_modules": selected,
        "astrology_status": context["astrology_status"],
        "cards": cards,
    }


def _normalize_modules(modules: list[str]) -> list[str]:
    if not modules or "full" in modules:
        return ["talent", "career", "city", "life_lesson"]
    valid = [module for module in modules if module in MODULE_TITLES]
    return valid or ["career"]


def _build_context(
    bazi_chart: dict[str, Any],
    birth_info: dict[str, Any],
    astrology: dict[str, Any] | None,
    analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    fallback_analysis = _fallback_analysis(bazi_chart)
    final_analysis = analysis or fallback_analysis
    ten_gods = bazi_chart["wuxing_score"].get("ten_gods_percentage") or {}
    strongest_ten_god = max(ten_gods, key=ten_gods.get) if ten_gods else "yin_star"
    weakest_element = min(bazi_chart["wuxing_score"]["percentage"], key=bazi_chart["wuxing_score"]["percentage"].get)
    astrology = astrology or {}
    return {
        "birth_info": birth_info,
        "bazi_chart": bazi_chart,
        "analysis": final_analysis,
        "day_master": bazi_chart["day_master"]["element"],
        "strength": final_analysis["final_judgment"],
        "yong": final_analysis.get("yong_shen", []),
        "ji": final_analysis.get("ji_shen", []),
        "strongest_ten_god": strongest_ten_god,
        "weakest_element": _element_name(weakest_element),
        "astrology": astrology,
        "astrology_status": (astrology.get("_meta") or {}).get("status", "missing"),
        "astrology_notice": (astrology.get("_meta") or {}).get("message", "星盘数据缺失，当前分析以八字为主。"),
    }


def _fallback_analysis(bazi_chart: dict[str, Any]) -> dict[str, Any]:
    strength = bazi_chart["preliminary"]["strength"]
    dm = bazi_chart["day_master"]["element"]
    generated_by = {"火": "木", "土": "火", "金": "土", "水": "金", "木": "水"}
    generates = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    controls = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
    controlled_by = {value: key for key, value in controls.items()}
    if strength == "身强":
        yong = [generates[dm], controlled_by[dm], controls[dm]]
        ji = [dm, generated_by[dm]]
    elif strength == "身弱":
        yong = [dm, generated_by[dm]]
        ji = [generates[dm], controlled_by[dm], controls[dm]]
    else:
        yong = [dm, generated_by[dm]]
        ji = []
    return {"final_judgment": strength, "confidence": 60, "yong_shen": yong[:3], "ji_shen": ji[:3], "fallback": True}


def _talent_card(context: dict[str, Any]) -> dict[str, Any]:
    mode = _talent_mode(context["strongest_ten_god"])
    mc = _astro_sign(context, "mc")
    sun = _astro_sign(context, "sun")
    mercury = _astro_sign(context, "mercury")
    return _base_card(
        "talent",
        "人生天赋",
        f"你更适合把优势放在{mode}能力上，做能沉淀经验、形成方法并影响他人的事情。",
        f"从整体倾向看，你不是只适合单点执行的人。你更容易在一件事里看见结构、规律和可优化空间。太阳{sun}、水星{mercury}与MC {mc}作为参考，说明表达方式和职业呈现需要被看见；八字里较突出的十神结构，则提示你适合把能力产品化、流程化或顾问化。",
        f"八字侧重看十神结构，当前最突出的结构是{_ten_god_label(context['strongest_ten_god'])}，日主为{context['day_master']}，喜用倾向为{'、'.join(context['yong']) or '待校准'}。",
        _astro_basis(context, f"参考太阳{sun}、水星{mercury}、木星{_astro_sign(context, 'jupiter')}与MC {mc}。"),
        [
            "把你擅长的经验整理成作品、案例或方法论。",
            "优先选择能持续积累专业声誉的方向，不要只做一次性消耗型任务。",
            "每季度复盘一次：哪些能力被别人反复需要，那就是你的可放大天赋。",
        ],
    )


def _career_card(context: dict[str, Any]) -> dict[str, Any]:
    yong = context["yong"]
    career_type = "稳定平台中的专业岗位" if "金" in yong or "土" in yong else "创新变化快、需要表达和连接的岗位"
    work_mode = "先在平台里积累资源，再考虑独立项目" if context["strength"] != "身强" else "可以保留创业或自由职业选项，但要控制节奏"
    return _base_card(
        "career",
        "职业方向",
        f"你可以优先考虑{career_type}，适合走“专业能力 + 资源整合”的路线。",
        f"职业选择上，不建议只看行业名，而要看岗位是否允许你持续形成壁垒。对你更友好的工作通常有清晰的成长路径、可复用的方法、稳定的资源入口，同时也给你一定表达或决策空间。{work_mode}。",
        f"八字以喜忌、十神结构和事业相关组合为主。当前判断为{context['strength']}，喜用五行为{'、'.join(yong) or '待校准'}，忌讳五行为{'、'.join(context['ji']) or '暂不明显'}。",
        _astro_basis(context, f"参考MC {_astro_sign(context, 'mc')}、太阳{_astro_sign(context, 'sun')}、水星{_astro_sign(context, 'mercury')}、土星{_astro_sign(context, 'saturn')}。"),
        [
            "优先投递能积累行业经验、作品或客户资源的岗位。",
            "面试时重点判断直属上级、组织资源和成长路径，而不只看薪资。",
            "如果想创业，先用副业或项目制验证，不建议一开始全仓押注。",
        ],
    )


def _city_card(context: dict[str, Any]) -> dict[str, Any]:
    ranking = _city_ranking(context)
    card = _base_card(
        "city",
        "适合发展的城市",
        "你更适合资源密集、机会流动快，同时能让你持续积累专业标签的城市。",
        "城市匹配度只代表命理倾向和职业环境层面的参考，不代表必须迁移。真正的选择还要结合行业机会、家庭成本、签证政策和你的现实资源。",
        f"八字侧重喜忌五行和当前大运。当前喜用五行为{'、'.join(context['yong']) or '待校准'}，因此更偏向选择能承载这些气质的城市环境。",
        _astro_basis(context, f"星盘侧以MC {_astro_sign(context, 'mc')}、北交点{_astro_sign(context, 'northNode')}和九宫主题作为辅助。"),
        [
            "优先选择产业资源丰富、岗位流动性高的城市。",
            "不要只看城市五行，也要看你的目标行业在当地是否有真实机会。",
            "短期迁移成本高时，可以先通过远程项目、出差或短住测试匹配度。",
        ],
    )
    card["city_ranking"] = ranking
    return card


def _life_lesson_card(context: dict[str, Any]) -> dict[str, Any]:
    weak = context["weakest_element"]
    north = _astro_sign(context, "northNode")
    south = _astro_sign(context, "southNode")
    saturn = _astro_sign(context, "saturn")
    return _base_card(
        "life_lesson",
        "人生课题",
        f"你的人生课题是减少惯性消耗，把注意力放回长期建设和稳定选择上。",
        f"你容易卡住的地方，不一定是能力不够，而是节奏被外界拉走后，很难持续投资真正重要的方向。北交点{north}、南交点{south}和土星{saturn}作为参考，提醒你需要从熟悉的旧模式里走出来；八字里较弱或较失衡的{weak}，也提示你要补足对应的生活策略。",
        f"八字侧重看忌神、失衡十神和反复出现的问题。当前忌讳倾向为{'、'.join(context['ji']) or '暂不明显'}，较弱五行为{weak}。",
        _astro_basis(context, f"参考北交点{north}、南交点{south}、土星{saturn}。"),
        [
            "遇到重大选择时，把短期情绪和长期收益分开写下来。",
            "减少反复救火式努力，建立能稳定推进的周计划。",
            "主动寻找能约束你、提醒你、给你反馈的外部系统。",
        ],
    )


def _base_card(
    module: str,
    title: str,
    answer: str,
    explanation: str,
    bazi_basis: str,
    astrology_basis: str,
    suggestions: list[str],
) -> dict[str, Any]:
    return {
        "module": module,
        "title": title,
        "answer": answer,
        "explanation": explanation,
        "professional_basis": {"bazi": bazi_basis, "astrology": astrology_basis},
        "suggestions": suggestions,
    }


def _city_ranking(context: dict[str, Any]) -> list[dict[str, Any]]:
    yong = set(context["yong"])
    ranking = []
    for city in CANDIDATE_CITIES:
        profile = CITY_PROFILES[city]
        overlap = yong.intersection(profile["elements"])
        score = 72 + len(overlap) * 10
        if "平台" in profile["tags"] and context["strength"] != "身强":
            score += 4
        if "创新" in profile["tags"] and "火" in yong:
            score += 4
        score = min(score, 96)
        ranking.append({"city": city, "score": score, "reason": _city_reason(city, profile, overlap)})
    return sorted(ranking, key=lambda item: item["score"], reverse=True)[:5]


def _city_reason(city: str, profile: dict[str, Any], overlap: set[str]) -> str:
    if overlap:
        return f"{city}的{profile['tags'][0]}和{profile['tags'][1]}气质，与当前喜用五行{'、'.join(sorted(overlap))}更匹配。"
    return f"{city}的{profile['tags'][0]}与{profile['tags'][1]}资源有参考价值，但需要结合具体岗位机会判断。"


def _summary(cards: list[dict[str, Any]], context: dict[str, Any]) -> str:
    if not cards:
        return "这份导航会从命盘倾向和现实选择两个层面，帮你缩小人生方向。"
    return f"从命盘倾向看，你更适合选择能放大{_talent_mode(context['strongest_ten_god'])}能力、并持续积累专业标签的路径。"


def _talent_mode(ten_god: str) -> str:
    return {
        "yin_star": "研究型和咨询顾问型",
        "bijie": "资源整合型和团队协作型",
        "shi_shang": "表达型和创造型",
        "cai_star": "商业型和资源配置型",
        "guan_sha": "管理型和规则执行型",
    }.get(ten_god, "复合型")


def _ten_god_label(key: str) -> str:
    return {
        "yin_star": "印星",
        "bijie": "比劫",
        "shi_shang": "食伤",
        "cai_star": "财星",
        "guan_sha": "官杀",
    }.get(key, key)


def _astro_sign(context: dict[str, Any], key: str) -> str:
    value = context["astrology"].get(key) or {}
    return value.get("sign", "待接入")


def _astro_basis(context: dict[str, Any], text: str) -> str:
    if context["astrology_status"] != "ready":
        return f"{context['astrology_notice']} {text}"
    return text


def _element_name(key: str) -> str:
    return {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}.get(key, key)
