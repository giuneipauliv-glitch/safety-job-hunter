# -*- coding: utf-8 -*-
"""
抓取层：双后端
- backend='playwright'：真实浏览器，自动过 JS 挑战（云端 Actions 与本地首选）
- backend='chrome_dump'：调用系统 Chrome headless --dump-dom（本地无 Playwright 时兜底）
返回渲染后的完整 HTML；遇到安全验证页返回 None
"""
import random
import re
import subprocess
import sys
import time

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')

VERIFY_MARKS = ['Security Verification', '人机验证', '访问验证', '滑动验证']


def is_verify_page(html: str) -> bool:
    if not html:
        return True
    return any(m in html for m in VERIFY_MARKS)


def _find_chrome() -> str:
    candidates = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    ]
    import os
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def fetch_chrome_dump(url: str, timeout: int = 90) -> str:
    chrome = _find_chrome()
    if not chrome:
        return None
    import tempfile
    profile = tempfile.mkdtemp(prefix='zhp_')
    cmd = [
        chrome, '--headless=new', '--disable-gpu', '--no-first-run',
        '--disable-extensions', '--disable-dev-shm-usage', '--no-sandbox',
        f'--user-data-dir={profile}',
        '--virtual-time-budget=15000',
        '--dump-dom', url,
    ]
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return p.stdout.decode('utf-8', 'ignore')
    except Exception:
        return None


def fetch_playwright(url: str, timeout: int = 60000, headless: bool = True,
                     channel: str = None) -> str:
    """channel: 'chrome' 使用系统 Chrome；None 用 playwright 自带 chromium"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    with sync_playwright() as pw:
        try:
            launch_kw = {'headless': headless, 'args': ['--disable-blink-features=AutomationControlled']}
            if channel:
                launch_kw['channel'] = channel
            browser = pw.chromium.launch(**launch_kw)
            ctx = browser.new_context(
                user_agent=UA,
                viewport={'width': 1366, 'height': 900},
                locale='zh-CN',
            )
            page = ctx.new_page()
            page.goto(url, wait_until='domcontentloaded', timeout=timeout)
            # 等待渲染/验证挑战完成
            page.wait_for_timeout(6000)
            html = page.content()
            browser.close()
            return html
        except Exception:
            try:
                browser.close()
            except Exception:
                pass
            return None


def fetch_page(url: str, backend: str = 'playwright', retry: int = 3,
               interval: tuple = (2, 5)) -> str:
    """抓取单个 URL，失败重试。返回 HTML 或 None"""
    for attempt in range(retry):
        if backend == 'playwright':
            html = fetch_playwright(url)
        else:
            html = fetch_chrome_dump(url)
        if html and not is_verify_page(html):
            return html
        wait = random.uniform(*interval) * (attempt + 1)
        time.sleep(wait)
    return None


def detect_job_type(title: str) -> str:
    """从标题判断校招/社招/实习（智联主站岗位默认社招）"""
    from config import CAMPUS_KEYWORDS
    if any(k in title for k in CAMPUS_KEYWORDS):
        return '校招'
    if any(k in title for k in ('实习', '实习生', '兼职')):
        return '实习'
    return '社招'


def is_noise_title(title: str) -> bool:
    """网络安全/IT 类岗位过滤（传统安全工程行业的无关噪声）
    规则：标题含网络/信息/数据等 IT 词直接排除，
    即使同时含“安全工程”子串（如“网络安全工程师”“信息安全工程师”）。
    """
    from config import NOISE_TITLE_WORDS
    return any(w in title for w in NOISE_TITLE_WORDS)


def fetch_all(keywords: list, pages: int, backend: str = 'playwright',
              interval: tuple = (2, 5), progress=None) -> list:
    """抓取全部关键词×页数的岗位列表（智联主站，社招为主，sm=2 最新发布）"""
    from config import ZHAOPIN_SOU_TEMPLATE
    from src.parse import parse_page

    all_jobs = []
    for kw in keywords:
        for page_no in range(1, pages + 1):
            url = ZHAOPIN_SOU_TEMPLATE.format(kw=quote(kw), page=page_no)
            html = fetch_page(url, backend=backend, interval=interval)
            if html:
                jobs = parse_page(html)
                for j in jobs:
                    if is_noise_title(j['title']):
                        continue
                    j['keyword'] = kw
                    j['source'] = 'zhaopin'
                    j['job_type'] = detect_job_type(j['title'])
                all_jobs.extend(jobs)
                if progress:
                    progress(f'[{kw} p{page_no}] 抓到 {len(jobs)} 条（含噪声已滤）')
            else:
                if progress:
                    progress(f'[{kw} p{page_no}] 被拦截或超时')
            time.sleep(random.uniform(*interval))
    return all_jobs


def quote(s: str) -> str:
    from urllib.parse import quote
    return quote(s, safe='')
