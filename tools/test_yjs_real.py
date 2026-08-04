# -*- coding: utf-8 -*-
"""真实抓取应届生求职网安全类专业栏目，验证解析"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fetch_yjs import fetch  # noqa: E402

jobs = fetch(progress=lambda m: print(m))
print('=' * 40)
print('抓到:', len(jobs))
for j in jobs[:12]:
    print(' | '.join([
        f"[{j['job_type']}]", j['title'][:20], j['company'][:16],
        j['city'] or '?', '发布日期:' + (j.get('publish_date') or ''),
        '源:' + ','.join(j['tags'])[:14],
    ]))
