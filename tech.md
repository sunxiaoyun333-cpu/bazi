# 八字Agent - 完整技术规格文档 V1.0

## 一、文件结构

```
bazi-agent/
├── frontend/                          # Next.js 前端
│   ├── app/
│   │   ├── layout.tsx                 # 根布局
│   │   ├── page.tsx                   # 首页（输入页）
│   │   ├── globals.css
│   │   └── reading/
│   │       └── [sessionId]/
│   │           └── page.tsx           # 算命主流程页
│   │
│   ├── components/
│   │   ├── ui/                        # 基础UI组件（shadcn）
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   └── progress.tsx
│   │   │
│   │   ├── input/                     # 第一步：信息输入
│   │   │   ├── BirthInfoForm.tsx      # 主表单
│   │   │   ├── DatePicker.tsx         # 日期选择器
│   │   │   ├── TimePicker.tsx         # 时间选择器
│   │   │   └── LocationPicker.tsx     # 地点选择器
│   │   │
│   │   ├── chart/                     # 第二步：八字排盘展示
│   │   │   ├── BaziChart.tsx          # 八字命盘主组件
│   │   │   ├── PillarCard.tsx         # 单柱展示（年/月/日/时）
│   │   │   ├── WuxingRadar.tsx        # 五行分布图
│   │   │   └── ConfirmButton.tsx      # 确认排盘按钮
│   │   │
│   │   ├── questions/                 # 第三步：问答交互
│   │   │   ├── QuestionFlow.tsx       # 问题流程控制
│   │   │   ├── QuestionCard.tsx       # 单题展示
│   │   │   └── OptionButton.tsx       # 选项按钮
│   │   │
│   │   └── report/                    # 第四步：分析报告
│   │       ├── ReportLayout.tsx       # 报告整体布局
│   │       ├── ReportSection.tsx      # 每个大类区块
│   │       ├── WuxingBadge.tsx        # 五行标签
│   │       ├── JewelryCard.tsx        # 饰品推荐卡片
│   │       └── ShareButton.tsx        # 分享按钮
│   │
│   ├── lib/
│   │   ├── api.ts                     # 前端API调用封装
│   │   ├── types.ts                   # 前端类型定义
│   │   └── utils.ts                   # 工具函数
│   │
│   ├── hooks/
│   │   ├── useSession.ts              # session状态管理
│   │   └── useSSE.ts                  # SSE流式接收hook
│   │
│   └── constants/
│       ├── wuxing.ts                  # 五行常量
│       └── jewelry.ts                 # 饰品映射常量
│
├── backend/                           # Python FastAPI 后端
│   ├── main.py                        # FastAPI入口
│   ├── requirements.txt
│   ├── .env
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── session.py                 # session相关路由
│   │   ├── bazi.py                    # 八字计算路由
│   │   ├── questions.py               # 问题生成路由
│   │   └── report.py                  # 报告生成路由
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── bazi_engine.py             # 八字计算引擎（核心）
│   │   ├── solar_time.py              # 真太阳时换算
│   │   ├── question_generator.py      # 问题生成服务
│   │   ├── report_generator.py        # 报告生成服务
│   │   └── claude_client.py           # Claude API封装
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── session.py                 # Session数据模型
│   │   ├── bazi.py                    # 八字数据模型
│   │   ├── question.py                # 问题数据模型
│   │   └── report.py                  # 报告数据模型
│   │
│   ├── data/
│   │   ├── heavenly_stems.json        # 天干数据
│   │   ├── earthly_branches.json      # 地支数据
│   │   ├── nayin.json                 # 纳音数据
│   │   ├── cities.json                # 城市经纬度数据
│   │   └── jewelry_mapping.json       # 五行饰品映射
│   │
│   └── prompts/
│       ├── question_prompt.py         # 问题生成提示词
│       └── report_prompt.py           # 报告生成提示词
│
├── docker-compose.yml
└── README.md
```

---

## 二、数据结构

### 2.1 核心枚举与常量

