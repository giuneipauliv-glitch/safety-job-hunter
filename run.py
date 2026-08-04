# -*- coding: utf-8 -*-
"""
主流程：抓取 -> 去重合并 -> 生成网页
用法：
  python run.py                    # 云端/本地 Playwright 抓取（默认）
  python run.py --backend chrome_dump   # 本机无 Playwright 时用系统 Chrome
  python run.py --pages 1          # 每关键词只抓 1 页（快速测试）
  python run.py --keywords 安全工程师,EHS   # 只抓指定关键词
退出码：0 成功；2 全部被拦截（供 GitHub Actions 触发失败通知）
"""
import argparse
import json
import os
import sys
import time

# 固定工作目录到项目根，保证所有相对路径一致
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (KEYWORDS, CORE_KEYWORDS, EXTRA_KEYWORDS, PAGES_CORE,  # noqa: E402
                    PAGES_EXTRA, PAGES_PER_KEYWORD, JOBS_FILE, REQUEST_INTERVAL, SOURCES)
from src.fetch import fetch_all as fetch_zhaopin  # noqa: E402
from src.fetch_iguopin import fetch as fetch_iguopin  # noqa: E402
from src.store import load_jobs, merge_jobs, save_jobs  # noqa: E402
import build_site  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description='安全工程招聘信息抓取')
    parser.add_argument('--backend', default='playwright', choices=['playwright', 'chrome_dump'])
    parser.add_argument('--pages', type=int, default=PAGES_PER_KEYWORD)
    parser.add_argument('--keywords', default=None, help='逗号分隔，默认使用全部关键词')
    parser.add_argument('--interval', type=float, default=None, help='抓取间隔秒数(默认随机2-5)')
    parser.add_argument('--sources', default=None, help='逗号分隔：zhaopin,iguopin（默认全部启用源）')
    args = parser.parse_args()

    # 数据源开关
    if args.sources:
        for s in list(SOURCES.keys()):
            SOURCES[s] = s in [x.strip() for x in args.sources.split(',')]

    keywords = [k.strip() for k in args.keywords.split(',')] if args.keywords else KEYWORDS
    interval = (args.interval, args.interval) if args.interval else REQUEST_INTERVAL

    existing = load_jobs(JOBS_FILE)
    print(f'已有数据: {existing["meta"].get("total", 0)} 条, 关键词 {len(keywords)} 个')

    t0 = time.time()
    all_fresh = []

    # 关键词分级：核心词多页，扩展词少页
    if args.pages:  # 显式指定时统一用指定页数
        core_pages = args.pages
        extra_pages = args.pages
    else:
        core_pages = PAGES_CORE
        extra_pages = PAGES_EXTRA
    core_kws = [k for k in keywords if k in CORE_KEYWORDS]
    extra_kws = [k for k in keywords if k not in CORE_KEYWORDS]

    def run_zhaopin(kws, pages, label):
        return fetch_zhaopin(kws, pages, backend=args.backend, interval=interval,
                             progress=lambda m: print(f'  {m}'))

    # 1) 智联主站（社招为主）
    if SOURCES.get('zhaopin', True):
        fresh = []
        if core_kws:
            fresh += run_zhaopin(core_kws, core_pages, '核心')
        if extra_kws:
            fresh += run_zhaopin(extra_kws, extra_pages, '扩展')
        print(f'[智联主站] 原始 {len(fresh)} 条')
        all_fresh.extend(fresh)

    # 2) 国聘（国企/央企，校招+社招）
    if SOURCES.get('iguopin', True):
        from config import IGUOPIN_NATURE_ALL
        fresh = fetch_iguopin(keywords, 1, nature=IGUOPIN_NATURE_ALL or None,
                              progress=lambda m: print(f'  {m}'))
        print(f'[国聘] 原始 {len(fresh)} 条')
        all_fresh.extend(fresh)

    fresh = all_fresh
    print(f'抓取完成: 原始 {len(fresh)} 条, 耗时 {time.time()-t0:.0f}s')

    if not fresh:
        if existing.get('jobs'):
            print('!! 全部请求被拦截或失败，本次未更新（保留旧数据）')
            sys.exit(2)
        print('!! 首次运行且抓取失败，无任何数据')
        sys.exit(2)

    merged = merge_jobs(existing, fresh)
    save_jobs(merged, JOBS_FILE)
    print(f"合并完成: 总计 {merged['meta']['total']} 条, 今日新增 {merged['meta']['new_today']} 条")

    build_site.build(merged)

    # 抓取摘要（供 workflow 日志/通知）
    summary = {
        'updated_at': merged['meta']['updated_at'],
        'total': merged['meta']['total'],
        'new_today': merged['meta']['new_today'],
        'raw_fetched': len(fresh),
    }
    os.makedirs('logs', exist_ok=True)
    with open('logs/last_run.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print('运行摘要已写入 logs/last_run.json')


if __name__ == '__main__':
    main()
