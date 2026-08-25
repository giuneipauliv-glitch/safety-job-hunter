# -*- coding: utf-8 -*-
"""
飞书多维表格同步（校招专区版）：
- 只同步校招岗位（job_type=校招），避开免费版 2000 行限制
- 每日增量：新增在招校招岗，自动删除已结束的（报名截止过期 / 长期未更新）
- 国内直连 open.feishu.cn，无需 VPN
用法：python src/sync_feishu.py
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API = 'https://open.feishu.cn/open-apis'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_PATH = os.path.join(ROOT, 'feishu_config.json')
JOBS_PATH = os.path.join(ROOT, 'data', 'jobs.json')
BATCH = 500

# 校招岗"视为结束"：无报名截止日期的岗位，最近 N 天未再出现即下架
STALE_DAYS = 10

FIELD_MAP = [
    ('职位名称', 'title'),
    ('公司', 'company'),
    ('城市', 'city'),
    ('薪资', 'salary_text'),
    ('学历', 'education'),
    ('经验', 'experience'),
    ('岗位类型', 'job_type'),
    ('来源', 'source'),
    ('要求标签', 'tags'),
    ('发现日期', 'first_seen'),
    ('报名截止', 'end_time'),
    ('投递链接', 'link'),
]
FIELD_TYPE = {'投递链接': 15, '岗位类型': 3, '来源': 3}
SRC_NAMES = {'zhaopin': '智联招聘', 'iguopin': '国聘', 'yjs': '应届生网', 'chern': '化工英才网'}


def load_cfg():
    with open(CFG_PATH, encoding='utf-8') as f:
        return json.load(f)


def api(method, path, data=None, token=None):
    req = urllib.request.Request(API + path, method=method)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    if data is not None:
        req.data = json.dumps(data, ensure_ascii=False).encode('utf-8')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8', 'ignore'))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode('utf-8', 'ignore'))


def get_token(cfg):
    r = api('POST', '/auth/v3/tenant_access_token/internal', {
        'app_id': cfg['app_id'], 'app_secret': cfg['app_secret']})
    if r.get('code') != 0:
        raise RuntimeError(f'token 获取失败: {r.get("msg")}')
    return r['tenant_access_token']


def ensure_fields(token, app_token, table_id):
    r = api('GET', f'/bitable/v1/apps/{app_token}/tables/{table_id}/fields', token=token)
    if r.get('code') != 0:
        print('❌ 读取字段失败:', r.get('msg'))
        return False
    names = {f['field_name'] for f in r.get('data', {}).get('items', [])}
    need = [fname for fname, _ in FIELD_MAP] + ['岗位ID']
    for fname in need:
        if fname not in names:
            ftype = FIELD_TYPE.get(fname, 1)
            r = api('POST', f'/bitable/v1/apps/{app_token}/tables/{table_id}/fields',
                    {'field_name': fname, 'type': ftype}, token=token)
            if r.get('code') != 0:
                print(f'❌ 创建字段 {fname} 失败: {r.get("msg")}')
                return False
            print(f'  已创建字段: {fname}')
    return True


def fetch_records(token, app_token, table_id):
    """返回 {job_id: record_id}"""
    mapping = {}
    page_token = None
    while True:
        path = f'/bitable/v1/apps/{app_token}/tables/{table_id}/records?page_size=500'
        if page_token:
            path += f'&page_token={page_token}'
        r = api('GET', path, token=token)
        if r.get('code') != 0:
            break
        data = r.get('data', {})
        for rec in data.get('items', []):
            jid = rec.get('fields', {}).get('岗位ID')
            if jid:
                mapping[str(jid)] = rec['record_id']
        if data.get('has_more') and data.get('page_token'):
            page_token = data['page_token']
        else:
            break
    return mapping


def is_ended(job):
    """校招岗是否已结束：报名截止过期，或长期未在搜索中出现"""
    end = str(job.get('end_time') or '')
    if end and end < datetime.now().strftime('%Y-%m-%d'):
        return True
    last = str(job.get('last_seen') or '')
    if last:
        try:
            last_dt = datetime.strptime(last, '%Y-%m-%d')
            if datetime.now() - last_dt > timedelta(days=STALE_DAYS):
                return True
        except ValueError:
            pass
    return False


def build_record(job):
    fields = {}
    for fname, key in FIELD_MAP:
        val = job.get(key)
        if key == 'source':
            val = SRC_NAMES.get(val, val)
        if key == 'tags':
            val = ' / '.join((val or [])[:8])
        if key == 'end_time' and not val:
            continue
        if key == 'link' and val:
            fields[fname] = {'text': '投递', 'link': val}
            continue
        if val:
            fields[fname] = str(val)
    fields['岗位ID'] = job.get('job_id', '')
    return fields


def batch_delete(token, app_token, table_id, record_ids):
    for i in range(0, len(record_ids), BATCH):
        r = api('POST',
                f'/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_delete',
                {'records': record_ids[i:i + BATCH]}, token=token)
        if r.get('code') != 0:
            print(f'❌ 删除批次失败: {r.get("msg")}')
            return False
    return True


def batch_create(token, app_token, table_id, jobs):
    for i in range(0, len(jobs), BATCH):
        r = api('POST',
                f'/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create',
                {'records': [{'fields': build_record(j)} for j in jobs[i:i + BATCH]]},
                token=token)
        if r.get('code') != 0:
            print(f'❌ 写入批次失败: {r.get("msg")}')
            return False
        print(f'  已写入 {min(i + BATCH, len(jobs))}/{len(jobs)}')
        time.sleep(0.5)
    return True


def sync(cfg=None):
    cfg = cfg or load_cfg()
    token = get_token(cfg)
    app_token = cfg['app_token']
    table_id = cfg['table_id']

    if not ensure_fields(token, app_token, table_id):
        return 1

    # 表格现有记录
    existing = fetch_records(token, app_token, table_id)
    print(f'表格现有 {len(existing)} 条')

    # 本地在招校招岗
    with open(JOBS_PATH, encoding='utf-8') as f:
        jobs = json.load(f).get('jobs', [])
    campus_active = [j for j in jobs
                     if j.get('job_type') == '校招' and not is_ended(j)]
    campus_ids = {j.get('job_id') for j in campus_active}
    print(f'本地在招校招岗 {len(campus_active)} 条（已过滤结束岗位）')

    # 删除：表格里有但已不在招（含之前的非校招数据 + 已结束的校招）
    to_delete = [rid for jid, rid in existing.items() if jid not in campus_ids]
    if to_delete:
        print(f'删除 {len(to_delete)} 条（已结束/非校招）')
        if not batch_delete(token, app_token, table_id, to_delete):
            return 1

    # 新增：在招校招不在表格
    to_add = [j for j in campus_active if j['job_id'] not in existing]
    if to_add:
        print(f'新增 {len(to_add)} 条')
        if not batch_create(token, app_token, table_id, to_add):
            return 1

    print(f'✅ 校招同步完成：表格现有 {len(existing) - len(to_delete) + len(to_add)} 条在招校招岗')
    return 0


if __name__ == '__main__':
    sys.exit(sync())