```typescript
// frontend/constants/wuxing.ts

// 天干
enum HeavenlyStem {
  JIA = "甲",  // 木阳
  YI = "乙",   // 木阴
  BING = "丙", // 火阳
  DING = "丁", // 火阴
  WU = "戊",   // 土阳
  JI = "己",   // 土阴
  GENG = "庚", // 金阳
  XIN = "辛",  // 金阴
  REN = "壬",  // 水阳
  GUI = "癸"   // 水阴
}

// 地支
enum EarthlyBranch {
  ZI = "子",   // 水
  CHOU = "丑", // 土
  YIN = "寅",  // 木
  MAO = "卯",  // 木
  CHEN = "辰", // 土
  SI = "巳",   // 火
  WU = "午",   // 火
  WEI = "未",  // 土
  SHEN = "申", // 金
  YOU = "酉",  // 金
  XU = "戌",   // 土
  HAI = "亥"   // 水
}

// 五行
enum WuxingElement {
  WOOD = "木",
  FIRE = "火",
  EARTH = "土",
  METAL = "金",
  WATER = "水"
}

// 十神
enum TenGods {
  ZHENGYIN = "正印",
  PIANYIN = "偏印",
  JIECAI = "劫财",
  BIJIAN = "比肩",
  SHANGGUAN = "伤官",
  SHISHEN = "食神",
  ZHENGCAI = "正财",
  PIANCAI = "偏财",
  ZHENGGUAN = "正官",
  QIANSHA = "七杀"
}

// 日主强弱判断
enum DayMasterStrength {
  STRONG = "身强",
  WEAK = "身弱",
  NEUTRAL = "中和",
  CONG_GE = "从格"
}
```

### 2.2 Session 数据结构

```typescript
// frontend/lib/types.ts

interface Session {
  sessionId: string                    // UUID
  status: SessionStatus
  createdAt: string                    // ISO 8601
  updatedAt: string
  birthInfo: BirthInfo | null
  baziChart: BaziChart | null
  questions: Question[] | null
  userAnswers: UserAnswer[] | null
  report: Report | null
}

enum SessionStatus {
  INIT = "init",                       // 刚创建
  CHART_READY = "chart_ready",         // 排盘完成，等待确认
  CHART_CONFIRMED = "chart_confirmed", // 用户确认排盘
  QUESTIONS_READY = "questions_ready", // 问题生成完成
  QUESTIONS_ANSWERED = "questions_answered", // 问题回答完毕
  REPORT_GENERATING = "report_generating",   // 报告生成中
  REPORT_READY = "report_ready"        // 报告完成
}
```

### 2.3 出生信息

```typescript
interface BirthInfo {
  // 用户输入
  solarDate: string         // "1990-05-15" 阳历
  solarTime: string         // "14:30"
  city: string              // "上海"
  district?: string         // "浦东新区"（可选，提高精度）
  gender: "male" | "female"
  
  // 系统换算
  longitude: number         // 121.4737
  latitude: number          // 31.2304
  trueSolar: {
    date: string            // "1990-05-15"
    time: string            // "14:22"（真太阳时换算后）
    adjustMinutes: number   // -8（修正分钟数，便于展示）
  }
  lunarDate: {
    year: number            // 1990
    month: number           // 4
    day: number             // 21
    isLeapMonth: boolean    // false
  }
}
```

### 2.4 八字排盘数据

