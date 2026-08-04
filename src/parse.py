# -*- coding: utf-8 -*-
"""
智联招聘搜索页 HTML 解析器
策略：不依赖具体 CSS class（页面改版不易碎），而是：
  1. html.parser 把整页转成 token 流（text / link / img）
  2. 按 jobdetail 链接切分为岗位卡片
  3. 用正则对卡片内文本分类提取字段
"""
import re
import sys
from html.parser import HTMLParser

sys.path.insert(0, '.')
from config import OUTSOURCE_IMG_MARK, INDUSTRY_WORDS  # noqa: E402

# ---------- 正则常量 ----------
RE_SALARY = re.compile(r'([\d.]+)\s*[-~—至]\s*([\d.]+)\s*(万|千|k|K)?\s*元?\s*(/月|/年|每月|每年)?')
RE_EDU = re.compile(r'博士|硕士|本科|大专|中专|高中|学历不限|初中')
RE_EXP = re.compile(r'经验不限|应届生|在校生|\d+\s*[-~]\s*\d+\s*年|\d+\s*年以上|\d+\s*年以下')
RE_LOCATION = re.compile(r'^[\u4e00-\u9fa5]{2,12}(?:·[\u4e00-\u9fa5]{1,12}){1,3}$')
RE_COMPANY_TYPE = re.compile(r'民营|国企|股份制企业|外商独资|中外合资|合资|事业单位|集体企业|其它|其他')
RE_COMPANY_SIZE = re.compile(r'(\d+)\s*[-~]\s*(\d+)\s*人|(\d+)\s*人以下|(\d+)\s*人以上')
RE_JOB_ID = re.compile(r'jobdetail/([A-Z0-9]+)\.htm')

EDU_LEVEL = {'博士': 6, '硕士': 5, '本科': 4, '大专': 3, '中专': 2, '高中': 1, '学历不限': 0, '初中': 0}
EXP_LEVEL = {'经验不限': 0, '应届生': 1, '在校生': 0}


