# 八字Agent · Codex 开发指令文档 v2.0

---

## 给 Codex 的开场说明

```
你是一个全栈开发工程师。
你需要在一天内独立完成一个"八字命理Agent"Web应用的完整开发。
本文档包含你需要知道的一切：
  - 产品是什么
  - 要构建什么
  - 用哪些开源库（已确定，直接用）
  - API如何调用
  - 每个页面长什么样
  - 逻辑如何运作

关于计算层：
  核心计算依赖 sxtwl（寿星万年历）处理节气和农历
  城市经纬度使用静态JSON数据文件
  不要自己实现节气算法，直接调用 sxtwl
```

---

## 一、产品是什么

### 一句话

> 用户输入出生日期、时间、地点，系统用 sxtwl
> 排出精确八字命盘，通过3道问答校准命主身强/身弱，
> 最终用 AI 生成包含事业、感情、健康等维度的完整
> 命理分析报告，并给出五行饰品推荐和生活建议。

### 核心流程（7步）

```
Step 1  用户填写出生信息（年月日时 + 地点 + 性别）
Step 2  系统用 sxtwl 计算真太阳时，排出精确八字四柱
Step 3  展示八字命盘，用户确认
Step 4  AI 生成3道校准问题
Step 5  用户依次回答3道题
Step 6  AI 流式生成完整命理报告
Step 7  展示报告（六维度 + 喜忌 + 饰品 + 建议）
```

---

## 二、技术栈

```
前端：
  框架：  Next.js 14（App Router）
  样式：  TailwindCSS
  组件：  shadcn/ui
  语言：  TypeScript

后端：
  框架：  Python 3.11 + FastAPI
  语言：  Python
  Session：内存字典（dict + TTL）

核心计算库（重点）：
  sxtwl       节气精确时刻 + 农历转换 + 基础干支
  lunardate   农历备用方案
  城市数据    静态 JSON 文件（modood 数据集）

AI API（二选一）：
  选项A：Google Gemini
    库：    google-generativeai
    模型：  gemini-1.5-flash
  选项B：OpenAI
    库：    openai
    模型：  gpt-4o-mini

部署：
  前端：Vercel
  后端：Railway
```

---

## 三、依赖安装

```bash
# backend/requirements.txt

fastapi==0.109.0
uvicorn[standard]==0.27.0
python-dotenv==1.0.0
pydantic==2.6.0

# 核心计算
sxtwl==0.0.9
lunardate==0.2.0

# AI（按需选一个）
google-generativeai==0.5.0
openai==1.12.0

# 测试
pytest==8.0.0
httpx==0.26.0
```

```bash
# 安装
pip install -r requirements.txt

# 验证 sxtwl 安装
python -c "import sxtwl; print('sxtwl OK')"
```

---

## 四、数据准备（开始写代码前先做）

### 4.1 城市经纬度数据

```bash
# 第一步：下载城市数据
# 在 backend/data/ 目录下执行

# 使用 uiwjs 的数据（含经纬度，覆盖全国地级市）
curl -L -o city_raw.json \
  "https://raw.githubusercontent.com/uiwjs/province-city-china/master/dist/data.json"
```

```python
# backend/scripts/prepare_cities.py
# 运行此脚本将原始数据转换为项目格式
# 执行：python backend/scripts/prepare_cities.py

import json
import os

def prepare():
    raw_path = os.path.join(os.path.dirname(__file__), "../data/city_raw.json")
    out_path = os.path.join(os.path.dirname(__file__), "../data/cities.json")

    with open(raw_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    cities = {}

    def process(node: dict):
        name = node.get("name", "")
        lng  = node.get("longitude") or node.get("lng")
        lat  = node.get("latitude")  or node.get("lat")

        if name and lng and lat:
            try:
                entry = {
                    "longitude": float(lng),
                    "latitude":  float(lat),
                }
                # 存原名
                cities[name] = entry
                # 存去后缀名
                clean = name.replace("市","").replace("区","") \
                            .replace("县","").replace("省","")
                if clean and clean != name:
                    cities[clean] = entry
            except (ValueError, TypeError):
                pass

        for child in node.get("children", []):
            process(child)

    if isinstance(raw, list):
        for item in raw:
            process(item)
    else:
        process(raw)

    # 补充重要城市（防止数据集遗漏）
    FALLBACK = {
        "北京":    {"longitude": 116.4074, "latitude": 39.9042},
        "上海":    {"longitude": 121.4737, "latitude": 31.2304},
        "广州":    {"longitude": 113.2644, "latitude": 23.1291},
        "深圳":    {"longitude": 114.0579, "latitude": 22.5431},
        "成都":    {"longitude": 104.0665, "latitude": 30.5723},
        "武汉":    {"longitude": 114.3054, "latitude": 30.5931},
        "西安":    {"longitude": 108.9480, "latitude": 34.2658},
        "杭州":    {"longitude": 120.1551, "latitude": 30.2741},
        "南京":    {"longitude": 118.7969, "latitude": 32.0603},
        "重庆":    {"longitude": 106.5516, "latitude": 29.5630},
        "乌鲁木齐":{"longitude": 87.6177,  "latitude": 43.8256},
        "拉萨":    {"longitude": 91.1322,  "latitude": 29.6625},
        "哈尔滨":  {"longitude": 126.6424, "latitude": 45.7569},
        "昆明":    {"longitude": 102.8329, "latitude": 24.8801},
    }

    for k, v in FALLBACK.items():
        if k not in cities:
            cities[k] = v

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cities, f, ensure_ascii=False, indent=2)

    print(f"城市数据准备完成，共 {len(cities)} 条")

if __name__ == "__main__":
    prepare()
```

```bash
# 执行数据准备
python backend/scripts/prepare_cities.py
# 输出：城市数据准备完成，共 XXX 条
```

### 4.2 验证 sxtwl 节气数据

```python
# backend/scripts/verify_sxtwl.py
# 运行此脚本验证 sxtwl 的节气和干支是否正确

import sxtwl

STEMS    = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

# 节气名称（sxtwl 内部顺序，从冬至开始）
QI_NAMES = [
    "冬至","小寒","大寒","立春","雨水","惊蛰",
    "春分","清明","谷雨","立夏","小满","芒种",
    "夏至","小暑","大暑","立秋","处暑","白露",
    "秋分","寒露","霜降","立冬","小雪","大雪",
]

print("=" * 50)
print("验证 sxtwl 节气计算（1990年）")
print("=" * 50)

for i, name in enumerate(QI_NAMES):
    jd  = sxtwl.getQi(1990, i)
    day = sxtwl.JD2DD(jd)
    print(f"{name}: {int(day.Y)}年{int(day.M):02d}月{int(day.D):02d}日 "
          f"{int(day.h):02d}:{int(day.m):02d}")

print()
print("=" * 50)
print("验证阳历转农历（1990-05-15）")
print("=" * 50)

d = sxtwl.fromSolar(1990, 5, 15)
print(f"农历：{int(d.Lyear)}年 {int(d.Lmonth)}月 {int(d.Lday)}日")
print(f"是否闰月：{bool(d.isLrun)}")
print(f"年柱：{STEMS[int(d.Lyear_Gan)]}{BRANCHES[int(d.Lyear_Zhi)]}")
print(f"月柱：{STEMS[int(d.Lmonth_Gan)]}{BRANCHES[int(d.Lmonth_Zhi)]}")
print(f"日柱：{STEMS[int(d.Lday_Gan)]}{BRANCHES[int(d.Lday_Zhi)]}")

# 期望：庚午年 辛巳月 癸亥日
```

---

## 五、环境变量

```bash
# backend/.env

# AI 选择（gemini 或 openai）
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-flash
GEMINI_API_KEY=your_key_here

# 如果用 OpenAI
# AI_PROVIDER=openai
# AI_MODEL=gpt-4o-mini
# OPENAI_API_KEY=your_key_here

SESSION_TTL_HOURS=24
CORS_ORIGINS=http://localhost:3000
```