```typescript
interface BaziChart {
  // 四柱
  pillars: {
    year: Pillar
    month: Pillar
    day: Pillar
    hour: Pillar
  }
  
  // 日主信息
  dayMaster: {
    stem: string              // "甲"
    element: WuxingElement    // "木"
    yinYang: "阳" | "阴"
  }
  
  // 十神关系
  tenGods: {
    yearStem: TenGods
    monthStem: TenGods
    hourStem: TenGods
    yearBranch: TenGods
    monthBranch: TenGods
    dayBranch: TenGods
    hourBranch: TenGods
  }
  
  // 五行力量分析
  wuxingScore: WuxingScore
  
  // 六亲宫位（重要的星）
  palaces: {
    spouse: string            // 配偶宫（日支）
    parents: string           // 父母宫
    children: string          // 子女宫
    wealth: string            // 财帛宫
  }
  
  // 特殊神煞（MVP阶段选择性实现）
  shenshas?: ShenSha[]
  
  // 大运
  dayun: DaYun[]
  
  // 算法初判
  preliminary: {
    strength: DayMasterStrength     // "身弱"
    confidence: "high" | "medium" | "low"
    keyFactors: string[]            // ["月令不生日主", "财官过旺"]
    questionTemplate: "A" | "B" | "C"  // 对应三套问题模板
  }
}

interface Pillar {
  stem: string              // "甲"
  branch: string            // "子"
  stemElement: WuxingElement
  branchElement: WuxingElement
  hiddenStems: string[]     // 地支藏干 ["癸", "壬"]
  nayin: string             // 纳音 "海中金"
}

interface WuxingScore {
  wood: number              // 0-100 相对分值
  fire: number
  earth: number
  metal: number
  water: number
  // 十神分组分值
  yinStar: number           // 印星（正印+偏印）
  bijie: number             // 比劫（比肩+劫财）
  shiShang: number          // 食伤（食神+伤官）
  caiStar: number           // 财星（正财+偏财）
  guanSha: number           // 官杀（正官+七杀）
}

interface DaYun {
  index: number             // 第几步大运
  stem: string              // "丙"
  branch: string            // "午"
  element: WuxingElement
  startAge: number          // 8
  endAge: number            // 18
  startYear: number         // 1998
  endYear: number           // 2008
  tenGod: TenGods           // "食神"
}
```

### 2.5 问题与回答数据

```typescript
interface Question {
  id: number                // 1, 2, 3
  dimension: string         // "性格特质" | "过往经历" | "行为模式"
  question: string          // 问题文本
  options: QuestionOption[]
}

interface QuestionOption {
  key: "A" | "B" | "C" | "D"
  text: string              // 选项文本（用户可见）
  signal: string            // 命理信号（仅后端/AI可见）
  strengthHint: DayMasterStrength | null  // 倾向的强弱方向
}

interface UserAnswer {
  questionId: number
  selectedKey: "A" | "B" | "C" | "D"
  signal: string            // 选中选项的命理信号
  strengthHint: DayMasterStrength | null
}

// 综合判断结果
interface StrengthAnalysis {
  finalJudgment: DayMasterStrength    // "身弱"
  confidence: number                  // 75（百分比）
  algorithmScore: number              // 50（算法权重）
  answerScore: {                      // 问题回答权重
    strong: number
    weak: number
    neutral: number
    congGe: number
  }
  yongShen: string[]                  // 用神 ["印", "比"]
  jiShen: string[]                    // 忌神 ["财", "官", "杀"]
}
```

### 2.6 报告数据结构

```typescript
interface Report {
  sessionId: string
  generatedAt: string
  
  // 综合判断
  strengthAnalysis: StrengthAnalysis
  
  // 五行喜忌
  wuxingAnalysis: {
    lacking: WuxingElement[]          // 缺失五行 ["水", "木"]
    excess: WuxingElement[]           // 过旺五行 ["火"]
    favorable: WuxingElement[]        // 喜用 ["水", "木"]
    unfavorable: WuxingElement[]      // 忌讳 ["火", "土"]
  }
  
  // 各维度分析（流式生成，逐段到达）
  sections: ReportSection[]
  
  // 实用建议
  recommendations: Recommendations
}

interface ReportSection {
  id: string
  title: string             // "事业与财运"
  icon: string              // emoji或图标名
  content: string           // AI生成的分析文字
  highlight?: string        // 关键结论摘要
  isGenerated: boolean      // 流式生成状态
}

// 固定的报告大类
const REPORT_SECTIONS = [
  { id: "career",    title: "事业与财运", icon: "💼" },
  { id: "love",      title: "感情与婚姻", icon: "💕" },
  { id: "health",    title: "健康与体质", icon: "🌿" },
  { id: "family",    title: "家庭与六亲", icon: "🏠" },
  { id: "wealth",    title: "财富格局",   icon: "💰" },
  { id: "overall",   title: "整体格局与人生主题", icon: "✨" },
]

interface Recommendations {
  // 饰品推荐
  jewelry: JewelryRecommendation[]
  
  // 有利方位
  directions: {
    favorable: string[]     // ["北方", "东方"]
    unfavorable: string[]   // ["南方"]
    reason: string
  }
  
  // 幸运颜色
  colors: {
    favorable: string[]     // ["黑色", "蓝色", "绿色"]
    unfavorable: string[]   // ["红色"]
  }
  
  // 小建议
  lifestyleTips: string[]   // ["多接近水元素环境", "佩戴黑色系饰品"]
  
  // 适合长期居住方位
  livingDirection: {
    best: string            // "城市偏北或偏东区域"
    reason: string
    secondBest?: string
  }
}

interface JewelryRecommendation {
  element: WuxingElement    // "水"
  category: string          // "晶石类"
  items: JewelryItem[]
  wearingAdvice: string     // "建议左手佩戴"
}

interface JewelryItem {
  name: string              // "海蓝宝"
  description: string       // "补水气，助贵人运"
  color: string             // "#4A90D9"
  priority: "首选" | "次选"
}
```

