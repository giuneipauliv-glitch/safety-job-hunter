# -*- coding: utf-8 -*-
import json
import sys
import collections

sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open(r'E:\work space\safety-job-hunter\data\jobs.json', encoding='utf-8'))
jobs = d['jobs']
print('total:', len(jobs))
print('job_type:', dict(collections.Counter(j['job_type'] for j in jobs)))
print('source:', dict(collections.Counter(j['source'] for j in jobs)))
print('has_cert:', sum(1 for j in jobs if j['has_cert']))
print('有薪资:', sum(1 for j in jobs if j['salary']), '/ 面议:', sum(1 for j in jobs if j['salary_text'] == '面议'))
print('有end_time:', sum(1 for j in jobs if j.get('end_time')))
print('--- 抽样 8 条 ---')
for j in jobs[:8]:
    print(' | '.join([
        f"[{j['job_type']}|{j['source']}]",
        j['title'],
        j['company'][:24],
        j['city'] or '全国',
        j['salary_text'],
        '学历' + j['education'],
        '经验' + j['experience'],
        '截止' + (j.get('end_time') or ''),
        'tags=' + ','.join(j['tags'][:4]),
    ]))
