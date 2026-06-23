from __future__ import annotations

from datetime import datetime
from typing import Any

from data.event_question_bank import DAYUN_TRANSITION_DEFAULT, EVENT_QUESTIONS
from services.liuyear_service import CONTROLS, GENERATES, compute_past_years, find_best_contrast_years

RECENT_YEAR_WINDOW = 6
MIN_MEMORY_AGE = 12


TEN_GOD_LABELS = {
    "yin_star": "印星",
    "bijie": "比劫",
    "shi_shang": "食伤",
    "cai_star": "财星",
    "guan_sha": "官杀",
}


def generate_questions(bazi_chart: dict[str, Any], birth_info: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    past_years = _recent_memory_years(bazi_chart, birth_info)
    best_years, worst_years = find_best_contrast_years(past_years, count=min(3, len(past_years)))
    return [
        _build_anchor_question(best_years, worst_years),
        _build_event_question(bazi_chart),
        _build_dayun_transition_question(bazi_chart, birth_info),
    ]


def _recent_memory_years(bazi_chart: dict[str, Any], birth_info: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    current_year = datetime.now().year
    birth_year = _birth_year(birth_info)
    start_year = current_year - RECENT_YEAR_WINDOW
    if birth_year:
        start_year = max(start_year, birth_year + MIN_MEMORY_AGE)
    count = max(2, current_year - start_year)
    years = compute_past_years(bazi_chart, count=count, current_year=current_year)
    return years or compute_past_years(bazi_chart, count=3, current_year=current_year)


def _birth_year(birth_info: dict[str, Any] | None) -> int | None:
    if not birth_info:
        return None
    solar_date = str(birth_info.get("solar_date") or "")
    try:
        return int(solar_date[:4])
    except (TypeError, ValueError):
        return None


def _build_anchor_question(best_years: list[dict[str, Any]], worst_years: list[dict[str, Any]]) -> dict[str, Any]:
    best = best_years[-1]
    worst = worst_years[0] if worst_years[0]["year"] != best["year"] else (best_years[0] if len(best_years) > 1 else worst_years[0])
    best_text = f"{best['year']}（{best['ganzhi']}年）"
    worst_text = f"{worst['year']}（{worst['ganzhi']}年）"
    diff = best["total_score"] - worst["total_score"]
    intro = (
        f"系统优先选择你更容易记得的近几年。根据命盘流年，{best_text} 和 {worst_text} 的五行作用反差较明显，适合用来做经历校验。"
        if diff >= 2.5
        else f"系统优先选择你更容易记得的近几年。请回忆 {best_text} 和 {worst_text} 这两年，它们在流年五行上仍有可比较的差异。"
    )
    best_reason = _year_reason(best)
    worst_reason = _year_reason(worst)
    return {
        "id": 1,
        "type": "anchor",
        "dimension": "流年锚点",
        "intro": intro,
        "question": "这两年里，哪一年你整体过得更顺？",
        "context": "凭第一直觉，不用想太复杂。",
        "options": [
            {
                "key": "A",
                "text": f"{best['year']}年更顺",
                "reason": best_reason,
                "signal": f"{best['ganzhi']}年偏喜用：{best_reason}",
                "strength_hint": "confirmed_favorable",
                "mapped_year": best["year"],
                "mapped_score": best["total_score"],
                "year_tendency": "favorable",
            },
            {
                "key": "B",
                "text": f"{worst['year']}年更顺",
                "reason": worst_reason,
                "signal": f"{worst['ganzhi']}年原本偏挑战：{worst_reason}。若反而更顺，说明喜忌需要反向校正。",
                "strength_hint": "reversed_favorable",
                "mapped_year": worst["year"],
                "mapped_score": worst["total_score"],
                "year_tendency": "unfavorable",
            },
            {"key": "C", "text": "两年感觉差不多", "reason": "如果近年体感差异不明显，说明流年触发度可能弱于大运或现实环境因素。", "signal": "流年反差不明显", "strength_hint": "neutral", "mapped_year": None, "year_tendency": "neutral"},
            {"key": "D", "text": "两年都挺难的", "reason": "如果两个近年都偏难，可能代表当前阶段整体承压，需要结合大运和事件题继续判断。", "signal": "整体运势偏弱，日主可能持续受压", "strength_hint": "both_hard", "mapped_year": None, "year_tendency": "both_hard"},
        ],
        "_meta": {"best_year": best, "worst_year": worst, "score_diff": round(diff, 2), "year_window": RECENT_YEAR_WINDOW, "selection_basis": "recent_memory_weighted_liunian_contrast"},
    }


def _year_reason(year_item: dict[str, Any]) -> str:
    tendency = year_item.get("tendency", "中性")
    stem = year_item.get("stem", "")
    branch = year_item.get("branch", "")
    stem_element = year_item.get("stem_element", "")
    branch_element = year_item.get("branch_element", "")
    score = year_item.get("total_score", 0)
    return f"{stem}{branch}流年，天干{stem}属{stem_element}、地支{branch}属{branch_element}，综合分{score}，系统判为{tendency}"


def _build_event_question(bazi_chart: dict[str, Any]) -> dict[str, Any]:
    tg_pct = bazi_chart["wuxing_score"].get("ten_gods_percentage") or {}
    if not tg_pct:
        return EVENT_QUESTIONS["general_fortune"]
    strongest = max(tg_pct, key=tg_pct.get)
    key_map = {
        "guan_sha": "career_pressure",
        "cai_star": "wealth_change",
        "yin_star": "mentor_resource",
        "shi_shang": "expression_output",
        "bijie": "peer_competition",
    }
    question = dict(EVENT_QUESTIONS.get(key_map.get(strongest, ""), EVENT_QUESTIONS["general_fortune"]))
    question["_meta"] = {"strongest_ten_god": strongest, "strongest_ten_god_label": TEN_GOD_LABELS.get(strongest, strongest)}
    return question


def _build_dayun_transition_question(bazi_chart: dict[str, Any], birth_info: dict[str, Any] | None) -> dict[str, Any]:
    dayun_list = bazi_chart["dayun"]["list"]
    current_year = datetime.now().year
    current = None
    previous = None
    for index, dayun in enumerate(dayun_list):
        if dayun["start_year"] <= current_year <= dayun["end_year"]:
            current = dayun
            previous = dayun_list[index - 1] if index > 0 else None
            break
    if not current:
        return dict(DAYUN_TRANSITION_DEFAULT)

    cur_gz = f"{current['stem']}{current['branch']}"
    if previous:
        prev_gz = f"{previous['stem']}{previous['branch']}"
        question = f"大约 {current['start_year']} 年你换了新的大运（{cur_gz}，{current['ten_god']}），\n和之前那十年（{prev_gz}）相比，你感觉："
    else:
        question = f"你目前走的是 {cur_gz}（{current['ten_god']}）大运，\n这十年整体感觉怎么样？"

    item = dict(DAYUN_TRANSITION_DEFAULT)
    item["question"] = question
    item["_meta"] = {"current_dayun": current, "prev_dayun": previous, "birth_info": birth_info or {}}
    item["options"] = [
        {**item["options"][0], "text": f"换运后明显更好，{cur_gz}这十年比之前顺"},
        {**item["options"][1], "text": f"换运后反而更难，{cur_gz}这十年比之前累"},
        item["options"][2],
        item["options"][3],
    ]
    return item


def analyze_answers(bazi_chart: dict[str, Any], questions: list[dict[str, Any]], selected_answers: list[dict[str, Any]]) -> dict[str, Any]:
    lookup = {(q["id"], option["key"]): (q, option) for q in questions for option in q["options"]}
    algo = bazi_chart["preliminary"]["strength"]
    dm_element = bazi_chart["day_master"]["element"]
    scores = {"身强": 0.0, "身弱": 0.0, "中和": 0.0, "从格": 0.0}
    scores[algo] = 50.0
    score_breakdown = {
        "initial": {
            "judgment": algo,
            "scores": {key: round(value, 1) for key, value in scores.items()},
            "reason": "理论初判基础分",
        },
        "answer_adjustments": [],
    }
    yong_hints: list[str] = []
    ji_hints: list[str] = []
    saved_answers = []

    for answer in selected_answers:
        key = answer["selected_key"].upper()
        qid = answer["question_id"]
        pair = lookup.get((qid, key))
        if not pair:
            raise ValueError("回答数据不完整，请重新作答")
        question, option = pair
        q_type = question.get("type", "")
        mapped_type = option.get("mapped_type", "")
        hint = option.get("strength_hint", "")
        year_tendency = option.get("year_tendency", "")

        saved = {
            "question_id": qid,
            "selected_key": key,
            "question_type": q_type,
            "dimension": question.get("dimension"),
            "signal": option.get("signal"),
            "strength_hint": hint,
            "mapped_type": mapped_type,
            "year_tendency": year_tendency,
            "event_type": option.get("event_type"),
            "mapped_year": option.get("mapped_year"),
            "_meta": question.get("_meta", {}),
        }
        saved_answers.append(saved)
        before_scores = dict(scores)

        if q_type == "anchor":
            if year_tendency == "favorable":
                scores[algo] += 25.0
            elif year_tendency == "unfavorable":
                opposite = "身弱" if algo == "身强" else "身强"
                scores[opposite] += 35.0
                scores[algo] -= 10.0
            elif year_tendency == "neutral":
                scores["中和"] += 10.0
            elif year_tendency == "both_hard":
                scores["身弱"] += 20.0
        elif q_type == "event":
            _score_event(option.get("event_type", ""), hint, algo, scores, yong_hints, ji_hints)
        elif q_type == "dayun_transition":
            current_dayun = (question.get("_meta") or {}).get("current_dayun") or {}
            current_element = current_dayun.get("element", "")
            if mapped_type == "current_good":
                if current_element:
                    yong_hints.append(current_element)
                scores[algo] += 10.0
            elif mapped_type == "current_bad":
                if current_element:
                    ji_hints.append(current_element)
                opposite = "身弱" if algo == "身强" else "身强"
                scores[opposite] += 10.0
            elif mapped_type == "volatile":
                scores["中和"] += 5.0

        delta = {
            key: round(scores[key] - before_scores.get(key, 0.0), 1)
            for key in scores
            if round(scores[key] - before_scores.get(key, 0.0), 1) != 0
        }
        saved["score_delta"] = delta
        score_breakdown["answer_adjustments"].append(
            {
                "question_id": qid,
                "question_type": q_type,
                "selected_key": key,
                "selected_text": option.get("text"),
                "signal": option.get("signal"),
                "delta": delta,
                "scores_after": {item_key: round(value, 1) for item_key, value in scores.items()},
            }
        )

    scores = {key: max(0.0, value) for key, value in scores.items()}
    final = max(scores, key=scores.get)
    yong_shen, ji_shen = _build_yong_ji(final, dm_element, yong_hints, ji_hints)
    final_scores = {key: round(value, 1) for key, value in scores.items()}
    score_breakdown["final"] = {
        "judgment": final,
        "scores": final_scores,
        "confidence": min(95, round(scores[final])),
        "yong_shen": yong_shen,
        "ji_shen": ji_shen,
    }
    return {
        "final_judgment": final,
        "confidence": min(95, round(scores[final])),
        "algorithm_score": scores.get(algo, 0),
        "theoretical_score": score_breakdown["initial"],
        "answer_score": scores,
        "scores": final_scores,
        "score_breakdown": score_breakdown,
        "adjusted": final != algo,
        "algo_base": algo,
        "answers": saved_answers,
        "yong_shen": yong_shen,
        "ji_shen": ji_shen,
        "evidence": {"yong_hints": sorted(set(yong_hints)), "ji_hints": sorted(set(ji_hints))},
    }


def _score_event(event_type: str, hint: str, algo: str, scores: dict[str, float], yong_hints: list[str], ji_hints: list[str]) -> None:
    if event_type == "career_up":
        yong_hints.append("官")
        scores["身弱" if algo == "身弱" else "身强"] += 12.0
    elif event_type == "career_down":
        ji_hints.append("官")
        scores["身弱"] += 15.0
    elif event_type in {"wealth_up", "wealth_stable"}:
        yong_hints.append("财")
        scores["身强"] += 15.0
    elif event_type == "wealth_down":
        ji_hints.append("财")
        scores["身弱"] += 15.0
    elif event_type == "support_up":
        yong_hints.append("印")
        scores["身弱"] += 12.0
    elif event_type == "support_down":
        ji_hints.append("印")
        scores["身强"] += 12.0
    elif event_type == "output_up":
        yong_hints.append("食伤")
        scores["身强"] += 12.0
    elif event_type in {"peer_bad", "competition_loss"}:
        ji_hints.append("比劫")
        scores["身弱"] += 10.0
    elif event_type == "peer_good":
        yong_hints.append("比劫")
        scores["身弱"] += 10.0
    elif event_type == "health_bad":
        scores["身弱"] += 15.0
    elif hint in scores:
        scores[hint] += 8.0


def _build_yong_ji(final: str, dm_element: str, yong_hints: list[str], ji_hints: list[str]) -> tuple[list[str], list[str]]:
    generated_by = {value: key for key, value in GENERATES.items()}
    controlled_by = {value: key for key, value in CONTROLS.items()}
    if final == "身弱":
        base_yong = [dm_element, generated_by.get(dm_element, "")]
        base_ji = [GENERATES.get(dm_element, ""), controlled_by.get(dm_element, ""), CONTROLS.get(dm_element, "")]
    elif final == "身强":
        base_yong = [GENERATES.get(dm_element, ""), controlled_by.get(dm_element, ""), CONTROLS.get(dm_element, "")]
        base_ji = [dm_element, generated_by.get(dm_element, "")]
    elif final == "中和":
        base_yong = [dm_element, generated_by.get(dm_element, "")]
        base_ji = []
    else:
        base_yong = []
        base_ji = []

    ten_god_to_element = {
        "官": controlled_by.get(dm_element, ""),
        "印": generated_by.get(dm_element, ""),
        "财": CONTROLS.get(dm_element, ""),
        "食伤": GENERATES.get(dm_element, ""),
        "比劫": dm_element,
    }
    extra_yong = [ten_god_to_element.get(item, item) for item in yong_hints]
    extra_ji = [ten_god_to_element.get(item, item) for item in ji_hints]
    return _merge_elements(extra_yong, base_yong)[:3], _merge_elements(extra_ji, base_ji)[:3]


def _merge_elements(*groups: list[str]) -> list[str]:
    result = []
    for group in groups:
        for element in group:
            if element and element not in result:
                result.append(element)
    return result