---

## 三、API 设计

### 3.1 接口总览

```
POST   /api/session/create           创建会话
GET    /api/session/{sessionId}      获取会话状态

POST   /api/bazi/calculate           计算八字排盘
GET    /api/bazi/{sessionId}         获取排盘结果
POST   /api/bazi/{sessionId}/confirm 用户确认排盘

POST   /api/questions/generate       生成问题（确认后触发）
GET    /api/questions/{sessionId}    获取问题列表
POST   /api/questions/{sessionId}/answer  提交回答

GET    /api/report/{sessionId}       获取报告（SSE流式）
GET    /api/report/{sessionId}/full  获取完整报告（非流式）
```

### 3.2 接口详细规格

#### 创建会话

```
POST /api/session/create

Request: {}  // 无需参数

Response 200:
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "init",
  "createdAt": "2024-01-15T10:30:00Z"
}
```

#### 计算八字排盘

```
POST /api/bazi/calculate

Request:
{
  "sessionId": "550e8400...",
  "solarDate": "1990-05-15",
  "solarTime": "14:30",
  "city": "上海",
  "district": "浦东新区",     // 可选
  "gender": "female"
}

Response 200:
{
  "sessionId": "550e8400...",
  "birthInfo": {
    "solarDate": "1990-05-15",
    "solarTime": "14:30",
    "city": "上海",
    "longitude": 121.4737,
    "latitude": 31.2304,
    "trueSolar": {
      "date": "1990-05-15",
      "time": "14:22",
      "adjustMinutes": -8
    },
    "lunarDate": {
      "year": 1990,
      "month": 4,
      "day": 21,
      "isLeapMonth": false
    }
  },
  "baziChart": {
    "pillars": {
      "year":  { "stem": "庚", "branch": "午", "stemElement": "金", "branchElement": "火", "hiddenStems": ["丁", "己"], "nayin": "路旁土" },
      "month": { "stem": "辛", "branch": "巳", "stemElement": "金", "branchElement": "火", "hiddenStems": ["丙", "庚", "戊"], "nayin": "白蜡金" },
      "day":   { "stem": "癸", "branch": "亥", "stemElement": "水", "branchElement": "水", "hiddenStems": ["壬", "甲"], "nayin": "大海水" },
      "hour":  { "stem": "甲", "branch": "申", "stemElement": "木", "branchElement": "金", "hiddenStems": ["庚", "壬", "戊"], "nayin": "泉中水" }
    },
    "dayMaster": {
      "stem": "癸",
      "element": "水",
      "yinYang": "阴"
    },
    "wuxingScore": {
      "wood": 10,
      "fire": 35,
      "earth": 20,
      "metal": 25,
      "water": 10,
      "yinStar": 10,
      "bijie": 10,
      "shiShang": 10,
      "caiStar": 20,
      "guanSha": 50
    },
    "tenGods": {
      "yearStem": "正官",
      "monthStem": "偏官",
      "hourStem": "伤官",
      "yearBranch": "正财",
      "monthBranch": "正财",
      "dayBranch": "劫财",
      "hourBranch": "正官"
    },
    "dayun": [...],
    "preliminary": {
      "strength": "身弱",
      "confidence": "high",
      "keyFactors": ["月令火克水，官杀过旺，日主无力"],
      "questionTemplate": "B"
    }
  }
}

Response 400:
{
  "error": "INVALID_DATE",
  "message": "出生日期格式错误"
}

Response 400:
{
  "error": "CITY_NOT_FOUND",
  "message": "未找到该城市，请尝试省会城市名"
}
```

