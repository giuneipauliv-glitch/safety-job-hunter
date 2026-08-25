# -*- coding: utf-8 -*-
"""智联校招抓取器单关键词测试"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fetch_zhaopin_xy import fetch  # noqa: E402

jobs = fetch(['安全工程师'], pages=1, progress=lambda m: print(m))
print('=' * 40)
print('总条数:', len(jobs))
for j in jobs[:10]:
    print(' | '.join([
        j['title'][:22],
        j['company'][:14],
        j['city'],
        '学历' + (j['education'] or '?'),
        '截止' + (j.get('end_time') or ''),
        ','.join(j['tags'][:2]),
    ]))
