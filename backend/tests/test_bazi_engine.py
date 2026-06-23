from datetime import datetime

from services.bazi_engine import (
    calculate_bazi,
    calculate_day_pillar,
    calculate_hour_pillar,
    calculate_month_pillar,
    calculate_ten_god,
    calculate_true_solar_time,
    calculate_year_pillar,
)


class TestTrueSolarTime:
    def test_shanghai_correction(self):
        dt = datetime(1990, 5, 15, 14, 30)
        _, correction = calculate_true_solar_time(dt, 121.4737)
        assert -15 <= correction <= -5

    def test_urumqi_correction(self):
        dt = datetime(1990, 5, 15, 14, 30)
        _, correction = calculate_true_solar_time(dt, 87.6177)
        assert correction < -100

    def test_beijing_near_zero(self):
        dt = datetime(2000, 9, 22, 12, 0)
        _, correction = calculate_true_solar_time(dt, 116.4074)
        assert -10 <= correction <= 5


class TestFourPillars:
    def test_case_1_before_lichun(self):
        dt = datetime(1984, 2, 3, 12, 0)
        year_pillar = calculate_year_pillar(dt)
        assert year_pillar.stem == "癸"
        assert year_pillar.branch == "亥"

    def test_case_1_after_lichun(self):
        dt = datetime(1984, 2, 5, 12, 0)
        year_pillar = calculate_year_pillar(dt)
        assert year_pillar.stem == "甲"
        assert year_pillar.branch == "子"

    def test_case_2_standard(self):
        dt = datetime(1990, 5, 15, 14, 22)

        year_pillar = calculate_year_pillar(dt)
        month_pillar = calculate_month_pillar(dt)
        day_pillar = calculate_day_pillar(dt)
        hour_pillar = calculate_hour_pillar(dt, day_pillar.stem)

        assert year_pillar.stem == "庚"
        assert year_pillar.branch == "午"
        assert month_pillar.stem == "辛"
        assert month_pillar.branch == "巳"
        assert day_pillar.stem == "庚"
        assert day_pillar.branch == "辰"
        assert hour_pillar.stem == "甲"
        assert hour_pillar.branch == "申"

    def test_day_pillar_known_almanac_case(self):
        day_pillar = calculate_day_pillar(datetime(2001, 11, 16))
        assert day_pillar.stem == "癸"
        assert day_pillar.branch == "未"

    def test_hour_pillar_gui_day_mao_shi(self):
        hour_pillar = calculate_hour_pillar(datetime(2001, 11, 16, 6, 0), "癸")
        assert hour_pillar.stem == "乙"
        assert hour_pillar.branch == "卯"

    def test_case_3_year_boundary(self):
        dt = datetime(2000, 2, 3, 12, 0)
        year_pillar = calculate_year_pillar(dt)
        month_pillar = calculate_month_pillar(dt)

        assert year_pillar.stem == "己"
        assert year_pillar.branch == "卯"
        assert month_pillar.branch == "丑"

    def test_hour_pillar_zi_shi(self):
        dt = datetime(1990, 5, 15, 23, 30)
        day_pillar = calculate_day_pillar(dt)
        hour_pillar = calculate_hour_pillar(dt, day_pillar.stem)
        assert hour_pillar.branch == "子"

    def test_hour_pillar_wu_shi(self):
        dt = datetime(1990, 5, 15, 12, 0)
        day_pillar = calculate_day_pillar(dt)
        hour_pillar = calculate_hour_pillar(dt, day_pillar.stem)
        assert hour_pillar.branch == "午"


class TestTenGods:
    def test_bijian(self):
        assert calculate_ten_god("甲", "甲") == "比肩"

    def test_jiecai(self):
        assert calculate_ten_god("甲", "乙") == "劫财"

    def test_zhengyin(self):
        assert calculate_ten_god("甲", "癸") == "正印"

    def test_qiansha(self):
        assert calculate_ten_god("甲", "庚") == "七杀"

    def test_zhengguan(self):
        assert calculate_ten_god("甲", "辛") == "正官"


class TestFullCalculation:
    def test_full_case_shanghai_female(self):
        result = calculate_bazi(
            solar_year=1990,
            solar_month=5,
            solar_day=15,
            solar_hour=14,
            solar_minute=30,
            city="上海",
            gender="female",
        )

        chart = result["bazi_chart"]

        assert chart["day_master"]["stem"] == "庚"
        assert chart["day_master"]["element"] == "金"
        assert chart["pillars"]["year"]["stem"] == "庚"
        assert chart["pillars"]["month"]["stem"] == "辛"
        assert chart["pillars"]["day"]["stem"] == "庚"
        assert chart["preliminary"]["strength"] == "身强"
        assert chart["dayun"]["forward"] is False

    def test_unknown_time(self):
        result = calculate_bazi(
            solar_year=1990,
            solar_month=5,
            solar_day=15,
            solar_hour=0,
            solar_minute=0,
            city="北京",
            gender="male",
            unknown_time=True,
        )

        chart = result["bazi_chart"]
        assert chart["unknown_time_note"] is not None
        assert chart["pillars"]["hour"]["branch"] == "子"

    def test_return_structure(self):
        result = calculate_bazi(
            solar_year=1985,
            solar_month=8,
            solar_day=20,
            solar_hour=10,
            solar_minute=0,
            city="北京",
            gender="male",
        )

        assert "birth_info" in result
        assert "bazi_chart" in result

        chart = result["bazi_chart"]
        assert "pillars" in chart
        assert "day_master" in chart
        assert "ten_gods" in chart
        assert "wuxing_score" in chart
        assert "dayun" in chart
        assert "preliminary" in chart
        assert "palaces" in chart

        pct = chart["wuxing_score"]["percentage"]
        total = sum(pct.values())
        assert 99 <= total <= 101, f"五行百分比合计异常：{total}"
