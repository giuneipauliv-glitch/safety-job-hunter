# -*- coding: utf-8 -*-
"""
应届生求职网（yingjiesheng.com）抓取器
- 校招信息聚合站，服务端渲染，GBK 编码
- 按专业栏目抓取：安全科学与工程类
- 列表页字段：公司、职位、地点、信息源、日期（学历/薪资需详情页，暂缺）
"""
import re
import sys
import time
import urllib.request

sys.path.insert(0, '.')
from config import YJS_PROFESSION_URL  # noqa: E402

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')

RE_JOB_LINK = re.compile(r'/job-\d+-\d+-\d+\.html')
RE_DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
SOURCE_WORDS = ['前程无忧', '51job', '高校', '大学', '学院', '人才网', '就业',
                '网申', '公司', '集团', '科技', '招聘网', '事业单位']


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode('gbk', 'ignore')


def parse_list(html: str):
    """GBK HTML -> 原始记录列表"""
    from src.parse import PageParser
    parser = PageParser()
    try:
        parser.feed(html)
    except Exception:
        return []
    tokens = parser.tokens

    records = []
    cur = None
    for tok in tokens:
        if tok[0] == 'link' and RE_JOB_LINK.search(tok[1]):
            # 先关闭已完成的记录（含 title 且 job_links>=2），再处理新链接
            if cur is not None and cur.get('job_links', 0) >= 2 and cur.get('title'):
                records.append(cur)
                cur = None
            if cur is None:
                cur = {'company': tok[2], 'title': '', 'link': tok[1],
                       'texts': [], 'job_links': 1}
            else:
                cur['job_links'] += 1
                if cur['job_links'] == 2:
                    cur['title'] = tok[2]
                    cur['link'] = tok[1]
        elif tok[0] == 'link' and cur is not None:
            cur['texts'].append(tok[2])
        elif tok[0] == 'text' and cur is not None:
            cur['texts'].append(tok[1])
    if cur is not None and cur.get('title'):
        records.append(cur)
    return records


def make_job(rec: dict) -> dict:
    title = rec.get('title') or ''
    if not title or '校园大使' in title or '兼职' in title:
        return None

    texts = [t.strip() for t in rec.get('texts', []) if t and t.strip()]
    location = ''
    source = ''
    date = ''
    for t in texts:
        if not date:
            m = RE_DATE.search(t)
            if m:
                date = m.group(0)
                t = t.replace(m.group(0), '').strip()
                if not t:
                    continue
        if not location and ('[' in t or ',' in t or '，' in t or '全国' in t
                             or re.search(r'[\u4e00-\u9fa5]{2,6}(省|市|区|县)', t)):
            location = t.strip('[]')
            for w in SOURCE_WORDS:
                location = location.replace(w, '')
            location = re.sub(r'\(.*?\)', '', location).strip(' ,，;；')
            continue
        if not source and any(w in t for w in SOURCE_WORDS):
            source = t
            continue
        if not location and t:
            location = t
            for w in SOURCE_WORDS:
                location = location.replace(w, '')
            location = location.strip(' ,，;；')

    # 城市：取地点最后一段（"福建,苏州" -> 苏州；"[全国]" -> 全国）
    city = ''
    if location:
        parts = [p.strip() for p in re.split(r'[,，;；]', location) if p.strip()]
        city = parts[-1] if parts else location
        for w in SOURCE_WORDS:
            city = city.replace(w, '')
        city = re.sub(r'\(.*?\)', '', city).strip()

    job_type = '实习' if any(k in title for k in ('实习', '兼职')) else '校招'
    from src.fetch import is_noise_title
    if is_noise_title(title):
        return None

    item = {
        'job_id': 'yjs_' + re.sub(r'\D', '', rec['link'])[-20:],
        'title': title,
        'salary': None,
        'salary_text': '',
        'education': '',
        'edu_level': -1,
        'experience': '',
        'exp_level': 0,
        'location': location,
        'city': city,
        'district': '',
        'company': rec.get('company') or '',
        'company_url': '',
        'company_type': '',
        'company_size': '',
        'industry': '',
        'tags': [s for s in (source, date) if s],
        'link': 'https://www.yingjiesheng.com' + rec['link'],
        'outsource': False,
        'source': 'yjs',
        'job_type': job_type,
        'keyword': '专业栏目',
        'publish_date': date,
    }
    from config import CERT_KEYWORDS
    all_t = ' '.join([title, item['company'], ' '.join(item['tags'])])
    item['has_cert'] = any(k in all_t for k in CERT_KEYWORDS)
    return item


def fetch(pages: int = 1, progress=None) -> list:
    """抓取安全科学与工程类专业栏目（可扩展城市子页）"""
    results = []
    url = YJS_PROFESSION_URL
    try:
        html = fetch_html(url)
    except Exception as e:
        if progress:
            progress(f'[应届生网] 请求失败: {e}')
        return results
    for rec in parse_list(html):
        job = make_job(rec)
        if job:
            results.append(job)
    if progress:
        progress(f'[应届生网] 专业栏目抓到 {len(results)} 条')
    return results
