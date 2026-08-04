# -*- coding: utf-8 -*-
"""单独上传 .github/workflows/update.yml，打印完整诊断信息"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

TOKEN = ''
for _p in (r'E:\work space\.gh_token', os.path.expanduser('~/.gh_token')):
    if os.path.exists(_p):
        with open(_p, encoding='utf-8') as f:
            TOKEN = f.read().strip()
        break

API = 'https://api.github.com'
OWNER = 'giuneipauliv-glitch'
REPO = 'safety-job-hunter'
BRANCH = 'main'
PATH = '.github/workflows/update.yml'
FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    '.github', 'workflows', 'update.yml')


def b64encode_str(s):
    return base64.b64encode(s.encode()).decode()


def api(method, url, data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header('Authorization', f'token {TOKEN}')
    req.add_header('User-Agent', 'job-radar-deploy')
    req.add_header('Accept', 'application/vnd.github+json')
    if data is not None:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode('utf-8', 'ignore') or '{}')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8', 'ignore') or '{}')


with open(FILE, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

print('file size:', len(b64) // 4 * 3)

# 1. GET 现状
s, r = api('GET', f'{API}/repos/{OWNER}/{REPO}/contents/{PATH}')
print('GET status:', s, '| keys:', sorted(r.keys())[:8] if isinstance(r, dict) else r)

# 2. PUT
body = {'message': 'add workflow', 'content': b64, 'branch': BRANCH}
s2, r2 = api('PUT', f'{API}/repos/{OWNER}/{REPO}/contents/{PATH}', body)
print('PUT status:', s2)
print('PUT response:', json.dumps(r2, ensure_ascii=False)[:400])

# 3. 兜底尝试：先建 .github/workflows/ 下的占位文件（目录预热）
if s2 not in (200, 201):
    print('--- 对照1: 创建 .github/placeholder.txt ---')
    s_p1, r_p1 = api('PUT', f'{API}/repos/{OWNER}/{REPO}/contents/.github/placeholder.txt', {
        'message': 'add .github test', 'content': b64encode_str('x'),
        'branch': BRANCH,
    })
    print('placeholder status:', s_p1, json.dumps(r_p1, ensure_ascii=False)[:150] if isinstance(r_p1, dict) else r_p1)

    print('--- 对照2: 创建 .github/workflows/.keep ---')
    s_p2, r_p2 = api('PUT', f'{API}/repos/{OWNER}/{REPO}/contents/.github/workflows/.keep', {
        'message': 'add dir placeholder', 'content': b64encode_str(''),
        'branch': BRANCH,
    })
    print('keep status:', s_p2, json.dumps(r_p2, ensure_ascii=False)[:150] if isinstance(r_p2, dict) else r_p2)
    if s_p2 in (200, 201):
        s4, r4 = api('PUT', f'{API}/repos/{OWNER}/{REPO}/contents/{PATH}', body)
        print('retry PUT status:', s4, json.dumps(r4, ensure_ascii=False)[:200] if isinstance(r4, dict) else r4)

    print('--- 对照3: 创建 workflow/update.yaml（换扩展名） ---')
    s_p3, r_p3 = api('PUT', f'{API}/repos/{OWNER}/{REPO}/contents/.github/workflows/update.yaml', body)
    print('yaml PUT status:', s_p3, json.dumps(r_p3, ensure_ascii=False)[:150] if isinstance(r_p3, dict) else r_p3)

    print('--- 对照4: 创建 top/workflow.yml（非隐藏目录对照） ---')
    s_p4, r_p4 = api('PUT', f'{API}/repos/{OWNER}/{REPO}/contents/workflows/update.yml', body)
    print('top-level PUT status:', s_p4, json.dumps(r_p4, ensure_ascii=False)[:150] if isinstance(r_p4, dict) else r_p4)

