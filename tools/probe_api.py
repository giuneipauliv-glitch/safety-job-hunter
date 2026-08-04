# -*- coding: utf-8 -*-
"""探测多数据源 API 通道：智联 POST 接口 / 国聘 API"""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')


def post_json(url, data, headers):
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'),
                                 headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'ignore')[:800]
    except Exception as e:
        return None, str(e)[:300]


print('===== 1. 智联 fe-api search/positions (POST) =====')
zp_body = {
    'p': 1, 'pageSize': 20, 'cityId': 0, 'kw': '安全工程师', 'kt': 3,
    'bt': '', 'we': -1, 'jt': -1, 'sl': -1, 'el': -1, 'cq': -1,
    'workExperience': -1, 'education': -1, 'companyType': -1,
    'employmentType': -1, 'jobWelfareTag': -1, 'sort': 0, 'netTag': '3.1',
}
zp_headers = {
    'Content-Type': 'application/json;charset=UTF-8',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': UA,
    'Referer': 'https://www.zhaopin.com/',
}
code, body = post_json('https://fe-api.zhaopin.com/c/i/search/positions', zp_body, zp_headers)
print('status:', code)
if body and body.startswith('{'):
    d = json.loads(body)
    results = d.get('data', {}).get('results') or d.get('data', {}).get('list') or []
    print('code:', d.get('code'), '| results:', len(results))
    if results:
        r = results[0]
        print('sample keys:', sorted(r.keys())[:20])
        print('sample title:', r.get('name') or r.get('jobName'))
else:
    print('raw head:', body[:300])

print()
print('===== 2. 国聘 gp-api jobs/v1/list (POST, cujiuye 子站) =====')
gp_body = {'page': 1, 'page_size': 20, 'keyword': '安全工程师', 'nature': ['115xW5oQ']}
gp_headers = {
    'Content-Type': 'application/json;charset=UTF-8',
    'Accept': 'application/json, text/plain, */*',
    'Device': 'pc', 'Subsite': 'cujiuye', 'Version': '5.0.0',
    'User-Agent': UA,
}
code, body = post_json('https://gp-api.iguopin.com/api/jobs/v1/list', gp_body, gp_headers)
print('status:', code)
if body and body.startswith('{'):
    d = json.loads(body)
    print('code:', d.get('code'), '| msg:', d.get('msg') or d.get('message'))
    lst = (d.get('data') or {}).get('list') or []
    print('list len:', len(lst))
    if lst:
        r = lst[0]
        print('sample keys:', sorted(r.keys())[:25])
        print('sample job_name:', r.get('job_name'))
else:
    print('raw head:', body[:300])

print()
print('===== 3. 国聘主站 API（Subsite=www 或空） =====')
for subsite in ['', 'www']:
    h = dict(gp_headers)
    h['Subsite'] = subsite if subsite else 'cujiuye'
    code, body = post_json('https://gp-api.iguopin.com/api/jobs/v1/list', gp_body, h)
    print(f'subsite={subsite!r}: status={code} head={body[:150]}')
