# -*- coding: utf-8 -*-
"""诊断应届生求职网真实页面结构"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fetch_yjs import fetch_html, parse_list  # noqa: E402

url = 'https://www.yingjiesheng.com/zhuanye/anquankexue/'
try:
    html = fetch_html(url)
    print('HTML 长度:', len(html))
    # 检查编码
    print('含乱码特征:', html.count('\ufffd'))
    # 找 job 链接模式
    pats = {
        '/job-数字': len(re.findall(r'/job-\d+-\d+-\d+\.html', html)),
        '/job/': len(re.findall(r'/job/[A-Za-z0-9]+\.html', html)),
        'jobdetail': html.count('jobdetail'),
        'zhaopin': html.count('zhaopin'),
        '网申': html.count('网申'),
    }
    print('链接模式统计:', pats)
    # 打印一段含职位的文本
    idx = html.find('安全工程')
    if idx >= 0:
        print('--- 安全工程附近 ---')
        print(html[max(0, idx - 300):idx + 300])
    recs = parse_list(html)
    print('parse_list 记录数:', len(recs))
except Exception as e:
    print('抓取失败:', e)