#### 确认排盘

```
POST /api/bazi/{sessionId}/confirm

Request: {}

Response 200:
{
  "sessionId": "550e8400...",
  "status": "chart_confirmed",
  "nextStep": "questions"
}
```

#### 生成问题

```
POST /api/questions/generate

Request:
{
  "sessionId": "550e8400..."
}

Response 200:
{
  "sessionId": "550e8400...",
  "questions": [
    {
      "id": 1,
      "dimension": "性格特质",
      "question": "在工作和生活中，你通常更接近哪种状态？",
      "options": [
        {
          "key": "A",
          "text": "配合他人、执行落实，做好分内的事",
          "signal": "身弱信号"
        },
        {
          "key": "B",
          "text": "独立思考、自己拍板，不太需要别人指导",
          "signal": "身强信号"
        },
        {
          "key": "C",
          "text": "喜欢表达和创造，有很多想法想输出",
          "signal": "食伤旺信号"
        },
        {
          "key": "D",
          "text": "顺势而为，环境好就好，环境差就调整",
          "signal": "从格信号"
        }
      ]
    },
    // Q2, Q3...
  ]
}
```

#### 提交回答

```
POST /api/questions/{sessionId}/answer

Request:
{
  "answers": [
    { "questionId": 1, "selectedKey": "A" },
    { "questionId": 2, "selectedKey": "C" },
    { "questionId": 3, "selectedKey": "A" }
  ]
}

Response 200:
{
  "sessionId": "550e8400...",
  "status": "questions_answered",
  "strengthAnalysis": {
    "finalJudgment": "身弱",
    "confidence": 83,
    "yongShen": ["印", "比"],
    "jiShen": ["财", "官", "杀"]
  },
  "nextStep": "report"
}
```

#### 获取报告（SSE 流式）

```
GET /api/report/{sessionId}
Header: Accept: text/event-stream

// SSE 事件流格式：

// 1. 报告开始
event: report_start
data: {
  "sessionId": "550e8400...",
  "totalSections": 6
}

// 2. 每个章节流式输出
event: section_start
data: { "sectionId": "career", "title": "事业与财运" }

event: section_chunk
data: { "sectionId": "career", "chunk": "您的八字中..." }

event: section_chunk
data: { "sectionId": "career", "chunk": "官杀过旺..." }

event: section_end
data: { "sectionId": "career", "highlight": "事业需借力，忌单打独斗" }

// 3. 重复直到所有章节完成

// 4. 推荐内容（非流式，一次性返回）
event: recommendations
data: {
  "wuxingAnalysis": { ... },
  "jewelry": [ ... ],
  "directions": { ... },
  "colors": { ... },
  "lifestyleTips": [ ... ],
  "livingDirection": { ... }
}

// 5. 完成
event: report_complete
data: { "sessionId": "550e8400...", "generatedAt": "2024-01-15T10:35:00Z" }

// 错误处理
event: error
data: { "code": "GENERATION_FAILED", "message": "生成失败，请重试" }
```

---

## 四、页面流程

### 4.1 流程状态机

```
[Step 1: 信息输入]
        ↓ 提交表单
[Step 2: 排盘计算中] (loading ~2s)
        ↓ 计算完成
[Step 3: 八字展示] ← 用户可以在这里返回修改
        ↓ 点击"确认排盘"
[Step 4: 问题生成中] (loading ~3s, Claude生成)
        ↓ 生成完成
[Step 5: 问题作答] (3题，逐题展示)
        ↓ 第3题作答完成，自动提交
[Step 6: 报告生成中] (流式，逐段展示)
        ↓ 全部生成完成
[Step 7: 完整报告展示]
        ↓
[分享 / 保存 / 结束]
```

