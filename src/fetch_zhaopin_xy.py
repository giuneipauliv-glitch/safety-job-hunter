# -*- coding: utf-8 -*-
"""
智联校招频道（xiaoyuan.zhaopin.com）抓取器
- 需要登录态（本地 zp-profile），仅本地运行
- 解析 window.__INITIAL_DATA__ 内嵌 JSON
- 字段：职位/公司/城市/学历/报名截止/行业/规模
"""
import json
import re
import sys
import time

sys.path.insert(0, '.')
from config import CORE_KEYWORDS  # noqa: E402

SEARCH_URL = ('https://xiaoyuan.zhaopin.com/search/index?jn=2&kw={kw}&page={page}')
DETAIL_URL = 'https://m.zhaopin.com/xiaoyuan/position/detail?id={number}'


def fetch_list(kw: str, page: int, progress=None):
    """抓取一页校招职位，返回原始记录列表"""
    from src.fetch import fetch_chrome_dump
    url = SEARCH_URL.format(kw=__import__('urllib.parse', fromlist=['quote']).quote(kw), page=page)
    html = fetch_chrome_dump(url, timeout=90)
    if not html:
        if progress:
            progress(f'[智联校招 {kw} p{page}] 抓取失败')
        return []
    m = re.search(r'window\.__INITIAL_DATA__\s*=\s*(\{.*?\})\s*</script>', html, re.S)
    if not m:
        if progress:
            progress(f'[智联校招 {kw} p{page}] 未找到数据（可能未登录）')
        return []
    try:
        data = json.loads(m.group(1))
        lst = data.get('position', {}).get('positionState', {}).get('list', [])
        return lst
    except Exception as e:
        if progress:
            progress(f'[智联校招 {kw} p{page}] 解析失败: {e}')
        return []


def ts_to_date(ts):
    """毫秒时间戳 -> YYYY-MM-DD"""
    if not ts:
        return ''
    try:
        import datetime
        return datetime.datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')
    except Exception:
        return ''


def make_job(raw: dict, kw: str) -> dict:
    from src.fetch import is_noise_title
    from src.parse import EDU_LEVEL

    number = str(raw.get('number') or '')
    name = str(raw.get('name') or '')
    if not number or not name:
        return None
    if is_noise_title(name):
        return None

    edu = str(raw.get('education') or '')
    city = str(raw.get('cityDistrict') or '')
    if not city:
        camp = raw.get('campusJobDetail') or {}
        city = str(camp.get('cityName') or '')

    tags = []
    for t in (raw.get('campusTags') or []):
        lbl = t.get('label')
        if lbl:
            tags.append(str(lbl))
    for c in (raw.get('commercialLabel') or []):
        tn = c.get('typeName')
        if tn:
            tags.append(str(tn))

    # 薪资（校招多为面议）
    salary_text = ''
    for key in ('salaryText', 'salary', 'salaryRange', 'salaryDesc'):
        v = raw.get(key)
        if isinstance(v, str) and v:
            salary_text = v
            break
    from src.parse import normalize_salary
    salary = normalize_salary(salary_text)

    camp = raw.get('campusJobDetail') or {}
    end_ts = camp.get('applyEndTime') or raw.get('applyEndTime')
    item = {
        'job_id': f'xy_{number}',
        'title': name,
        'salary': salary,
        'salary_text': salary_text,
        'education': edu,
        'edu_level': EDU_LEVEL.get(edu, -1),
        'experience': '',
        'exp_level': 0,
        'location': city,
        'city': city,
        'district': '',
        'company': str(camp.get('companyName') or raw.get('companyName') or ''),
        'company_url': str(raw.get('companyUrl') or ''),
        'company_type': str(camp.get('orgTypeName') or ''),
        'company_size': str(camp.get('orgSizeName') or raw.get('companySize') or ''),
        'industry': str(camp.get('industryName') or raw.get('industryName') or ''),
        'tags': tags,
        'link': DETAIL_URL.format(number=number),
        'outsource': False,
        'source': 'zhaopin_xy',
        'job_type': '校招',
        'keyword': kw,
        'end_time': ts_to_date(end_ts),
    }
    from config import CERT_KEYWORDS
    all_t = ' '.join([name, item['company'], ' '.join(tags)])
    item['has_cert'] = any(k in all_t for k in CERT_KEYWORDS)
    return item


def fetch(keywords: list = None, pages: int = 2, progress=None) -> list:
    kws = keywords or CORE_KEYWORDS
    results = []
    for kw in kws:
        for page in range(1, pages + 1):
            raw_list = fetch_list(kw, page, progress)
            for raw in raw_list:
                job = make_job(raw, kw)
                if job:
                    results.append(job)
            if progress:
                progress(f'[智联校招 {kw} p{page}] 原始 {len(raw_list)} 条')
            time.sleep(2)
    return results
