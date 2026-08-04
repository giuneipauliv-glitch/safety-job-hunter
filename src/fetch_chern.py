# -*- coding: utf-8 -*-
"""
化工英才网（chenhr.com）抓取器
- 化工行业垂直平台，安环岗位专区最集中
- 列表页 JS 渲染，需要 Playwright；站点有频率限制（429），慢速+容错
- 列表页字段：职位、公司、地点、薪资、学历、经验（GBK 编码）
"""
import re
import sys
import time

sys.path.insert(0, '.')
from config import CHERN_SEARCH_URL, CORE_KEYWORDS, EXTRA_KEYWORDS  # noqa: E402

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')


def fetch_with_playwright(url: str, timeout: int = 40000) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    with sync_playwright() as pw:
        browser = None
        try:
            browser = pw.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
            ctx = browser.new_context(user_agent=UA, locale='zh-CN')
            page = ctx.new_page()
            page.goto(url, wait_until='domcontentloaded', timeout=timeout)
            page.wait_for_timeout(5000)
            html = page.content()
            browser.close()
            return html
        except Exception:
            try:
                if browser:
                    browser.close()
            except Exception:
                pass
            return None


def parse_list(html: str):
    """GBK HTML -> 原始记录列表（文本流解析）"""
    from src.parse import PageParser
    parser = PageParser()
    try:
        parser.feed(html)
    except Exception:
        return []
    tokens = parser.tokens

    # 职位链接模式：/job/xxx.html 或 /job/S45UR.html
    records = []
    cur = None
    for tok in tokens:
        if tok[0] == 'link':
            href, text = tok[1], tok[2]
            if re.search(r'/job/\w+\.html', href):
                if cur is None:
                    cur = {'title': text, 'link': href, 'texts': []}
                elif cur.get('texts'):
                    # 新的职位卡片开始
                    records.append(cur)
                    cur = {'title': text, 'link': href, 'texts': []}
            elif cur is not None and text:
                cur['texts'].append(text)
        elif tok[0] == 'text' and cur is not None:
            cur['texts'].append(tok[1])
    if cur is not None:
        records.append(cur)
    return records


def make_job(rec: dict, keyword: str) -> dict:
    title = rec.get('title') or ''
    if not title:
        return None
    from src.fetch import is_noise_title
    if is_noise_title(title):
        return None

    texts = [t.strip() for t in rec.get('texts', []) if t and t.strip()]
    salary_text = ''
    education = ''
    experience = ''
    location = ''
    company = ''
    company_type = ''
    for t in texts:
        if not salary_text and re.search(r'[\d.]+[千万元]?\s*[-~]\s*[\d.]+[千万元]?', t):
            salary_text = t
            continue
        if not education and t in ('学历不限', '不限', '中专', '高中', '大专', '本科', '硕士', '博士'):
            education = t
            continue
        if not experience and re.search(r'\d+\s*年|经验不限|应届', t):
            experience = t
            continue
        if not location and ('省' in t or '市' in t or t.endswith('区') or t.endswith('县')):
            location = t
            continue
        if not company and re.search(r'(公司|集团|厂|院|所|中心|部)$', t) and len(t) >= 4:
            company = t
            continue
        if not company_type and t in ('民营', '国企', '外商独资', '股份制', '合资', '事业单位'):
            company_type = t
            continue

    from src.parse import normalize_salary, parse_exp_level, EDU_LEVEL
    item = {
        'job_id': 'ch_' + re.sub(r'\D', '', rec['link'])[-18:],
        'title': title,
        'salary': normalize_salary(salary_text),
        'salary_text': salary_text,
        'education': education,
        'edu_level': EDU_LEVEL.get(education, -1),
        'experience': experience,
        'exp_level': parse_exp_level(experience) if experience else 0,
        'location': location,
        'city': location.replace('省', '省·').split('·')[0] if location else '',
        'district': '',
        'company': company,
        'company_url': '',
        'company_type': company_type,
        'company_size': '',
        'industry': '化工',
        'tags': [],
        'link': 'https://www.chenhr.com' + rec['link'],
        'outsource': False,
        'source': 'chern',
        'job_type': '社招',
        'keyword': keyword,
    }
    from config import CERT_KEYWORDS
    all_t = ' '.join([title, company])
    item['has_cert'] = any(k in all_t for k in CERT_KEYWORDS)
    return item


def fetch(keywords: list = None, pages: int = 1, progress=None) -> list:
    """按关键词搜索抓取（慢速 + 容错）"""
    kws = keywords or (CORE_KEYWORDS + EXTRA_KEYWORDS)[:8]  # 化工站默认抓核心词，控制总量
    results = []
    for kw in kws:
        url = CHERN_SEARCH_URL.format(kw=__import__('urllib.parse', fromlist=['quote']).quote(kw))
        html = fetch_with_playwright(url)
        if not html:
            if progress:
                progress(f'[化工英才网 {kw}] 失败（JS渲染或限流）')
            continue
        n = 0
        for rec in parse_list(html):
            job = make_job(rec, kw)
            if job:
                results.append(job)
                n += 1
        if progress:
            progress(f'[化工英才网 {kw}] {n} 条')
        time.sleep(4)  # 限流保护
    return results
