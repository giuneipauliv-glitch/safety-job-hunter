# -*- coding: utf-8 -*-
"""抓取层新逻辑测试：噪声过滤 / 校招识别"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fetch import is_noise_title, detect_job_type  # noqa: E402


class TestNoiseFilter(unittest.TestCase):
    def test_it_noise(self):
        self.assertTrue(is_noise_title('网络安全工程师'))
        self.assertTrue(is_noise_title('信息安全工程师'))
        self.assertTrue(is_noise_title('大数据安全分析师'))
        self.assertTrue(is_noise_title('渗透测试工程师'))

    def test_traditional_kept(self):
        self.assertFalse(is_noise_title('化工安全工程师'))
        self.assertFalse(is_noise_title('矿山安全工程师'))
        self.assertFalse(is_noise_title('安全工程专业应届生'))
        self.assertFalse(is_noise_title('注册安全工程师'))


class TestJobType(unittest.TestCase):
    def test_campus(self):
        self.assertEqual(detect_job_type('2026届校招安全工程师'), '校招')
        self.assertEqual(detect_job_type('安全工程师（校园招聘）'), '校招')
        self.assertEqual(detect_job_type('应届生安全员'), '校招')

    def test_intern(self):
        self.assertEqual(detect_job_type('安全工程师实习生'), '实习')
        self.assertEqual(detect_job_type('兼职安全员'), '实习')

    def test_social(self):
        self.assertEqual(detect_job_type('安全工程师'), '社招')
        self.assertEqual(detect_job_type('注册安全工程师（化工）'), '社招')


if __name__ == '__main__':
    unittest.main(verbosity=2)
