from __future__ import annotations

import json
from typing import Any


MODULE_TITLES = {
    "talent": "人生天赋",
    "career": "职业方向",
    "city": "适合发展的城市",
    "life_lesson": "人生课题",
}

REPORT_PROMPT_TEMPLATE = """你是一个温柔、坚定、具体的人生/职业策略顾问。
你只能基于下面的 analysis JSON 生成报告，不允许脱离 analysis JSON 自由发挥。

analysis JSON:
__ANALYSIS_JSON__

强制规则：
1. 每一个判断都必须包含：依据、现实表现、具体建议。
2. 禁止只输出抽象词，例如“管理型能力”“专业标签”“长期主义”“方法论”“能量”“潜力”“成长”。如果必须使用，必须解释它在现实中对应什么能力、岗位、场景或行动。
3. 职业建议必须具体到岗位类型，例如 AI产品运营、AI产品助理、知识库运营、项目助理、B端客户成功、海外产品运营、内容运营、业务流程优化、SOP搭建、用户研究助理等。
4. 必须输出不适合方向，并说明如果不得不做如何降低损耗。
5. 必须输出赚钱策略：短期靠什么技能换工资；中期靠什么案例提高议价；长期靠什么专业标签形成复利。
6. 必须输出未来 3 个月行动计划，每个月至少 3 条具体动作。
7. 必须结合问答校验结果，不能只根据八字或星盘下结论。
8. 语气温柔、坚定、具体，不要玄学鸡汤。

输出结构必须是 JSON：
{
  "core_profile": {"title": "", "one_sentence": "", "basis": "", "real_world": "", "advice": ""},
  "basis": {"bazi": [], "astrology": [], "qa": []},
  "real_world_patterns": [],
  "career_directions": [{"job": "", "why": "", "entry": "", "skill_gap": ""}],
  "unsuitable_directions": [{"type": "", "reason": "", "damage_control": ""}],
  "money_path": [{"stage": "", "focus": "", "actions": []}],
  "three_month_plan": [{"month": "", "actions": []}],
  "life_lesson": {
    "core_issue": "",
    "real_world_patterns": [],
    "hidden_cost": "",
    "breakthrough_method": "",
    "practice_plan": [{"action": "", "how_to_do_it": "", "frequency": ""}],
    "decision_questions": []
  },
  "key_reminders": []
}
"""

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

CAREER_POOLS = {
    "yin_star": [
        ("知识库运营", "把零散信息整理成可检索、可复用的资料体系。", "先做一个个人知识库样例：行业资料、FAQ、SOP、标签体系各 1 份。", "补 Notion/飞书文档、信息架构、基础数据标注能力。"),
        ("AI产品助理", "适合把用户需求、资料、流程翻译成产品需求文档。", "从 AI 工具测评、竞品拆解、PRD 模板练习切入。", "补需求拆解、原型表达和简单数据看板能力。"),
        ("用户研究助理", "适合做访谈整理、问题归因、用户画像和洞察沉淀。", "先做 5 个真实访谈样本，输出问题清单和用户分层。", "补访谈提纲、样本记录和结论可视化能力。"),
    ],
    "shi_shang": [
        ("内容运营", "适合把复杂信息转成用户愿意看的内容。", "先做一个垂直账号或专题栏目，连续输出 12 篇。", "补选题策划、标题测试、数据复盘能力。"),
        ("AI内容工作流运营", "适合用 AI 提高内容生产、审核、改写和分发效率。", "搭建一套从选题到发布的 AI SOP，并做前后效率对比。", "补提示词、内容质检表和自动化工具能力。"),
        ("社群运营", "适合把用户问题转成活动、话题和反馈机制。", "从小社群做签到、答疑、主题活动和用户分层。", "补活动节奏、用户分层和转化记录能力。"),
    ],
    "guan_sha": [
        ("项目助理", "适合跟进进度、拆任务、盯风险，让事情按节点落地。", "先熟悉项目周报、会议纪要、风险清单和排期表。", "补项目管理工具、跨部门沟通和优先级判断能力。"),
        ("业务流程优化", "适合把混乱流程整理成清晰步骤和责任边界。", "挑一个真实流程画泳道图，标出卡点和优化建议。", "补流程图、SOP、指标定义能力。"),
        ("SOP搭建", "适合把重复工作标准化，减少团队沟通成本。", "先做 3 份可直接执行的 SOP：客服、内容、交付各 1 份。", "补模板设计、验收标准和培训表达能力。"),
    ],
    "cai_star": [
        ("B端客户成功", "适合连接客户需求、交付资源和续费价值。", "从客户问题记录、使用培训、续费风险表切入。", "补行业知识、沟通记录和客户分层能力。"),
        ("产品运营", "适合围绕用户增长、转化、留存做具体动作。", "先做一个产品转化漏斗分析和 3 个优化实验方案。", "补数据分析、活动设计和用户反馈闭环能力。"),
        ("商业化运营", "适合把资源、产品和收入目标连接起来。", "从套餐梳理、竞品价格、成交案例复盘切入。", "补基础财务意识、报价逻辑和案例包装能力。"),
    ],
    "bijie": [
        ("社区运营", "适合维护关系、组织协作、促成用户之间的连接。", "先做用户分层、核心用户访谈和活动日历。", "补社区规则、志愿者机制和数据记录能力。"),
        ("B端客户成功", "适合在客户与内部团队之间做稳定沟通桥梁。", "先从客户问题台账、交付状态表、复盘邮件切入。", "补结构化表达、冲突处理和续费判断能力。"),
        ("项目协调", "适合把多人协作中的信息同步和资源调度做好。", "先练习会议纪要、责任人清单、下一步动作追踪。", "补排期、风险预警和向上汇报能力。"),
    ],
}


