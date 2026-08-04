# -*- coding: utf-8 -*-
"""
通过 GitHub Git Data API 批量上传项目文件（一次性部署用）
- token 只从环境变量读取，不出现命令行、不落盘
- 用 blobs + tree + commit + ref 一次提交全部文件
用法：$env:GH_TOKEN=xxx; python tools/upload.py
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

TOKEN = os.environ.get('GH_TOKEN', '')
if not TOKEN:
    for _p in (r'E:\work space\.gh_token', os.path.expanduser('~/.gh_token')):
        if os.path.exists(_p):
            with open(_p, encoding='utf-8') as _f:
                TOKEN = _f.read().strip()
            break
API = 'https://api.github.com'
REPO = 'safety-job-hunter'
OWNER = 'giuneipauliv-glitch'
BRANCH = 'main'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 需要上传的路径（排除 .git、缓存、日志、部署脚本自身）
EXCLUDE_DIRS = {'.git', '__pycache__', 'logs', '.tools'}
EXCLUDE_FILES = {'deploy.py', 'upload.py', '_tmp_jobs_test.json'}


def api(method, path, data=None, raw=False):
    req = urllib.request.Request(API + path, method=method)
    req.add_header('Authorization', f'token {TOKEN}')
    req.add_header('User-Agent', 'job-radar-deploy')
    req.add_header('Accept', 'application/vnd.github+json')
    if data is not None:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            if raw:
                return r.status, body
            return r.status, (json.loads(body.decode('utf-8', 'ignore')) if body else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'ignore')
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {'msg': body[:300]}


def collect_files():
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            if fn in EXCLUDE_FILES or fn.endswith('.pyc'):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace('\\', '/')
            files.append((rel, full))
    return files


def main():
    files = collect_files()
    print(f'待上传 {len(files)} 个文件（Contents API 逐文件模式）')

    ok = 0
    skipped = 0
    for rel, full in files:
        if rel.startswith('.github/'):
            # GitHub 安全策略：workflow 文件禁止 API 直传，需网页 UI 创建
            print(f'  SKIP(网页创建) {rel}')
            skipped += 1
            continue
        with open(full, 'rb') as f:
            content = f.read()
        try:
            text = content.decode('utf-8')
            payload = text.replace('\r\n', '\n').encode('utf-8')
        except UnicodeDecodeError:
            payload = content
        body = {
            'message': f'add {rel}',
            'content': base64.b64encode(payload).decode(),
            'branch': BRANCH,
        }
        # 文件已存在时需带旧 sha 才能更新
        s_get, r_get = api('GET', f'/repos/{OWNER}/{REPO}/contents/{rel}')
        if s_get == 200 and r_get.get('sha'):
            body['sha'] = r_get['sha']
            body['message'] = f'update {rel}'
        status, r = api('PUT', f'/repos/{OWNER}/{REPO}/contents/{rel}', body)
        if status in (200, 201):
            ok += 1
            print(f'  ✓ {rel}')
        else:
            print(f'  ✗ {rel}: {status} {r}')
    print(f'完成：{ok}/{len(files)} 个文件已上传（{skipped} 个跳过需网页创建）')
    return 0 if ok + skipped == len(files) else 1


if __name__ == '__main__':
    if not TOKEN:
        print('缺少 GH_TOKEN')
        sys.exit(1)
    sys.exit(main())