```bash
# frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## 六、文件结构

```
bazi-agent/
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                   # 首页：信息输入
│   │   ├── globals.css
│   │   └── reading/
│   │       └── [sessionId]/
│   │           └── page.tsx           # 主流程页
│   │
│   ├── components/
│   │   ├── ui/                        # shadcn 组件
│   │   ├── BirthInfoForm.tsx          # Step1 表单
│   │   ├── BaziChart.tsx              # Step3 命盘展示
│   │   ├── WuxingBar.tsx              # 五行分布条
│   │   ├── DayunList.tsx              # 大运列表
│   │   ├── QuestionFlow.tsx           # Step5 问答
│   │   ├── QuestionCard.tsx           # 单题卡片
│   │   ├── ReportStream.tsx           # Step6/7 流式报告
│   │   ├── ReportSection.tsx          # 单章节
│   │   ├── JewelryCard.tsx            # 饰品推荐
│   │   └── LoadingState.tsx           # 加载状态
│   │
│   ├── lib/
│   │   ├── api.ts                     # API 调用封装
│   │   ├── types.ts                   # TypeScript 类型
│   │   └── utils.ts
│   │
│   └── hooks/
│       └── useSSE.ts                  # SSE 流式接收
│
├── backend/
│   ├── main.py                        # FastAPI 入口
│   ├── requirements.txt
│   ├── .env
│   │
│   ├── routers/
│   │   ├── session.py
│   │   ├── bazi.py
│   │   ├── questions.py
│   │   └── report.py
│   │
│   ├── services/
│   │   ├── bazi_engine.py             # 八字计算（基于sxtwl）
│   │   ├── city_service.py            # 城市经纬度查询
│   │   ├── solar_time.py              # 真太阳时换算
│   │   ├── ai_client.py              # AI 统一客户端
│   │   ├── question_service.py        # 问题生成
│   │   └── report_service.py          # 报告生成
│   │
│   ├── prompts/
│   │   ├── question_prompt.py
│   │   └── report_prompt.py
│   │
│   ├── data/
│   │   ├── city_raw.json              # 下载的原始数据
│   │   ├── cities.json                # 整理后的城市经纬度
│   │   └── jewelry_mapping.py         # 饰品映射
│   │
│   ├── store/
│   │   └── session_store.py           # 内存 Session
│   │
│   └── scripts/
│       ├── prepare_cities.py          # 数据准备脚本
│       └── verify_sxtwl.py            # 验证脚本
│
└── README.md
```

---

## 七、后端核心实现

### 7.1 城市服务

```python
# backend/services/city_service.py

import json
import os
from typing import Optional

_CITIES: dict | None = None

def _load_cities() -> dict:
    global _CITIES
    if _CITIES is None:
        path = os.path.join(
            os.path.dirname(__file__), "../data/cities.json"
        )
        with open(path, "r", encoding="utf-8") as f:
            _CITIES = json.load(f)
    return _CITIES


def get_coordinates(city_name: str) -> Optional[dict]:
    """
    城市名 → 经纬度
    支持：全称 / 去后缀 / 模糊匹配
    返回：{"longitude": float, "latitude": float} 或 None
    """
    cities = _load_cities()

    # 1. 精确匹配
    if city_name in cities:
        return cities[city_name]

    # 2. 去后缀匹配
    for suffix in ["市", "区", "县", "省", "自治区", "特别行政区"]:
        clean = city_name.replace(suffix, "")
        if clean in cities:
            return cities[clean]

    # 3. 包含匹配（取第一个）
    for key, val in cities.items():
        if city_name in key or key in city_name:
            return val

    return None


def list_all_cities() -> list[str]:
    """返回所有可用城市名列表"""
    return list(_load_cities().keys())
```

### 7.2 真太阳时服务

```python
# backend/services/solar_time.py

import math
from datetime import datetime, timedelta

BEIJING_LONGITUDE = 120.0


def get_equation_of_time(day_of_year: int) -> float:
    """
    均时差（Equation of Time）
    单位：分钟，精度：约 ±30秒
    基于 Spencer(1971) 近似公式
    """
    B = math.radians((360.0 / 365.0) * (day_of_year - 81))
    eot = (
        9.87  * math.sin(2 * B)
        - 7.53 * math.cos(B)
        - 1.5  * math.sin(B)
    )
    return eot


def beijing_to_true_solar(
    dt: datetime,
    longitude: float,
) -> tuple[datetime, int]:
    """
    北京时间 → 真太阳时

    计算步骤：
      ① 地方平时修正 = (出生地经度 - 120°) × 4 分钟/度
      ② 均时差修正   = f(出生日期) ≈ ±16分钟
      ③ 真太阳时     = 北京时间 + ① + ②

    Args:
        dt:        北京时间 datetime
        longitude: 出生地东经度数

    Returns:
        (真太阳时 datetime, 总修正分钟数)
    """
    # ① 经度修正
    longitude_correction = (longitude - BEIJING_LONGITUDE) * 4.0

    # ② 均时差
    doy = dt.timetuple().tm_yday
    eot = get_equation_of_time(doy)

    # ③ 合计（四舍五入到整分钟）
    total_minutes = round(longitude_correction + eot)
    true_solar_dt = dt + timedelta(minutes=total_minutes)

    return true_solar_dt, total_minutes
```

### 7.3 八字计算引擎（基于 sxtwl）

```python
# backend/services/bazi_engine.py
#
# 依赖：
#   sxtwl  —— 节气精确时刻、农历转换、基础干支索引
#   自实现 —— 时柱、十神、五行评分、大运、身强身弱
#
# sxtwl 节气索引对照（getQi 第二参数）：
#   0=冬至  1=小寒  2=大寒  3=立春  4=雨水  5=惊蛰
#   6=春分  7=清明  8=谷雨  9=立夏 10=小满 11=芒种
#  12=夏至 13=小暑 14=大暑 15=立秋 16=处暑 17=白露
#  18=秋分 19=寒露 20=霜降 21=立冬 22=小雪 23=大雪

import sxtwl
import math
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
from services.solar_time import beijing_to_true_solar
from services.city_service import get_coordinates


# ============================================================
# 常量
# ============================================================

STEMS    = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

STEM_ELEMENT = {
    "甲":"木","乙":"木","丙":"火","丁":"火","戊":"土",
    "己":"土","庚":"金","辛":"金","壬":"水","癸":"水",
}

STEM_YIN_YANG = {
    "甲":"阳","丙":"阳","戊":"阳","庚":"阳","壬":"阳",
    "乙":"阴","丁":"阴","己":"阴","辛":"阴","癸":"阴",
}

BRANCH_ELEMENT = {
    "子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火",
    "午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水",
}

# 地支藏干：(天干, 权重)  本气=3 中气=2 余气=1
BRANCH_HIDDEN = {
    "子":[("癸",3)],
    "丑":[("己",3),("癸",1),("辛",2)],
    "寅":[("甲",3),("丙",1),("戊",2)],
    "卯":[("乙",3)],
    "辰":[("戊",3),("乙",1),("癸",2)],
    "巳":[("丙",3),("庚",2),("戊",1)],
    "午":[("丁",3),("己",2)],
    "未":[("己",3),("丁",1),("乙",2)],
    "申":[("庚",3),("壬",2),("戊",1)],
    "酉":[("辛",3)],
    "戌":[("戊",3),("辛",1),("丁",2)],
    "亥":[("壬",3),("甲",2)],
}

# 纳音表
NAYIN = {
    ("甲","子"):"海中金",("乙","丑"):"海中金",
    ("丙","寅"):"炉中火",("丁","卯"):"炉中火",
    ("戊","辰"):"大林木",("己","巳"):"大林木",
    ("庚","午"):"路旁土",("辛","未"):"路旁土",
    ("壬","申"):"剑锋金",("癸","酉"):"剑锋金",
    ("甲","戌"):"山头火",("乙","亥"):"山头火",
    ("丙","子"):"涧下水",("丁","丑"):"涧下水",
    ("戊","寅"):"城头土",("己","卯"):"城头土",
    ("庚","辰"):"白蜡金",("辛","巳"):"白蜡金",
    ("壬","午"):"杨柳木",("癸","未"):"杨柳木",
    ("甲","申"):"泉中水",("乙","酉"):"泉中水",
    ("丙","戌"):"屋上土",("丁","亥"):"屋上土",
    ("戊","子"):"霹雳火",("己","丑"):"霹雳火",
    ("庚","寅"):"松柏木",("辛","卯"):"松柏木",
    ("壬","辰"):"长流水",("癸","巳"):"长流水",
    ("甲","午"):"沙中金",("乙","未"):"沙中金",
    ("丙","申"):"山下火",("丁","酉"):"山下火",
    ("戊","戌"):"平地木",("己","亥"):"平地木",
    ("庚","子"):"壁上土",("辛","丑"):"壁上土",
    ("壬","寅"):"金箔金",("癸","卯"):"金箔金",
    ("甲","辰"):"覆灯火",("乙","巳"):"覆灯火",
    ("丙","午"):"天河水",("丁","未"):"天河水",
    ("戊","申"):"大驿土",("己","酉"):"大驿土",
    ("庚","戌"):"钗钏金",("辛","亥"):"钗钏金",
    ("壬","子"):"桑柘木",("癸","丑"):"桑柘木",
    ("甲","寅"):"大溪水",("乙","卯"):"大溪水",
    ("丙","辰"):"沙中土",("丁","巳"):"沙中土",
    ("戊","午"):"天上火",("己","未"):"天上火",
    ("庚","申"):"石榴木",("辛","酉"):"石榴木",
    ("壬","戌"):"大海水",("癸","亥"):"大海水",
}

# 月令旺衰系数  {月支: {五行: 系数}}
MONTH_STRENGTH = {
    "寅":{"木":3.0,"火":1.5,"土":0.5,"金":0.3,"水":1.0},
    "卯":{"木":3.5,"火":1.5,"土":0.3,"金":0.3,"水":1.0},
    "辰":{"木":1.5,"火":1.0,"土":3.0,"金":0.5,"水":0.5},
    "巳":{"木":0.5,"火":3.0,"土":1.5,"金":1.0,"水":0.3},
    "午":{"木":0.5,"火":3.5,"土":1.5,"金":0.3,"水":0.3},
    "未":{"木":1.0,"火":1.5,"土":3.0,"金":0.5,"水":0.5},
    "申":{"木":0.3,"火":0.5,"土":1.5,"金":3.0,"水":1.0},
    "酉":{"木":0.3,"火":0.3,"土":1.0,"金":3.5,"水":1.5},
    "戌":{"木":0.5,"火":1.0,"土":3.0,"金":1.5,"水":0.5},
    "亥":{"木":1.0,"火":0.3,"土":0.3,"金":0.5,"水":3.0},
    "子":{"木":1.0,"火":0.3,"土":0.3,"金":1.0,"水":3.5},
    "丑":{"木":0.5,"火":0.5,"土":3.0,"金":1.5,"水":1.0},
}

