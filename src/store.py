# -*- coding: utf-8 -*-
"""
数据存储层：去重 + 增量合并
- 按 job_id 去重
- 已存在岗位更新 last_seen；新增岗位记录 first_seen
- is_new = 今日首次发现
- 网页端按 last_seen 过滤活跃岗位，历史数据全保留
"""
import json
import os
import time
from datetime import datetime, timedelta

DEFAULT_KEEP_DAYS = 60  # 活跃岗位保留天数（last_seen 距今）


def today_str() -> str:
    return datetime.now().strftime('%Y-%m-%d')


def load_jobs(path: str) -> dict:
    if not os.path.exists(path):
        return {'meta': {}, 'jobs': []}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'meta': {}, 'jobs': []}


def merge_jobs(existing: dict, fresh: list, keep_days: int = DEFAULT_KEEP_DAYS) -> dict:
    today = today_str()
    jobs_map = {}
    for j in existing.get('jobs', []):
        if j.get('job_id'):
            jobs_map[j['job_id']] = j

    new_count = 0
    seen_fresh = set()
    for item in fresh:
        jid = item.get('job_id')
        if not jid or jid in seen_fresh:
            continue
        seen_fresh.add(jid)
        if jid in jobs_map:
            old = jobs_map[jid]
            # 字段有更新则刷新（薪资/标题可能变）
            old['last_seen'] = today
            if item.get('salary_text'):
                old['salary_text'] = item['salary_text']
                old['salary'] = item['salary']
            if item.get('has_cert'):
                old['has_cert'] = True
            # 合并标签
            old_tags = set(old.get('tags', []))
            for t in item.get('tags', []):
                if t not in old_tags:
                    old['tags'].append(t)
        else:
            item['first_seen'] = today
            item['last_seen'] = today
            jobs_map[jid] = item
            new_count += 1

    # 清理长期未见的岗位（下架）
    cutoff = (datetime.now() - timedelta(days=keep_days)).strftime('%Y-%m-%d')
    jobs = [j for j in jobs_map.values() if j.get('last_seen', today) >= cutoff]

    # 排序：今日新增 > first_seen 倒序
    jobs.sort(key=lambda j: (j.get('first_seen', ''), j.get('job_id', '')), reverse=True)

    return {
        'meta': {
            'updated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_date': today,
            'total': len(jobs),
            'new_today': new_count,
            'source': '智联招聘',
        },
        'jobs': jobs,
    }


def save_jobs(data: dict, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