def generate_navigation_report(
    modules: list[str],
    bazi_chart: dict[str, Any],
    birth_info: dict[str, Any],
    astrology: dict[str, Any] | None,
    analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    selected = _normalize_modules(modules)
    analysis_json = build_navigation_analysis(bazi_chart, birth_info, astrology, analysis)
    report_sections = _build_strategy_report(analysis_json)
    return {
        "summary": report_sections["core_profile"]["one_sentence"],
        "selected_modules": selected,
        "astrology_status": (astrology or {}).get("_meta", {}).get("status", "missing"),
        "analysis_json": analysis_json,
        "report_prompt": REPORT_PROMPT_TEMPLATE.replace("__ANALYSIS_JSON__", json.dumps(analysis_json, ensure_ascii=False, indent=2)),
        "report_sections": report_sections,
        "cards": _legacy_cards(report_sections, selected),
    }


def build_navigation_analysis(
    bazi_chart: dict[str, Any],
    birth_info: dict[str, Any],
    astrology: dict[str, Any] | None,
    qa_analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    astrology = astrology or {}
    qa = qa_analysis or _fallback_qa_analysis(bazi_chart)
    ten_gods = bazi_chart["wuxing_score"].get("ten_gods_percentage") or {}
    strongest_ten_god = max(ten_gods, key=ten_gods.get) if ten_gods else "yin_star"
    percentages = bazi_chart["wuxing_score"]["percentage"]
    strongest_element = max(percentages, key=percentages.get)
    weakest_element = min(percentages, key=percentages.get)
    yong = qa.get("yong_shen") or _fallback_yong_ji(bazi_chart)[0]
    ji = qa.get("ji_shen") or _fallback_yong_ji(bazi_chart)[1]
    career_directions = _career_directions(strongest_ten_god)
    unsuitable = _unsuitable_directions(strongest_ten_god, ji)
    money = _money_strategy(career_directions, strongest_ten_god)
    plan = _three_month_plan(career_directions)
    life_lesson = _life_lesson(strongest_ten_god, ji, qa)
    bazi_signals = [
        _signal("日主", f"日主为{bazi_chart['day_master']['stem']}，五行属{bazi_chart['day_master']['element']}。", "用于判断适合的工作节奏和资源需求。"),
        _signal("强弱", f"经历校验后判断为{qa.get('final_judgment', bazi_chart['preliminary']['strength'])}，置信度{qa.get('confidence', bazi_chart['preliminary'].get('confidence', 60))}%。", "决定是更适合借平台蓄力，还是主动输出和承担。"),
        _signal("五行", f"最强五行为{_element_name(strongest_element)}，最弱五行为{_element_name(weakest_element)}。", "强处代表容易调用的能力，弱处代表需要制度和训练补足。"),
        _signal("十神", f"当前最突出的十神结构是{_ten_god_label(strongest_ten_god)}。", _ten_god_real_world(strongest_ten_god)),
    ]
    astrology_signals = _astrology_signals(astrology)
    qa_validation = _qa_validation(qa)
    core_traits = [
        _trait("适合把混乱问题整理成清晰步骤", bazi_signals[3]["basis"], "在现实中对应需求整理、流程拆解、文档沉淀、项目跟进。"),
        _trait("需要能积累作品和案例的环境", "问答校验会改变喜忌结论，说明现实反馈比单纯盘面更重要。", "选择岗位时要看能不能留下案例，而不是只看头衔。"),
        _trait("适合从助理型、运营型、流程型岗位切入", _astro_compact_basis(astrology), "先用执行和整理能力进入行业，再逐步承担策略和项目。"),
    ]
    strengths = [
        "能把复杂信息整理成清单、文档、流程或复盘，适合做交付可见的工作。",
        "适合在真实项目中积累案例，而不是只靠泛泛学习提升安全感。",
        "如果有稳定反馈机制，进步会明显快于独自摸索。",
    ]
    risks = [
        "容易把“学习更多”当成准备完成，但没有作品和案例就很难提高议价。",
        "如果长期做临时救火、杂务和无复盘工作，会消耗精力但沉淀很少。",
        "方向频繁切换会让简历缺少主线，需要用 3 个月周期验证一个方向。",
    ]
    evidence_chain = [
        "八字先给出强弱、喜忌和十神结构，确定适合的能力使用方式。",
        "星盘补充人格表达、职业呈现和行动风格，避免只用八字下结论。",
        "问答校验把用户真实经历纳入判断，优先采用与现实反馈一致的结论。",
        "职业建议只落到岗位、切入方式、能力缺口和 3 个月动作，不输出空泛结论。",
    ]
    return {
        "core_traits": core_traits,
        "bazi_signals": bazi_signals,
        "astrology_signals": astrology_signals,
        "qa_validation": qa_validation,
        "strengths": strengths,
        "risks": risks,
        "suitable_career_directions": career_directions,
        "unsuitable_directions": unsuitable,
        "money_strategy": money,
        "three_month_plan": plan,
        "life_lesson": life_lesson,
        "evidence_chain": evidence_chain,
        "meta": {
            "birth_name": birth_info.get("name") or "",
            "selected_basis": "bazi_astrology_qa_structured_analysis",
            "strongest_ten_god": strongest_ten_god,
            "yong_shen": yong,
            "ji_shen": ji,
        },
    }


def _build_strategy_report(analysis_json: dict[str, Any]) -> dict[str, Any]:
    first_job = analysis_json["suitable_career_directions"][0]["job"]
    second_job = analysis_json["suitable_career_directions"][1]["job"]
    return {
        "core_profile": {
            "title": "核心画像",
            "one_sentence": f"你的发展路线更适合从{first_job}、{second_job}这类可沉淀案例的岗位切入，用文档、流程、用户反馈和项目结果建立职业主线。",
            "basis": analysis_json["evidence_chain"][0],
            "real_world": "现实中不要只追求看起来高级的方向，而要选择能让你每天留下可复用成果的岗位：文档、SOP、用户访谈、项目复盘、数据看板或案例集。",
            "advice": "未来 3 个月只验证 1 条主线，先做出能给面试官看的 3 个作品，再扩大投递范围。",
        },
        "basis": {
            "bazi": analysis_json["bazi_signals"],
            "astrology": analysis_json["astrology_signals"],
            "qa": analysis_json["qa_validation"],
        },
        "real_world_patterns": [
            _judgment("你适合做“整理问题并推动落地”的角色", "八字十神和问答校验共同指向需要把能力落在具体成果上。", "学习、工作中会更擅长把混乱资料整理成清单、流程、文档和复盘。", "求职时优先展示作品集，而不是只说自己学习能力强。"),
            _judgment("你需要避开只有消耗、没有沉淀的岗位", "风险信号显示临时救火和杂务会稀释职业主线。", "短期会很忙，但简历上说不清自己负责了什么结果。", "接任务前问清楚：结果交付物是什么、数据指标是什么、能不能复盘。"),
            _judgment("你不需要一开始就做大决策岗位", "当前策略更适合从助理、运营、流程和客户成功切入。", "先在项目里练拆解、沟通、文档和复盘，逐渐获得更大责任。", "投递岗位时选择“有导师、有流程、有项目”的团队。"),
        ],
        "career_directions": analysis_json["suitable_career_directions"],
        "unsuitable_directions": analysis_json["unsuitable_directions"],
        "money_path": analysis_json["money_strategy"],
        "three_month_plan": analysis_json["three_month_plan"],
        "life_lesson": analysis_json["life_lesson"],
        "key_reminders": [
            "不要频繁换方向。至少用 3 个月验证一个岗位方向，再判断是否调整。",
            "不要只学习不产出。每周至少留下 1 个可展示成果：文档、流程图、拆解报告、复盘或案例。",
            "不要长期只做杂务。杂务可以做，但必须转化成 SOP、效率优化或项目经验。",
            "不要把职业建议理解成命定。它是用来缩小试错范围的策略，不是限制你的天花板。",
        ],
    }


def _normalize_modules(modules: list[str]) -> list[str]:
    if not modules or "full" in modules:
        return ["talent", "career", "city", "life_lesson"]
    valid = [module for module in modules if module in MODULE_TITLES]
    return valid or ["career"]


def _signal(title: str, basis: str, real_world: str) -> dict[str, str]:
    return {"title": title, "basis": basis, "real_world": real_world}


def _trait(title: str, basis: str, real_world: str) -> dict[str, str]:
    return {"trait": title, "basis": basis, "real_world": real_world}


def _judgment(title: str, basis: str, real_world: str, advice: str) -> dict[str, str]:
    return {"title": title, "basis": basis, "real_world": real_world, "advice": advice}


def _career_directions(strongest_ten_god: str) -> list[dict[str, str]]:
    items = CAREER_POOLS.get(strongest_ten_god, CAREER_POOLS["yin_star"])
    if strongest_ten_god != "guan_sha":
        items = items + CAREER_POOLS["guan_sha"][:1]
    return [
        {"job": job, "why": why, "entry": entry, "skill_gap": skill_gap}
        for job, why, entry, skill_gap in items[:4]
    ]


def _unsuitable_directions(strongest_ten_god: str, ji: list[str]) -> list[dict[str, str]]:
    return [
        {
            "type": "纯重复执行岗",
            "reason": "这类岗位只要求按指令完成动作，很少让你沉淀流程、案例或方法，做久了简历会变薄。",
            "damage_control": "如果短期必须做，把每天重复任务整理成 SOP，并记录你节省了多少时间或减少了多少错误。",
        },
        {
            "type": "无沉淀销售",
            "reason": "只靠临场话术和短期冲业绩，容易消耗情绪，也很难转化成长期专业资产。",
            "damage_control": "选择有行业知识、客户分层、复盘机制的销售支持或客户成功方向，不要只做陌拜。",
        },
        {
            "type": "长期临时救火型岗位",
            "reason": f"当前忌讳信号包含{'、'.join(ji) or '节奏失衡'}，长期救火会让你被外部节奏牵着走。",
            "damage_control": "给每个救火任务补一张复盘表：原因、处理步骤、下次预防机制，逼它沉淀为流程经验。",
        },
        {
            "type": "没有流程和成长路径的杂务型岗位",
            "reason": f"{_ten_god_label(strongest_ten_god)}需要被转化成具体能力，如果工作没有反馈和升级路径，很难形成竞争力。",
            "damage_control": "入职前问清楚 3 个月后负责什么指标、能否参与项目、是否有固定复盘。",
        },
    ]


def _money_strategy(career_directions: list[dict[str, str]], strongest_ten_god: str) -> list[dict[str, Any]]:
    first_job = career_directions[0]["job"]
    return [
        {
            "stage": "短期：靠技能换工资",
            "focus": f"围绕{first_job}训练可被雇主直接使用的技能。",
            "actions": [
                "做 3 份样例作品：一份竞品拆解、一份 SOP、一份用户问题复盘。",
                "把 Excel/飞书/Notion/AI 工具用到实际项目里，展示前后效率变化。",
                "面试时用“问题-动作-结果”讲案例，不只说自己认真负责。",
            ],
        },
        {
            "stage": "中期：靠案例提高议价",
            "focus": "把工作成果包装成能证明价值的项目案例。",
            "actions": [
                "每月复盘一个项目：目标、过程、数据、踩坑、下一步优化。",
                "积累 2-3 个能说明你解决过真实问题的案例，而不是只罗列职责。",
                f"把{_ten_god_label(strongest_ten_god)}对应的优势翻译成岗位语言，例如需求整理、流程推进、用户反馈闭环。",
            ],
        },
        {
            "stage": "长期：靠专业标签形成复利",
            "focus": "这里的“专业标签”不是口号，而是别人想到某类问题时会想到你。",
            "actions": [
                "固定一个细分主题持续输出，例如 AI知识库运营、B端客户成功、SOP搭建或用户研究。",
                "把作品集更新成公开可读版本：案例截图、流程图、复盘结论、数据变化。",
                "争取在同一条主线上连续做 6-12 个月，形成比跳来跳去更强的可信度。",
            ],
        },
    ]


def _three_month_plan(career_directions: list[dict[str, str]]) -> list[dict[str, Any]]:
    job = career_directions[0]["job"]
    return [
        {
            "month": "第 1 个月：确定主线并做基础作品",
            "actions": [
                f"选定一个主投方向：{job}，不要同时投 5 个完全不同方向。",
                "拆 10 个目标岗位 JD，整理高频能力词和工具要求。",
                "完成 1 份竞品/岗位拆解报告，控制在 3-5 页，能给别人看懂。",
            ],
        },
        {
            "month": "第 2 个月：做项目样例并开始小范围投递",
            "actions": [
                "完成 1 份 SOP 或业务流程图，展示你如何把混乱任务变清楚。",
                "完成 1 份用户问题复盘或数据看板，展示你如何发现问题。",
                "投递 20 个匹配岗位，每次面试后记录被问到的问题和短板。",
            ],
        },
        {
            "month": "第 3 个月：优化作品集和面试表达",
            "actions": [
                "把前两个月作品整理成一页作品集目录，附上每个案例的结果。",
                "准备 5 个面试故事：冲突、推进、复盘、学习、失败修正各 1 个。",
                "根据反馈二选一：继续深挖当前方向，或只微调到相邻岗位，不大幅跳转。",
            ],
        },
    ]


def _life_lesson(strongest_ten_god: str, ji: list[str], qa: dict[str, Any]) -> dict[str, Any]:
    mode = {
        "yin_star": "容易在资料、课程和思考里停留太久，真正对外发布的作品偏少。",
        "bijie": "容易被人情、比较和团队节奏带走，自己的主线推进变慢。",
        "shi_shang": "容易想法很多、开头很快，但后续复盘、收尾和结果包装不足。",
        "cai_star": "容易被短期机会和收入波动牵动，忽略长期可复用的能力资产。",
        "guan_sha": "容易被规则、评价和任务压力推着走，忙完很多事却没有留下自己的成果。",
    }.get(strongest_ten_god, "容易同时尝试太多方向，导致每条线都没有形成清晰成果。")
    qa_note = "问答校验已纳入现实经历，说明这个课题要用真实结果来修正，而不是只靠盘面判断。"
    if not (qa.get("answers") or []):
        qa_note = "当前问答校验不足，建议先用 3 个月行动结果继续验证这个课题。"
    return {
        "core_issue": f"你反复卡住的核心模式是：{mode}这会让你看起来一直在努力，但成果没有稳定沉淀到作品、履历、技能或收入里。",
        "real_world_patterns": [
            "频繁怀疑方向：看到新机会、新课程或别人评价后，容易重新推翻原计划。",
            "做了很多零散任务：临时任务、帮忙、学习笔记很多，但能放进作品集或简历的成果偏少。",
            "长期项目推进慢：重要但不紧急的事，比如作品集、案例复盘、求职准备，经常被日常琐事挤掉。",
            "学了很多但没有转化：收藏、听课、研究不少，但没有变成案例、收入、岗位竞争力或可展示页面。",
        ],
        "hidden_cost": f"如果不处理这个模式，现实代价不是“运气不好”，而是忙了很久却没有成长资产：简历没有变强、作品集没有增加、收入议价没有提高，还会因为一直换方向而缺少复利。{qa_note}",
        "breakthrough_method": "把每一次学习、任务和选择都绑定到一个可见交付物上。所谓交付物，就是别人能看到、能评价、能证明你能力的东西，例如一份 SOP、一页项目复盘、一个用户访谈总结、一张流程图、一个数据看板或一个可公开的作品链接。",
        "practice_plan": [
            {
                "action": "每天留下一个最小成果",
                "how_to_do_it": "每天结束前用 15 分钟写下：今天做了什么、产出了什么文件/截图/链接、它能证明哪项能力。如果没有产出，就补一个 5 行复盘。",
                "frequency": "每天 1 次，连续 30 天。",
            },
            {
                "action": "每周整理一份作品材料",
                "how_to_do_it": "从本周任务里选 1 件事，整理成“问题-动作-结果-下一步”的小案例，哪怕只有半页也要保存到作品集文件夹。",
                "frequency": "每周 1 次，固定在周日或休息日前。",
            },
            {
                "action": "给临时任务加边界",
                "how_to_do_it": "接任务前先问：这件事的交付物是什么？截止时间是什么？做完能不能沉淀为模板、流程或案例？如果三个都没有，只投入必要时间。",
                "frequency": "每次接新任务前执行。",
            },
            {
                "action": "建立 3 个月方向账本",
                "how_to_do_it": "只追踪一个主方向，记录投递岗位、作品数量、面试反馈、收入机会。不要用情绪判断方向，用数据判断。",
                "frequency": "每周更新 1 次，连续 12 周。",
            },
        ],
        "decision_questions": [
            "这件事做完以后，能不能变成作品、案例、技能证明或收入机会？",
            "如果 3 个月后回看，这个选择会让我的简历更清楚，还是只是让我更忙？",
            "我现在是在解决真实问题，还是在用学习、搜索和准备逃避交付？",
            f"这件事是否会加重我当前需要避开的模式：{'、'.join(ji) if ji else '无复盘、无沉淀、无边界'}？",
        ],
    }


def _astrology_signals(astrology: dict[str, Any]) -> list[dict[str, str]]:
    if (astrology.get("_meta") or {}).get("status") != "ready":
        return [_signal("星盘", "星盘数据暂不可用。", "当前报告以八字和问答校验为主，星盘不参与关键结论。")]
    return [
        _signal("太阳", _planet_text(astrology, "sun"), "对应核心自我和主动投入的领域，帮助判断适合在哪类事情上持续发光。"),
        _signal("月亮", _planet_text(astrology, "moon"), "对应情绪安全感和压力下的反应，帮助判断工作环境是否消耗。"),
        _signal("水星", _planet_text(astrology, "mercury"), "对应表达、学习和信息处理方式，帮助判断适合内容、产品、研究还是沟通岗位。"),
        _signal("MC", _planet_text(astrology, "mc"), "对应职业呈现和社会评价，帮助判断长期适合建立什么职业形象。"),
        _signal("土星", _planet_text(astrology, "saturn"), "对应需要训练的纪律和边界，提醒职业发展不要只靠灵感。"),
    ]


def _qa_validation(qa: dict[str, Any]) -> list[dict[str, str]]:
    answers = qa.get("answers") or []
    if not answers:
        return [_signal("问答校验", "暂未完成经历问答。", "报告会降低确定性，并提醒用户用现实经历继续校准。")]
    rows = []
    for answer in answers[:4]:
        rows.append(
            _signal(
                f"Q{answer.get('question_id')} {answer.get('dimension') or '经历反馈'}",
                answer.get("signal") or "用户选择已纳入强弱与喜忌校验。",
                _qa_real_world(answer),
            )
        )
    return rows


def _qa_real_world(answer: dict[str, Any]) -> str:
    if answer.get("mapped_year"):
        return f"该反馈绑定到 {answer['mapped_year']} 年，用来判断顺逆年份是否与理论流年一致。"
    if answer.get("event_type"):
        return "该反馈用于判断职业、财富、支持系统或健康压力是否与十神倾向一致。"
    return "该反馈用于校正大运体感，避免只按盘面静态下结论。"


def _planet_text(astrology: dict[str, Any], key: str) -> str:
    body = astrology.get(key) or {}
    name = {"sun": "太阳", "moon": "月亮", "mercury": "水星", "mc": "MC", "saturn": "土星"}.get(key, key)
    sign = body.get("sign_zh") or body.get("sign") or "未知星座"
    degree = body.get("degree_display") or ""
    house = f"第{body['house']}宫" if body.get("house") else "宫位待定"
    return f"{name}落入{sign}{degree}，{house}。"


def _astro_compact_basis(astrology: dict[str, Any]) -> str:
    if (astrology.get("_meta") or {}).get("status") != "ready":
        return "星盘数据暂不可用，因此不把星盘作为唯一依据。"
    return f"{_planet_text(astrology, 'sun')} {_planet_text(astrology, 'mc')}"


def _fallback_qa_analysis(bazi_chart: dict[str, Any]) -> dict[str, Any]:
    yong, ji = _fallback_yong_ji(bazi_chart)
    return {
        "final_judgment": bazi_chart["preliminary"]["strength"],
        "confidence": bazi_chart["preliminary"].get("confidence", 60),
        "yong_shen": yong,
        "ji_shen": ji,
        "answers": [],
    }


def _fallback_yong_ji(bazi_chart: dict[str, Any]) -> tuple[list[str], list[str]]:
    strength = bazi_chart["preliminary"]["strength"]
    dm = bazi_chart["day_master"]["element"]
    generated_by = {"火": "木", "土": "火", "金": "土", "水": "金", "木": "水"}
    generates = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    controls = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
    controlled_by = {value: key for key, value in controls.items()}
    if strength == "身强":
        return [generates[dm], controlled_by[dm], controls[dm]], [dm, generated_by[dm]]
    if strength == "身弱":
        return [dm, generated_by[dm]], [generates[dm], controlled_by[dm], controls[dm]]
    return [dm, generated_by[dm]], []


def _legacy_cards(report_sections: dict[str, Any], selected: list[str]) -> list[dict[str, Any]]:
    cards = []
    if "career" in selected:
        cards.append(
            {
                "module": "career",
                "title": "适合的职业方向",
                "answer": report_sections["core_profile"]["one_sentence"],
                "explanation": report_sections["core_profile"]["real_world"],
                "professional_basis": {
                    "bazi": "详见 report_sections.basis.bazi",
                    "astrology": "详见 report_sections.basis.astrology",
                },
                "suggestions": [item["entry"] for item in report_sections["career_directions"][:3]],
            }
        )
    if "city" in selected:
        cards.append({"module": "city", "title": "城市参考", "answer": "城市选择需结合岗位机会和生活成本。", "explanation": "当前版本保留城市评分作为辅助，不作为主报告核心。", "professional_basis": {"bazi": "按喜用五行和城市产业气质参考。", "astrology": "按 MC、九宫和迁移主题辅助。"}, "suggestions": ["优先看岗位密度。", "先短住或远程项目测试。", "不要只因城市标签迁移。"], "city_ranking": _city_ranking(report_sections)})
    return cards or [
        {
            "module": "full",
            "title": "人生导航",
            "answer": report_sections["core_profile"]["one_sentence"],
            "explanation": report_sections["core_profile"]["real_world"],
            "professional_basis": {"bazi": "详见结构化依据。", "astrology": "详见结构化依据。"},
            "suggestions": report_sections["key_reminders"][:3],
        }
    ]


def _city_ranking(report_sections: dict[str, Any]) -> list[dict[str, Any]]:
    ranking = []
    for index, city in enumerate(CANDIDATE_CITIES[:5]):
        profile = CITY_PROFILES[city]
        ranking.append({"city": city, "score": 92 - index * 3, "reason": f"{city}的{profile['tags'][0]}和{profile['tags'][1]}资源可作为岗位机会参考。"})
    return ranking


def _ten_god_real_world(key: str) -> str:
    return {
        "yin_star": "现实中更适合研究、资料整理、知识库、用户洞察和顾问式表达。",
        "bijie": "现实中更适合协作、社群、客户关系、项目协调和资源整合。",
        "shi_shang": "现实中更适合内容、表达、产品反馈、创意输出和用户沟通。",
        "cai_star": "现实中更适合商业转化、客户经营、产品运营和资源配置。",
        "guan_sha": "现实中更适合项目推进、流程管理、规则执行和风险控制。",
    }.get(key, "现实中适合复合型岗位，需要用项目验证具体优势。")


def _ten_god_label(key: str) -> str:
    return {
        "yin_star": "印星",
        "bijie": "比劫",
        "shi_shang": "食伤",
        "cai_star": "财星",
        "guan_sha": "官杀",
    }.get(key, key)


def _element_name(key: str) -> str:
    return {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}.get(key, key)
