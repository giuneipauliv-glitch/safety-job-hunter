# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'E:\work space\safety-job-hunter')
from src.fetch_yjs import parse_list, make_job

html = '''
<html><body>
<a href="/job-005-654-425.html">[上海]某某化工有限公司</a>
<a href="/job-005-654-425.html">安全工程师</a>
上海 前程无忧 2026-08-03
<a href="/job-007-981-552.html">[北京]某某建设集团</a>
<a href="/job-007-981-552.html">2026届安全员</a>
北京,上海 高校人才网 2026-08-01
</body></html>
'''
recs = parse_list(html)
print('records:', len(recs))
for r in recs:
    print('---')
    print('company:', r.get('company'))
    print('title:', r.get('title'))
    print('link:', r.get('link'))
    print('texts:', r.get('texts'))
    j = make_job(r)
    if j:
        print('job:', j['title'], '| city:', j['city'], '| loc:', j['location'], '| date:', j.get('publish_date'))
