from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from html import escape
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from services.bazi_engine import CITY_COORDINATES, calculate_bazi, list_city_options, list_region_hierarchy
from services.astrology_engine import calculate_western_chart
from services.navigation_service import generate_navigation_report
from services.question_service import analyze_answers as analyze_calibration_answers
from services.question_service import generate_questions as generate_calibration_questions


SESSION_TTL_HOURS = 24

app = FastAPI(title="Bazi Agent MVP")
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS: dict[str, dict[str, Any]] = {}


class BaziRequest(BaseModel):
    session_id: str | None = None
    sessionId: str | None = None
    name: str | None = None
    solar_date: str | None = None
    solarDate: str | None = None
    solar_time: str | None = Field(default="14:30")
    solarTime: str | None = None
    city: str = Field("上海")
    gender: str = Field("female", pattern="^(male|female)$")
    unknown_time: bool | None = False
    unknownTime: bool | None = None


class SessionRequest(BaseModel):
    session_id: str | None = None
    sessionId: str | None = None


class Answer(BaseModel):
    question_id: int | None = None
    questionId: int | None = None
    selected_key: str | None = None
    selectedKey: str | None = None


class AnswerRequest(SessionRequest):
    answers: list[Answer]


class NavigationRequest(SessionRequest):
    modules: list[str] = Field(default_factory=list)


def _now() -> datetime:
    return datetime.utcnow()


def _session_id(payload: SessionRequest | BaziRequest | str) -> str:
    if isinstance(payload, str):
        sid = payload
    else:
        sid = payload.session_id or payload.sessionId
    if not sid or sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="会话不存在或已过期，请重新开始")
    return sid


def _clean_expired_sessions() -> None:
    cutoff = _now() - timedelta(hours=SESSION_TTL_HOURS)
    expired = [sid for sid, item in SESSIONS.items() if item["updated_at"] < cutoff]
    for sid in expired:
        SESSIONS.pop(sid, None)


def _touch(session: dict[str, Any]) -> None:
    session["updated_at"] = _now()


def _public_session(session: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": session["session_id"],
        "sessionId": session["session_id"],
        "status": session["status"],
        "created_at": session["created_at"].isoformat() + "Z",
        "updated_at": session["updated_at"].isoformat() + "Z",
        "birth_info": session.get("birth_info"),
        "bazi_chart": session.get("bazi_chart"),
        "questions": session.get("questions"),
        "answers": session.get("answers"),
        "analysis": session.get("analysis"),
        "report": session.get("report"),
        "astrology": session.get("astrology"),
        "navigation_report": session.get("navigation_report"),
    }


def _normalize_city(city: str) -> str:
    if city in CITY_COORDINATES:
        return city
    aliases = {
        "鍖椾含": "北京",
        "涓婃捣": "上海",
        "澶╂触": "天津",
        "閲嶅簡": "重庆",
        "骞垮窞": "广州",
        "娣卞湷": "深圳",
        "鎴愰兘": "成都",
        "姝︽眽": "武汉",
        "瑗垮畨": "西安",
        "鏉窞": "杭州",
        "鍗椾含": "南京",
        "涔岄瞾鏈ㄩ綈": "乌鲁木齐",
        "鎷夎惃": "拉萨",
        "鏄嗘槑": "昆明",
        "棣欐腐": "香港",
        "婢抽棬": "澳门",
        "鍙板寳": "台北",
    }
    return aliases.get(city, city)


def _display_value(value: Any) -> str:
    # The current calculation engine stores several traditional labels as mojibake.
    # The web UI keeps domain copy readable by translating common values at the edge.
    text = str(value)
    translations = {
        "鏈?": "木",
        "鐏?": "火",
        "鍦?": "土",
        "閲?": "金",
        "姘?": "水",
        "闃?": "阳/阴",
        "韬己": "身强",
        "韬急": "身弱",
        "涓拰": "中和",
        "浠庢牸": "从格",
    }
    return translations.get(text, text)


def _element_name(key: str) -> str:
    return {
        "wood": "木",
        "fire": "火",
        "earth": "土",
        "metal": "金",
        "water": "水",
    }.get(key, key)


