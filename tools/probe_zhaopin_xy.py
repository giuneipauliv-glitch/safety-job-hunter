# -*- coding: utf-8 -*-
"""探测智联校招搜索页：登录态能否访问 + 页面结构"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fetch import fetch_chrome_dump, is_verify_page  # noqa: E402

url = 'https://xiaoyuan.zhaopin.com/search/index?jn=2&kw=%E5%AE%89%E5%85%A8%E5%B7%A5%E7%A8%8B%E5%B8%88'
html = fetch_chrome_dump(url, timeout=90)
if not html:
    print('❌ 抓取返回空')
    sys.exit(1)
print('HTML 长度:', len(html))
print('验证页?', is_verify_page(html))
print('登录跳转?', 'passport' in html or 'additional' in html)
# 链接模式
pats = {
    'jobdetail主站': len(re.findall(r'jobdetail/[A-Z0-9]+\.htm', html)),
    'joblink校招': len(re.findall(r'joblink|jobId', html, re.I)),
    'position': html.count('position'),
    '职位卡片类名': len(re.findall(r'joblist|job-card|position-item', html, re.I)),
}
print('链接模式:', pats)
# 保存 HTML 供分析
with open(r'E:\work space\safety-job-hunter\tools\_xy_probe.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('已保存 _xy_probe.html')
