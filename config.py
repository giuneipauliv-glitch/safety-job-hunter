# -*- coding: utf-8 -*-
"""
安全工程招聘信息聚合 · 全局配置
关键词覆盖安全工程行业全部常见岗位变体（含 EHS/HSE、注安、消防、危化等）
"""

# ============ 搜索关键词（分级：核心词抓更多页，扩展词覆盖变体） ============
# 核心词：岗位基数大，多抓几页
CORE_KEYWORDS = [
    "安全工程师",
    "注册安全工程师",
    "安全员",
    "安全管理",
    "安全生产",
    "安全",
]
# 扩展词：变体/细分方向，每词 1-2 页
EXTRA_KEYWORDS = [
    "EHS", "HSE", "QHSE",
    "安全评价师", "安全总监", "安全主管", "安全经理", "安全主任",
    "安全专员", "安全顾问", "安全专家", "安全技术员", "安全工程师助理",
    "消防工程师", "注册消防工程师", "消防设施操作员", "消防员",
    "职业健康", "环保安全", "安全环保",
    "危化品", "化工安全", "矿山安全", "建筑安全", "施工安全",
    "应急管理", "安全咨询", "安全督查", "注安", "安全生产管理员",
]
KEYWORDS = CORE_KEYWORDS + EXTRA_KEYWORDS

# 每关键词抓取页数（核心词 / 扩展词；1 页约 60 条）
PAGES_CORE = 5
PAGES_EXTRA = 2
PAGES_PER_KEYWORD = 3  # 默认值（--pages 未指定时的兜底）

# 噪声岗位过滤：标题命中排除词且不含“安全工程”字样的岗位丢弃（如网络安全/信息安全）
NOISE_TITLE_WORDS = ["网络", "信息", "数据", "渗透", "攻防", "软件", "Web", "前端",
                     "后端", "算法", "人工智能", "云安全", "区块链", "大数据", "运维"]

# 校招补充关键词（标题含以下词的岗位优先标记校招）
CAMPUS_KEYWORDS = ["校招", "校园招聘", "应届", "2025届", "2026届", "2027届", "毕业生", "管培生"]

# ============ 数据源开关（True=启用） ============
SOURCES = {
    "zhaopin": True,      # 智联招聘主站（社招为主，建议家庭网络跑）
    "iguopin": True,      # 国聘（国企/央企，校招+社招）
    "yjs": True,          # 应届生求职网（校招聚合，SSR 可抓）
    "chern": False,       # 化工英才网（限流严格暂关，待优化）
    "zhaopin_xy": False,  # 智联校招频道（待接入）
}

# 云端 Actions 默认只跑这些源（智联对数据中心 IP 反爬，留本地跑）
CLOUD_SOURCES = "iguopin,yjs"

# ============ 应届生求职网 ============
# 安全科学与工程类专业栏目（按专业聚合校招职位）
YJS_PROFESSION_URL = "https://www.yingjiesheng.com/zhuanye/anquankexue/"
# 备用：按关键词搜索（待验证）
YJS_SEARCH_URL = "https://www.yingjiesheng.com/search?q={kw}"

# ============ 化工英才网 ============
CHERN_SEARCH_URL = "https://www.chenhr.com/job/list/{kw}/"

# ============ 国聘 API ============
IGUOPIN_API = "https://gp-api.iguopin.com/api/jobs/v1/list"
IGUOPIN_HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "Device": "pc",
    "Subsite": "cujiuye",
    "Version": "5.0.0",
}
# nature 取值：校招/社招（值以探测结果为准，探测前先跑全量）
IGUOPIN_NATURE_ALL = []

# 每个关键词抓取的页数（1 页约 60 条，按最新发布）
PAGES_PER_KEYWORD = 2

# 抓取请求间隔（秒），避免触发风控
REQUEST_INTERVAL = (2, 5)

# 请求失败重试次数
MAX_RETRY = 3

# ============ 智联搜索 URL 模板（sm=2 最新发布排序，配合多页抓取覆盖新岗位） ============
ZHAOPIN_SOU_TEMPLATE = "https://www.zhaopin.com/sou/kw{kw}/p{page}?sm=2"

# 排序参数候选（智能匹配/薪酬最高/最新发布），抓取时逐个尝试
SORT_PARAMS = ["", "sm=1", "sm=2"]

# 外派岗图片特征（卡片内有该图标的为外派/驻外岗）
OUTSOURCE_IMG_MARK = "tag_JD_waipai"

# ============ 数据文件路径 ============
DATA_DIR = "data"
JOBS_FILE = "data/jobs.json"
LOG_DIR = "logs"
SITE_DIR = "docs"

# ============ 证书关键词（用于网页高亮"需证"岗位） ============
CERT_KEYWORDS = [
    "注册安全工程师", "注安", "安全评价师", "安评师", "安全员证",
    "安全员资格证", "安全员C", "消防工程师", "消防设施操作员",
    "注册消防", "安全管理资格", "特种作业",
]

# ============ 行业词表（用于识别公司所属行业） ============
INDUSTRY_WORDS = [
    "技术服务", "咨询服务", "石油", "石化", "化工", "检测", "认证",
    "计量", "培训", "教育", "制造", "建筑", "工程", "矿山", "煤炭",
    "电力", "能源", "新能源", "环保", "交通", "物流", "物业", "房地产",
    "医药", "食品", "冶金", "机械", "电子", "通信", "互联网", "咨询",
    "监理", "施工", "设计院", "安环", "应急",
]