### 4.2 各页面详细规格

#### Step 1 - 信息输入页 (`/`)

```
┌─────────────────────────────────┐
│  🔮  八字命盘                    │
│  填写你的出生信息，开启命理解析    │
├─────────────────────────────────┤
│                                 │
│  出生日期 *                      │
│  [  1990  ] 年 [ 05 ] 月 [ 15 ] 日│
│                                 │
│  出生时间 *                      │
│  [ 14 ] 时 [ 30 ] 分            │
│  ℹ️ 不知道时间？选择"不详"        │
│                                 │
│  出生地点 *                      │
│  [ 上海市 ▼ ] [ 浦东新区 ▼ ]     │
│                                 │
│  性别 *                          │
│  ● 男  ○ 女                     │
│                                 │
│  ┌─────────────────────────┐    │
│  │    开始排盘  →           │    │
│  └─────────────────────────┘    │
│                                 │
│  * 出生时间精确到小时即可        │
└─────────────────────────────────┘
```

**交互细节**：
- 年份范围：1900-2005（可调整）
- 时间不详时，时柱按"子时"处理，报告中注明时柱仅供参考
- 地点选择：省→市两级联动下拉
- 表单验证：全部必填，提交前本地校验

#### Step 2/3 - 排盘展示页 (`/reading/[sessionId]`)

```
// Step 2: 计算中
┌─────────────────────────────────┐
│                                 │
│         ⚙️ 正在排盘...           │
│                                 │
│  换算真太阳时  ████████░░  80%  │
│                                 │
│  "北京时间 14:30 → 真太阳时 14:22"│
│  "修正：西偏北京 -8分钟"         │
│                                 │
└─────────────────────────────────┘

// Step 3: 展示排盘
┌─────────────────────────────────┐
│  你的八字命盘                    │
│  真太阳时：1990年5月15日 14:22   │
├─────────────────────────────────┤
│                                 │
│  时柱    日柱    月柱    年柱    │
│  甲      癸      辛      庚      │
│  申      亥      巳      午      │
│                                 │
│  ──── 十神 ────                 │
│  伤官    —      偏官    正官     │
│  正官   劫财    正财    正财     │
│                                 │
│  ──── 五行分布 ────              │
│  木 ██░░░░░ 10%                 │
│  火 █████░░ 35%  ⚠️ 偏旺        │
│  土 ███░░░░ 20%                 │
│  金 ████░░░ 25%                 │
│  水 ██░░░░░ 10%  ⚠️ 偏弱        │
│                                 │
│  ──── 大运 ────                 │
│  8岁  18岁  28岁  38岁  48岁    │
│  壬戌  癸亥  甲子  乙丑  丙寅   │
│                                 │
├─────────────────────────────────┤
│  确认信息无误？                  │
│  [← 返回修改]  [确认排盘 →]     │
└─────────────────────────────────┘
```

#### Step 4/5 - 问题作答

```
// Step 4: 问题生成中
┌─────────────────────────────────┐
│                                 │
│    🤔 正在根据你的八字           │
│       生成专属问题...            │
│                                 │
│    ████████████░░░░  75%        │
│                                 │
└─────────────────────────────────┘

// Step 5: 逐题展示（Q1）
┌─────────────────────────────────┐
│  问题 1 / 3                     │
│  ████████░░░░░░░░  33%          │
├─────────────────────────────────┤
│                                 │
│  在工作和生活中，                │
│  你通常更接近哪种状态？          │
│                                 │
│  ┌─────────────────────────┐   │
│  │ A  配合他人、执行落实，   │   │
│  │    做好分内的事           │   │
│  └─────────────────────────┘   │
│  ┌─────────────────────────┐   │
│  │ B  独立思考、自己拍板，   │   │
│  │    不太需要别人指导       │   │
│  └─────────────────────────┘   │
│  ┌─────────────────────────┐   │
│  │ C  喜欢表达和创造，      │   │
│  │    有很多想法想输出       │   │
│  └─────────────────────────┘   │
│  ┌─────────────────────────┐   │
│  │ D  顺势而为，环境好就好， │   │
│  │    环境差就调整           │   │
│  └─────────────────────────┘   │
│                                 │
│  选择后自动进入下一题            │
└─────────────────────────────────┘
```

