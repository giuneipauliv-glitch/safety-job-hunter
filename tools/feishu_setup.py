# -*- coding: utf-8 -*-
"""
飞书多维表格初始化：验证凭证 → 创建表格应用 → 创建数据表与字段
用法：python tools/feishu_setup.py
输出：app_token / table_id（写入 feishu_config.json）
"""
import json
import os
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')
API = 'https://open.feishu.cn/open-apis'
CFG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'feishu_config.json')


def load_cfg():
    with open(CFG, encoding='utf-8') as f:
        return json.load(f)


def post(path, data, token=None):
    req = urllib.request.Request(API + path, data=json.dumps(data).encode('utf-8'),
                                 method='POST')
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8', 'ignore'))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode('utf-8', 'ignore'))


def main():
    cfg = load_cfg()
    print('1. 获取 tenant_access_token...')
    r = post('/auth/v3/tenant_access_token/internal', {
        'app_id': cfg['app_id'], 'app_secret': cfg['app_secret']})
    if r.get('code') != 0:
        print('❌ 凭证无效:', r.get('msg'))
        return 1
    token = r['tenant_access_token']
    print('✅ token 获取成功')

    print('2. 创建多维表格应用...')
    r = post('/bitable/v1/apps', {'name': '安全工程岗位雷达'}, token)
    if r.get('code') != 0:
        print('❌ 创建表格失败:', r.get('msg'))
        return 1
    app_token = r['data']['app']['app_token']
    print('✅ 表格已创建 app_token:', app_token)

    print('3. 创建数据表与字段...')
    fields = [
        {'field_name': '职位名称', 'type': 1},
        {'field_name': '公司', 'type': 1},
        {'field_name': '城市', 'type': 1},
        {'field_name': '薪资', 'type': 1},
        {'field_name': '学历', 'type': 1},
        {'field_name': '经验', 'type': 1},
        {'field_name': '岗位类型', 'type': 3},
        {'field_name': '来源', 'type': 3},
        {'field_name': '要求标签', 'type': 1},
        {'field_name': '发现日期', 'type': 1},
        {'field_name': '报名截止', 'type': 1},
        {'field_name': '投递链接', 'type': 15},
    ]
    r = post(f'/bitable/v1/apps/{app_token}/tables', {
        'table': {'name': '岗位', 'fields': fields}}, token)
    if r.get('code') != 0:
        print('❌ 建表失败:', r.get('msg'))
        return 1
    table_id = r['data']['table_id']
    print('✅ 数据表已创建 table_id:', table_id)

    cfg['app_token'] = app_token
    cfg['table_id'] = table_id
    with open(CFG, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1)
    print('✅ 配置已保存到 feishu_config.json')
    print('app_token:', app_token)
    print('table_id:', table_id)
    return 0


if __name__ == '__main__':
    sys.exit(main())
