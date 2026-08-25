# -*- coding: utf-8 -*-
"""
网页生成器：data/jobs.json + guide.py -> docs/index.html
输出单文件静态页（数据内联），GitHub Pages 直接托管
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from guide import GUIDE  # noqa: E402

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'site', 'template.html')


def render_guide_html(guide: dict) -> str:
    """报考指南数据结构 -> HTML 卡片"""
    blocks = []
    for sec in guide['sections']:
        rows = ''.join(
            f'<div class="g-row"><span class="g-k">{k}</span><span class="g-v">{v}</span></div>'
            for k, v in sec['items']
        )
        badge = f'<span class="g-badge">{sec["badge"]}</span>' if sec.get('badge') else ''
        blocks.append(
            f'<div class="g-card"><div class="g-head"><span class="g-icon">{sec["icon"]}</span>'
            f'<h3>{sec["title"]}</h3>{badge}</div><div class="g-body">{rows}</div></div>'
        )
    notice = f'<p class="g-notice">⚠️ {guide["notice"]}</p>'
    return f'<div class="guide-wrap">{notice}<div class="g-grid">{"".join(blocks)}</div></div>'


def build(data: dict, out_path: str = None):
    """生成 docs/index.html"""
    if out_path is None:
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs', 'index.html')

    jobs = data.get('jobs', [])
    meta = data.get('meta', {})
    # 今日新增 = 首次发现于最近一次更新日期
    today = meta.get('updated_date', '')
    for j in jobs:
        j['_is_new'] = j.get('first_seen') == today

    payload = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    guide_html = render_guide_html(GUIDE)

    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        tpl = f.read()

    html = (tpl
            .replace('/*__DATA__*/', payload)
            .replace('<!--__GUIDE__-->', guide_html))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'site built: {out_path} ({len(jobs)} jobs, {len(html)//1024} KB)')


if __name__ == '__main__':
    with open('data/jobs.json', 'r', encoding='utf-8') as f:
        build(json.load(f))