def _question_bank(chart: dict[str, Any], birth_info: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return generate_calibration_questions(chart, birth_info)


def _analyze_answers(chart: dict[str, Any], answers: list[Answer], birth_info: dict[str, Any] | None = None) -> dict[str, Any]:
    selected = [
        {
            "question_id": answer.question_id or answer.questionId,
            "selected_key": (answer.selected_key or answer.selectedKey or "").upper(),
        }
        for answer in answers
    ]
    try:
        return analyze_calibration_answers(chart, chart.get("_questions") or _question_bank(chart, birth_info), selected)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _build_report(session: dict[str, Any]) -> dict[str, Any]:
    chart = session["bazi_chart"]
    analysis = session["analysis"]
    pct = chart["wuxing_score"]["percentage"]
    low = sorted(pct.items(), key=lambda item: item[1])[:2]
    high = sorted(pct.items(), key=lambda item: item[1], reverse=True)[:2]
    favorable = analysis["yong_shen"]
    unfavorable = analysis["ji_shen"]
    day_master = _display_value(chart["day_master"]["element"])
    strength = analysis["final_judgment"]

    sections = [
        {
            "id": "overall",
            "title": "整体格局与人生主题",
            "content": f"你的日主五行为{day_master}，算法初判结合三题校准后，更接近{strength}。这类命盘的重点不在追求单一答案，而在找到能让自己持续稳定发挥的环境。当前五行最低的是{'、'.join(_element_name(k) for k, _ in low)}，最高的是{'、'.join(_element_name(k) for k, _ in high)}，报告会围绕补偏、避过旺来展开。",
            "highlight": f"综合判断：{strength}，置信度 {analysis['confidence']}%",
        },
        {
            "id": "career",
            "title": "事业与财运",
            "content": "事业上适合选择规则清晰、目标可拆解的赛道。若你处在压力较大的阶段，不宜只靠硬扛，最好把资源、人脉、流程和复盘机制建起来。财运更适合稳健积累，先保证现金流和专业壁垒，再考虑高波动机会。",
            "highlight": "先稳结构，再放大机会。",
        },
        {
            "id": "love",
            "title": "感情与婚姻",
            "content": "亲密关系里，你需要被理解的不是表面情绪，而是背后的节奏感。适合与你长期相处的人，往往能尊重你的边界，也愿意共同规划生活。遇到矛盾时，少用冷处理，多把具体需求说清楚。",
            "highlight": "稳定沟通比短期热度更重要。",
        },
        {
            "id": "health",
            "title": "健康与体质",
            "content": "健康建议以作息、睡眠、补水和规律运动为核心。五行偏弱处对应的生活习惯要长期补，不建议用极端方式快速调整。压力高时，优先降低熬夜和高刺激饮食。",
            "highlight": "用可持续的小习惯补能量。",
        },
        {
            "id": "family",
            "title": "家庭与六亲",
            "content": "家庭关系中容易出现责任感和期待值不对等的情况。你更适合把边界讲清楚，把能承担的部分稳定做好；无法承担的部分，不要用沉默硬接。这样反而更利于长期关系。",
            "highlight": "边界清楚，关系更稳。",
        },
        {
            "id": "wealth",
            "title": "财富格局",
            "content": "财富格局不宜只看进账速度，也要看守成能力。建议采用主业现金流、低风险储蓄、长期投资三层结构。重大投资前留出冷静期，避免在情绪高点做决定。",
            "highlight": "财运的关键词是节奏和纪律。",
        },
    ]

    jewelry = [
        {
            "element": "水",
            "category": "补水类",
            "items": [
                {"name": "海蓝宝", "description": "帮助情绪沉静，适合需要稳定表达的人。", "color": "#4A90D9", "priority": "首选"},
                {"name": "黑曜石", "description": "增强边界感，适合压力较多的阶段。", "color": "#111827", "priority": "次选"},
            ],
            "wearing_advice": "可选深色或蓝色系，日常低调佩戴即可。",
        },
        {
            "element": "金",
            "category": "补金类",
            "items": [
                {"name": "白水晶", "description": "增强清晰度和秩序感。", "color": "#F8FAFC", "priority": "首选"},
                {"name": "银饰", "description": "适合简洁、稳定、利落的搭配风格。", "color": "#CBD5E1", "priority": "次选"},
            ],
            "wearing_advice": "以简洁线条为佳，避免过度堆叠。",
        },
    ]

    return {
        "session_id": session["session_id"],
        "generated_at": _now().isoformat() + "Z",
        "strength_analysis": analysis,
        "wuxing_analysis": {
            "lacking": [_element_name(k) for k, _ in low],
            "excess": [_element_name(k) for k, _ in high],
            "favorable": favorable,
            "unfavorable": unfavorable,
        },
        "sections": sections,
        "recommendations": {
            "jewelry": jewelry,
            "directions": {"favorable": ["北方", "西方"], "unfavorable": ["南方"], "reason": "方向建议按喜用五行取象，作为生活环境选择参考。"},
            "colors": {"favorable": ["黑色", "蓝色", "白色", "银色"], "unfavorable": ["大面积红色", "过重黄色"]},
            "lifestyle_tips": ["保持稳定睡眠窗口", "重要决定先写下成本和收益", "多接触水域、清爽通风的空间"],
            "living_direction": {"best": "城市偏北或偏西区域", "second_best": "临水、通风、采光稳定的居住环境", "reason": "取金水清润之象，利于稳定节奏。"},
        },
    }


def _sse(event: str, data: dict[str, Any]) -> str:
    import json

    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/", response_class=HTMLResponse)
def preview_page() -> str:
    regions_json = json.dumps(list_region_hierarchy(), ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI人生导航 Agent</title>
  <style>
    :root {{ --ink:#2d2a26; --muted:#8c8273; --soft:#a39e93; --line:#e5e2d9; --paper:#f9f8f3; --wash:#f1efe7; --panel:#fff; --accent:#6b705c; --gold:#b5a48b; --red:#c45b3e; --blue:#446a8b; --font-body:"Inter","HarmonyOS Sans SC","MiSans","Noto Sans SC","PingFang SC","Microsoft YaHei UI","Microsoft YaHei",Arial,sans-serif; --font-display:"Noto Serif SC","Source Han Serif SC","Songti SC","STSong","SimSun",serif; --shadow:0 18px 48px rgba(74,68,58,.08); }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; min-height:100vh; color:var(--ink); background:radial-gradient(circle at top,rgba(241,239,231,.72),var(--paper) 70%); font-family:var(--font-body); }}
    main {{ width:min(1180px,100%); margin:0 auto; padding:28px 18px 52px; }}
    header {{ position:sticky; top:0; z-index:10; display:flex; justify-content:space-between; gap:16px; align-items:center; margin:-28px -18px 22px; padding:16px max(18px,calc((100vw - 1180px)/2 + 18px)); background:rgba(255,255,255,.72); border-bottom:1px solid var(--line); backdrop-filter:blur(14px); }}
    h1 {{ margin:0 0 6px; font-family:var(--font-display); font-size:30px; font-weight:700; letter-spacing:0; color:#5a5a40; }}
    p {{ margin:0; }}
    .muted {{ color:var(--muted); line-height:1.7; }}
    .layout {{ display:grid; grid-template-columns:380px 1fr; gap:22px; align-items:start; }}
    .landing {{ display:none; }}
    .page-home {{ width:100%; padding:0 0 48px; }}
    .page-home header,.page-home .layout {{ display:none; }}
    .page-home .landing {{ display:block; }}
    .landing-hero {{ position:relative; min-height:100vh; display:grid; place-items:center; overflow:hidden; background:radial-gradient(circle at center,rgba(241,239,231,.82) 0%,var(--paper) 72%); color:var(--ink); }}
    .landing-hero::before {{ content:""; position:absolute; inset:0; opacity:.12; background:url('/static/hero-cosmic-navigation-ref.jpg') center/cover no-repeat; mix-blend-mode:multiply; }}
    .landing-hero::after {{ content:""; position:absolute; width:min(780px,82vw); aspect-ratio:1; border:1px dashed rgba(181,164,139,.42); border-radius:50%; opacity:.58; animation:heroBreathRing 16s ease-in-out infinite; }}
    .hero-astrolabe-breath {{ position:absolute; z-index:0; width:min(940px,94vw); aspect-ratio:1; color:var(--gold); opacity:.24; pointer-events:none; user-select:none; animation:heroAstrolabeBreath 16s ease-in-out infinite; }}
    .hero-astrolabe-breath svg {{ width:100%; height:100%; display:block; }}
    @keyframes heroAstrolabeBreath {{ 0%,100% {{ opacity:.18; transform:scale(.97); filter:saturate(.86) blur(.15px); }} 50% {{ opacity:.34; transform:scale(1.03); filter:saturate(1.03) blur(0); }} }}
    @keyframes heroBreathRing {{ 0%,100% {{ opacity:.38; transform:scale(.985); }} 50% {{ opacity:.68; transform:scale(1.018); }} }}
    .landing-inner {{ position:relative; z-index:1; width:min(980px,100%); margin:0 auto; padding:76px 20px 110px; text-align:center; }}
    .landing-copy {{ width:min(780px,100%); margin:0 auto; display:flex; flex-direction:column; align-items:center; }}
    .eyebrow {{ display:inline-flex; align-items:center; gap:8px; border:1px solid var(--line); border-radius:999px; background:var(--wash); color:var(--accent); padding:7px 14px; font-family:"JetBrains Mono","Consolas",monospace; font-size:12px; font-weight:700; letter-spacing:3px; text-transform:uppercase; margin-bottom:28px; }}
    .eyebrow::before {{ content:"✦"; color:var(--gold); }}
    .landing h1 {{ font-family:var(--font-display); font-size:clamp(42px,7vw,78px); font-weight:700; font-style:italic; line-height:1.12; margin:0 0 22px; color:#5a5a40; letter-spacing:0; }}
    .landing-lead {{ width:min(680px,100%); font-size:18px; line-height:1.9; color:var(--muted); margin-bottom:36px; }}
    .landing-actions {{ display:flex; gap:14px; flex-wrap:wrap; align-items:center; justify-content:center; }}
    .landing-actions button {{ min-width:190px; min-height:54px; border-radius:14px; font-size:14px; letter-spacing:1.8px; text-transform:uppercase; }}
    .landing-actions .secondary {{ background:rgba(255,255,255,.72); color:var(--accent); border:1px solid var(--line); box-shadow:none; }}
    .landing-proof {{ display:flex; gap:10px; flex-wrap:wrap; justify-content:center; margin-top:30px; }}
    .landing-proof span {{ border:1px solid var(--line); border-radius:999px; padding:7px 12px; color:var(--muted); background:rgba(255,255,255,.58); font-size:13px; }}
    .landing-band {{ width:min(1100px,100%); margin:-92px auto 0; padding:0 20px 28px; position:relative; z-index:2; }}
    .landing-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:18px; }}
    .landing-feature {{ border:1px solid var(--line); border-radius:22px; background:rgba(255,255,255,.88); padding:24px; box-shadow:var(--shadow); }}
    .landing-feature strong {{ display:block; margin-bottom:9px; font-family:var(--font-display); color:#5a5a40; font-size:18px; }}
    .landing-feature p {{ color:var(--muted); line-height:1.75; font-size:13px; }}
    .page-input {{ width:min(760px,100%); }}
    .page-input header {{ display:block; width:min(650px,100%); margin:0 auto 22px; position:static; padding:0; background:transparent; border:0; text-align:left; }}
    .page-input header .badge {{ display:none; }}
    .page-input .layout {{ display:block; width:min(650px,100%); margin:0 auto; }}
    .page-input #stage {{ display:none; }}
    .page-result #birthForm {{ display:none; }}
    .page-result .layout {{ display:block; }}
    .panel {{ background:rgba(255,255,255,.9); border:1px solid var(--line); border-radius:22px; box-shadow:var(--shadow); overflow:hidden; }}
    form {{ padding:44px 46px; display:grid; gap:22px; }}
    .form-intro {{ display:flex; align-items:center; gap:14px; padding-bottom:26px; border-bottom:1px solid var(--line); margin-bottom:8px; }}
    .form-icon {{ width:50px; height:50px; display:grid; place-items:center; border-radius:18px; background:var(--wash); color:var(--accent); }}
    .form-icon svg {{ width:26px; height:26px; }}
    .form-intro h2 {{ margin:0; font-size:27px; line-height:1.1; }}
    .form-intro p {{ margin-top:6px; color:var(--muted); font-size:13px; line-height:1.55; }}
    label {{ display:grid; gap:8px; font-size:12px; font-family:var(--font-display); font-weight:700; letter-spacing:1px; color:var(--muted); }}
    input,select {{ width:100%; min-height:50px; border:1px solid var(--line); border-radius:14px; padding:13px 16px; font-family:var(--font-body); font-size:16px; background:var(--paper); color:var(--ink); outline:none; transition:border-color .18s ease, box-shadow .18s ease, background .18s ease; }}
    input:focus,select:focus {{ border-color:var(--accent); box-shadow:0 0 0 3px rgba(107,112,92,.12); background:white; }}
    button {{ border:0; border-radius:12px; padding:13px 16px; background:var(--accent); color:white; font-family:var(--font-body); font-size:15px; font-weight:800; cursor:pointer; transition:transform .18s ease, opacity .18s ease, background .18s ease; }}
    button:hover {{ transform:translateY(-1px); }}
    button.secondary {{ background:var(--wash); color:var(--accent); border:1px solid var(--line); }}
    button:disabled {{ opacity:.6; cursor:progress; }}
    .inline {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
    .check {{ display:flex; align-items:center; gap:10px; color:var(--ink); font-family:var(--font-body); letter-spacing:0; font-weight:700; }}
    .check input {{ width:auto; }}
    #stage {{ min-height:520px; padding:28px; }}
    .stepbar {{ display:flex; gap:8px; margin-bottom:22px; flex-wrap:wrap; }}
    .step {{ display:inline-flex; align-items:center; padding:7px 11px; border:1px solid var(--line); border-radius:999px; color:var(--muted); font-size:12px; background:white; }}
    .step.on {{ border-color:rgba(107,112,92,.44); color:white; background:var(--accent); }}
    .pillars {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:18px 0; }}
    .pillar {{ border:1px solid var(--line); border-radius:18px; padding:16px; text-align:center; background:linear-gradient(180deg,#fff,var(--paper)); box-shadow:0 10px 24px rgba(74,68,58,.05); }}
    .pillar small {{ color:var(--muted); font-family:"JetBrains Mono","Consolas",monospace; font-size:11px; letter-spacing:1px; }}
    .gz {{ font-family:var(--font-display); font-size:38px; font-weight:700; margin:10px 0; color:#5a5a40; }}
    .chart-title {{ text-align:center; margin:6px 0 24px; }}
    .chart-title h2 {{ font-size:30px; font-style:italic; margin-bottom:8px; }}
    .chart-title p {{ color:var(--muted); }}
    .chart-top {{ display:grid; grid-template-columns:2fr 1fr; gap:22px; align-items:stretch; }}
    .info-strip {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-bottom:22px; }}
    .info-cell {{ display:flex; gap:12px; align-items:center; padding:20px 24px; background:white; border:1px solid var(--line); border-radius:18px; box-shadow:0 10px 24px rgba(74,68,58,.04); }}
    .info-cell .icon {{ color:var(--gold); font-size:24px; }}
    .info-cell small {{ display:block; color:var(--muted); font-family:var(--font-display); letter-spacing:1px; text-transform:uppercase; margin-bottom:4px; }}
    .info-cell strong {{ color:var(--ink); font-size:18px; }}
    .pillar-board {{ display:grid; grid-template-columns:repeat(4,1fr); gap:18px; }}
    .pillar-card {{ min-height:430px; padding:26px 24px; border:1px solid var(--line); border-radius:20px; background:linear-gradient(180deg,#fff,#faf8f2); text-align:center; box-shadow:0 12px 28px rgba(74,68,58,.05); }}
    .pillar-card.day-master {{ border-color:#b6a17b; box-shadow:0 0 0 3px rgba(181,164,139,.28),0 16px 30px rgba(74,68,58,.08); }}
    .pillar-index {{ color:var(--muted); font-family:"JetBrains Mono","Consolas",monospace; font-size:12px; letter-spacing:4px; text-transform:uppercase; margin-bottom:8px; }}
    .pillar-title {{ font-family:var(--font-display); color:#5a5a40; font-weight:700; font-size:18px; padding-bottom:18px; border-bottom:1px solid var(--line); }}
    .ten-god {{ display:inline-block; margin:24px 0 18px; padding:5px 12px; border-radius:6px; background:var(--wash); border:1px solid var(--line); color:var(--muted); font-size:13px; }}
    .gz-stack {{ display:grid; gap:10px; place-items:center; padding:16px; border-radius:16px; background:var(--paper); border:1px solid rgba(229,226,217,.72); }}
    .gz-row {{ display:flex; align-items:center; justify-content:center; gap:10px; }}
    .gz-char {{ font-family:var(--font-display); font-size:46px; line-height:1; font-weight:700; color:#c65a3d; }}
    .gz-char.branch {{ color:#5f6b50; }}
    .element-tag {{ padding:3px 8px; border:1px solid var(--line); border-radius:6px; background:white; color:var(--muted); font-size:13px; }}
    .hidden-stems {{ margin-top:22px; padding-top:16px; border-top:1px solid var(--line); }}
    .hidden-stems small {{ display:block; color:var(--muted); font-family:"JetBrains Mono","Consolas",monospace; letter-spacing:2px; margin-bottom:10px; }}
    .hidden-stems div {{ display:flex; justify-content:space-between; padding:7px 10px; margin-top:6px; background:var(--paper); border:1px solid rgba(229,226,217,.72); border-radius:8px; color:var(--muted); }}
    .astro-card {{ min-height:100%; padding:32px; background:white; border:1px solid var(--line); border-radius:20px; box-shadow:0 12px 28px rgba(74,68,58,.05); }}
    .astro-card h2 {{ display:flex; gap:10px; align-items:center; margin-bottom:8px; }}
    .astro-card .astro-panel {{ display:block; margin-top:24px; }}
    .astro-card .astro-list {{ margin-top:16px; }}
    .elements-card {{ margin-top:24px; padding:32px; background:white; border:1px solid var(--line); border-radius:20px; box-shadow:0 14px 32px rgba(74,68,58,.06); }}
    .elements-card h2 {{ display:flex; gap:10px; align-items:center; margin-bottom:6px; }}
    .element-row {{ margin-top:24px; }}
    .element-head {{ display:grid; grid-template-columns:auto 1fr auto auto; gap:12px; align-items:center; margin-bottom:9px; }}
    .element-icon {{ width:42px; height:42px; display:grid; place-items:center; border-radius:10px; background:var(--wash); font-family:var(--font-display); font-size:24px; font-weight:700; }}
    .element-name {{ font-weight:800; }}
    .element-weight {{ color:var(--muted); font-family:"JetBrains Mono","Consolas",monospace; font-size:12px; margin-left:6px; }}
    .element-percent {{ font-weight:800; }}
    .element-status {{ border:1px solid var(--line); border-radius:6px; padding:3px 8px; font-size:12px; color:var(--muted); background:#faf8f2; }}
    .element-track {{ height:10px; border-radius:999px; background:#efede8; overflow:hidden; }}
    .element-fill {{ height:100%; border-radius:999px; background:var(--accent); }}
    .chart-actions {{ display:flex; justify-content:flex-end; gap:12px; margin-top:24px; }}
    .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
    section {{ border-top:1px solid var(--line); padding-top:18px; margin-top:18px; }}
    h2 {{ margin:0 0 12px; font-family:var(--font-display); color:#5a5a40; font-size:21px; font-weight:700; }}
    .bar {{ display:grid; grid-template-columns:42px 1fr 48px; align-items:center; gap:10px; margin:8px 0; }}
    .track {{ height:10px; border-radius:999px; background:var(--wash); overflow:hidden; }}
    .fill {{ height:100%; background:linear-gradient(90deg,var(--gold),var(--red)); }}
    .option {{ width:100%; margin:8px 0; text-align:left; background:white; color:var(--ink); border:1px solid var(--line); border-radius:14px; }}
    .option:hover {{ border-color:var(--accent); }}
    .section-card {{ border:1px solid var(--line); border-radius:18px; padding:18px; margin:12px 0; background:#fff; box-shadow:0 10px 24px rgba(74,68,58,.04); }}
    .astro-panel {{ display:grid; grid-template-columns:minmax(260px,360px) 1fr; gap:14px; align-items:start; }}
    .astro-chart {{ width:100%; aspect-ratio:1; display:block; background:var(--paper); border:1px solid var(--line); border-radius:18px; }}
    .astro-body {{ cursor:pointer; outline:none; }}
    .astro-body circle {{ transition:fill .18s ease, stroke .18s ease, stroke-width .18s ease, filter .18s ease; }}
    .astro-body text {{ pointer-events:none; transition:fill .18s ease, font-weight .18s ease; }}
    .astro-body:hover circle,.astro-body.selected circle {{ fill:#fff7df; stroke:var(--gold); stroke-width:2.5; filter:drop-shadow(0 0 8px rgba(181,164,139,.45)); }}
    .astro-body:hover text,.astro-body.selected text {{ fill:#5a4a25; font-weight:800; }}
    .astro-body.related circle {{ fill:#fffdf8; stroke:#b59b57; stroke-width:2; }}
    .astro-body.dimmed {{ opacity:.28; }}
    .aspect-line {{ transition:opacity .18s ease, stroke-width .18s ease; }}
    .aspect-line.focused {{ opacity:.92; stroke-width:2.4; }}
    .aspect-line.dimmed {{ opacity:.08; }}
    .astro-left {{ display:grid; gap:12px; }}
    .astro-placement-summary {{ border:1px solid var(--line); border-radius:18px; padding:16px; background:#fff; box-shadow:0 10px 24px rgba(74,68,58,.04); }}
    .astro-placement-summary h3 {{ margin:0 0 10px; font-family:var(--font-display); color:#5a5a40; font-size:18px; }}
    .placement-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; }}
    .placement-item {{ border:1px solid rgba(229,226,217,.78); border-radius:12px; padding:10px; background:var(--paper); font-size:13px; line-height:1.55; }}
    .placement-item strong {{ display:block; color:var(--ink); margin-bottom:2px; }}
    .astro-list {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; }}
    .astro-item {{ border:1px solid var(--line); border-radius:12px; padding:10px; background:#fff; font-size:13px; }}
    .astro-item strong {{ display:block; margin-bottom:3px; color:var(--ink); }}
    .astro-side {{ display:grid; gap:12px; }}
    .astro-explain-card {{ border:1px solid var(--line); border-radius:18px; padding:18px; background:#fff; box-shadow:0 12px 28px rgba(74,68,58,.05); }}
    .astro-explain-card h3 {{ margin:0 0 6px; font-family:var(--font-display); color:#5a5a40; font-size:20px; }}
    .astro-title-row {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
    .dignity-badge {{ display:inline-flex; align-items:center; padding:4px 9px; border-radius:999px; border:1px solid rgba(181,164,139,.5); background:#faf4df; color:#8a6a24; font-size:12px; font-weight:800; }}
    .astro-position {{ color:var(--muted); font-size:13px; margin-bottom:12px; }}
    .tag-row {{ display:flex; gap:8px; flex-wrap:wrap; margin:10px 0 14px; }}
    .tag {{ display:inline-flex; align-items:center; padding:5px 9px; border:1px solid var(--line); border-radius:999px; background:var(--wash); color:var(--accent); font-size:12px; font-weight:700; }}
    .astro-explain-card dl {{ display:grid; gap:10px; margin:0; }}
    .astro-explain-card dt {{ font-weight:800; color:var(--ink); }}
    .astro-explain-card dd {{ margin:3px 0 0; color:var(--muted); line-height:1.7; }}
    .aspect-focus-card {{ border:1px solid var(--line); border-radius:16px; padding:14px; margin-top:14px; background:var(--paper); }}
    .aspect-focus-card h4 {{ margin:0 0 10px; color:var(--ink); font-size:15px; }}
    .aspect-row {{ display:grid; grid-template-columns:1fr auto; gap:10px; padding:9px 0; border-top:1px solid rgba(229,226,217,.85); }}
    .aspect-row:first-of-type {{ border-top:0; }}
    .aspect-row strong {{ color:var(--ink); }}
    .aspect-row span {{ color:var(--muted); font-size:12px; }}
    .astro-drawer-close {{ display:none; }}
    .module-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; margin:18px 0; }}
    .module-option {{ display:flex; align-items:center; gap:10px; border:1px solid var(--line); border-radius:18px; padding:16px; background:white; color:var(--ink); cursor:pointer; transition:transform .18s ease, border-color .18s ease, background .18s ease; }}
    .module-option:hover {{ transform:translateY(-2px); border-color:rgba(107,112,92,.45); background:var(--wash); }}
    .module-option input {{ width:auto; }}
    details {{ border-top:1px solid var(--line); margin-top:12px; padding-top:10px; }}
    summary {{ cursor:pointer; color:var(--accent); font-weight:600; }}
    .city-row {{ display:grid; grid-template-columns:72px 52px 1fr; gap:10px; padding:9px 0; border-bottom:1px solid var(--line); }}
    .strategy-hero {{ border:1px solid var(--line); border-radius:22px; padding:24px; background:linear-gradient(180deg,#fff,#fbfaf5); box-shadow:var(--shadow); margin:14px 0; }}
    .strategy-hero h2 {{ font-size:26px; margin-bottom:10px; }}
    .report-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; margin-top:14px; }}
    .strategy-card {{ border:1px solid var(--line); border-radius:18px; padding:18px; background:#fff; box-shadow:0 10px 24px rgba(74,68,58,.04); }}
    .strategy-card.wide {{ grid-column:1 / -1; }}
    .strategy-card h3 {{ margin:0 0 12px; font-family:var(--font-display); color:#5a5a40; font-size:20px; }}
    .strategy-card h4 {{ margin:14px 0 7px; color:var(--ink); font-size:15px; }}
    .basis-list,.strategy-list {{ display:grid; gap:10px; margin:0; padding:0; list-style:none; }}
    .basis-list li,.strategy-list li,.plan-action {{ border:1px solid rgba(229,226,217,.82); border-radius:12px; padding:12px; background:var(--paper); line-height:1.65; }}
    .basis-list strong,.strategy-list strong {{ display:block; color:var(--ink); margin-bottom:4px; }}
    .career-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }}
    .career-card {{ border:1px solid rgba(229,226,217,.9); border-radius:16px; padding:14px; background:var(--paper); }}
    .career-card h4 {{ margin:0 0 8px; font-family:var(--font-display); color:#5a5a40; font-size:18px; }}
    .money-stage,.month-card {{ border:1px solid rgba(229,226,217,.9); border-radius:16px; padding:14px; background:var(--paper); margin-top:10px; }}
    .month-card ol,.money-stage ul {{ margin:8px 0 0; padding-left:20px; line-height:1.8; color:var(--muted); }}
    .badge {{ display:inline-flex; padding:5px 10px; border-radius:999px; border:1px solid var(--line); color:var(--accent); background:var(--wash); font-size:13px; }}
    .error {{ color:#8a2f21; background:#fff7f5; border:1px solid #e2b4a9; padding:14px; border-radius:14px; }}
    .modal-backdrop {{ position:fixed; inset:0; z-index:20; display:grid; place-items:center; padding:18px; background:rgba(24,32,38,.42); }}
    .modal {{ width:min(720px,100%); max-height:90vh; overflow:auto; background:var(--panel); border-radius:22px; border:1px solid var(--line); box-shadow:0 24px 60px rgba(24,32,38,.22); padding:24px; }}
    .score-table {{ width:100%; border-collapse:collapse; margin:10px 0; font-size:14px; }}
    .score-table th,.score-table td {{ text-align:left; border-bottom:1px solid var(--line); padding:9px 6px; vertical-align:top; }}
    .score-table th {{ color:var(--muted); font-weight:600; }}
    .delta-up {{ color:var(--accent); font-weight:700; }}
    .delta-down {{ color:#9c3f32; font-weight:700; }}
    .modal-actions {{ display:flex; justify-content:flex-end; margin-top:14px; }}
    @media (max-width:820px) {{ main {{ padding-left:14px; padding-right:14px; }} .layout,.grid,.astro-panel,.landing-grid,.module-grid,.inline,.chart-top,.info-strip,.pillar-board,.report-grid,.career-grid {{ grid-template-columns:1fr; }} header {{ display:block; margin-left:-14px; margin-right:-14px; }} .pillars {{ grid-template-columns:repeat(2,1fr); }} .landing-hero {{ min-height:86vh; }} .landing h1 {{ font-size:40px; }} .landing-lead {{ font-size:16px; }} form,#stage {{ padding:22px; }} .form-intro {{ align-items:flex-start; }} .pillar-card {{ min-height:auto; }} .element-head {{ grid-template-columns:auto 1fr auto; }} .element-status {{ grid-column:2 / 4; width:max-content; }} .astro-side.selected {{ position:fixed; left:0; right:0; bottom:0; z-index:30; padding:14px; background:linear-gradient(180deg,rgba(248,246,239,0),rgba(248,246,239,.92) 18%,rgba(248,246,239,1)); }} .astro-side.selected .astro-list, .astro-side.selected details {{ display:none; }} .astro-side.selected .astro-explain-card {{ max-height:78vh; overflow:auto; border-radius:22px 22px 0 0; box-shadow:0 -16px 38px rgba(36,32,24,.18); }} .astro-drawer-close {{ display:inline-flex; margin-left:auto; padding:8px 10px; font-size:12px; }} }}
  </style>
</head>
<body>
  <main id="app" class="page-home">
    <div id="landing" class="landing">
      <div class="landing-hero">
        <div class="hero-astrolabe-breath" aria-hidden="true">
          <svg viewBox="0 0 800 800">
            <circle cx="400" cy="400" r="380" stroke="rgba(181,164,139,.30)" stroke-width="1" fill="none"/>
            <circle cx="400" cy="400" r="360" stroke="rgba(181,164,139,.16)" stroke-width=".6" stroke-dasharray="3 4" fill="none"/>
            <circle cx="400" cy="400" r="310" stroke="rgba(107,112,92,.20)" stroke-width="1" fill="none"/>
            <circle cx="400" cy="400" r="260" stroke="rgba(181,164,139,.16)" stroke-width=".6" stroke-dasharray="5 5" fill="none"/>
            <circle cx="400" cy="400" r="215" stroke="rgba(107,112,92,.16)" stroke-width="1" fill="none"/>
            <circle cx="400" cy="400" r="170" stroke="rgba(181,164,139,.12)" stroke-width=".7" fill="none"/>
            <circle cx="400" cy="400" r="110" stroke="rgba(107,112,92,.20)" stroke-width="1" fill="none"/>
            <circle cx="400" cy="400" r="60" stroke="rgba(196,91,62,.16)" stroke-width="1.5" stroke-dasharray="2 3" fill="none"/>
            <path d="M400 340 405 395 460 400 405 405 400 460 395 405 340 400 395 395Z" fill="rgba(181,164,139,.10)" stroke="rgba(181,164,139,.28)" stroke-width=".8"/>
            <circle cx="400" cy="400" r="4.5" fill="rgba(196,91,62,.62)"/>
          </svg>
        </div>
        <div class="landing-inner">
          <div class="landing-copy">
            <p class="eyebrow">八字 × 星盘 × 经历校验</p>
            <h1>AI人生导航 Agent</h1>
            <p class="landing-lead">以权威八字排盘为核心，合参真实星盘与经历校验，把命盘结构转译为事业、城市、天赋与人生路径的可执行建议。</p>
            <div class="landing-actions">
              <button onclick="startExperience()">开始体验</button>
              <button class="secondary" onclick="document.querySelector('#landingIntro').scrollIntoView({{ behavior:'smooth' }})">了解校验方式</button>
            </div>
            <div class="landing-proof">
              <span>真太阳时校正</span>
              <span>喜忌分数透明</span>
              <span>经历校验后再下结论</span>
            </div>
          </div>
        </div>
      </div>
      <div id="landingIntro" class="landing-band">
        <div class="landing-grid">
          <div class="landing-feature"><strong>1. 精准四柱推演</strong><p>根据出生时间和地点生成八字排盘、五行分布与基础星盘，先建立可靠的结构判断。</p></div>
          <div class="landing-feature"><strong>2. 流年经历校核</strong><p>通过真实年份、关键事件和大运感受反向校准喜忌，避免只停留在静态命盘。</p></div>
          <div class="landing-feature"><strong>3. 模块化人生导航</strong><p>围绕事业、天赋、城市和人生课题，输出结论、依据和可以执行的建议。</p></div>
        </div>
      </div>
    </div>
    <header>
      <div><h1>AI人生导航 Agent</h1><p class="muted">结合八字、基础星盘与问答校验的人生方向建议</p></div>
      <span class="badge">FastAPI 本地预览</span>
    </header>
    <div class="layout">
      <form id="birthForm" class="panel">
        <div class="form-intro">
          <div class="form-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M12 3.5l1.2 2.8 2.8 1.2-2.8 1.2-1.2 2.8-1.2-2.8L8 7.5l2.8-1.2L12 3.5Z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/>
              <path d="M18 12.5l.8 1.8 1.7.7-1.7.8-.8 1.7-.8-1.7-1.7-.8 1.7-.7.8-1.8Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
              <path d="M6.8 12.2a4.8 4.8 0 1 0 5 5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
            </svg>
          </div>
          <div>
            <h2>录入出生基本信息</h2>
            <p>我们将根据出生地点与真太阳时校对命盘参数</p>
          </div>
        </div>
        <label>姓名 / 称呼<input name="name" type="text" placeholder="例如：李明轩" /></label>
        <div class="inline">
          <label>出生日期<input name="solar_date" type="date" value="1990-05-15" required /></label>
          <label>出生时间<input name="solar_time" type="time" value="14:30" required /></label>
        </div>
        <div class="inline">
          <label>省份<select id="provinceSelect"></select></label>
          <label>城市/州/盟<select id="citySelect"></select></label>
        </div>
        <div class="inline">
          <label>区县<select id="districtSelect"></select></label>
          <label>性别<select name="gender"><option value="female">女</option><option value="male">男</option></select></label>
        </div>
        <label class="check"><input name="unknown_time" type="checkbox" /> 出生时间不详</label>
        <input name="city" id="selectedRegion" type="hidden" value="上海" />
        <button id="submit" type="submit">开始排盘</button>
      </form>
      <div id="stage" class="panel"></div>
    </div>
  </main>
  <script>
    const app = document.querySelector("#app");
    const form = document.querySelector("#birthForm");
    const stage = document.querySelector("#stage");
    const submit = document.querySelector("#submit");
    const provinceSelect = document.querySelector("#provinceSelect");
    const citySelect = document.querySelector("#citySelect");
    const districtSelect = document.querySelector("#districtSelect");
    const selectedRegion = document.querySelector("#selectedRegion");
    const regions = {regions_json};
    let sessionId = null;
    let chartPayload = null;

    const el = (html) => {{ stage.innerHTML = html; }};
    function setPage(page) {{
      if (page === "home") {{
        app.className = "page-home";
        stage.innerHTML = "";
      }} else if (page === "input") {{
        app.className = "page-input";
        stage.innerHTML = "";
      }} else {{
        app.className = "page-result";
      }}
      window.scrollTo({{ top:0, behavior:"smooth" }});
    }}
    function navigatePage(page, push=true) {{
      setPage(page);
      const state = {{ page }};
      if (push) {{
        if (history.state?.page === page) history.replaceState(state, "", location.href);
        else history.pushState(state, "", location.href);
      }}
    }}
    const showHomePage = () => navigatePage("home");
    const showInputPage = () => navigatePage("input");
    const showResultPage = () => navigatePage("result");
    window.startExperience = showInputPage;
    window.backToHome = showHomePage;
    window.backToInput = showInputPage;
    history.replaceState({{ page:"home" }}, "", location.href);
    window.addEventListener("popstate", (event) => {{
      setPage(event.state?.page || "home");
    }});
    const steps = (active) => `<div class="stepbar">${{["出生信息","命盘概览","经历校验","选择问题","导航报告"].map((s,i)=>`<span class="step ${{i===active?"on":""}}">${{s}}</span>`).join("")}}</div>`;
    const apiBase = location.protocol === "file:" ? "http://127.0.0.1:8000" : "";
    const apiUrl = (url) => url.startsWith("http") ? url : `${{apiBase}}${{url}}`;
    const post = async (url, body={{}}) => {{
      const res = await fetch(apiUrl(url), {{ method:"POST", headers:{{"Content-Type":"application/json"}}, body:JSON.stringify(body) }});
      const data = await res.json().catch(()=>({{detail:"请求失败"}}));
      if (!res.ok) throw new Error(data.detail || data.message || "请求失败");
      return data;
    }};
    const pillarName = {{ hour:"时柱", day:"日柱", month:"月柱", year:"年柱" }};
    const elementName = {{ wood:"木", fire:"火", earth:"土", metal:"金", water:"水" }};
    const translate = (v) => ({{"木":"木","火":"火","土":"土","金":"金","水":"水","身强":"身强","身弱":"身弱","中和":"中和","从格":"从格","鏈?":"木","鐏?":"火","鍦?":"土","閲?":"金","姘?":"水","韬己":"身强","韬急":"身弱","涓拰":"中和","浠庢牸":"从格"}}[v] || v);

    function fillSelect(select, items, placeholder) {{
      select.innerHTML = "";
      if (placeholder) {{
        const option = document.createElement("option");
        option.value = "";
        option.textContent = placeholder;
        select.appendChild(option);
      }}
      items.forEach(item => {{
        const option = document.createElement("option");
        option.value = item.value;
        option.textContent = item.label;
        select.appendChild(option);
      }});
    }}

    function currentProvince() {{
      return regions.find(item => item.value === provinceSelect.value) || regions[0];
    }}

    function currentCity() {{
      const province = currentProvince();
      return (province?.cities || []).find(item => item.value === citySelect.value) || (province?.cities || [])[0];
    }}

    function syncRegionValue() {{
      const city = currentCity();
      const district = (city?.districts || []).find(item => item.value === districtSelect.value);
      selectedRegion.value = district?.value || city?.value || provinceSelect.value || "上海";
    }}

    function refreshCities(preferredCity) {{
      const province = currentProvince();
      fillSelect(citySelect, province?.cities || [], "");
      if (preferredCity && [...citySelect.options].some(o => o.value === preferredCity)) {{
        citySelect.value = preferredCity;
      }}
      refreshDistricts();
    }}

    function refreshDistricts(preferredDistrict) {{
      const city = currentCity();
      const districts = city?.districts || [];
      fillSelect(districtSelect, districts, districts.length ? "不选择区县，使用市级经纬度" : "无区县数据，使用市级经纬度");
      if (preferredDistrict && [...districtSelect.options].some(o => o.value === preferredDistrict)) {{
        districtSelect.value = preferredDistrict;
      }}
      syncRegionValue();
    }}

    function initRegions() {{
      fillSelect(provinceSelect, regions, "");
      provinceSelect.value = "上海";
      refreshCities("上海");
      refreshDistricts("上海浦东新区");
      provinceSelect.addEventListener("change", () => refreshCities());
      citySelect.addEventListener("change", () => refreshDistricts());
      districtSelect.addEventListener("change", syncRegionValue);
    }}

    const astroBodies = [
      ["sun", "\u592a\u9633", "\u65e5", "sun"],
      ["moon", "\u6708\u4eae", "\u6708", "moon"],
      ["ascendant", "\u4e0a\u5347", "ASC", "ascendant"],
      ["mc", "MC", "MC", "mc"],
      ["mercury", "\u6c34\u661f", "\u6c34", "mercury"],
      ["venus", "\u91d1\u661f", "\u91d1", "venus"],
      ["mars", "\u706b\u661f", "\u706b", "mars"],
      ["jupiter", "\u6728\u661f", "\u6728", "jupiter"],
      ["saturn", "\u571f\u661f", "\u571f", "saturn"],
      ["northNode", "\u5317\u4ea4", "\u5317", "north_node"],
    ];
    const signLabels = ["\u767d\u7f8a","\u91d1\u725b","\u53cc\u5b50","\u5de8\u87f9","\u72ee\u5b50","\u5904\u5973","\u5929\u79e4","\u5929\u874e","\u5c04\u624b","\u6469\u7faf","\u6c34\u74f6","\u53cc\u9c7c"];
    const signIndex = {{"Aries":0,"Taurus":1,"Gemini":2,"Cancer":3,"Leo":4,"Virgo":5,"Libra":6,"Scorpio":7,"Sagittarius":8,"Capricorn":9,"Aquarius":10,"Pisces":11}};
    const aspectColors = {{ conjunction:"#2a766d", opposition:"#ad503c", trine:"#2f6fa3", square:"#a97828", sextile:"#5a8f61" }};
    let activeAstroKey = null;
    let currentAstrology = null;
    const polarPoint = (degree, radius, cx=200, cy=200) => {{
      const rad = (degree - 90) * Math.PI / 180;
      return [cx + radius * Math.cos(rad), cy + radius * Math.sin(rad)];
    }};
    const bodyDegree = (body) => typeof body?.longitude === "number" ? body.longitude : ((signIndex[body?.sign] ?? 0) * 30 + (body?.degree || 15));
    const bodyLabel = (body) => `${{body?.sign_zh || signLabels[signIndex[body?.sign] ?? 0] || body?.sign || ""}} ${{body?.degree_display || (body?.degree !== undefined ? `${{body.degree}}\u00b0` : "")}}${{body?.house ? ` \u00b7 \u7b2c${{body.house}}\u5bab` : ""}}`;
    const interpKey = (key) => key === "northNode" ? "north_node" : key;
    const aspectLabels = {{ conjunction:"合相", opposition:"对冲", trine:"三分", square:"四分", sextile:"六合" }};
    const aspectMeaning = {{
      conjunction:"两股能量叠加在一起，主题会被明显放大。",
      opposition:"两股能量相互拉扯，需要在关系和选择中寻找平衡。",
      trine:"能量流动顺畅，是较容易发挥的天赋连接。",
      square:"能量存在摩擦，会形成压力，也能推动成长。",
      sextile:"能量可以互相支持，需要主动使用才会显化。"
    }};
    const canonicalAstroKey = (key) => key === "northNode" ? "north_node" : key;
    const sourceAstroKey = (key) => key === "north_node" ? "northNode" : key;
    const visibleAstroKeys = new Set(astroBodies.map(item => item[3]));
    const astroLabelByKey = (key) => {{
      const found = astroBodies.find(item => item[3] === canonicalAstroKey(key) || item[0] === key);
      return found ? found[1] : key;
    }};
    const aspectKeySet = (aspect) => [canonicalAstroKey(aspect.from), canonicalAstroKey(aspect.to)];
    const visibleAspects = (astrology) => (astrology.aspects || []).filter(item => aspectKeySet(item).every(key => visibleAstroKeys.has(key)));
    const focusedAspects = (astrology) => activeAstroKey ? visibleAspects(astrology).filter(item => aspectKeySet(item).includes(activeAstroKey)) : [];

    function selectAstroBody(key) {{
      activeAstroKey = interpKey(key);
      updateAstroPanel();
    }}

    function clearAstroSelection() {{
      activeAstroKey = null;
      updateAstroPanel();
    }}

    document.addEventListener("click", (event) => {{
      if (!activeAstroKey) return;
      const target = event.target instanceof Element ? event.target : null;
      if (!target) return;
      if (target.closest(".astro-body, .astro-explain-card, button, select, input, label, a")) return;
      clearAstroSelection();
    }});

    function updateAstroPanel() {{
      const section = document.getElementById("astroSection");
      if (section && currentAstrology) section.outerHTML = renderAstroPanel(currentAstrology);
    }}

    function renderAstroWheel(astrology) {{
      if (!astrology) return "";
      const houses = astrology.houses || [];
      const bodies = astroBodies
        .map(([key, label, glyph, interpretationKey]) => ({{ key, label, glyph, interpretationKey, body: astrology[key] }}))
        .filter(item => item.body);
      const focusAspects = focusedAspects(astrology);
      const relatedKeys = new Set(activeAstroKey ? [activeAstroKey] : []);
      focusAspects.forEach(item => aspectKeySet(item).forEach(key => relatedKeys.add(key)));
      const signLines = Array.from({{length:12}}, (_, index) => {{
        const [x1,y1] = polarPoint(index * 30, 172);
        const [x2,y2] = polarPoint(index * 30, 190);
        const [tx,ty] = polarPoint(index * 30 + 15, 178);
        return `<line x1="${{x1.toFixed(1)}}" y1="${{y1.toFixed(1)}}" x2="${{x2.toFixed(1)}}" y2="${{y2.toFixed(1)}}" stroke="#d9e2e4" />
          <text x="${{tx.toFixed(1)}}" y="${{ty.toFixed(1)}}" text-anchor="middle" dominant-baseline="middle" font-size="10" fill="#65717b">${{signLabels[index]}}</text>`;
      }}).join("");
      const houseLines = houses.map(item => {{
        const [x1,y1] = polarPoint(item.longitude, 64);
        const [x2,y2] = polarPoint(item.longitude, 156);
        const [tx,ty] = polarPoint(item.longitude + 7, 76);
        return `<line x1="${{x1.toFixed(1)}}" y1="${{y1.toFixed(1)}}" x2="${{x2.toFixed(1)}}" y2="${{y2.toFixed(1)}}" stroke="#c8dcda" />
          <text x="${{tx.toFixed(1)}}" y="${{ty.toFixed(1)}}" text-anchor="middle" dominant-baseline="middle" font-size="9" fill="#65717b">${{item.house}}</text>`;
      }}).join("");
      const aspectLines = visibleAspects(astrology).map(item => {{
        const from = astrology[item.from];
        const to = astrology[item.to];
        if (!from || !to) return "";
        const [x1,y1] = polarPoint(bodyDegree(from), 96);
        const [x2,y2] = polarPoint(bodyDegree(to), 96);
        const isFocused = activeAstroKey && aspectKeySet(item).includes(activeAstroKey);
        const cls = activeAstroKey ? (isFocused ? "aspect-line focused" : "aspect-line dimmed") : "aspect-line";
        return `<line class="${{cls}}" x1="${{x1.toFixed(1)}}" y1="${{y1.toFixed(1)}}" x2="${{x2.toFixed(1)}}" y2="${{y2.toFixed(1)}}" stroke="${{aspectColors[item.type] || "#9aa6ad"}}" stroke-width="1.2" opacity=".55" />`;
      }}).join("");
      const bodyNodes = bodies.map((item, index) => {{
        const degree = bodyDegree(item.body);
        const radius = 124 + (index % 2) * 16;
        const [x,y] = polarPoint(degree, radius);
        const [lx,ly] = polarPoint(degree, 146);
        const selected = activeAstroKey === item.interpretationKey ? " selected" : "";
        const related = activeAstroKey && relatedKeys.has(item.interpretationKey) && !selected ? " related" : "";
        const dimmed = activeAstroKey && !relatedKeys.has(item.interpretationKey) ? " dimmed" : "";
        const tooltip = `${{item.label}} \u00b7 ${{bodyLabel(item.body)}}`;
        return `<line x1="${{x.toFixed(1)}}" y1="${{y.toFixed(1)}}" x2="${{lx.toFixed(1)}}" y2="${{ly.toFixed(1)}}" stroke="#d9e2e4" />
          <g class="astro-body${{selected}}${{related}}${{dimmed}}" role="button" tabindex="0" aria-label="${{tooltip}}" onclick="selectAstroBody('${{item.key}}')" onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();selectAstroBody('${{item.key}}')}}">
            <title>${{tooltip}}</title>
            <circle cx="${{x.toFixed(1)}}" cy="${{y.toFixed(1)}}" r="12" fill="#fffdf8" stroke="#2a766d" />
            <text x="${{x.toFixed(1)}}" y="${{y.toFixed(1)}}" text-anchor="middle" dominant-baseline="middle" font-size="${{item.glyph.length > 1 ? 8 : 15}}" fill="#182026">${{item.glyph}}</text>
          </g>`;
      }}).join("");
      return `<svg class="astro-chart" viewBox="0 0 400 400" role="img" aria-label="\u661f\u76d8\u8f6e\u76d8">
        <circle cx="200" cy="200" r="190" fill="#ffffff" stroke="#d9e2e4" />
        <circle cx="200" cy="200" r="158" fill="none" stroke="#d9e2e4" />
        <circle cx="200" cy="200" r="106" fill="none" stroke="#d9e2e4" />
        <circle cx="200" cy="200" r="62" fill="#fbfcfc" stroke="#edf1f2" />
        ${{signLines}}${{houseLines}}${{aspectLines}}${{bodyNodes}}
      </svg>`;
    }}

    function renderAstroInfo(astrology) {{
      const interpretation = astrology.astrology_interpretation || {{}};
      const interpretations = interpretation.planet_interpretations || {{}};
      if (!activeAstroKey) {{
        const summary = interpretation.summary || {{ title:"\u6838\u5fc3\u661f\u76d8\u6458\u8981", description:"\u70b9\u51fb\u661f\u76d8\u4e2d\u7684\u661f\u4f53\uff0c\u67e5\u770b\u5bf9\u5e94\u89e3\u91ca\u3002", items:[] }};
        const items = (summary.items || []).map(item => `<li>${{item}}</li>`).join("");
        return `<div class="astro-explain-card"><h3>${{summary.title || "\u6838\u5fc3\u661f\u76d8\u6458\u8981"}}</h3><p class="muted">${{summary.description || "\u70b9\u51fb\u661f\u76d8\u4e2d\u7684\u661f\u4f53\uff0c\u67e5\u770b\u5bf9\u5e94\u89e3\u91ca\u3002"}}</p>${{items ? `<ul>${{items}}</ul>` : ""}}</div>`;
      }}
      const data = interpretations[activeAstroKey] || interpretations[activeAstroKey === "north_node" ? "northNode" : activeAstroKey];
      if (!data) return `<div class="astro-explain-card"><button class="secondary astro-drawer-close" onclick="clearAstroSelection()">\u8fd4\u56de\u6458\u8981</button><h3>\u89e3\u91ca\u751f\u6210\u4e2d</h3><p class="muted">\u8be5\u661f\u4f53\u89e3\u91ca\u6b63\u5728\u751f\u6210\u4e2d\u3002</p></div>`;
      const tags = (data.keywords || []).map(item => `<span class="tag">${{item}}</span>`).join("");
      const dignity = data.dignity || {{}};
      const dignityBadge = dignity.label ? `<span class="dignity-badge" title="${{dignity.description || ""}}">${{dignity.label}}</span>` : "";
      const aspectRows = focusedAspects(astrology).map(item => {{
        const [left, right] = aspectKeySet(item);
        const other = left === activeAstroKey ? right : left;
        const otherBody = astrology[sourceAstroKey(other)];
        const otherText = `${{astroLabelByKey(other)}}${{otherBody ? ` · ${{bodyLabel(otherBody)}}` : ""}}`;
        const label = aspectLabels[item.type] || item.type;
        const meaning = aspectMeaning[item.type] || "\u8fd9\u7ec4\u76f8\u4f4d\u9700\u7ed3\u5408\u661f\u4f53\u548c\u5bab\u4f4d\u7efc\u5408\u89e3\u8bfb\u3002";
        return `<div class="aspect-row"><div><strong>${{label}} · ${{otherText}}</strong><span>${{meaning}}</span></div><span>\u5bb9\u8bb8\u5ea6 ${{item.orb}}\u00b0</span></div>`;
      }}).join("");
      const aspectCard = `<div class="aspect-focus-card"><h4>\u76f8\u4f4d\u805a\u7126</h4>${{aspectRows || `<p class="muted">\u6682\u672a\u627e\u5230\u4e0e\u8be5\u70b9\u76f8\u8fde\u7684\u4e3b\u8981\u76f8\u4f4d\u3002</p>`}}</div>`;
      return `<div class="astro-explain-card">
        <button class="secondary astro-drawer-close" onclick="clearAstroSelection()">\u8fd4\u56de\u6458\u8981</button>
        <div class="astro-title-row"><h3>${{data.name}}</h3>${{dignityBadge}}</div>
        <div class="astro-position">${{data.position_text || ""}}</div>
        ${{dignity.description ? `<p class="muted">${{dignity.description}}</p>` : ""}}
        <strong>${{data.theme || "\u661f\u4f53\u4e3b\u9898"}}</strong>
        <div class="tag-row">${{tags}}</div>
        <dl>
          <div><dt>\u57fa\u7840\u542b\u4e49</dt><dd>${{data.basic_meaning || "\u8be5\u661f\u4f53\u89e3\u91ca\u6b63\u5728\u751f\u6210\u4e2d\u3002"}}</dd></div>
          <div><dt>\u4e2a\u4eba\u5316\u89e3\u91ca</dt><dd>${{data.personalized_interpretation || "\u8be5\u661f\u4f53\u89e3\u91ca\u6b63\u5728\u751f\u6210\u4e2d\u3002"}}</dd></div>
          <div><dt>\u5bab\u4f4d\u89e3\u91ca</dt><dd>${{data.house_interpretation || "\u8be5\u661f\u4f53\u89e3\u91ca\u6b63\u5728\u751f\u6210\u4e2d\u3002"}}</dd></div>
          <div><dt>\u5efa\u8bae</dt><dd>${{data.advice || "\u8be5\u661f\u4f53\u89e3\u91ca\u6b63\u5728\u751f\u6210\u4e2d\u3002"}}</dd></div>
        </dl>
        ${{aspectCard}}
        <p style="margin-top:14px"><button class="secondary" onclick="clearAstroSelection()">\u8fd4\u56de\u6458\u8981</button></p>
      </div>`;
    }}

    function renderAstroPlacementSummary(astrology) {{
      const rows = astroBodies
        .map(([key, label]) => [label, astrology[key]])
        .filter(([, body]) => body)
        .map(([label, body]) => `<div class="placement-item"><strong>${{label}}</strong><span>落入 ${{bodyLabel(body)}}</span></div>`)
        .join("");
      return `<div class="astro-placement-summary">
        <h3>\u661f\u4f53\u843d\u4f4d\u6982\u62ec</h3>
        <div class="placement-grid">${{rows}}</div>
      </div>`;
    }}

    function renderAstroPanel(astrology) {{
      if (!astrology) return "";
      currentAstrology = astrology;
      const status = astrology._meta?.message || "\u5f53\u524d\u6392\u76d8\uff1a\u73b0\u4ee3\u897f\u5360 \u00b7 Tropical \u56de\u5f52\u9ec4\u9053 \u00b7 Placidus/P\u5236";
      const sideClass = activeAstroKey ? "astro-side selected" : "astro-side";
      return `<section id="astroSection">
        <h2>\u661f\u76d8\u8f85\u52a9</h2>
        <p class="muted">${{status}}\u3002\u661f\u76d8\u7528\u4e8e\u8865\u5145\u4eba\u683c\u8868\u8fbe\u3001\u804c\u4e1a\u53d6\u5411\u548c\u5173\u7cfb\u4e3b\u9898\uff0c\u6700\u7ec8\u5224\u65ad\u4f1a\u4e0e\u516b\u5b57\u559c\u5fcc\u548c\u95ee\u7b54\u6821\u9a8c\u5408\u5e76\u3002</p>
        <div class="astro-panel">
          <div class="astro-left">
            ${{renderAstroWheel(astrology)}}
            ${{renderAstroPlacementSummary(astrology)}}
          </div>
          <div class="${{sideClass}}">
            ${{renderAstroInfo(astrology)}}
          </div>
        </div>
      </section>`;
    }}

    function elementTone(key) {{
      return {{
        fire: ["火", "#c45b3e", "#fff0eb"],
        wood: ["木", "#6b705c", "#f0f3ec"],
        water: ["水", "#446a8b", "#edf3f7"],
        metal: ["金", "#8c8273", "#f2efea"],
        earth: ["土", "#b5a48b", "#f4efe6"],
      }}[key] || [key, "#6b705c", "#f1efe7"];
    }}

    function renderElementRows(pct) {{
      const english = {{ fire:"Fire", wood:"Wood", water:"Water", metal:"Metal", earth:"Earth" }};
      return Object.entries(pct).sort((a,b) => b[1] - a[1]).map(([key, value]) => {{
        const [label, color, bg] = elementTone(key);
        const status = value >= 35 ? "过旺" : value <= 10 ? "过弱" : value <= 18 ? "偏弱" : "中和";
        return `<div class="element-row">
          <div class="element-head">
            <span class="element-icon" style="color:${{color}};background:${{bg}}">${{label}}</span>
            <span class="element-name">${{label}} ${{english[key] || key}} <span class="element-weight">WT: ${{value}}</span></span>
            <span class="element-percent">${{value}}%</span>
            <span class="element-status">${{status}}</span>
          </div>
          <div class="element-track"><div class="element-fill" style="width:${{value}}%;background:${{color}}"></div></div>
        </div>`;
      }}).join("");
    }}

    function renderPillarCard(key, index, data, chart) {{
      const isDay = key === "day";
      const hidden = (data.hidden_stems || data.hiddenStems || []).slice(0, 2);
      const tenGodKey = `${{key}}_stem`;
      const tenGod = isDay ? "日主" : (chart.ten_gods?.[tenGodKey] || data.ten_god || data.tenGod || "待定");
      return `<div class="pillar-card ${{isDay ? "day-master" : ""}}">
        <div class="pillar-index">${{isDay ? "日元 SELF" : `PILLAR ${{index}}`}}</div>
        <div class="pillar-title">${{pillarName[key]}}</div>
        <span class="ten-god">${{tenGod}}</span>
        <div class="gz-stack">
          <div class="gz-row"><span class="gz-char">${{data.stem}}</span><span class="element-tag">${{translate(data.stem_element)}}</span></div>
          <div class="gz-row"><span class="gz-char branch">${{data.branch}}</span><span class="element-tag">${{translate(data.branch_element)}}</span></div>
        </div>
        <div class="hidden-stems">
          <small>藏干藏神 HIDDEN</small>
          ${{hidden.length ? hidden.map((item, idx) => {{
            const stem = typeof item === "string" ? item : item.stem;
            const weight = typeof item === "string" ? "" : item.weight;
            const god = idx === 0 ? (chart.ten_gods?.[`${{key}}_branch_main`] || "") : "";
            return `<div><span>${{stem}}</span><span>${{god || (weight ? `权重${{weight}}` : "藏干")}}</span></div>`;
          }}).join("") : `<div><span>--</span><span>暂无</span></div>`}}
        </div>
      </div>`;
    }}

    function renderChart(data) {{
      chartPayload = data;
      activeAstroKey = "sun";
      const birth = data.birth_info;
      const chart = data.bazi_chart;
      const astrology = data.astrology;
      const pillars = chart.pillars;
      const pct = chart.wuxing_score.percentage;
      const pillarOrder = [
        ["year", "年柱"],
        ["month", "月柱"],
        ["day", "日柱"],
        ["hour", "时柱"],
      ];
      const pillarCards = pillarOrder.map(([key, label]) => {{
        const item = pillars[key];
        const tenGod = key === "day" ? "日主" : (chart.ten_gods?.[`${{key}}_stem`] || "");
        return `<div class="pillar">
          <small>${{label}}${{tenGod ? ` · ${{tenGod}}` : ""}}</small>
          <div class="gz">${{item.stem}}${{item.branch}}</div>
          <p class="muted">天干 ${{translate(item.stem_element)}} · 地支 ${{translate(item.branch_element)}}</p>
        </div>`;
      }}).join("");
      const wuxingBars = Object.entries(pct).map(([key, value]) => `
        <div class="bar">
          <strong>${{elementName[key] || key}}</strong>
          <div class="track"><div class="fill" style="width:${{value}}%"></div></div>
          <span>${{value}}%</span>
        </div>`).join("");
      el(`${{steps(1)}}
        <h2>命盘概览</h2>
        <p class="muted">${{birth.name ? `${{birth.name}} · ` : ""}}${{birth.solar_date}} ${{birth.solar_time}} · ${{birth.city}} · 真太阳时 ${{birth.true_solar.date}} ${{birth.true_solar.time}}，校正 ${{birth.true_solar.adjust_minutes}} 分钟</p>
        <div class="pillars">${{pillarCards}}</div>
        <section class="grid">
          <div>
            <h2>日主与强弱</h2>
            <p>日主：<strong>${{chart.day_master.stem}}（${{translate(chart.day_master.element)}}）</strong></p>
            <p>初判：<strong>${{translate(chart.preliminary.strength)}}</strong>，置信度 ${{chart.preliminary.confidence}}%</p>
            <p class="muted">${{chart.preliminary.key_factors.join("；")}}</p>
          </div>
          <div>
            <h2>五行分布</h2>
            ${{wuxingBars}}
          </div>
        </section>
        ${{renderAstroPanel(astrology)}}
        <section>
          <button class="secondary" onclick="backToInput()">返回修改</button>
          <button onclick="confirmChart()">确认命盘，开始校验</button>
        </section>`);
    }}

    function renderScoreCells(scores) {{
      return Object.entries(scores || {{}})
        .map(([name, value]) => `<span class="badge">${{translate(name)}}：${{value}}</span>`)
        .join(" ");
    }}

    function renderDelta(delta) {{
      const items = Object.entries(delta || {{}});
      if (!items.length) return '<span class="muted">无分数变化</span>';
      return items.map(([name, value]) => {{
        const cls = value >= 0 ? "delta-up" : "delta-down";
        const sign = value > 0 ? "+" : "";
        return `<span class="${{cls}}">${{translate(name)}} ${{sign}}${{value}}</span>`;
      }}).join("；");
    }}

    function showCalibrationSummary(analysis) {{
      const breakdown = analysis.score_breakdown || {{}};
      const initial = breakdown.initial || analysis.theoretical_score || {{}};
      const final = breakdown.final || {{}};
      const adjustments = breakdown.answer_adjustments || [];
      const rows = adjustments.map(item => `<tr>
        <td>Q${{item.question_id}}</td>
        <td>${{item.selected_key}}. ${{item.selected_text || ""}}<br><span class="muted">${{item.signal || ""}}</span></td>
        <td>${{renderDelta(item.delta)}}</td>
      </tr>`).join("");
      el(`${{steps(2)}}
        <h2>经历校验完成</h2>
        <p class="muted">请先确认最终喜忌判断，再选择想了解的模块。</p>
        <div class="modal-backdrop">
          <div class="modal">
            <h2>最终喜忌判断</h2>
            <p><strong>最终格局：${{translate(analysis.final_judgment)}}</strong>，置信度 ${{analysis.confidence}}%。</p>
            <p class="muted" style="margin-top:8px;">初判：${{translate(analysis.algo_base)}}。理论基础分：${{renderScoreCells(initial.scores)}}。</p>
            <section>
              <h2>分数明细</h2>
              <table class="score-table">
                <thead><tr><th>题目</th><th>你的选择</th><th>加减分</th></tr></thead>
                <tbody>${{rows}}</tbody>
              </table>
              <p>最终分数：${{renderScoreCells(analysis.scores || final.scores)}}</p>
            </section>
            <section>
              <h2>喜忌结论</h2>
              <p>喜用：${{(analysis.yong_shen || []).join("、") || "待进一步校准"}}；忌神：${{(analysis.ji_shen || []).join("、") || "暂不明显"}}。</p>
            </section>
            <div class="modal-actions"><button onclick="showModuleSelection()">确定</button></div>
          </div>
        </div>`);
    }}

    function showModuleSelection() {{
      el(`${{steps(3)}}<h2>你最想了解什么？</h2>
        <p class="muted">可以多选。系统会结合刚才的流年锚点、真实事件和大运感受，再生成导航建议。</p>
        <div class="module-grid">
          <label class="module-option"><input type="checkbox" value="career" /> 我适合做什么工作？</label>
          <label class="module-option"><input type="checkbox" value="talent" /> 我的天赋优势是什么？</label>
          <label class="module-option"><input type="checkbox" value="city" /> 我适合去哪座城市发展？</label>
          <label class="module-option"><input type="checkbox" value="life_lesson" /> 我的人生课题是什么？</label>
          <label class="module-option"><input type="checkbox" value="full" /> 查看完整人生导航报告</label>
        </div>
        <section><button class="secondary" onclick="renderChart(chartPayload)">返回命盘</button> <button onclick="generateNavigation()">生成导航报告</button></section>`);
    }}

    async function generateNavigation() {{
      const selected = [...document.querySelectorAll('.module-option input:checked')].map(item => item.value);
      const modules = selected.length ? selected : ["career"];
      el(`${{steps(4)}}<h2>正在生成你的人生导航...</h2><p class="muted">会优先给结论，再给解释和可执行建议。</p>`);
      try {{
        const data = await post("/api/navigation/generate", {{ session_id: sessionId, modules }});
        renderNavigationReport(data.report);
      }} catch (error) {{
        el(`<div class="error">${{error.message}}</div>`);
      }}
    }}

    function renderNavigationReport(report) {{
      const sections = report.report_sections;
      if (!sections) {{
        el(`${{steps(4)}}<h2>人生导航报告</h2><p class="section-card">${{report.summary}}</p>
          <div>${{report.cards.map(renderNavigationCard).join("")}}</div>`);
        return;
      }}
      el(`${{steps(4)}}<h2>人生导航报告</h2>
        <p class="muted">已结合出生信息、八字结构、现代西占基础盘，以及你的经历问答校验。以下报告优先给现实动作，不做空泛判断。</p>
        ${{report.astrology_status !== "ready" ? `<p class="muted">现代西占排盘暂不可用，当前分析以八字与问答校验为主。</p>` : ""}}
        ${{renderStrategyReport(sections, report.analysis_json)}}`);
    }}

    function renderStrategyReport(sections, analysis) {{
      return `<div class="strategy-hero">
          <h2>${{sections.core_profile.title}}</h2>
          <p><strong>${{sections.core_profile.one_sentence}}</strong></p>
          <p class="muted" style="margin-top:10px;">${{sections.core_profile.real_world}}</p>
          <p class="muted" style="margin-top:8px;">${{sections.core_profile.advice}}</p>
        </div>
        <div class="report-grid">
          <div class="strategy-card wide">
            <h3>盘面依据</h3>
            <div class="grid">
              ${{renderBasisBlock("八字依据", sections.basis.bazi)}}
              ${{renderBasisBlock("星盘依据", sections.basis.astrology)}}
            </div>
            ${{renderBasisBlock("问答校验依据", sections.basis.qa)}}
          </div>
          <div class="strategy-card wide">
            <h3>现实表现</h3>
            <ul class="strategy-list">${{sections.real_world_patterns.map(renderJudgmentItem).join("")}}</ul>
          </div>
          <div class="strategy-card wide">
            <h3>适合的职业方向</h3>
            <div class="career-grid">${{sections.career_directions.map(renderCareerDirection).join("")}}</div>
          </div>
          <div class="strategy-card">
            <h3>不适合的方向</h3>
            <ul class="strategy-list">${{sections.unsuitable_directions.map(renderUnsuitableDirection).join("")}}</ul>
          </div>
          <div class="strategy-card">
            <h3>赚钱路径</h3>
            ${{sections.money_path.map(renderMoneyStage).join("")}}
          </div>
          <div class="strategy-card wide">
            <h3>未来 3 个月行动计划</h3>
            ${{sections.three_month_plan.map(renderMonthPlan).join("")}}
          </div>
          <div class="strategy-card wide">
            <h3>人生课题</h3>
            ${{renderLifeLesson(sections.life_lesson)}}
          </div>
          <div class="strategy-card wide">
            <h3>关键提醒</h3>
            <ul>${{sections.key_reminders.map(item => `<li>${{item}}</li>`).join("")}}</ul>
            <details><summary>查看 analysis JSON 证据链</summary>
              <ul class="basis-list">${{(analysis?.evidence_chain || []).map(item => `<li>${{item}}</li>`).join("")}}</ul>
            </details>
          </div>
        </div>`;
    }}

    function renderBasisBlock(title, items) {{
      return `<div><h4>${{title}}</h4><ul class="basis-list">${{(items || []).map(item => `<li><strong>${{item.title || item.trait || "依据"}}</strong><span class="muted">${{item.basis || ""}}</span><br><span class="muted">${{item.real_world || ""}}</span></li>`).join("")}}</ul></div>`;
    }}

    function renderJudgmentItem(item) {{
      return `<li><strong>${{item.title}}</strong><span class="muted">依据：${{item.basis}}</span><br><span class="muted">现实表现：${{item.real_world}}</span><br><span class="muted">具体建议：${{item.advice}}</span></li>`;
    }}

    function renderCareerDirection(item) {{
      return `<div class="career-card">
        <h4>${{item.job}}</h4>
        <p class="muted"><strong>为什么适合：</strong>${{item.why}}</p>
        <p class="muted"><strong>如何切入：</strong>${{item.entry}}</p>
        <p class="muted"><strong>需要补什么：</strong>${{item.skill_gap}}</p>
      </div>`;
    }}

    function renderUnsuitableDirection(item) {{
      return `<li><strong>${{item.type}}</strong><span class="muted">不适合原因：${{item.reason}}</span><br><span class="muted">如果不得不做：${{item.damage_control}}</span></li>`;
    }}

    function renderMoneyStage(item) {{
      return `<div class="money-stage"><strong>${{item.stage}}</strong><p class="muted">${{item.focus}}</p><ul>${{item.actions.map(action => `<li>${{action}}</li>`).join("")}}</ul></div>`;
    }}

    function renderMonthPlan(item) {{
      return `<div class="month-card"><strong>${{item.month}}</strong><ol>${{item.actions.map(action => `<li>${{action}}</li>`).join("")}}</ol></div>`;
    }}

    function renderLifeLesson(item) {{
      if (!item) return `<p class="muted">人生课题正在生成中。</p>`;
      return `<div class="month-card">
          <strong>核心卡点</strong>
          <p class="muted">${{item.core_issue}}</p>
        </div>
        <div class="report-grid">
          <div class="strategy-card">
            <h4>现实中的具体表现</h4>
            <ul>${{(item.real_world_patterns || []).map(text => `<li>${{text}}</li>`).join("")}}</ul>
          </div>
          <div class="strategy-card">
            <h4>不处理的现实代价</h4>
            <p class="muted">${{item.hidden_cost}}</p>
            <h4>突破方法</h4>
            <p class="muted">${{item.breakthrough_method}}</p>
          </div>
        </div>
        <div class="career-grid" style="margin-top:12px;">
          ${{(item.practice_plan || []).map(step => `<div class="career-card"><h4>${{step.action}}</h4><p class="muted"><strong>怎么做：</strong>${{step.how_to_do_it}}</p><p class="muted"><strong>频率：</strong>${{step.frequency}}</p></div>`).join("")}}
        </div>
        <div class="month-card">
          <strong>重大选择前先问自己</strong>
          <ol>${{(item.decision_questions || []).map(question => `<li>${{question}}</li>`).join("")}}</ol>
        </div>`;
    }}

    function renderNavigationCard(card) {{
      const cityRows = card.city_ranking ? `<div>${{card.city_ranking.map(item => `<div class="city-row"><strong>${{item.city}}</strong><span>${{item.score}}</span><span>${{item.reason}}</span></div>`).join("")}}</div>` : "";
      return `<div class="section-card">
        <h2>${{card.title}}</h2>
        <p><strong>${{card.answer}}</strong></p>
        <p class="muted" style="margin-top:10px;">${{card.explanation}}</p>
        ${{cityRows}}
        <section><h2>可执行建议</h2><ul>${{card.suggestions.map(s => `<li>${{s}}</li>`).join("")}}</ul></section>
        <details><summary>查看专业依据</summary>
          <p class="muted"><strong>八字依据：</strong>${{card.professional_basis.bazi}}</p>
          <p class="muted"><strong>星盘依据：</strong>${{card.professional_basis.astrology}}</p>
        </details>
      </div>`;
    }}

    async function confirmChart() {{
      await post(`/api/bazi/${{sessionId}}/confirm`);
      el(`${{steps(2)}}<h2>正在生成经历校验问题...</h2><p class="muted">我们会用过去年份、真实事件和大运感受校验喜忌，让结论更贴近你的实际经历。</p>`);
      const data = await post("/api/questions/generate", {{ session_id: sessionId }});
      renderQuestions(data.questions, 0, []);
    }}

    function renderQuestions(questions, index, answers) {{
      if (index >= questions.length) return submitAnswers(answers);
      const q = questions[index];
      el(`${{steps(2)}}<h2>问题 ${{index+1}} / ${{questions.length}}</h2><p>${{q.question}}</p>
        ${{q.intro ? `<p class="section-card">${{q.intro}}</p>` : ""}}
        ${{q.context ? `<p class="muted">${{q.context}}</p>` : ""}}
        <section>${{q.options.map(o=>`<button class="option" onclick="pickAnswer(${{q.id}},'${{o.key}}')"><strong>${{o.key}}</strong> ${{o.text}}${{o.reason ? `<br><span class="muted">${{o.reason}}</span>` : ""}}</button>`).join("")}}</section>`);
      window.pickAnswer = (question_id, selected_key) => {{
        answers.push({{ question_id, selected_key }});
        setTimeout(() => renderQuestions(questions, index + 1, answers), 350);
      }};
    }}

    async function submitAnswers(answers) {{
      el(`${{steps(2)}}<h2>正在综合校验...</h2><p class="muted">正在把你的经历反馈转成喜忌证据，再进入人生导航模块选择。</p>`);
      const data = await post(`/api/questions/${{sessionId}}/answer`, {{ session_id: sessionId, answers }});
      showCalibrationSummary(data.analysis);
    }}

    function renderReport() {{
      el(`${{steps(3)}}<h2>你的命理报告</h2><p class="muted">正在生成...</p><div id="report"></div>`);
      const report = document.querySelector("#report");
      const source = new EventSource(apiUrl(`/api/report/${{sessionId}}/stream`));
      source.addEventListener("section_chunk", (event) => {{
        const data = JSON.parse(event.data);
        report.innerHTML += `<div class="section-card"><h2>${{data.title}}</h2><p>${{data.content}}</p><p class="muted">${{data.highlight || ""}}</p></div>`;
      }});
      source.addEventListener("recommendations", (event) => {{
        const data = JSON.parse(event.data);
        report.innerHTML += `<div class="section-card"><h2>喜忌与建议</h2><p>喜用：${{data.wuxing.favorable.join("、")}}；忌神：${{data.wuxing.unfavorable.join("、")}}</p><p>幸运色：${{data.recommendations.colors.favorable.join("、")}}</p><p>居住方位：${{data.recommendations.living_direction.best}}</p><p>饰品：${{data.recommendations.jewelry.map(j=>j.category).join("、")}}</p></div>`;
      }});
      source.addEventListener("report_complete", () => {{ source.close(); }});
      source.addEventListener("error", () => {{ source.close(); }});
    }}

    form.addEventListener("submit", async (event) => {{
      event.preventDefault();
      submit.disabled = true;
      syncRegionValue();
      showResultPage();
      el(`${{steps(0)}}<h2>正在排盘...</h2><p class="muted">换算真太阳时、生成四柱和五行分布。</p>`);
      try {{
        const session = await post("/api/session/create");
        sessionId = session.session_id;
        const values = Object.fromEntries(new FormData(form).entries());
        values.unknown_time = form.unknown_time.checked;
        values.session_id = sessionId;
        const data = await post("/api/bazi/calculate", values);
        renderChart(data);
      }} catch (error) {{
        el(`<div class="error">${{error.message}}</div>`);
      }} finally {{
        submit.disabled = false;
      }}
    }});
    initRegions();
  </script>
</body>
</html>"""


@app.post("/api/session/create")
def create_session() -> dict[str, Any]:
    _clean_expired_sessions()
    sid = str(uuid4())
    SESSIONS[sid] = {
        "session_id": sid,
        "status": "init",
        "created_at": _now(),
        "updated_at": _now(),
    }
    return {"session_id": sid, "sessionId": sid, "status": "init", "created_at": SESSIONS[sid]["created_at"].isoformat() + "Z"}


@app.get("/api/cities")
def get_cities() -> dict[str, Any]:
    options = list_city_options()
    return {"count": len(options), "cities": options}


@app.get("/api/regions")
def get_regions() -> dict[str, Any]:
    regions = list_region_hierarchy()
    return {"count": len(regions), "regions": regions}


@app.get("/api/session/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    sid = _session_id(session_id)
    return _public_session(SESSIONS[sid])


@app.post("/api/bazi/calculate")
def calculate(request: BaziRequest) -> dict[str, Any]:
    sid = _session_id(request)
    solar_date = request.solar_date or request.solarDate
    solar_time = request.solar_time or request.solarTime or "23:00"
    unknown_time = bool(request.unknown_time if request.unknown_time is not None else request.unknownTime)
    if not solar_date:
        raise HTTPException(status_code=400, detail="请填写出生日期")
    try:
        birth_date = datetime.strptime(solar_date, "%Y-%m-%d")
        birth_time = datetime.strptime(solar_time, "%H:%M")
        result = calculate_bazi(
            solar_year=birth_date.year,
            solar_month=birth_date.month,
            solar_day=birth_date.day,
            solar_hour=birth_time.hour,
            solar_minute=birth_time.minute,
            city=_normalize_city(request.city),
            gender=request.gender,
            unknown_time=unknown_time,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    session = SESSIONS[sid]
    display_name = (request.name or "").strip()
    if display_name:
        result["birth_info"]["name"] = display_name
    session["birth_info"] = result["birth_info"]
    session["bazi_chart"] = result["bazi_chart"]
    session["astrology"] = calculate_western_chart(result["birth_info"])
    session["status"] = "chart_ready"
    _touch(session)
    return {"session_id": sid, "sessionId": sid, "astrology": session["astrology"], **result}


@app.get("/api/bazi/{session_id}")
def get_bazi(session_id: str) -> dict[str, Any]:
    sid = _session_id(session_id)
    session = SESSIONS[sid]
    if "bazi_chart" not in session:
        raise HTTPException(status_code=404, detail="尚未排盘")
    return {"session_id": sid, "birth_info": session["birth_info"], "bazi_chart": session["bazi_chart"]}


@app.post("/api/bazi/{session_id}/confirm")
def confirm_bazi(session_id: str) -> dict[str, Any]:
    sid = _session_id(session_id)
    session = SESSIONS[sid]
    if "bazi_chart" not in session:
        raise HTTPException(status_code=400, detail="请先完成排盘")
    session["status"] = "chart_confirmed"
    _touch(session)
    return {"session_id": sid, "sessionId": sid, "status": session["status"], "next_step": "questions"}


@app.post("/api/questions/generate")
def generate_questions(request: SessionRequest) -> dict[str, Any]:
    sid = _session_id(request)
    session = SESSIONS[sid]
    if session.get("status") not in {"chart_confirmed", "questions_ready", "questions_answered", "report_ready"}:
        raise HTTPException(status_code=400, detail="请先确认命盘")
    questions = _question_bank(session["bazi_chart"], session.get("birth_info"))
    session["questions"] = questions
    session["bazi_chart"]["_questions"] = questions
    session["status"] = "questions_ready"
    _touch(session)
    return {"session_id": sid, "sessionId": sid, "questions": questions}


@app.get("/api/questions/{session_id}")
def get_questions(session_id: str) -> dict[str, Any]:
    sid = _session_id(session_id)
    return {"session_id": sid, "questions": SESSIONS[sid].get("questions", [])}


@app.post("/api/questions/{session_id}/answer")
def submit_answers(session_id: str, request: AnswerRequest) -> dict[str, Any]:
    sid = _session_id(session_id)
    if request.session_id or request.sessionId:
        _session_id(request)
    session = SESSIONS[sid]
    if not session.get("questions"):
        raise HTTPException(status_code=400, detail="请先生成问题")
    analysis = _analyze_answers(session["bazi_chart"], request.answers, session.get("birth_info"))
    session["answers"] = analysis.pop("answers")
    session["analysis"] = analysis
    session["status"] = "questions_answered"
    session.pop("report", None)
    _touch(session)
    return {"session_id": sid, "sessionId": sid, "analysis": analysis}


@app.post("/api/navigation/generate")
def generate_navigation(request: NavigationRequest) -> dict[str, Any]:
    sid = _session_id(request)
    session = SESSIONS[sid]
    if not session.get("bazi_chart") or not session.get("birth_info"):
        raise HTTPException(status_code=400, detail="请先完成出生信息分析")
    if not session.get("astrology"):
        session["astrology"] = calculate_western_chart(session["birth_info"])
    report = generate_navigation_report(
        modules=request.modules,
        bazi_chart=session["bazi_chart"],
        birth_info=session["birth_info"],
        astrology=session.get("astrology"),
        analysis=session.get("analysis"),
    )
    session["navigation_report"] = report
    session["status"] = "navigation_ready"
    _touch(session)
    return {"session_id": sid, "sessionId": sid, "report": report}


@app.get("/api/report/{session_id}/stream")
async def stream_report(session_id: str) -> StreamingResponse:
    sid = _session_id(session_id)
    session = SESSIONS[sid]
    if not session.get("analysis"):
        raise HTTPException(status_code=400, detail="请先提交校准问题")
    report = _build_report(session)
    session["status"] = "report_generating"
    _touch(session)

    async def events():
        yield _sse("report_start", {"session_id": sid})
        for section in report["sections"]:
            yield _sse("section_start", {"id": section["id"], "title": section["title"]})
            await asyncio.sleep(0.15)
            yield _sse("section_chunk", section)
            yield _sse("section_end", {"id": section["id"]})
        yield _sse(
            "recommendations",
            {
                "wuxing": report["wuxing_analysis"],
                "recommendations": report["recommendations"],
            },
        )
        session["report"] = report
        session["status"] = "report_ready"
        _touch(session)
        yield _sse("report_complete", {"session_id": sid, "status": "report_ready"})

    return StreamingResponse(events(), media_type="text/event-stream")


@app.get("/api/report/{session_id}/full")
@app.get("/api/report/{session_id}")
def get_report(session_id: str) -> dict[str, Any]:
    sid = _session_id(session_id)
    session = SESSIONS[sid]
    if not session.get("analysis"):
        raise HTTPException(status_code=400, detail="请先提交校准问题")
    if not session.get("report"):
        session["report"] = _build_report(session)
        session["status"] = "report_ready"
        _touch(session)
    return session["report"]