# 位置权重
POSITION_WEIGHT = {
    "year_stem":  1.0,
    "month_stem": 1.5,
    "day_stem":   1.5,
    "hour_stem":  1.0,
    "year_branch":  1.0,
    "month_branch": 2.0,   # 月令最重
    "day_branch":   1.5,
    "hour_branch":  1.0,
}

HIDDEN_WEIGHT = {3: 1.0, 2: 0.6, 1: 0.3}

# 五行生克
GENERATES    = {"木":"火","火":"土","土":"金","金":"水","水":"木"}
CONTROLS     = {"木":"土","火":"金","土":"水","金":"木","水":"火"}
GENERATED_BY = {v: k for k, v in GENERATES.items()}
CONTROLLED_BY= {v: k for k, v in CONTROLS.items()}

# sxtwl 节气索引
QI_INDEX = {
    "冬至":0,"小寒":1,"大寒":2,"立春":3,"雨水":4,"惊蛰":5,
    "春分":6,"清明":7,"谷雨":8,"立夏":9,"小满":10,"芒种":11,
    "夏至":12,"小暑":13,"大暑":14,"立秋":15,"处暑":16,"白露":17,
    "秋分":18,"寒露":19,"霜降":20,"立冬":21,"小雪":22,"大雪":23,
}

# 月建对应的"节"
JIE_TO_BRANCH = {
    "立春":"寅","惊蛰":"卯","清明":"辰","立夏":"巳",
    "芒种":"午","小暑":"未","立秋":"申","白露":"酉",
    "寒露":"戌","立冬":"亥","大雪":"子","小寒":"丑",
}

JIE_NAMES = list(JIE_TO_BRANCH.keys())


# ============================================================
# sxtwl 工具函数
# ============================================================

def _get_qi_datetime(year: int, qi_name: str) -> datetime:
    """
    用 sxtwl 获取指定年份某节气的精确时刻
    注意：小寒/大寒在1月，sxtwl.getQi(year, 1/2) 返回该年1月的小寒/大寒
    """
    idx = QI_INDEX[qi_name]
    jd  = sxtwl.getQi(year, idx)
    d   = sxtwl.JD2DD(jd)
    return datetime(int(d.Y), int(d.M), int(d.D), int(d.h), int(d.m))


def _get_lichun(year: int) -> datetime:
    """获取指定年立春时刻"""
    return _get_qi_datetime(year, "立春")


def _get_all_jie(year: int) -> list[tuple[str, datetime]]:
    """
    获取某年附近所有月建"节"的时刻
    为确保覆盖年首年尾，同时取上一年和下一年的节
    """
    result = []
    for y in [year - 1, year, year + 1]:
        for name in JIE_NAMES:
            try:
                dt = _get_qi_datetime(y, name)
                result.append((name, dt))
            except Exception:
                pass
    result.sort(key=lambda x: x[1])
    return result


# ============================================================
# 四柱计算
# ============================================================

def _calc_year_pillar(true_solar_dt: datetime) -> tuple[str, str]:
    """
    年柱：以立春为界
    sxtwl 提供精确立春时刻
    """
    year   = true_solar_dt.year
    lichun = _get_lichun(year)

    ref_year = year if true_solar_dt >= lichun else year - 1

    # 甲子年 = 1984
    offset = (ref_year - 1984) % 60
    if offset < 0:
        offset += 60

    return STEMS[offset % 10], BRANCHES[offset % 12]


def _calc_month_pillar(
    true_solar_dt: datetime,
    year_stem: str
) -> tuple[str, str]:
    """
    月柱：以12个"节"为界
    sxtwl 提供精确节气时刻
    """
    all_jie = _get_all_jie(true_solar_dt.year)

    # 找当前时间所在区间的节
    current_jie_name = "立春"  # 默认
    for i in range(len(all_jie) - 1):
        name, dt      = all_jie[i]
        _, next_dt    = all_jie[i + 1]
        if dt <= true_solar_dt < next_dt:
            current_jie_name = name
            break
    else:
        # 超过最后一个节
        current_jie_name = all_jie[-1][0]

    month_branch = JIE_TO_BRANCH[current_jie_name]

    # 月干：五虎遁年起月
    YEAR_TO_START = {
        "甲":2,"己":2,   # 丙寅
        "乙":4,"庚":4,   # 戊寅
        "丙":6,"辛":6,   # 庚寅
        "丁":8,"壬":8,   # 壬寅
        "戊":0,"癸":0,   # 甲寅
    }
    BRANCH_ORDER = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"]

    start   = YEAR_TO_START[year_stem]
    offset  = BRANCH_ORDER.index(month_branch)
    stem_i  = (start + offset) % 10

    return STEMS[stem_i], month_branch


def _calc_day_pillar(true_solar_dt: datetime) -> tuple[str, str]:
    """
    日柱：用 sxtwl.fromSolar 直接获取
    sxtwl 内部基于万年历查表，精度高
    """
    d = sxtwl.fromSolar(
        true_solar_dt.year,
        true_solar_dt.month,
        true_solar_dt.day
    )
    stem   = STEMS[int(d.Lday_Gan)]
    branch = BRANCHES[int(d.Lday_Zhi)]
    return stem, branch


def _calc_hour_pillar(
    true_solar_dt: datetime,
    day_stem: str
) -> tuple[str, str]:
    """
    时柱：五鼠遁日起时
    子时 = 23:00-01:00（跨日）
    """
    h   = true_solar_dt.hour
    m   = true_solar_dt.minute
    tot = h * 60 + m

    # 时支索引
    if tot >= 23 * 60 or tot < 1 * 60:
        branch_i = 0   # 子
    else:
        branch_i = (tot + 60) // 120

    branch = BRANCHES[branch_i]

    # 时干：五鼠遁
    DAY_TO_START = {
        "甲":0,"己":0,   # 甲子
        "乙":2,"庚":2,   # 丙子
        "丙":4,"辛":4,   # 戊子
        "丁":6,"壬":6,   # 庚子
        "戊":8,"癸":8,   # 壬子
    }
    start  = DAY_TO_START[day_stem]
    stem_i = (start + branch_i) % 10

    return STEMS[stem_i], branch


# ============================================================
# 十神计算
# ============================================================

def _ten_god(day_stem: str, target_stem: str) -> str:
    dm_el  = STEM_ELEMENT[day_stem]
    dm_yy  = STEM_YIN_YANG[day_stem]
    tg_el  = STEM_ELEMENT[target_stem]
    tg_yy  = STEM_YIN_YANG[target_stem]
    same   = (dm_yy == tg_yy)

    if dm_el == tg_el:
        return "比肩" if same else "劫财"
    if GENERATES[dm_el] == tg_el:
        return "食神" if same else "伤官"
    if GENERATED_BY[dm_el] == tg_el:
        return "偏印" if same else "正印"
    if CONTROLS[dm_el] == tg_el:
        return "偏财" if same else "正财"
    if CONTROLLED_BY[dm_el] == tg_el:
        return "七杀" if same else "正官"
    return "未知"


def _calc_ten_gods(pillars: dict, day_stem: str) -> dict:
    result = {}
    positions = {
        "year_stem":         pillars["year"]["stem"],
        "month_stem":        pillars["month"]["stem"],
        "hour_stem":         pillars["hour"]["stem"],
        "year_branch_main":  pillars["year"]["hidden_stems"][0][0],
        "month_branch_main": pillars["month"]["hidden_stems"][0][0],
        "day_branch_main":   pillars["day"]["hidden_stems"][0][0],
        "hour_branch_main":  pillars["hour"]["hidden_stems"][0][0],
    }
    for pos, stem in positions.items():
        result[pos] = _ten_god(day_stem, stem)
    return result


# ============================================================
# 五行力量评分
# ============================================================

