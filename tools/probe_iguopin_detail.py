# -*- coding: utf-8 -*-
"""查看国聘 API 单条完整记录结构，确定字段映射"""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

req = urllib.request.Request(
    'https://gp-api.iguopin.com/api/jobs/v1/list',
    data=json.dumps({'page': 1, 'page_size': 3, 'keyword': '安全工程师',
                     'nature': ['115xW5oQ']}).encode('utf-8'),
    headers={
        'Content-Type': 'application/json;charset=UTF-8',
        'Device': 'pc', 'Subsite': 'cujiuye', 'Version': '5.0.0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0',
    },
    method='POST',
)
with urllib.request.urlopen(req, timeout=30) as resp:
    d = json.loads(resp.read().decode('utf-8', 'ignore'))

lst = d['data']['list']
print('total:', d['data']['total'], '| got:', len(lst))
for i, r in enumerate(lst):
    print(f'--- 记录 {i} ---')
    for k, v in r.items():
        if isinstance(v, (dict, list)):
            print(f'  {k}: {json.dumps(v, ensure_ascii=False)[:220]}')
        else:
            print(f'  {k}: {v}')