class PageParser(HTMLParser):
    """把 HTML 转成 token 流"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tokens = []
        self._a_stack = []   # [(href, [texts])]
        self._skip = 0       # script/style 嵌套深度

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript'):
            self._skip += 1
        if self._skip:
            return
        d = dict(attrs)
        if tag == 'a':
            self._a_stack.append((d.get('href', ''), []))
        elif tag == 'img':
            src = d.get('src', '') or d.get('data-src', '')
            if src:
                self.tokens.append(('img', src))

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript'):
            self._skip = max(0, self._skip - 1)
            return
        if self._skip:
            return
        if tag == 'a' and self._a_stack:
            href, texts = self._a_stack.pop()
            t = ''.join(texts).strip()
            self.tokens.append(('link', href, t))

    def handle_data(self, data):
        if self._skip:
            return
        if self._a_stack:
            self._a_stack[-1][1].append(data)
        else:
            t = data.strip()
            if t:
                self.tokens.append(('text', t))


def parse_page(html: str) -> list:
    """HTML -> 岗位字典列表"""
    parser = PageParser()
    try:
        parser.feed(html)
    except Exception:
        return []
    tokens = parser.tokens

    # 按 jobdetail 链接切卡片：
    #   卡片 = 从上一个 jobdetail 链接(含) 到下一个 jobdetail 链接(不含) 的全部 token
    #   img（如外派图标）一律先进 pending，归入它之后出现的岗位，避免错位
    cards = []
    cur = None
    cur_href = ''
    pending = []
    for tok in tokens:
        if tok[0] == 'link' and 'jobdetail/' in tok[1]:
            if cur is not None:
                cards.append({'tokens': cur, 'href': cur_href})
            cur = pending + [tok]
            cur_href = tok[1]
            pending = []
        elif tok[0] == 'img':
            pending.append(tok)   # 待归属图标
        elif cur is not None:
            cur.append(tok)
    if cur is not None:
        cards.append({'tokens': cur, 'href': cur_href})

    jobs = []
    for card in cards:
        job = extract_card(card)
        if job.get('title'):
            jobs.append(job)
    return jobs


def extract_card(card: dict) -> dict:
    """从单卡片 token 流提取字段
    按公司链接位置分前后：岗位信息在 pre，公司性质/规模/行业在 post
    """
    toks = card['tokens']
    job = {
        'job_id': '',
        'title': '',
        'salary': None,       # (min, max) 元/月
        'salary_text': '',
        'education': '',
        'edu_level': -1,
        'experience': '',
        'exp_level': -1,
        'location': '',
        'city': '',
        'district': '',
        'company': '',
        'company_url': '',
        'company_type': '',
        'company_size': '',
        'industry': '',
        'tags': [],
        'link': card.get('href', ''),
        'outsource': False,
        'has_cert': False,
    }

    m = RE_JOB_ID.search(card.get('href', ''))
    if m:
        job['job_id'] = m.group(1)

    pre_texts, post_texts = [], []
    seen_company = False
    for tok in toks:
        if tok[0] == 'img':
            if OUTSOURCE_IMG_MARK in tok[1]:
                job['outsource'] = True
        elif tok[0] == 'link':
            href, text = tok[1], tok[2]
            if 'jobdetail/' in href and not job['title']:
                job['title'] = text
            elif 'companydetail' in href and text:
                job['company'] = text
                job['company_url'] = href
                seen_company = True
            elif text:
                (post_texts if seen_company else pre_texts).append(text)
        elif tok[0] == 'text':
            (post_texts if seen_company else pre_texts).append(tok[1])

    # ---- pre：薪资 / 学历 / 经验 / 地点 / 要求标签 ----
    for t in pre_texts:
        t = t.strip()
        if not t:
            continue
        if not job['salary_text']:
            ns = normalize_salary(t)
            if ns:
                job['salary'] = ns
                job['salary_text'] = t
                continue
        if not job['education']:
            m = RE_EDU.search(t)
            if m and len(t) <= 8:
                job['education'] = m.group(0)
                job['edu_level'] = EDU_LEVEL.get(m.group(0), -1)
                continue
        if not job['experience']:
            m = RE_EXP.search(t)
            if m and len(t) <= 10:
                job['experience'] = m.group(0)
                job['exp_level'] = parse_exp_level(m.group(0))
                continue
        if not job['location'] and RE_LOCATION.match(t):
            job['location'] = t
            parts = t.split('·')
            job['city'] = parts[0]
            job['district'] = parts[1] if len(parts) > 1 else ''
            continue
        # 其余短文本归为要求标签
        if len(t) <= 30 and t not in pre_texts[:pre_texts.index(t)]:
            job['tags'].append(t)

    # ---- post：公司性质 / 规模 / 行业 ----
    for t in post_texts:
        t = t.strip()
        if not t:
            continue
        if not job['company_type'] and RE_COMPANY_TYPE.search(t) and len(t) <= 8:
            job['company_type'] = t
            continue
        if not job['company_size'] and RE_COMPANY_SIZE.search(t) and len(t) <= 10:
            job['company_size'] = t
            continue
        if not job['industry']:
            for w in INDUSTRY_WORDS:
                if w in t and len(t) <= 12:
                    job['industry'] = t
                    break
            if job['industry']:
                continue

    # 去重标签
    seen = set()
    uniq_tags = []
    for t in job['tags']:
        if t not in seen:
            seen.add(t)
            uniq_tags.append(t)
    job['tags'] = uniq_tags

    # 证书要求检测
    from config import CERT_KEYWORDS
    all_text = ' '.join([job['title'], job['company'], ' '.join(job['tags'])])
    job['has_cert'] = any(k in all_text for k in CERT_KEYWORDS)
    return job


def normalize_salary(text: str):
    """'8000-16000元' '1-1.5万' '6-8千/月' '10-20万/年' -> (min, max) 元/月"""
    if not text or '面议' in text:
        return None
    m = RE_SALARY.search(text)
    if not m:
        return None
    lo, hi = float(m.group(1)), float(m.group(2))
    unit = m.group(3) or ''
    if unit in ('万',):
        lo, hi = lo * 10000, hi * 10000
    elif unit in ('千', 'k', 'K'):
        lo, hi = lo * 1000, hi * 1000
    if '年' in text:
        lo, hi = lo / 12, hi / 12
    return round(lo), round(hi)


def parse_exp_level(text: str) -> int:
    m = re.search(r'(\d+)\s*[-~]\s*(\d+)\s*年', text)
    if m:
        years = (int(m.group(1)) + int(m.group(2))) / 2
        if years <= 1:
            return 1
        if years <= 3:
            return 2
        if years <= 5:
            return 3
        if years <= 10:
            return 4
        return 5
    if '应届' in text:
        return 1
    if '不限' in text:
        return 0
    if '以上' in text:
        m2 = re.search(r'(\d+)\s*年以上', text)
        if m2:
            y = int(m2.group(1))
            return 5 if y >= 10 else (4 if y >= 5 else 3)
        return 3
    return 0


def salary_text_friendly(salary_text: str) -> str:
    """薪资文本加粗美化：'8000-16000元' -> '8k-16k'"""
    ns = normalize_salary(salary_text)
    if not ns:
        return salary_text or '面议'
    lo, hi = ns
    if lo >= 10000 and hi >= 10000:
        return f'{lo/10000:.1f}万-{hi/10000:.1f}万'.replace('.0万', '万')
    return f'{lo//1000}k-{hi//1000}k'