def _calc_wuxing_score(pillars: dict, day_stem: str) -> dict:
    """
    五行力量评分
    = 位置权重 × 月令旺衰系数（含藏干权重）
    """
    month_branch = pillars["month"]["branch"]
    ms = MONTH_STRENGTH[month_branch]

    raw = {"木":0.0,"火":0.0,"土":0.0,"金":0.0,"水":0.0}
    tg  = {"印星":0.0,"比劫":0.0,"食伤":0.0,"财星":0.0,"官杀":0.0}

    def add(stem: str, base_w: float):
        el  = STEM_ELEMENT[stem]
        val = base_w * ms[el]
        raw[el] += val

        god = _ten_god(day_stem, stem)
        if god in ("正印","偏印"):     tg["印星"]  += val
        elif god in ("比肩","劫财"):   tg["比劫"]  += val
        elif god in ("食神","伤官"):   tg["食伤"]  += val
        elif god in ("正财","偏财"):   tg["财星"]  += val
        elif god in ("正官","七杀"):   tg["官杀"]  += val

    # 天干
    for name, key in [("year","year_stem"),("month","month_stem"),("hour","hour_stem")]:
        add(pillars[name]["stem"], POSITION_WEIGHT[key])

    # 日主天干
    add(day_stem, POSITION_WEIGHT["day_stem"])

    # 地支藏干
    for name, key in [
        ("year","year_branch"),("month","month_branch"),
        ("day","day_branch"),  ("hour","hour_branch"),
    ]:
        for hs, hw in pillars[name]["hidden_stems"]:
            add(hs, POSITION_WEIGHT[key] * HIDDEN_WEIGHT[hw])

    # 转百分比
    total = sum(raw.values()) or 1
    pct   = {k: round(v / total * 100, 1) for k, v in raw.items()}

    tg_total = sum(tg.values()) or 1
    tg_pct   = {k: round(v / tg_total * 100, 1) for k, v in tg.items()}

    return {"raw": raw, "percentage": pct, "ten_gods_percentage": tg_pct}


# ============================================================
# 大运计算
# ============================================================

def _calc_dayun(
    pillars:    dict,
    birth_dt:   datetime,
    gender:     str,
    birth_year: int,
) -> dict:
    """
    大运：顺逆行 + 起运年龄
    阳年男 / 阴年女 → 顺行
    阴年男 / 阳年女 → 逆行
    起运 = 出生到最近节的天数 ÷ 3（天=年）
    """
    year_stem  = pillars["year"]["stem"]
    is_yang    = (STEM_YIN_YANG[year_stem] == "阳")
    is_male    = (gender == "male")
    forward    = (is_yang and is_male) or (not is_yang and not is_male)

    # 起运天数
    start_age = _dayun_start_age(birth_dt, forward)

    # 月柱作为大运起点，顺/逆推
    m_stem   = pillars["month"]["stem"]
    m_branch = pillars["month"]["branch"]
    m_si     = STEMS.index(m_stem)
    m_bi     = BRANCHES.index(m_branch)
    day_stem = pillars["day"]["stem"]

    dayun_list = []
    for i in range(8):
        step = i + 1
        si = (m_si   + step if forward else m_si   - step) % 10
        bi = (m_bi   + step if forward else m_bi   - step) % 12
        s  = STEMS[si]
        b  = BRANCHES[bi]
        age_start = start_age + i * 10

        dayun_list.append({
            "index":      i,
            "stem":       s,
            "branch":     b,
            "element":    STEM_ELEMENT[s],
            "ten_god":    _ten_god(day_stem, s),
            "start_age":  age_start,
            "end_age":    age_start + 9,
            "start_year": birth_year + age_start,
            "end_year":   birth_year + age_start + 9,
        })

    return {
        "forward":   forward,
        "start_age": start_age,
        "list":      dayun_list,
    }


def _dayun_start_age(birth_dt: datetime, forward: bool) -> int:
    """
    计算起大运年龄
    用 sxtwl 精确节气时刻计算出生到最近节的天数
    """
    year     = birth_dt.year
    all_jie  = _get_all_jie(year)

    if forward:
        # 找下一个节
        future = [(n, dt) for n, dt in all_jie if dt > birth_dt]
        if future:
            days = (future[0][1].date() - birth_dt.date()).days
        else:
            days = 90
    else:
        # 找上一个节
        past = [(n, dt) for n, dt in all_jie if dt < birth_dt]
        if past:
            days = (birth_dt.date() - past[-1][1].date()).days
        else:
            days = 90

    return max(1, round(days / 3.0))


# ============================================================
# 算法初判（身强/身弱）
# ============================================================

def _preliminary_analysis(
    wuxing_score: dict,
    pillars:      dict,
    day_stem:     str,
) -> dict:
    """
    基于五行分布初步判断身强/身弱
    返回：strength / confidence / key_factors / question_template
    """
    tg_pct = wuxing_score["ten_gods_percentage"]

    supporting = tg_pct.get("印星",0) + tg_pct.get("比劫",0)
    opposing   = tg_pct.get("官杀",0) + tg_pct.get("财星",0) + tg_pct.get("食伤",0)

    # 月令是否得令
    month_main = pillars["month"]["hidden_stems"][0][0]
    month_god  = _ten_god(day_stem, month_main)
    month_supports = month_god in ("正印","偏印","比肩","劫财")

    factors = []
    factors.append("月令生扶日主（得令）" if month_supports else "月令不生日主（失令）")

    # 从格检测：某一方 > 80% 且日主极弱
    max_tg = max(tg_pct.values()) if tg_pct else 0
    if max_tg > 80 and supporting < 15 and not month_supports:
        factors.append("八字一方极旺，疑似从格")
        return {
            "strength":          "从格",
            "confidence":        "medium",
            "key_factors":       factors,
            "question_template": "C",
            "supporting_ratio":  round(supporting, 1),
            "opposing_ratio":    round(opposing, 1),
        }

    if supporting >= 50:
        strength   = "身强"
        template   = "A"
        confidence = "high" if supporting >= 65 else "medium"
        factors.append(f"印比合计 {supporting:.0f}%，生扶有力")
    elif supporting <= 35:
        strength   = "身弱"
        template   = "B"
        confidence = "high" if opposing >= 65 else "medium"
        factors.append(f"官杀财食伤合计 {opposing:.0f}%，克泄过重")
    else:
        strength   = "中和"
        template   = "B"
        confidence = "low"
        factors.append(f"印比 {supporting:.0f}% 与官杀财食 {opposing:.0f}% 接近")

    # 月令矛盾降低置信度
    if not month_supports and strength == "身强":
        confidence = "medium"
        factors.append("虽印比占优但月令失令，置信度降低")
    if month_supports and strength == "身弱":
        confidence = "medium"
        factors.append("虽克泄过重但月令得助，置信度降低")

    return {
        "strength":          strength,
        "confidence":        confidence,
        "key_factors":       factors,
        "question_template": template,
        "supporting_ratio":  round(supporting, 1),
        "opposing_ratio":    round(opposing, 1),
    }


# ============================================================
# 构建单柱数据
# ============================================================

def _build_pillar(stem: str, branch: str) -> dict:
    return {
        "stem":           stem,
        "branch":         branch,
        "stem_element":   STEM_ELEMENT[stem],
        "branch_element": BRANCH_ELEMENT[branch],
        "hidden_stems":   BRANCH_HIDDEN[branch],
        "nayin":          NAYIN.get((stem, branch), "未知"),
        "yin_yang":       STEM_YIN_YANG[stem],
    }


# ============================================================
# 主入口
# ============================================================

def calculate_bazi(
    solar_year:   int,
    solar_month:  int,
    solar_day:    int,
    solar_hour:   int,
    solar_minute: int,
    city:         str,
    gender:       str,          # "male" | "female"
    unknown_time: bool = False,
) -> dict:
    """
    八字排盘主函数

    流程：
      1. 城市 → 经纬度
      2. 北京时间 → 真太阳时（均时差 + 经度修正）
      3. sxtwl 精确节气 → 年柱、月柱
      4. sxtwl fromSolar → 日柱
      5. 五鼠遁 → 时柱
      6. 十神、五行评分、大运
      7. 算法初判
    """

    # ── 1. 经纬度 ──────────────────────────────────────────
    coords = get_coordinates(city)
    if not coords:
        raise ValueError(f"未找到城市：{city}，请使用最近的地级市名称")

    longitude = coords["longitude"]
    latitude  = coords["latitude"]

    # ── 2. 真太阳时 ────────────────────────────────────────
    if unknown_time:
        solar_hour, solar_minute = 23, 0

    birth_beijing = datetime(
        solar_year, solar_month, solar_day,
        solar_hour, solar_minute
    )
    true_solar_dt, correction = beijing_to_true_solar(birth_beijing, longitude)

    # ── 3. 农历（展示用）──────────────────────────────────
    lunar_day = sxtwl.fromSolar(solar_year, solar_month, solar_day)
    lunar = {
        "year":          int(lunar_day.Lyear),
        "month":         int(lunar_day.Lmonth),
        "day":           int(lunar_day.Lday),
        "is_leap_month": bool(lunar_day.isLrun),
    }

    # ── 4. 四柱 ────────────────────────────────────────────
    year_stem,  year_branch  = _calc_year_pillar(true_solar_dt)
    month_stem, month_branch = _calc_month_pillar(true_solar_dt, year_stem)
    day_stem,   day_branch   = _calc_day_pillar(true_solar_dt)
    hour_stem,  hour_branch  = _calc_hour_pillar(true_solar_dt, day_stem)

    pillars = {
        "year":  _build_pillar(year_stem,  year_branch),
        "month": _build_pillar(month_stem, month_branch),
        "day":   _build_pillar(day_stem,   day_branch),
        "hour":  _build_pillar(hour_stem,  hour_branch),
    }

    # ── 5. 十神 ────────────────────────────────────────────
    ten_gods = _calc_ten_gods(pillars, day_stem)

    # ── 6. 五行评分 ────────────────────────────────────────
    wuxing_score = _calc_wuxing_score(pillars, day_stem)

    # ── 7. 大运 ────────────────────────────────────────────
    dayun = _calc_dayun(pillars, true_solar_dt, gender, solar_year)

    # ── 8. 初判 ────────────────────────────────────────────
    preliminary = _preliminary_analysis(wuxing_score, pillars, day_stem)

    # ── 9. 组装 ────────────────────────────────────────────
    return {
        "birth_info": {
            "solar_date":     f"{solar_year}-{solar_month:02d}-{solar_day:02d}",
            "solar_time":     f"{solar_hour:02d}:{solar_minute:02d}",
            "city":           city,
            "longitude":      longitude,
            "latitude":       latitude,
            "unknown_time":   unknown_time,
            "true_solar": {
                "date":            true_solar_dt.strftime("%Y-%m-%d"),
                "time":            true_solar_dt.strftime("%H:%M"),
                "adjust_minutes":  correction,
            },
            "lunar": lunar,
            "gender": gender,
        },
        "bazi_chart": {
            "pillars":     pillars,
            "day_master": {
                "stem":     day_stem,
                "element":  STEM_ELEMENT[day_stem],
                "yin_yang": STEM_YIN_YANG[day_stem],
            },
            "ten_gods":      ten_gods,
            "wuxing_score":  wuxing_score,
            "dayun":         dayun,
            "preliminary":   preliminary,
            "unknown_time_note": (
                "时辰不详，以子时代入，时柱相关分析仅供参考"
                if unknown_time else None
            ),
        },
    }
