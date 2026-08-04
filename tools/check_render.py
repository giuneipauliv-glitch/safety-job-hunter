# -*- coding: utf-8 -*-
"""新界面渲染验证：分页/卡片/样式"""
import subprocess
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

cmd = [
    CHROME, '--headless=new', '--disable-gpu', '--no-first-run',
    '--disable-crash-reporter', '--disable-extensions',
    '--user-data-dir=E:\\work space\\.tools\\chrome-check2',
    '--virtual-time-budget=6000',
    '--dump-dom', 'file:///E:/work space/safety-job-hunter/docs/index.html',
]
p = subprocess.run(cmd, capture_output=True, timeout=90)
html = p.stdout.decode('utf-8', 'ignore')

checks = {
    '卡片数(应为30)': len(re.findall(r'class="job"', html)),
    '分页控件存在': len(re.findall(r'page-btn', html)),
    '分页信息': len(re.findall(r'第 \d+ / \d+ 页', html)),
    '统计条': len(re.findall(r'class="stat"', html)),
    '投递按钮': len(re.findall(r'class="apply"', html)),
    '报考指南卡片': len(re.findall(r'class="g-card"', html)),
    '玻璃卡片样式': html.count('backdrop-filter'),
    '渐变背景': html.count('radial-gradient'),
}
for k, v in checks.items():
    print(f'{k}: {v}')
ok = checks['卡片数(应为30)'] == 30 and checks['分页控件存在'] >= 10 and checks['报考指南卡片'] == 4
print('RENDER', 'OK' if ok else 'PROBLEM')
