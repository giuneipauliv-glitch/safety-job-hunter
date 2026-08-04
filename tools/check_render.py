# -*- coding: utf-8 -*-
"""渲染验证：Chrome 渲染本地网页 -> 检查 JS 是否成功执行"""
import subprocess
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

cmd = [
    CHROME, '--headless=new', '--disable-gpu', '--no-first-run',
    '--disable-crash-reporter', '--disable-extensions',
    '--user-data-dir=E:\\work space\\.tools\\chrome-dump-check',
    '--virtual-time-budget=6000',
    '--dump-dom', 'file:///E:/work space/safety-job-hunter/docs/index.html',
]
p = subprocess.run(cmd, capture_output=True, timeout=90)
html = p.stdout.decode('utf-8', 'ignore')

checks = {
    'job卡片渲染数量': len(re.findall(r'class="job"', html)),
    '统计条渲染': len(re.findall(r'class="stat"', html)),
    '薪资高亮': len(re.findall(r'class="salary', html)),
    '徽章(新增/证书/外派)': len(re.findall(r'class="badge', html)),
    '投递按钮': len(re.findall(r'class="apply"', html)),
    '报考指南卡片': len(re.findall(r'class="g-card"', html)),
    '城市下拉': len(re.findall(r'option', html)),
    '结果计数': len(re.findall(r'result-info', html)),
}
for k, v in checks.items():
    print(f'{k}: {v}')
ok = checks['job卡片渲染数量'] >= 8 and checks['报考指南卡片'] == 4
print('RENDER', 'OK' if ok else 'PROBLEM')