**交互细节**：
- 选择后立即高亮，0.5s 后自动跳转下一题
- 不提供"返回修改"，防止用户反复试探
- 第3题选择后显示"分析中..."过渡动画

#### Step 6/7 - 报告页

```
// Step 6: 流式生成中
┌─────────────────────────────────┐
│  📜 你的命理报告                 │
│  正在生成... 请稍候              │
├─────────────────────────────────┤
│                                 │
│  ✅  整体格局与人生主题           │
│  ─────────────────────────      │
│  你的八字以癸水为日主，生于巳月，  │
│  火旺水弱，官杀透出年时两柱，格   │
│  局偏向官杀混杂...              │
│  █ （光标闪烁，持续输出中）      │
│                                 │
│  ⏳  事业与财运  （等待中）       │
│  ⏳  感情与婚姻  （等待中）       │
│  ⏳  健康与体质  （等待中）       │
│  ⏳  家庭与六亲  （等待中）       │
│  ⏳  财富格局    （等待中）       │
│                                 │
└─────────────────────────────────┘

// Step 7: 报告完整展示
┌─────────────────────────────────┐
│  📜 癸水命主·命理全解            │
│  1990年5月15日  午时生           │
├─────────────────────────────────┤
│  [整体格局] [事业] [感情] [健康] │
│  [家庭] [财富] [喜忌] [建议]    │
│  （Tab切换）                     │
├─────────────────────────────────┤
│                                 │
│  ✨ 整体格局与人生主题            │
│  ─────────────────────────      │
│  你的八字以癸水为日主...（全文）  │
│                                 │
│  💼 事业与财运                   │
│  ─────────────────────────      │
│  ...                            │
│                                 │
│  ─ ─ ─ 喜用神与五行 ─ ─ ─      │
│                                 │
│  喜用：水 🔵  木 🟢             │
│  忌讳：火 🔴  土 🟡             │
│                                 │
│  ─ ─ ─ 推荐饰品 ─ ─ ─          │
│                                 │
│  💧 补水类（首选）               │
│  ┌──────┐ ┌──────┐ ┌──────┐   │
│  │海蓝宝 │ │蓝纹石 │ │黑曜石 │   │
│  │补水气 │ │助运势 │ │辟邪气 │   │
│  └──────┘ └──────┘ └──────┘   │
│                                 │
│  🌿 补木类（次选）               │
│  ┌──────┐ ┌──────┐            │
│  │绿幽灵 │ │翡翠   │            │
│  └──────┘ └──────┘            │
│                                 │
│  ─ ─ ─ 旺命建议 ─ ─ ─         │
│  ✓ 长期居住：城市偏北或偏东区域  │
│  ✓ 幸运颜色：黑色、蓝色、绿色   │
│  ✓ 日常小建议：...              │
│                                 │
├─────────────────────────────────┤
│  [🔗 分享报告]  [💾 保存]       │
└─────────────────────────────────┘
```

---

## 五、第一版验收标准

### 5.1 功能验收（必须全部通过）

#### F1 - 信息输入

```
✅ F1-01  可以正常输入年月日、时分、城市、性别
✅ F1-02  时间选择"不详"时，系统使用子时并在报告中注明
✅ F1-03  城市选择支持全国省会城市 + 直辖市（共约30个）
✅ F1-04  表单未填完整时，提交按钮禁用或提示错误
✅ F1-05  支持 1920-2005 年范围内的出生年份
```

#### F2 - 八字计算

```
✅ F2-01  真太阳时换算结果与人工校验一致（误差 < 1分钟）
✅ F2-02  四柱天干地支排列正确（以5个已知八字为基准测试）
✅ F2-03  五行归属判断正确（天干地支各自对应的五行）
✅ F2-04  十神计算正确（以日主为基准的十神关系）
✅ F2-05  大运起运时间计算正确（顺逆行规则正确）
✅ F2-06  五行力量分值合理（各项之和约等于100）
✅ F2-07  算法初判结果（身强/身弱/中和）在70%案例中与
          有经验命理爱好者判断一致
```

