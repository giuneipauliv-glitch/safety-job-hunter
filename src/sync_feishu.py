# -*- coding: utf-8 -*-
"""
飞书多维表格同步：把 data/jobs.json 增量同步到飞书表格
- 按 job_id 去重（表格内置"岗位ID"字段做查重）
- 国内直连 open.feishu.cn，无需 VPN
用法：python src/sync_feishu.py
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API = 'https://open.feishu.cn/open-apis'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_PATH = os.path.join(ROOT, 'feishu_config.json')
JOBS_PATH = os.path.join(ROOT, 'data', 'jobs.json')
BATCH = 500  # 飞书单次批量写入上限

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


FIELD_TYPE = {'投递链接': 15, '岗位类型': 3, '来源': 3}


def ensure_fields(token, app_token, table_id):
    """确保表格存在所有目标字段（缺失的自动创建，含查重用的岗位ID）"""
    r = api('GET', f'/bitable/v1/apps/{app_token}/tables/{table_id}/fields',
            token=token)
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


def fetch_existing_ids(token, app_token, table_id):
    """分页查询表格里已有的岗位ID"""
    ids = set()
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
                ids.add(str(jid))
        if data.get('has_more') and data.get('page_token'):
            page_token = data['page_token']
        else:
            break
    return ids


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


def sync(cfg=None):
    cfg = cfg or load_cfg()
    token = get_token(cfg)
    app_token = cfg['app_token']
    table_id = cfg['table_id']

    if not ensure_fields(token, app_token, table_id):
        print('❌ 字段检查/创建失败')
        return 1

    existing = fetch_existing_ids(token, app_token, table_id)
    print(f'表格已有 {len(existing)} 条记录')

    with open(JOBS_PATH, encoding='utf-8') as f:
        jobs = json.load(f).get('jobs', [])
    to_add = [j for j in jobs if str(j.get('job_id', '')) not in existing]
    print(f'本地共 {len(jobs)} 条，新增 {len(to_add)} 条')

    if not to_add:
        print('✅ 无新增，同步完成')
        return 0

    added = 0
    for i in range(0, len(to_add), BATCH):
        batch = to_add[i:i + BATCH]
        r = api('POST',
                f'/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create',
                {'records': [{'fields': build_record(j)} for j in batch]},
                token=token)
        if r.get('code') != 0:
            print(f'❌ 批次写入失败: {r.get("msg")}')
            return 1
        added += len(batch)
        print(f'  已写入 {added}/{len(to_add)}')
        time.sleep(0.5)
    print(f'✅ 同步完成，新增 {added} 条。飞书表格已更新')
    return 0


if __name__ == '__main__':
    sys.exit(sync())
