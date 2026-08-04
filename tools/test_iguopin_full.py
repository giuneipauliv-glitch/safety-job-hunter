# -*- coding: utf-8 -*-
"""国聘全量抓取测试：22 关键词 × 1 页，验证过滤效果"""
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import KEYWORDS  # noqa: E402
from src.fetch_iguopin import fetch  # noqa: E402

jobs = fetch(KEYWORDS, 1, nature=None, progress=lambda m: print('  ' + m))
print('=' * 50)
print('抓取总数:', len(jobs))
print('job_type:', dict(collections.Counter(j['job_type'] for j in jobs)))
print('来源:', dict(collections.Counter(j['source'] for j in jobs)))
print('关键词命中分布:', dict(collections.Counter(j['keyword'] for j in jobs).most_common(10)))
print('has_cert:', sum(1 for j in jobs if j['has_cert']))
print('--- 抽样 15 条 ---')
for j in jobs[:15]:
    print(' | '.join([
        f"[{j['job_type']}]", j['title'], j['company'][:20],
        j['city'] or '全国', j['salary_text'], '学历' + j['education'],
        '经验' + j['experience'], '截止' + (j.get('end_time') or ''),
    ]))
