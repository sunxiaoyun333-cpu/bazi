from __future__ import annotations


EVENT_QUESTIONS = {
    "career_pressure": {
        "id": 2,
        "type": "event",
        "dimension": "职场事件",
        "question": "过去几年，以下哪件事发生过？（选最符合的一项）",
        "context": "有就选有，没有就选最接近的。",
        "options": [
            {"key": "A", "text": "升职、被重用，或薪资有明显涨幅", "signal": "官星为喜，仕途顺畅", "strength_hint": "身弱", "mapped_type": "promoted", "event_type": "career_up"},
            {"key": "B", "text": "被辞退、降职，或被迫离职", "signal": "官杀克身，日主承压过重", "strength_hint": "身弱", "mapped_type": "demoted", "event_type": "career_down"},
            {"key": "C", "text": "自己主动辞职创业，或跳槽换了方向", "signal": "食伤旺，主动求变", "strength_hint": "身强", "mapped_type": "initiative_change", "event_type": "self_directed"},
            {"key": "D", "text": "工作一直比较稳定，没有大的变动", "signal": "官星平稳，格局中和", "strength_hint": "中和", "mapped_type": "stable", "event_type": "stable"},
        ],
    },
    "wealth_change": {
        "id": 2,
        "type": "event",
        "dimension": "财务事件",
        "question": "过去几年，以下哪件事发生过？（选最符合的一项）",
        "context": "金额按你的主观感受即可，不用精确。",
        "options": [
            {"key": "A", "text": "有过一笔意外之财，或副业、投资明显赚钱", "signal": "偏财星到位，或食伤生财", "strength_hint": "身强", "mapped_type": "windfall", "event_type": "wealth_up"},
            {"key": "B", "text": "有过较大的财务损失，比如亏损、被骗、借出难收", "signal": "比劫夺财，或财星受克", "strength_hint": "身弱", "mapped_type": "loss", "event_type": "wealth_down"},
            {"key": "C", "text": "买了房、车或大件，是重要资产变动", "signal": "财星稳定，身能任财", "strength_hint": "身强", "mapped_type": "asset", "event_type": "wealth_stable"},
            {"key": "D", "text": "收入比较稳定，没有特别大的起伏", "signal": "财星中性，格局平和", "strength_hint": "中和", "mapped_type": "stable", "event_type": "stable"},
        ],
    },
    "mentor_resource": {
        "id": 2,
        "type": "event",
        "dimension": "贵人资源",
        "question": "过去几年，以下哪件事发生过？（选最符合的一项）",
        "context": "回忆长辈、领导、学习、证书、资源方面。",
        "options": [
            {"key": "A", "text": "有长辈、前辈、领导帮你说话或提携", "signal": "正印发力，贵人为长辈权威", "strength_hint": "身弱", "mapped_type": "mentor_help", "event_type": "support_up"},
            {"key": "B", "text": "考试、考证、进修有明显进展", "signal": "印星旺，利学习考试", "strength_hint": "身弱", "mapped_type": "study_success", "event_type": "support_up"},
            {"key": "C", "text": "和长辈、父母或上司关系紧张，有明显矛盾", "signal": "印星受克，或枭神夺食", "strength_hint": "身强", "mapped_type": "mentor_conflict", "event_type": "support_down"},
            {"key": "D", "text": "主要靠自己，贵人不多，但也能扛住", "signal": "印弱但自立", "strength_hint": "身强", "mapped_type": "self_reliant", "event_type": "neutral"},
        ],
    },
    "expression_output": {
        "id": 2,
        "type": "event",
        "dimension": "创作表达",
        "question": "过去几年，以下哪件事发生过？（选最符合的一项）",
        "context": "创作、表达、才艺、副业、孩子相关。",
        "options": [
            {"key": "A", "text": "副业、创作、自媒体、才艺方面有收获或被认可", "signal": "食伤生财，才华得展", "strength_hint": "身强", "mapped_type": "expression_win", "event_type": "output_up"},
            {"key": "B", "text": "说错话、言多必失，或因表达问题惹麻烦", "signal": "伤官见官，言语带祸", "strength_hint": "身强", "mapped_type": "expression_trouble", "event_type": "output_bad"},
            {"key": "C", "text": "生了孩子，或孩子有重要变化", "signal": "食伤代表子女，子女宫动", "strength_hint": "中和", "mapped_type": "children", "event_type": "children"},
            {"key": "D", "text": "以上都没有，我比较低调，不爱出风头", "signal": "食伤弱，收敛格局", "strength_hint": "身弱", "mapped_type": "quiet", "event_type": "neutral"},
        ],
    },
    "peer_competition": {
        "id": 2,
        "type": "event",
        "dimension": "人际竞争",
        "question": "过去几年，以下哪件事发生过？（选最符合的一项）",
        "context": "朋友、合伙、团队、同行竞争相关。",
        "options": [
            {"key": "A", "text": "有朋友借钱没还，或合伙生意损失", "signal": "比劫夺财，同类损财", "strength_hint": "身弱", "mapped_type": "friend_loss", "event_type": "peer_bad"},
            {"key": "B", "text": "合伙或团队合作，一起做成了一件事", "signal": "比劫帮身，同伴助力", "strength_hint": "身弱", "mapped_type": "teamwork_win", "event_type": "peer_good"},
            {"key": "C", "text": "有强力竞争对手，被抢了客户或机会", "signal": "劫财夺财，竞争激烈", "strength_hint": "身强", "mapped_type": "competition_loss", "event_type": "peer_bad"},
            {"key": "D", "text": "朋友圈比较平稳，没有特别大的摩擦", "signal": "比劫平和，中性格局", "strength_hint": "中和", "mapped_type": "peer_stable", "event_type": "neutral"},
        ],
    },
    "general_fortune": {
        "id": 2,
        "type": "event",
        "dimension": "综合事件",
        "question": "过去五年，以下哪件事发生过？（选影响最大的一件）",
        "context": "有就选有，选对你影响最大的那个。",
        "options": [
            {"key": "A", "text": "生病住院，或动过手术", "signal": "忌神攻身，身体承压", "strength_hint": "身弱", "mapped_type": "health_issue", "event_type": "health_bad"},
            {"key": "B", "text": "搬家、换城市，或有重大居住变动", "signal": "驿马动，环境变化", "strength_hint": "中和", "mapped_type": "relocation", "event_type": "change"},
            {"key": "C", "text": "结婚、生子，或有重要感情变化", "signal": "配偶宫或子女宫被引动", "strength_hint": "中和", "mapped_type": "relationship_change", "event_type": "relationship"},
            {"key": "D", "text": "以上都没有，这几年生活比较平稳", "signal": "格局稳定，五行平和", "strength_hint": "中和", "mapped_type": "stable", "event_type": "neutral"},
        ],
    },
}


DAYUN_TRANSITION_DEFAULT = {
    "id": 3,
    "type": "dayun_transition",
    "dimension": "大运感受",
    "question": "您目前这个人生阶段（最近十年），和更早之前相比，整体感觉是？",
    "context": "从工作、收入、健康、人际综合来感受。",
    "options": [
        {"key": "A", "text": "比以前明显更顺，各方面都在变好", "signal": "当前大运为喜用", "strength_hint": "current_favorable", "mapped_type": "current_good"},
        {"key": "B", "text": "比以前明显更累，各方面都在走下坡", "signal": "当前大运为忌神", "strength_hint": "current_unfavorable", "mapped_type": "current_bad"},
        {"key": "C", "text": "跟以前差不多，没有太大变化", "signal": "大运影响中性", "strength_hint": "neutral", "mapped_type": "neutral"},
        {"key": "D", "text": "起伏比以前大，波动更明显了", "signal": "大运引动合冲，不稳定", "strength_hint": "volatile", "mapped_type": "volatile"},
    ],
}