```

### 7.4 Session 管理

```python
# backend/store/session_store.py

import time
import os
from copy import deepcopy
from typing import Optional

_TTL    = int(os.getenv("SESSION_TTL_HOURS", 24)) * 3600
_store: dict[str, dict] = {}


def create_session(session_id: str):
    _store[session_id] = {
        "id":         session_id,
        "status":     "init",
        "created_at": time.time(),
        "birth_info": None,
        "bazi_chart": None,
        "questions":  None,
        "answers":    None,
        "analysis":   None,
    }


def get_session(sid: str) -> Optional[dict]:
    s = _store.get(sid)
    if not s:
        return None
    if time.time() - s["created_at"] > _TTL:
        del _store[sid]
        return None
    return deepcopy(s)


def update_session(sid: str, updates: dict):
    if sid in _store:
        _store[sid].update(updates)
```

### 7.5 FastAPI 入口

```python
# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import uuid

load_dotenv()

from routers import bazi, questions, report

app = FastAPI(title="八字命理Agent", version="2.0.0")

origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bazi.router,      prefix="/api/bazi")
app.include_router(questions.router, prefix="/api/questions")
app.include_router(report.router,    prefix="/api/report")


@app.post("/api/session/create")
def create_session():
    from store.session_store import create_session as _create
    sid = str(uuid.uuid4())
    _create(sid)
    return {"session_id": sid, "status": "init"}


@app.get("/api/session/{session_id}/status")
def session_status(session_id: str):
    from store.session_store import get_session
    from fastapi import HTTPException
    s = get_session(session_id)
    if not s:
        raise HTTPException(404, "Session不存在或已过期")
    return {"session_id": session_id, "status": s["status"]}


@app.get("/health")
def health():
    return {"status": "ok"}
```

### 7.6 路由层

```python
# backend/routers/bazi.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.bazi_engine import calculate_bazi
from store.session_store import get_session, update_session

router = APIRouter()


class CalcRequest(BaseModel):
    session_id:   str
    solar_date:   str
    solar_time:   Optional[str] = None
    city:         str
    gender:       str
    unknown_time: bool = False


@router.post("/calculate")
def calculate(req: CalcRequest):
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(404, "Session不存在")

    try:
        y, m, d = [int(x) for x in req.solar_date.split("-")]

        if req.unknown_time or not req.solar_time:
            h, mi, unknown = 23, 0, True
        else:
            h, mi = [int(x) for x in req.solar_time.split(":")]
            unknown = False

        result = calculate_bazi(
            solar_year=y, solar_month=m, solar_day=d,
            solar_hour=h, solar_minute=mi,
            city=req.city, gender=req.gender,
            unknown_time=unknown,
        )

        update_session(req.session_id, {
            "status":     "chart_ready",
            "birth_info": result["birth_info"],
            "bazi_chart": result["bazi_chart"],
        })

        return {"session_id": req.session_id, "status": "chart_ready", **result}

    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"计算失败：{e}")


@router.post("/{session_id}/confirm")
def confirm(session_id: str):
    s = get_session(session_id)
    if not s:
        raise HTTPException(404, "Session不存在")
    if s["status"] != "chart_ready":
        raise HTTPException(400, "请先完成排盘计算")
    update_session(session_id, {"status": "chart_confirmed"})
    return {"session_id": session_id, "status": "chart_confirmed"}
```

```python
# backend/routers/questions.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.question_service import generate_questions
from store.session_store import get_session, update_session

router = APIRouter()

GENERATES     = {"木":"火","火":"土","土":"金","金":"水","水":"木"}
CONTROLS      = {"木":"土","火":"金","土":"水","金":"木","水":"火"}
GENERATED_BY  = {v:k for k,v in GENERATES.items()}
CONTROLLED_BY = {v:k for k,v in CONTROLS.items()}


class GenerateReq(BaseModel):
    session_id: str


class AnswerReq(BaseModel):
    session_id: str
    answers:    list[dict]


@router.post("/generate")
def generate(req: GenerateReq):
    s = get_session(req.session_id)
    if not s:
        raise HTTPException(404, "Session不存在")
    if s["status"] != "chart_confirmed":
        raise HTTPException(400, "请先确认排盘")

    try:
        qs = generate_questions(s["bazi_chart"])
        update_session(req.session_id, {
            "status":    "questions_ready",
            "questions": qs,
        })
        return {"session_id": req.session_id, "questions": qs}
    except Exception as e:
        raise HTTPException(500, f"问题生成失败：{e}")


@router.post("/{session_id}/answer")
def answer(session_id: str, req: AnswerReq):
    s = get_session(session_id)
    if not s:
        raise HTTPException(404, "Session不存在")

    qs = s.get("questions", [])

    enriched = []
    for ans in req.answers:
        q = next((q for q in qs if q["id"] == ans["question_id"]), None)
        if q:
            opt = next((o for o in q["options"]
                        if o["key"] == ans["selected_key"]), None)
            enriched.append({
                "question_id":   ans["question_id"],
                "selected_key":  ans["selected_key"],
                "signal":        opt["signal"] if opt else "",
                "strength_hint": opt.get("strength_hint") if opt else None,
            })

    analysis = _final_analysis(s["bazi_chart"], enriched)

    update_session(session_id, {
        "status":   "questions_answered",
        "answers":  enriched,
        "analysis": analysis,
    })

    return {"session_id": session_id, "status": "questions_answered", "analysis": analysis}


def _final_analysis(bazi_chart: dict, answers: list) -> dict:
    prelim     = bazi_chart["preliminary"]
    algo_str   = prelim["strength"]

    scores = {"身强":0.0,"身弱":0.0,"中和":0.0,"从格":0.0}
    scores[algo_str] += 50.0

    per_q = 50.0 / max(len(answers), 1)
    for ans in answers:
        h = ans.get("strength_hint")
        if h and h in scores:
            scores[h] += per_q

    final = max(scores, key=scores.get)

    # 用神忌神
    dm_el = bazi_chart["day_master"]["element"]

    if final == "身强":
        yong = [GENERATES[dm_el], CONTROLLED_BY[dm_el], CONTROLS[dm_el]]
        ji   = [dm_el, GENERATED_BY[dm_el]]
    elif final == "身弱":
        yong = [dm_el, GENERATED_BY[dm_el]]
        ji   = [GENERATES[dm_el], CONTROLLED_BY[dm_el], CONTROLS[dm_el]]
    elif final == "从格":
        tg_pct    = bazi_chart["wuxing_score"]["ten_gods_percentage"]
        strongest = max(tg_pct, key=tg_pct.get)
        EL_MAP = {"印星":GENERATED_BY[dm_el],"比劫":dm_el,
                  "食伤":GENERATES[dm_el],"财星":CONTROLS[dm_el],"官杀":CONTROLLED_BY[dm_el]}
        yong = [EL_MAP.get(strongest, dm_el)]
        ji   = []
    else:
        yong = [dm_el, GENERATED_BY[dm_el]]
        ji   = []

    # 去重去空
    yong = list(dict.fromkeys([x for x in yong if x]))
    ji   = list(dict.fromkeys([x for x in ji   if x]))

    return {
        "final_judgment": final,
        "confidence":     round(scores[final]),
        "yong_shen":      yong,
        "ji_shen":        ji,
        "scores":         scores,
    }
```

```python
# backend/routers/report.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from store.session_store import get_session, update_session
from services.report_service import stream_report
import json

router = APIRouter()