#### F3 - 问题生成与作答

```
✅ F3-01  用户确认排盘后，3个问题在10秒内生成完毕
✅ F3-02  问题语言自然，不出现命理专业术语
✅ F3-03  3个问题覆盖不同维度（性格/经历/行为各一个）
✅ F3-04  每道题有且仅有4个选项
✅ F3-05  选择选项后，0.5秒内自动进入下一题
✅ F3-06  3题全部回答后，自动触发报告生成
✅ F3-07  用户无法返回已作答的题目修改答案
```

#### F4 - 报告生成

```
✅ F4-01  报告以流式方式逐段展示，用户不需要等待全部完成
✅ F4-02  报告包含以下6个章节（内容不为空）：
          - 整体格局与人生主题
          - 事业与财运
          - 感情与婚姻
          - 健康与体质
          - 家庭与六亲
          - 财富格局
✅ F4-03  报告包含喜用神和忌神（各至少1个五行）
✅ F4-04  报告包含饰品推荐（至少2个五行类别，每类至少2种）
✅ F4-05  报告包含居住方位建议
✅ F4-06  报告包含幸运颜色建议
✅ F4-07  报告包含日常生活小建议（至少3条）
✅ F4-08  整个报告从提交回答到完全生成，不超过60秒
```

#### F5 - 流程完整性

```
✅ F5-01  完整走通主流程：输入→排盘→确认→问答→报告
✅ F5-02  每个步骤都有明确的加载状态提示
✅ F5-03  网络错误时有友好提示，不显示技术错误信息
✅ F5-04  报告生成失败时，提供"重新生成"按钮
✅ F5-05  用户使用同一个sessionId刷新页面，不丢失进度
```

### 5.2 数据验收（抽查案例）

```
基准测试案例（使用公开八字案例验证）：

案例1：1984年2月4日 23:00 北京 男
  期望：甲子年、甲寅月、甲子日、壬子时
  验证点：年月交替（立春后换年柱）、时柱计算

案例2：1990年5月15日 14:30 上海 女
  期望：庚午年、辛巳月、癸亥日、甲申时
  验证点：真太阳时修正、五行分布

案例3：2000年2月3日 12:00 成都 男
  期望：验证庚辰年、己丑月（立春前）
  验证点：年柱不随元旦换，以立春为界

案例4：出生时间不详案例
  验证点：系统正确标注"时柱仅供参考"
```

### 5.3 性能验收

```
✅ P1  首页加载时间 < 2秒（FCP）
✅ P2  八字计算响应时间 < 3秒
✅ P3  问题生成时间 < 10秒
✅ P4  报告首个章节开始输出时间 < 5秒
✅ P5  移动端（375px宽）布局正常，可正常使用
```

### 5.4 不在 MVP 范围内（明确排除）

```
❌  用户账号系统（登录/注册）
❌  历史记录保存（关闭页面后丢失）
❌  大运流年详细分析
❌  合婚功能
❌  神煞（桃花、驿马等）详细分析
❌  饰品商城/购买跳转
❌  分享功能（截图/链接分享）
❌  多语言支持
❌  付费墙/会员功能
```

---

## 六、开发优先级与顺序

```
Week 1：
  Day 1-2  │ 八字计算引擎（bazi_engine.py）
            │ 含：真太阳时、农历转换、四柱、十神、大运
  Day 3    │ 计算引擎单元测试（4个基准案例全部通过）
  Day 4-5  │ FastAPI 基础路由 + Session管理

Week 2：
  Day 6-7  │ 前端：信息输入页 + 排盘展示页
  Day 8    │ 前端↔后端联调（F2全部验收通过）
  Day 9-10 │ Claude问题生成 Prompt调优

Week 3：
  Day 11-12│ 报告生成 Prompt + SSE流式输出
  Day 13-14│ 前端：问答页 + 报告页
  Day 15   │ 完整流程联调 + 验收测试
```

---

这份文档可以直接开始开发了。建议第一步从 `bazi_engine.py` 开始写，把计算逻辑做对，其他一切都依赖这个基础。