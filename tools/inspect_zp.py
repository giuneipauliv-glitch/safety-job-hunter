# -*- coding: utf-8 -*-
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open(r'E:\work space\safety-job-hunter\data\jobs.json', encoding='utf-8'))
jobs = d['jobs']
zp = [j for j in jobs if j.get('source') == 'zhaopin']
print('智联岗位数:', len(zp))
print('--- 抽样 8 条 ---')
for j in zp[:8]:
    print(' | '.join([
        f"[{j['job_type']}]",
        j['title'][:18],
        j['company'][:16],
        j['city'],
        j['salary_text'],
        '学历' + (j['education'] or '?'),
        '经验' + (j['experience'] or '?'),
        '外派' if j['outsource'] else '',
    ]))