@router.get("/{session_id}/stream")
async def report_stream(session_id: str):
    s = get_session(session_id)
    if not s:
        raise HTTPException(404, "Session不存在")
    if s["status"] not in ("questions_answered","report_generating","report_ready"):
        raise HTTPException(400, "请先完成问答")

    update_session(session_id, {"status": "report_generating"})

    async def gen():
        try:
            async for evt in stream_report(s):
                yield f"event: {evt['type']}\ndata: {json.dumps(evt['data'], ensure_ascii=False)}\n\n"
            update_session(session_id, {"status": "report_ready"})
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"},
    )
```

### 7.7 AI 客户端

```python
# backend/services/ai_client.py

import os
from typing import Generator

PROVIDER = os.getenv("AI_PROVIDER", "gemini")
MODEL    = os.getenv("AI_MODEL",    "gemini-1.5-flash")


def complete(system: str, user: str,
             as_json: bool = False,
             temperature: float = 0.7) -> str:
    if PROVIDER == "gemini":
        return _gemini(system, user, as_json, temperature)
    return _openai(system, user, as_json, temperature)


def stream(system: str, user: str,
           temperature: float = 0.75) -> Generator[str, None, None]:
    if PROVIDER == "gemini":
        yield from _gemini_stream(system, user, temperature)
    else:
        yield from _openai_stream(system, user, temperature)


# ── Gemini ───────────────────────────────────────────────────

def _gemini(system, user, as_json, temperature):
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    cfg = {"temperature": temperature, "max_output_tokens": 4096}
    if as_json:
        cfg["response_mime_type"] = "application/json"

    model = genai.GenerativeModel(
        MODEL, generation_config=cfg, system_instruction=system
    )
    return model.generate_content(user).text


def _gemini_stream(system, user, temperature):
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    model = genai.GenerativeModel(
        MODEL,
        generation_config={"temperature": temperature, "max_output_tokens": 8192},
        system_instruction=system,
    )
    for chunk in model.generate_content(user, stream=True):
        if chunk.text:
            yield chunk.text


# ── OpenAI ───────────────────────────────────────────────────

def _openai(system, user, as_json, temperature):
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    kwargs = dict(
        model=MODEL, temperature=temperature, max_tokens=4096,
        messages=[{"role":"system","content":system},
                  {"role":"user","content":user}],
    )
    if as_json:
        kwargs["response_format"] = {"type": "json_object"}
    return client.chat.completions.create(**kwargs).choices[0].message.content


def _openai_stream(system, user, temperature):
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    for chunk in client.chat.completions.create(
        model=MODEL, temperature=temperature,
        max_tokens=8192, stream=True,
        messages=[{"role":"system","content":system},
                  {"role":"user","content":user}],
    ):
        c = chunk.choices[0].delta
        if c and c.content:
            yield c.content
```

### 7.8 问题生成服务

```python
# backend/services/question_service.py

import json
import re
from services.ai_client import complete
from prompts.question_prompt import build_prompt


def generate_questions(bazi_chart: dict) -> list[dict]:
    system_p, user_p = build_prompt(bazi_chart)
    raw = complete(system_p, user_p, as_json=True, temperature=0.6)

    try:
        data = json.loads(raw)
        return data.get("questions", [])
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            return json.loads(m.group()).get("questions", [])
        raise ValueError("问题生成格式错误")
```

```python
# backend/prompts/question_prompt.py

def build_prompt(bazi_chart: dict) -> tuple[str, str]:
    prelim   = bazi_chart["preliminary"]
    dm       = bazi_chart["day_master"]
    wux_pct  = bazi_chart["wuxing_score"]["percentage"]
    tg_pct   = bazi_chart["wuxing_score"]["ten_gods_percentage"]
    month_b  = bazi_chart["pillars"]["month"]["branch"]

    SYSTEM = """你是一位精通子平命理的命理师。
你的任务是根据命主八字信息，生成3道生活化选择题，
用于验证命主身强/身弱的初步算法判断。

规则：
1. 严格输出JSON，不输出其他内容
2. 每题4个选项(A/B/C/D)
3. 语言口语化，禁止命理专业术语
4. 每个选项含 signal（命理信号）和 strength_hint（身强/身弱/中和/从格）
5. 4个选项的 strength_hint 尽量覆盖不同方向，增加区分度"""

    USER = f"""八字信息：
日主：{dm['stem']}（{dm['element']}，{dm['yin_yang']}）
月令：{month_b}
算法初判：{prelim['strength']}（置信度：{prelim['confidence']}）
判断依据：{'；'.join(prelim['key_factors'])}
问题模板：{prelim['question_template']}

五行分布：木{wux_pct.get('木',0)}% 火{wux_pct.get('火',0)}% \
土{wux_pct.get('土',0)}% 金{wux_pct.get('金',0)}% 水{wux_pct.get('水',0)}%

十神分布：印星{tg_pct.get('印星',0)}% 比劫{tg_pct.get('比劫',0)}% \
食伤{tg_pct.get('食伤',0)}% 财星{tg_pct.get('财星',0)}% 官杀{tg_pct.get('官杀',0)}%

三个问题维度：
Q1 性格特质（验证日主旺衰的自我表现）
Q2 过往经历（2022-2024年实际经历验证用神方向）
Q3 行为模式（面对机会或压力时的应对方式）

输出格式：
{{
  "questions": [
    {{
      "id": 1,
      "dimension": "性格特质",
      "question": "问题（≤30字）",
      "options": [
        {{"key":"A","text":"选项（≤25字）","signal":"身强信号","strength_hint":"身强"}},
        {{"key":"B","text":"选项","signal":"身弱信号","strength_hint":"身弱"}},
        {{"key":"C","text":"选项","signal":"食伤旺","strength_hint":"中和"}},
        {{"key":"D","text":"选项","signal":"从格信号","strength_hint":"从格"}}
      ]
    }},
    {{ Q2 }},
    {{ Q3 }}
  ]
}}"""

    return SYSTEM, USER
```

### 7.9 报告生成服务

```python
# backend/services/report_service.py

import asyncio
from typing import AsyncGenerator
from services.ai_client import stream
from prompts.report_prompt import build_section_prompt
from data.jewelry_mapping import JEWELRY_MAP, DIRECTION_MAP, COLOR_MAP
from datetime import datetime

SECTIONS = [
    {"id":"overall", "title":"整体格局与人生主题"},
    {"id":"career",  "title":"事业与财运"},
    {"id":"love",    "title":"感情与婚姻"},
    {"id":"health",  "title":"健康与体质"},
    {"id":"family",  "title":"家庭与六亲"},
    {"id":"wealth",  "title":"财富格局"},
]


async def stream_report(session: dict) -> AsyncGenerator[dict, None]:
    bazi_chart = session["bazi_chart"]
    analysis   = session["analysis"]
    answers    = session.get("answers", [])
    birth_info = session["birth_info"]

    yield {"type":"report_start", "data":{"total_sections": len(SECTIONS)}}

    for sec in SECTIONS:
        sid, title = sec["id"], sec["title"]
        yield {"type":"section_start", "data":{"section_id":sid,"title":title}}

        sys_p, usr_p = build_section_prompt(
            bazi_chart, analysis, answers, birth_info, sid, title
        )

        content = ""
        for chunk in stream(sys_p, usr_p, temperature=0.75):
            content += chunk
            yield {"type":"section_chunk", "data":{"section_id":sid,"chunk":chunk}}
            await asyncio.sleep(0)

        highlight = content.replace('\n','')[:60] + "..."
        yield {"type":"section_end","data":{"section_id":sid,"highlight":highlight}}

    yield {"type":"recommendations","data":_build_recs(analysis)}
    yield {"type":"report_complete","data":{"generated_at":datetime.utcnow().isoformat()}}


def _build_recs(analysis: dict) -> dict:
    yong = analysis.get("yong_shen", [])
    ji   = analysis.get("ji_shen",   [])

    jewelry = [
        {"element":el, **JEWELRY_MAP[el]}
        for el in yong if el in JEWELRY_MAP
    ]

    return {
        "yong_shen": yong,
        "ji_shen":   ji,
        "jewelry":   jewelry,
        "directions": {
            "favorable":   [DIRECTION_MAP[e] for e in yong if e in DIRECTION_MAP],
            "unfavorable": [DIRECTION_MAP[e] for e in ji   if e in DIRECTION_MAP],
        },
        "colors": {
            "favorable":   [c for e in yong if e in COLOR_MAP
                              for c in COLOR_MAP[e]["favorable"]],
            "unfavorable": [c for e in ji   if e in COLOR_MAP
                              for c in COLOR_MAP[e]["unfavorable"]],
        },
    }
```

```python
# backend/prompts/report_prompt.py

