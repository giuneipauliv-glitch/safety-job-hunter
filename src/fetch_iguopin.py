# -*- coding: utf-8 -*-
"""
国聘（国资央企招聘平台）抓取器
- 优先：POST JSON API https://gp-api.iguopin.com/api/jobs/v1/list（已验证可用）
- 降级：Playwright 浏览器内 fetch（真实浏览器环境，绕过 CORS/风控）
返回统一岗位 schema（见 make_job）
"""
import json
import sys
import time
import urllib.request

sys.path.insert(0, '.')
from config import IGUOPIN_API, IGUOPIN_HEADERS  # noqa: E402

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')

JOB_DETAIL_URL = 'https://www.iguopin.com/job/detail?id={job_id}'


def _post(url, data, headers):
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'),
                                 headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8', 'ignore')


def _area_cn(raw):
    """district_list -> (地点文本, 城市, 区)"""
    try:
        areas = raw or []
        for a in areas:
            cn = str(a.get('area_cn') or '')
            if not cn or cn == '中国':
                continue
            parts = cn.replace(' - ', '-').split('-')
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) >= 2:
                # 省-市-区 / 城市-区
                city = parts[-2]
                district = parts[-1]
            else:
                # 单独城市/国家/地区
                city = parts[0]
                district = ''
            return cn, city, district
        return '中国', '', ''
    except Exception:
        return '', '', ''


# 国聘关键词为模糊匹配，用标题相关性过滤无关岗位
TITLE_RELEVANCE = ['安全', 'EHS', 'HSE', 'QHSE', '消防', '应急', '危化', '环保',
                   '职业健康', '注安', '安监', '安环', '隐患', '防护']


def make_job(raw: dict, keyword: str) -> dict:
    """国聘 API 原始记录 -> 统一岗位 schema"""
    job_id = str(raw.get('job_id') or '')
    if not job_id:
        return None
    title = str(raw.get('job_name') or '')
    if not title:
        return None
    # 标题相关性过滤（国聘模糊匹配会带出无关技术岗）
    if not any(k in title for k in TITLE_RELEVANCE):
        return None
    # 网络安全/IT 岗过滤
    from src.fetch import is_noise_title
    if is_noise_title(title):
        return None

    # 薪资（元/月）
    min_wage = raw.get('min_wage') or 0
    max_wage = raw.get('max_wage') or 0
    negotiable = bool(raw.get('is_negotiable'))
    if negotiable or (min_wage <= 0 and max_wage <= 0):
        salary = None
        salary_text = '面议'
    else:
        salary = (int(min_wage), int(max_wage) if max_wage >= min_wage else int(min_wage))
        salary_text = f'{min_wage}-{max_wage}元/月'

    edu = str(raw.get('education_cn') or '')
    exp = str(raw.get('experience_cn') or '')
    loc, city, district = _area_cn(raw.get('district_list'))

    company_info = raw.get('company_info') or {}
    company = str(raw.get('company_name') or company_info.get('name') or '')
    dep = str(raw.get('department_cn') or '')
    if dep and dep != company:
        dep_note = f'（{dep}）'
    else:
        dep_note = ''

    tags = []
    for k in ('job_tags_cn', 'job_custom_tags_cn'):
        v = raw.get(k) or []
        if isinstance(v, list):
            tags.extend(str(t) for t in v if t)
    tags = list(dict.fromkeys(tags))[:12]

    recruitment_type = str(raw.get('recruitment_type_cn') or raw.get('nature_cn') or '')
    if '校园' in recruitment_type or '校招' in recruitment_type:
        job_type = '校招'
    elif '实习' in recruitment_type:
        job_type = '实习'
    elif '社会' in recruitment_type or '社招' in recruitment_type:
        job_type = '社招'
    else:
        job_type = '校招' if raw.get('is_graduates') else '未知'

    from src.parse import normalize_salary, parse_exp_level, EDU_LEVEL

    item = {
        'job_id': f'gp_{job_id}',
        'title': title,
        'salary': salary,
        'salary_text': salary_text,
        'education': edu,
        'edu_level': EDU_LEVEL.get(edu, -1),
        'experience': exp,
        'exp_level': parse_exp_level(exp) if exp else 0,
        'location': loc,
        'city': city,
        'district': district,
        'company': company + dep_note,
        'company_url': '',
        'company_type': str(company_info.get('nature_cn') or ''),
        'company_size': str(company_info.get('scale_cn') or ''),
        'industry': str(company_info.get('industry_cn') or ''),
        'tags': tags,
        'link': JOB_DETAIL_URL.format(job_id=job_id),
        'outsource': False,
        'source': 'iguopin',
        'job_type': job_type,
        'keyword': keyword,
        'end_time': str(raw.get('end_time') or '')[:10],
    }
    from config import CERT_KEYWORDS
    all_t = ' '.join([title, company, ' '.join(tags)])
    item['has_cert'] = any(k in all_t for k in CERT_KEYWORDS)
    return item


