# -*- coding: utf-8 -*-
"""
GitHub 部署脚本（一次性）
用法：$env:GH_TOKEN=xxx; python tools/deploy.py validate|create-repo|pages|dispatch
token 只从环境变量读取，不写入任何文件
"""
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
OWNER = 'giuneipauliv-glitch'
REPO = 'safety-job-hunter'
FULL = f'{OWNER}/{REPO}'


def api(method, path, data=None):
    req = urllib.request.Request(API + path, method=method)
    req.add_header('Authorization', f'token {TOKEN}')
    req.add_header('User-Agent', 'job-radar-deploy')
    req.add_header('Accept', 'application/vnd.github+json')
    if data is not None:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode('utf-8', 'ignore')
            return r.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'ignore')
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {'msg': body[:200]}


def cmd_validate():
    status, me = api('GET', '/user')
    if status == 200:
        print(f'✅ token 有效，账号：{me.get("login")}（{me.get("name") or ""}）')
        return 0
    print(f'❌ token 无效: {status} {me}')
    return 1


def cmd_create_repo():
    status, r = api('POST', '/user/repos', {
        'name': REPO,
        'description': '安全工程岗位雷达：每日自动聚合智联+国聘安全类岗位，校招/社招筛选',
        'private': False,
        'auto_init': False,
    })
    if status in (200, 201):
        print(f'✅ 仓库已创建: {r.get("html_url")}')
        return 0
    if status == 422 and 'already exists' in str(r):
        print('ℹ️ 仓库已存在，跳过创建')
        return 0
    print(f'❌ 创建失败: {status} {r}')
    return 1


def cmd_cleanup():
    """删除诊断测试产生的多余文件（DELETE 需先 GET 拿 sha）"""
    for path in ('.github/placeholder.txt', 'workflows/update.yml'):
        s_get, r_get = api('GET', f'/repos/{FULL}/contents/{path}')
        if s_get != 200 or not r_get.get('sha'):
            print(f'⚠️ {path} 不存在或无法读取（{s_get}），跳过')
            continue
        status, r = api('DELETE', f'/repos/{FULL}/contents/{path}', {
            'message': f'remove {path}', 'sha': r_get['sha'],
        })
        if status in (200, 204):
            print(f'✅ 已删除 {path}')
        else:
            print(f'⚠️ 删除 {path}: {status} {r}')
    return 0


def cmd_pages():
    status, r = api('POST', f'/repos/{FULL}/pages', {
        'source': {'branch': 'main', 'path': '/docs'},
    })
    if status in (200, 201):
        print(f'✅ Pages 已启用: https://{r.get("html_url", "")}')
        return 0
    if status == 409:
        print('ℹ️ Pages 可能已启用，检查状态')
        s2, r2 = api('GET', f'/repos/{FULL}/pages')
        print('  Pages 状态:', r2.get('status'), '| URL:', r2.get('html_url'))
        if r2.get('source', {}).get('branch'):
            print('  分支配置:', r2.get('source'))
            return 0
        return 1
    print(f'❌ Pages 设置失败: {status} {r}')
    return 1


def cmd_dispatch():
    status, r = api('POST',
                    f'/repos/{FULL}/actions/workflows/update.yml/dispatches',
                    {'ref': 'main'})
    if status == 204:
        print('✅ 已触发 Actions 手动运行，可在仓库 Actions 页查看')
        return 0
    print(f'❌ 触发失败: {status} {r}')
    return 1


def cmd_run():
    status, r = api('GET', f'/repos/{REPO}/actions/workflows')
    print('工作流列表:', status)
    for w in r.get('workflows', []):
        print(f"  - {w['name']} [{w['state']}]")
    return 0


if __name__ == '__main__':
    if not TOKEN:
        print('缺少 GH_TOKEN 环境变量')
        sys.exit(1)
    fn = sys.argv[1] if len(sys.argv) > 1 else 'validate'
    handlers = {
        'validate': cmd_validate,
        'create-repo': cmd_create_repo,
        'cleanup': cmd_cleanup,
        'pages': cmd_pages,
        'dispatch': cmd_dispatch,
        'run': cmd_run,
    }
    sys.exit(handlers[fn]())