def build_section_prompt(
    bazi_chart, analysis, answers, birth_info,
    section_id, section_title
) -> tuple[str, str]:

    pillars  = bazi_chart["pillars"]
    dm       = bazi_chart["day_master"]
    wux_pct  = bazi_chart["wuxing_score"]["percentage"]
    dayun    = bazi_chart["dayun"]["list"]
    gender   = birth_info.get("gender","female")
    gender_cn= "男命" if gender=="male" else "女命"

    bazi_str = (
        f"{pillars['year']['stem']}{pillars['year']['branch']}年 "
        f"{pillars['month']['stem']}{pillars['month']['branch']}月 "
        f"{pillars['day']['stem']}{pillars['day']['branch']}日 "
        f"{pillars['hour']['stem']}{pillars['hour']['branch']}时"
    )

    cur_yun   = dayun[2] if len(dayun) > 2 else dayun[0]
    words_map = {
        "overall":"300-400字","career":"250-350字","love":"250-350字",
        "health":"200-300字", "family":"200-300字","wealth":"200-300字",
    }

    ans_lines = []
    dim_map   = {1:"性格特质",2:"过往经历",3:"行为模式"}
    for a in answers:
        ans_lines.append(
            f"Q{a['question_id']}({dim_map.get(a['question_id'],'')})"
            f"：选{a['selected_key']} → {a.get('signal','')}"
        )

    SYSTEM = f"""你是精通子平命理的命理师，有30年断命经验。
现在撰写【{section_title}】章节。

要求：
1. 语言专业易懂，有温度，结论明确
2. 所有判断回扣具体天干地支
3. 不做绝对化负面判断
4. 不预测具体年龄灾难或死亡
5. 字数：{words_map.get(section_id,'200-300字')}
6. 直接输出正文，不需要标题"""

    USER = f"""命主信息：
八字：{bazi_str}
日主：{dm['stem']}（{dm['element']} {dm['yin_yang']}）{gender_cn}
身强/身弱：{analysis['final_judgment']}
用神：{'、'.join(analysis['yong_shen'])}
忌神：{'、'.join(analysis['ji_shen'])}

五行：木{wux_pct.get('木',0)}% 火{wux_pct.get('火',0)}% \
土{wux_pct.get('土',0)}% 金{wux_pct.get('金',0)}% 水{wux_pct.get('水',0)}%

当前大运：{cur_yun['stem']}{cur_yun['branch']}（{cur_yun['ten_god']}）\
{cur_yun['start_age']}-{cur_yun['end_age']}岁

命主自述：
{chr(10).join(ans_lines) if ans_lines else '无'}

请撰写【{section_title}】。"""

    return SYSTEM, USER
```

---

## 八、前端核心实现

### 8.1 类型定义

```typescript
// frontend/lib/types.ts

export interface BirthInfo {
  solar_date:    string
  solar_time:    string
  city:          string
  longitude:     number
  latitude:      number
  unknown_time:  boolean
  gender:        string
  true_solar: {
    date:           string
    time:           string
    adjust_minutes: number
  }
  lunar: {
    year:          number
    month:         number
    day:           number
    is_leap_month: boolean
  }
}

export interface Pillar {
  stem:           string
  branch:         string
  stem_element:   string
  branch_element: string
  hidden_stems:   [string, number][]
  nayin:          string
  yin_yang:       string
}

export interface BaziChart {
  pillars: { year: Pillar; month: Pillar; day: Pillar; hour: Pillar }
  day_master: { stem: string; element: string; yin_yang: string }
  ten_gods:   Record<string, string>
  wuxing_score: {
    percentage:          Record<string, number>
    ten_gods_percentage: Record<string, number>
  }
  dayun: {
    forward:   boolean
    start_age: number
    list: Array<{
      index: number; stem: string; branch: string
      element: string; ten_god: string
      start_age: number; end_age: number
      start_year: number; end_year: number
    }>
  }
  preliminary: {
    strength:          string
    confidence:        string
    key_factors:       string[]
    question_template: string
  }
  unknown_time_note: string | null
}

export interface Question {
  id:        number
  dimension: string
  question:  string
  options: Array<{
    key:           string
    text:          string
    signal:        string
    strength_hint: string
  }>
}

export interface Analysis {
  final_judgment: string
  confidence:     number
  yong_shen:      string[]
  ji_shen:        string[]
}

export type SessionStep =
  | "loading_chart"
  | "show_chart"
  | "loading_questions"
  | "answering"
  | "generating_report"
  | "done"
  | "error"
```

### 8.2 API 封装

```typescript
// frontend/lib/api.ts

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: "请求失败" }))
    throw new Error(err.message ?? "请求失败")
  }
  return res.json()
}

export const api = {
  createSession: () =>
    post<{ session_id: string }>("/api/session/create"),

  calculateBazi: (p: {
    session_id: string; solar_date: string
    solar_time: string | null; city: string
    gender: string; unknown_time: boolean
  }) => post<{ session_id: string; bazi_chart: unknown; birth_info: unknown }>(
    "/api/bazi/calculate", p
  ),

  confirmChart: (sessionId: string) =>
    post(`/api/bazi/${sessionId}/confirm`),

  generateQuestions: (sessionId: string) =>
    post<{ questions: unknown[] }>("/api/questions/generate", { session_id: sessionId }),

  submitAnswers: (sessionId: string, answers: Array<{ question_id: number; selected_key: string }>) =>
    post<{ analysis: unknown }>(`/api/questions/${sessionId}/answer`, {
      session_id: sessionId, answers,
    }),
}
```

### 8.3 SSE Hook

```typescript
// frontend/hooks/useSSE.ts

import { useEffect, useRef, useState, useCallback } from "react"

export type SSEEvent = { type: string; data: Record<string, unknown> }

export function useSSE(sessionId: string | null, enabled: boolean) {
  const [events, setEvents] = useState<SSEEvent[]>([])
  const [done,   setDone]   = useState(false)
  const [error,  setError]  = useState<string | null>(null)
  const srcRef              = useRef<EventSource | null>(null)

  const reset = useCallback(() => {
    setEvents([]); setDone(false); setError(null)
  }, [])

  useEffect(() => {
    if (!enabled || !sessionId) return
    reset()

    const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
    const src  = new EventSource(`${BASE}/api/report/${sessionId}/stream`)
    srcRef.current = src

    const on = (type: string) => (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data)
        setEvents(prev => [...prev, { type, data }])
        if (type === "report_complete") { setDone(true); src.close() }
        if (type === "error")           { setError(data.message); src.close() }
      } catch {}
    }

    ;["report_start","section_start","section_chunk",
      "section_end","recommendations","report_complete","error"
    ].forEach(t => src.addEventListener(t, on(t) as EventListener))

    src.onerror = () => { setError("连接中断，请刷新重试"); src.close() }
    return () => src.close()
  }, [sessionId, enabled, reset])

  return { events, done, error }
}
```

### 8.4 首页

```typescript
// frontend/app/page.tsx
"use client"

import { useState }      from "react"
import { useRouter }     from "next/navigation"
import { api }           from "@/lib/api"

const PROVINCE_CITIES: Record<string, string[]> = {
  "北京":["北京"],"上海":["上海"],"天津":["天津"],"重庆":["重庆"],
  "广东":["广州","深圳","珠海","东莞","佛山","汕头"],
  "浙江":["杭州","宁波","温州","绍兴","嘉兴"],
  "江苏":["南京","苏州","无锡","南通","常州"],
  "四川":["成都","绵阳","德阳","泸州","宜宾"],
  "湖北":["武汉","宜昌","襄阳","荆州"],
  "湖南":["长沙","株洲","衡阳","岳阳"],
  "山东":["济南","青岛","烟台","淄博","威海"],
  "河南":["郑州","洛阳","开封","南阳"],
  "陕西":["西安","咸阳","宝鸡","延安"],
  "辽宁":["沈阳","大连","鞍山","抚顺"],
  "黑龙江":["哈尔滨","齐齐哈尔","大庆","佳木斯"],
  "吉林":["长春","吉林市","延吉"],
  "福建":["福州","厦门","泉州","漳州"],
  "云南":["昆明","大理","丽江","昭通"],
  "贵州":["贵阳","遵义","凯里"],
  "甘肃":["兰州","天水","张掖","酒泉"],
  "新疆":["乌鲁木齐","喀什","伊宁","库尔勒"],
  "西藏":["拉萨","日喀则","林芝"],
  "广西":["南宁","桂林","柳州","梧州"],
  "内蒙古":["呼和浩特","包头","赤峰","鄂尔多斯"],
  "海南":["海口","三亚","儋州"],
  "河北":["石家庄","保定","唐山","邯郸"],
  "山西":["太原","大同","临汾","运城"],
  "安徽":["合肥","芜湖","安庆","蚌埠"],
  "江西":["南昌","赣州","九江","景德镇"],
  "青海":["西宁","格尔木"],
  "宁夏":["银川","石嘴山"],
}

