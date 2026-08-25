# -*- coding: utf-8 -*-
"""打印智联校招职位列表第一条的完整字段"""
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
html = open(r'E:\work space\safety-job-hunter\tools\_xy_probe.html', encoding='utf-8').read()
m = re.search(r'window\.__INITIAL_DATA__\s*=\s*(\{.*?\})\s*</script>', html, re.S)
data = json.loads(m.group(1))
lst = data['position']['positionState']['list']
print('总数:', len(lst))
print('第一条字段:')
print(json.dumps(lst[0], ensure_ascii=False, indent=1)[:3000])
