# -*- coding: utf-8 -*-
"""应届生网 / 化工英才网 抓取器解析测试"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fetch_yjs import parse_list as yjs_parse, make_job as yjs_make  # noqa: E402


class TestYJS(unittest.TestCase):

    def test_parse_list(self):
        html = '''
        <html><body>
        <a href="/job-005-654-425.html">[上海]某某化工有限公司</a>
        <a href="/job-005-654-425.html">安全工程师</a>
        上海 前程无忧 2026-08-03
        <a href="/job-008-023-191.html">[全国]吉利</a>
        <a href="/job-008-023-191.html">校园大使</a>
        全国 武汉理工大学 2026-08-03
        <a href="/job-007-981-552.html">[北京]某某建设集团</a>
        <a href="/job-007-981-552.html">2026届安全员</a>
        北京,上海 高校人才网 2026-08-01
        </body></html>
        '''
        recs = yjs_parse(html)
        self.assertGreaterEqual(len(recs), 2)
        jobs = [yjs_make(r) for r in recs]
        jobs = [j for j in jobs if j]
        # 校园大使被过滤
        self.assertNotIn('校园大使', [j['title'] for j in jobs])
        # 2026届安全员 → 校招
        j1 = [j for j in jobs if '安全员' in j['title']][0]
        self.assertEqual(j1['job_type'], '校招')
        self.assertEqual(j1['source'], 'yjs')
        self.assertTrue(j1['link'].startswith('https://www.yingjiesheng.com'))
        # 城市解析：北京,上海 → 上海
        self.assertEqual(j1['city'], '上海')
        # 发布日期
        self.assertEqual(j1['publish_date'], '2026-08-01')

    def test_gbk_roundtrip(self):
        """GBK 编码中文解析"""
        text = '<a href="/job-001-002-003.html">[杭州]测试公司</a><a href="/job-001-002-003.html">安全工程师</a>杭州 网申 2026-07-01'
        recs = yjs_parse(text.encode('gbk').decode('gbk'))
        self.assertEqual(len(recs), 1)
        j = yjs_make(recs[0])
        self.assertEqual(j['title'], '安全工程师')


if __name__ == '__main__':
    unittest.main(verbosity=2)