def _parse_response(body: str):
    d = json.loads(body)
    data = d.get('data') or {}
    return data.get('list') or [], data.get('total') or 0


def fetch_api(keywords: list, pages: int = 1, nature: list = None,
              progress=None) -> list:
    """urllib 直连 API"""
    results = []
    for kw in keywords:
        for page in range(1, pages + 1):
            body = {'page': page, 'page_size': 100, 'keyword': kw}
            if nature:
                body['nature'] = nature
            try:
                resp = _post(IGUOPIN_API, body, {**IGUOPIN_HEADERS, 'User-Agent': UA})
                lst, total = _parse_response(resp)
            except Exception as e:
                if progress:
                    progress(f'[国聘 {kw} p{page}] 请求失败: {e}')
                return results  # API 失败即整体降级
            for r in lst:
                job = make_job(r, kw)
                if job:
                    results.append(job)
            if progress:
                progress(f'[国聘 {kw} p{page}] {len(lst)} 条（共 {total}）')
            time.sleep(0.8)
    return results


def fetch_playwright(keywords: list, pages: int = 1, progress=None) -> list:
    """浏览器内 fetch 兜底（API 被 token/风控拦截时）"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []
    script = """
    async (kw, page) => {
      const body = {page: page, page_size: 100, keyword: kw};
      const resp = await fetch('https://gp-api.iguopin.com/api/jobs/v1/list', {
        method: 'POST',
        headers: {'Content-Type': 'application/json;charset=UTF-8',
                  'Device': 'pc', 'Subsite': 'cujiuye', 'Version': '5.0.0'},
        body: JSON.stringify(body)
      });
      const d = await resp.json();
      return JSON.stringify(d.data ? d.data.list : []);
    }
    """
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        page = browser.new_page(user_agent=UA)
        try:
            page.goto('https://www.iguopin.com/', wait_until='domcontentloaded', timeout=45000)
            page.wait_for_timeout(3000)
        except Exception:
            pass
        for kw in keywords:
            for p in range(1, pages + 1):
                try:
                    out = page.evaluate(script, kw, p)
                    lst = json.loads(out)
                except Exception as e:
                    if progress:
                        progress(f'[国聘PW {kw} p{p}] 失败: {e}')
                    continue
                for r in lst:
                    job = make_job(r, kw)
                    if job:
                        results.append(job)
                if progress:
                    progress(f'[国聘PW {kw} p{p}] {len(lst)} 条')
                time.sleep(1)
        browser.close()
    return results


def fetch(keywords: list, pages: int = 1, nature: list = None, progress=None) -> list:
    """国聘入口：先 API 直连，失败降级浏览器"""
    got = fetch_api(keywords, pages, nature, progress)
    if got:
        return got
    if progress:
        progress('[国聘] API 直连失败，降级浏览器通道')
    return fetch_playwright(keywords, pages, progress)
