# -*- coding: utf-8 -*-
"""测试启动器：解决 embed 版 Python 的 sys.path 问题"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest  # noqa: E402

loader = unittest.TestLoader()
suite = loader.discover(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests'))
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
