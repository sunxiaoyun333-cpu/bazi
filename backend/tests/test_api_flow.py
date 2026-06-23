from main import (
    Answer,
    AnswerRequest,
    BaziRequest,
    NavigationRequest,
    SessionRequest,
    calculate,
    confirm_bazi,
    create_session,
    generate_navigation,
    generate_questions,
    get_report,
    get_cities,
    get_regions,
    submit_answers,
)
from services.astrology_engine import calculate_western_chart


def test_full_api_flow():
    created = create_session()
    session_id = created["session_id"]

    calculated = calculate(
        BaziRequest(
            session_id=session_id,
            solar_date="1990-05-15",
            solar_time="14:30",
            city="上海",
            gender="female",
            unknown_time=False,
        )
    )
    chart = calculated["bazi_chart"]
    assert chart["pillars"]["year"]["stem"]

    confirmed = confirm_bazi(session_id)
    assert confirmed["next_step"] == "questions"

    generated = generate_questions(SessionRequest(session_id=session_id))
    questions = generated["questions"]
    assert len(questions) == 3
    assert all(len(q["options"]) == 4 for q in questions)
    assert [q["type"] for q in questions] == ["anchor", "event", "dayun_transition"]
    assert questions[0]["intro"]
    assert questions[0]["_meta"]["best_year"]["year"]

    answered = submit_answers(
        session_id,
        AnswerRequest(
            session_id=session_id,
            answers=[
                Answer(question_id=1, selected_key="A"),
                Answer(question_id=2, selected_key="B"),
                Answer(question_id=3, selected_key="C"),
            ],
        ),
    )
    assert answered["analysis"]["final_judgment"] in {"身强", "身弱", "中和"}
    assert answered["analysis"]["evidence"] is not None
    assert answered["analysis"]["yong_shen"]
    breakdown = answered["analysis"]["score_breakdown"]
    assert breakdown["initial"]["scores"]
    assert len(breakdown["answer_adjustments"]) == 3
    assert breakdown["final"]["scores"] == answered["analysis"]["scores"]

    body = get_report(session_id)
    assert len(body["sections"]) == 6
    assert body["recommendations"]["jewelry"]

    navigation = generate_navigation(NavigationRequest(session_id=session_id, modules=["career"]))
    report = navigation["report"]
    nav_card = report["cards"][0]
    assert navigation["report"]["selected_modules"] == ["career"]
    assert "analysis_json" in report
    assert "report_sections" in report
    assert report["report_sections"]["career_directions"][0]["job"]
    assert nav_card["professional_basis"]["bazi"]


def test_city_catalog_supports_nationwide_city_and_district_names():
    cities = get_cities()
    assert cities["count"] > 3000
    values = {item["value"] for item in cities["cities"]}
    assert "乌鲁木齐" in values
    assert "上海浦东新区" in values or "浦东新区" in values

    regions = get_regions()
    assert regions["count"] >= 30
    shanghai = next(item for item in regions["regions"] if item["value"] == "上海")
    assert shanghai["cities"]
    assert any(district["label"] == "浦东新区" for district in shanghai["cities"][0]["districts"])

    created = create_session()
    calculated = calculate(
        BaziRequest(
            session_id=created["session_id"],
            solar_date="1990-05-15",
            solar_time="14:30",
            city="浦东新区",
            gender="female",
            unknown_time=False,
        )
    )
    assert calculated["birth_info"]["longitude"] > 120


def _prepared_navigation_session():
    created = create_session()
    session_id = created["session_id"]
    calculate(
        BaziRequest(
            session_id=session_id,
            solar_date="1990-05-15",
            solar_time="14:30",
            city="上海",
            gender="female",
            unknown_time=False,
        )
    )
    return session_id


def test_navigation_single_module():
    session_id = _prepared_navigation_session()
    result = generate_navigation(NavigationRequest(session_id=session_id, modules=["career"]))
    report = result["report"]
    assert report["selected_modules"] == ["career"]
    assert len(report["cards"]) == 1
    card = report["cards"][0]
    assert card["module"] == "career"
    assert card["answer"]
    assert card["explanation"]
    assert len(card["suggestions"]) == 3
    assert "professional_basis" in card
    assert report["analysis_json"]["suitable_career_directions"]
    assert report["report_sections"]["money_path"]
    assert len(report["report_sections"]["three_month_plan"]) == 3


def test_navigation_multiple_modules_and_city_ranking():
    session_id = _prepared_navigation_session()
    result = generate_navigation(NavigationRequest(session_id=session_id, modules=["talent", "city", "life_lesson"]))
    report = result["report"]
    assert report["selected_modules"] == ["talent", "city", "life_lesson"]
    assert report["analysis_json"]["core_traits"]
    assert report["analysis_json"]["life_lesson"]["core_issue"]
    assert len(report["analysis_json"]["life_lesson"]["practice_plan"]) >= 3
    assert report["report_sections"]["real_world_patterns"]
    assert report["report_sections"]["career_directions"]
    assert report["report_sections"]["life_lesson"]["decision_questions"]


def test_navigation_full_and_astrology_fallback_basis():
    session_id = _prepared_navigation_session()
    result = generate_navigation(NavigationRequest(session_id=session_id, modules=["full"]))
    report = result["report"]
    assert report["selected_modules"] == ["talent", "career", "city", "life_lesson"]
    assert report["astrology_status"] in {"ready", "fallback"}
    assert report["analysis_json"]["bazi_signals"]
    assert report["analysis_json"]["astrology_signals"]
    assert report["analysis_json"]["qa_validation"]
    assert report["report_sections"]["unsuitable_directions"]
    assert report["report_sections"]["life_lesson"]["hidden_cost"]
    assert "作品" in report["report_sections"]["life_lesson"]["hidden_cost"]
    assert report["report_sections"]["life_lesson"]["practice_plan"][0]["frequency"]
    assert report["report_sections"]["key_reminders"]
    assert "AI产品" in str(report["report_sections"]) or "项目助理" in str(report["report_sections"]) or "知识库运营" in str(report["report_sections"])
    if report["astrology_status"] == "fallback":
        assert any("星盘数据暂不可用" in item["basis"] for item in report["analysis_json"]["astrology_signals"])


def test_astrology_adapter_returns_expected_chart_shape():
    chart = calculate_western_chart(
        {
            "solar_date": "1990-05-15",
            "solar_time": "14:30",
            "timezone": "Asia/Shanghai",
            "longitude": 121.4737,
            "latitude": 31.2304,
        }
    )
    assert chart["_meta"]["status"] == "ready"
    assert chart["sun"]["sign"]
    assert 1 <= chart["moon"]["house"] <= 12
    assert chart["ascendant"]["sign"]
    assert "houses" in chart
    assert "aspects" in chart
    assert chart["_meta"]["provider"] == "pyswisseph"
    assert "longitude" in chart["sun"]
    assert "degree" in chart["mc"]
    assert len(chart["houses"]) == 12
    assert isinstance(chart["aspects"], list)
