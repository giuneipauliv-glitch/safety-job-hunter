# -*- coding: utf-8 -*-
"""
智联登录脚本（一次性/按需）：
用系统 Chrome（有头模式）打开智联，你在弹出的窗口里正常登录（扫码/账密），
登录成功后回到终端按回车，登录 Cookie 会保存在专用档案里，供后续抓取复用。
用法：python tools/login_zhaopin.py
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.fetch import _find_chrome, ZP_PROFILE  # noqa: E402

os.makedirs(ZP_PROFILE, exist_ok=True)

chrome = _find_chrome()
if not chrome:
    print('未找到 Chrome/Edge，无法继续')
    sys.exit(1)

print('正在打开智联招聘（专用登录窗口）...')
print('请在浏览器窗口中登录智联（扫码或账密均可）')
print('登录成功后，回到本窗口按回车继续\n')

p = subprocess.Popen([
    chrome, f'--user-data-dir={ZP_PROFILE}',
    '--no-first-run', '--disable-extensions', '--no-default-browser-check',
    'https://www.zhaopin.com/',
])

try:
    input('>>> 登录完成后按回车（或直接关掉浏览器窗口后按回车）...')
except EOFError:
    pass

# 关闭浏览器
try:
    p.terminate()
except Exception:
    pass
time.sleep(1)

# 验证档案里是否有 Cookie
cookies_dir = os.path.join(ZP_PROFILE, 'Default', 'Network')
has_cookie = os.path.exists(os.path.join(cookies_dir, 'Cookies'))
print('登录档案已保存:', ZP_PROFILE)
print('Cookie 文件存在:', '是' if has_cookie else '否（可能未登录成功，可重试）')
print('下次抓取会自动复用该登录态。Cookie 过期后重新运行本脚本即可。')