export default function Home() {
  const router  = useRouter()
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState("")

  const [form, setForm] = useState({
    year: "1990", month: "5", day: "15",
    hour: "14",   minute: "30",
    unknown_time: false,
    province: "上海", city: "上海",
    gender: "female",
  })

  const set = (k: string, v: unknown) => setForm(p => ({...p, [k]: v}))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true); setError("")
    try {
      const { session_id } = await api.createSession()

      const result = await api.calculateBazi({
        session_id,
        solar_date:   `${form.year}-${form.month.padStart(2,"0")}-${form.day.padStart(2,"0")}`,
        solar_time:   form.unknown_time ? null : `${form.hour.padStart(2,"0")}:${form.minute.padStart(2,"0")}`,
        city:         form.city,
        gender:       form.gender,
        unknown_time: form.unknown_time,
      })

      sessionStorage.setItem(`bazi_${session_id}`, JSON.stringify(result))
      router.push(`/reading/${session_id}`)
    } catch(e: unknown) {
      setError(e instanceof Error ? e.message : "提交失败")
    } finally {
      setLoading(false)
    }
  }

  const cities = PROVINCE_CITIES[form.province] ?? [form.province]

  return (
    <main className="min-h-screen bg-stone-950 text-stone-100 flex items-center justify-center px-4">
      <div className="w-full max-w-md">

        <div className="text-center mb-10">
          <div className="text-5xl mb-3">🔮</div>
          <h1 className="text-2xl font-bold text-amber-400">八字命理</h1>
          <p className="text-stone-400 text-sm mt-2">
            基于寿星万年历精确排盘 · 子平命理体系
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">

          {/* 出生日期 */}
          <div>
            <label className="text-sm text-stone-400 block mb-2">出生日期（阳历）</label>
            <div className="flex gap-2">
              {[
                { key:"year",  placeholder:"年", min:1920, max:2005, w:"w-24" },
                { key:"month", placeholder:"月", min:1,    max:12,   w:"w-16" },
                { key:"day",   placeholder:"日", min:1,    max:31,   w:"w-16" },
              ].map(f => (
                <input key={f.key} type="number"
                  placeholder={f.placeholder} min={f.min} max={f.max}
                  value={(form as Record<string,string>)[f.key]}
                  onChange={e => set(f.key, e.target.value)}
                  className={`${f.w} px-3 py-2 bg-stone-800 rounded-lg border border-stone-700 text-center focus:border-amber-400 outline-none`}
                />
              ))}
            </div>
          </div>

          {/* 出生时间 */}
          <div>
            <label className="text-sm text-stone-400 block mb-2">出生时间</label>
            {!form.unknown_time ? (
              <div className="flex items-center gap-2">
                <input type="number" placeholder="时" min={0} max={23}
                  value={form.hour}
                  onChange={e => set("hour", e.target.value)}
                  className="w-16 px-3 py-2 bg-stone-800 rounded-lg border border-stone-700 text-center focus:border-amber-400 outline-none"
                />
                <span className="text-stone-500">:</span>
                <input type="number" placeholder="分" min={0} max={59}
                  value={form.minute}
                  onChange={e => set("minute", e.target.value)}
                  className="w-16 px-3 py-2 bg-stone-800 rounded-lg border border-stone-700 text-center focus:border-amber-400 outline-none"
                />
                <button type="button" onClick={() => set("unknown_time", true)}
                  className="text-xs text-stone-500 hover:text-stone-300 ml-1">
                  时间不详？
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <span className="text-stone-400 text-sm">以子时代入，报告中会注明</span>
                <button type="button" onClick={() => set("unknown_time", false)}
                  className="text-xs text-amber-400 hover:text-amber-300">
                  我知道时间
                </button>
              </div>
            )}
          </div>

          {/* 出生地点 */}
          <div>
            <label className="text-sm text-stone-400 block mb-2">出生地点</label>
            <div className="flex gap-2">
              <select value={form.province}
                onChange={e => {
                  const p = e.target.value
                  set("province", p)
                  set("city", (PROVINCE_CITIES[p] ?? [p])[0])
                }}
                className="flex-1 px-3 py-2 bg-stone-800 rounded-lg border border-stone-700 focus:border-amber-400 outline-none">
                {Object.keys(PROVINCE_CITIES).map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
              <select value={form.city} onChange={e => set("city", e.target.value)}
                className="flex-1 px-3 py-2 bg-stone-800 rounded-lg border border-stone-700 focus:border-amber-400 outline-none">
                {cities.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>

          {/* 性别 */}
          <div>
            <label className="text-sm text-stone-400 block mb-2">性别</label>
            <div className="flex gap-3">
              {(["male","female"] as const).map(g => (
                <button key={g} type="button"
                  onClick={() => set("gender", g)}
                  className={`flex-1 py-2 rounded-lg border transition-colors ${
                    form.gender === g
                      ? "border-amber-400 bg-amber-400/10 text-amber-400"
                      : "border-stone-700 text-stone-400 hover:border-stone-500"
                  }`}>
                  {g === "male" ? "♂ 男" : "♀ 女"}
                </button>
              ))}
            </div>
          </div>

          {error && <p className="text-red-400 text-sm text-center">{error}</p>}

          <button type="submit" disabled={loading}
            className="w-full py-3 bg-amber-500 hover:bg-amber-400 disabled:bg-stone-700 text-stone-950 font-bold rounded-lg transition-colors">
            {loading ? "排盘中..." : "开始排盘 →"}
          </button>
        </form>

        <p className="text-center text-stone-600 text-xs mt-8">
          本工具基于传统子平命理推演，仅供参考，不构成任何决策建议
        </p>
      </div>
    </main>
  )
}
```

### 8.5 主流程页

```typescript
// frontend/app/reading/[sessionId]/page.tsx
"use client"

import { useEffect, useState }   from "react"
import { useParams, useRouter }  from "next/navigation"
import { api }                   from "@/lib/api"
import { SessionStep }           from "@/lib/types"
import BaziChart                 from "@/components/BaziChart"
import QuestionFlow              from "@/components/QuestionFlow"
import ReportStream              from "@/components/ReportStream"
import LoadingState              from "@/components/LoadingState"

export default function ReadingPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const router        = useRouter()

  const [step,      setStep]      = useState<SessionStep>("loading_chart")
  const [chartData, setChartData] = useState<Record<string, unknown> | null>(null)
  const [questions, setQuestions] = useState<unknown[]>([])
  const [errMsg,    setErrMsg]    = useState("")

  useEffect(() => {
    const stored = sessionStorage.getItem(`bazi_${sessionId}`)
    if (stored) {
      setChartData(JSON.parse(stored))
      setStep("show_chart")
    } else {
      setErrMsg("数据丢失，请返回重新填写")
      setStep("error")
    }
  }, [sessionId])

  const handleConfirm = async () => {
    setStep("loading_questions")
    try {
      await api.confirmChart(sessionId)
      const { questions: qs } = await api.generateQuestions(sessionId)
      setQuestions(qs)
      setStep("answering")
    } catch(e: unknown) {
      setErrMsg(e instanceof Error ? e.message : "操作失败")
      setStep("error")
    }
  }

  const handleAnswers = async (answers: Array<{ question_id: number; selected_key: string }>) => {
    try {
      await api.submitAnswers(sessionId, answers)
      setStep("generating_report")
    } catch(e: unknown) {
      setErrMsg(e instanceof Error ? e.message : "提交失败")
      setStep("error")
    }
  }

  return (
    <main className="min-h-screen bg-stone-950 text-stone-100">
      <div className="max-w-2xl mx-auto px-4 py-8">

        {step === "loading_chart" && <LoadingState message="正在排盘..." />}

        {step === "show_chart" && chartData && (
          <BaziChart
            data={chartData}
            onConfirm={handleConfirm}
            onBack={() => router.push("/")}
          />
        )}

        {step === "loading_questions" && (
          <LoadingState message="AI 正在根据你的八字生成专属问题..." />
        )}

        {step === "answering" && (
          <QuestionFlow questions={questions} onComplete={handleAnswers} />
        )}

        {(step === "generating_report" || step === "done") && (
          <ReportStream
            sessionId={sessionId}
            onComplete={() => setStep("done")}
          />
        )}

        {step === "error" && (
          <div className="text-center py-20">
            <p className="text-red-400 mb-4">{errMsg}</p>
            <button onClick={() => router.push("/")}
              className="px-6 py-2 bg-stone-700 rounded-lg hover:bg-stone-600">
              返回首页
            </button>
          </div>
        )}

      </div>
    </main>
  )
}
```

---

## 九、启动与验证

```bash
# ── 数据准备（只需一次）────────────────────────────────────
cd backend
python scripts/prepare_cities.py
python scripts/verify_sxtwl.py

# ── 后端 ───────────────────────────────────────────────────
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# ── 前端 ───────────────────────────────────────────────────
cd frontend
npm install
npm run dev

# ── 验证节点 ────────────────────────────────────────────────
# 1. http://localhost:3000            首页正常显示
# 2. POST /api/session/create        返回 session_id
# 3. POST /api/bazi/calculate        1990-05-15 14:30 上海 女
#    期望：庚午年 辛巳月 癸亥日 甲申时
# 4. 完整走通7步主流程
```

---

## 十、验收核对表

```
计算层（sxtwl）：
□ verify_sxtwl.py 运行无报错
□ 1990年立春时刻输出合理（约2月4日）
□ 1990-05-15 → 庚午年 辛巳月 癸亥日 甲申时
□ 2000-02-03（立春前）→ 年柱己卯
□ 真太阳时：上海修正约 -8 至 -12 分钟
□ 乌鲁木齐修正 < -100 分钟

城市数据：
□ cities.json 存在且条目 > 200
□ 上海 / 北京 / 乌鲁木齐 均可查到经纬度
□ 输入"上海市"也能匹配成功

流程：
□ 完整走通7步主流程无报错
□ 时辰不详：子时代入，报告有注明
□ 问答3题依次展示，选完自动下一题
□ 报告6章节全部有内容
□ 流式输出，首段5秒内开始
□ 饰品推荐与喜用五行对应正确
□ 移动端 375px 正常显示
□ 底部免责声明显示