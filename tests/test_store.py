# -*- coding: utf-8 -*-
"""数据合并（去重/增量/下架清理）单元测试"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.store import merge_jobs, load_jobs, save_jobs  # noqa: E402


def job(jid, title, **kw):
    base = {
        'job_id': jid, 'title': title, 'salary_text': '8000-12000元',
        'salary': (8000, 12000), 'education': '本科', 'edu_level': 4,
        'experience': '3-5年', 'exp_level': 3, 'location': '武汉·洪山',
        'city': '武汉', 'district': '洪山', 'company': '测试公司',
        'company_url': '', 'company_type': '民营', 'company_size': '20-99人',
        'industry': '技术服务', 'tags': ['安全管理'], 'link': f'http://x/{jid}',
        'outsource': False, 'has_cert': False, 'keyword': '安全工程师',
    }
    base.update(kw)
    return base


class TestMerge(unittest.TestCase):

    def test_new_and_existing(self):
        """新岗位新增，旧岗位更新 last_seen，不重复堆积"""
        existing = {'meta': {}, 'jobs': [job('A1', '老岗位', first_seen='2026-08-01', last_seen='2026-08-01')]}
        fresh = [
            job('A1', '老岗位'),                       # 已存在
            job('B2', '新岗位'),                       # 新增
            job('C3', '另一个新岗位'),                  # 新增
        ]
        merged = merge_jobs(existing, fresh)
        self.assertEqual(merged['meta']['new_today'], 2)
        self.assertEqual(merged['meta']['total'], 3)
        by_id = {j['job_id']: j for j in merged['jobs']}
        self.assertEqual(by_id['A1']['last_seen'], merged['meta']['updated_date'])
        self.assertEqual(by_id['A1']['first_seen'], '2026-08-01')
        self.assertEqual(by_id['B2']['first_seen'], merged['meta']['updated_date'])

    def test_duplicate_in_same_batch(self):
        """同批次重复抓取同一岗位只算一条"""
        fresh = [job('X1', '重复'), job('X1', '重复')]
        merged = merge_jobs({'meta': {}, 'jobs': []}, fresh)
        self.assertEqual(merged['meta']['total'], 1)
        self.assertEqual(merged['meta']['new_today'], 1)

    def test_expired_cleanup(self):
        """超过 keep_days 未再出现的岗位被清理"""
        existing = {'meta': {}, 'jobs': [
            job('OLD', '下架岗', first_seen='2026-05-01', last_seen='2026-05-01'),
            job('NEW', '活跃岗', first_seen='2026-08-01', last_seen='2026-08-01'),
        ]}
        merged = merge_jobs(existing, [], keep_days=30)
        ids = {j['job_id'] for j in merged['jobs']}
        self.assertIn('NEW', ids)
        self.assertNotIn('OLD', ids)

    def test_roundtrip_save_load(self):
        """save/load 往返无损"""
        data = merge_jobs({'meta': {}, 'jobs': []}, [job('Z1', '岗位')])
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'tools', '_tmp_jobs_test.json')
        try:
            save_jobs(data, p)
            loaded = load_jobs(p)
        finally:
            try:
                os.remove(p)
            except OSError:
                pass
        self.assertEqual(loaded['meta']['total'], 1)
        self.assertEqual(loaded['jobs'][0]['job_id'], 'Z1')


if __name__ == '__main__':
    unittest.main(verbosity=2)
