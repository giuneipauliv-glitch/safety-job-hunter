# -*- coding: utf-8 -*-
"""用智联真实抓取数据构造种子 jobs.json（开发测试用）"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.parse import salary_text_friendly  # noqa: E402

TODAY = '2026-08-03'
YESTERDAY = '2026-08-02'


def j(job_id, title, company, company_url, salary_text, location, exp, edu,
      ctype, csize, industry, tags, link, outsource=False, first_seen=TODAY,
      has_cert=None, source='zhaopin', job_type=None):
    from src.parse import normalize_salary, parse_exp_level, EDU_LEVEL
    if job_type is None:
        from src.fetch import detect_job_type
        job_type = detect_job_type(title)
    item = {
        'job_id': job_id, 'title': title, 'salary': normalize_salary(salary_text),
        'salary_text': salary_text, 'education': edu,
        'edu_level': EDU_LEVEL.get(edu, -1), 'experience': exp,
        'exp_level': parse_exp_level(exp), 'location': location,
        'city': location.split('·')[0],
        'district': location.split('·')[1] if '·' in location else '',
        'company': company, 'company_url': company_url,
        'company_type': ctype, 'company_size': csize, 'industry': industry,
        'tags': tags, 'link': link, 'outsource': outsource,
        'first_seen': first_seen, 'last_seen': TODAY, 'keyword': '安全工程师',
        'source': source, 'job_type': job_type,
    }
    if has_cert is None:
        from config import CERT_KEYWORDS
        all_t = ' '.join([title, company, ' '.join(tags)])
        item['has_cert'] = any(k in all_t for k in CERT_KEYWORDS)
    else:
        item['has_cert'] = has_cert
    return item


jobs = [
    j('CC814231290J00495375603', '安全工程师（安评师）',
      '连云港九九六注册安全工程师事务所有限公司', 'https://www.zhaopin.com/companydetail/CZ814231290.htm',
      '8000-16000元', '连云港·海州区·新东街道', '1-3年', '大专', '民营', '20-99人', '技术服务',
      ['安全工程', '安全生产', '注册安全工程师', '安全评价师证书', '注册环评工程师', '环境保护'],
      'http://www.zhaopin.com/jobdetail/CC814231290J00495375603.htm'),
    j('CC828204710J40924001612', '中级注册安全工程师',
      '北京鼎晟昊冉注册安全工程师事务所有限公司', 'https://www.zhaopin.com/companydetail/CZ828204710.htm',
      '6000-7000元', '北京·顺义·双丰', '经验不限', '大专', '民营', '20-99人', '技术服务',
      ['注册安全工程师'],
      'http://www.zhaopin.com/jobdetail/CC828204710J40924001612.htm'),
    j('CCL1327801410J40841892309', '驻点安全工程师',
      '深圳市安慧安全技术咨询有限公司', 'https://www.zhaopin.com/companydetail/CZL1327801410.htm',
      '1-1.5万', '深圳·福田·福田街道', '3-5年', '本科', '民营', '20-99人', '咨询服务',
      ['消防管理', '安全管理'],
      'http://www.zhaopin.com/jobdetail/CCL1327801410J40841892309.htm', outsource=True),
    j('CCL1248467090J40178247503', '注册安全工程师',
      '台州沐安安全咨询有限公司', 'https://www.zhaopin.com/companydetail/CZL1248467090.htm',
      '8000-12000元', '台州·玉环市·芦浦镇', '经验不限', '学历不限', '其它', '20人以下', '技术服务',
      ['注册安全工程师', '中级注册安全工程师'],
      'http://www.zhaopin.com/jobdetail/CCL1248467090J40178247503.htm', outsource=True),
    j('CC628139980J40866505311', '安全工程师',
      '南京周全安全咨询有限公司', 'https://www.zhaopin.com/companydetail/CZ628139980.htm',
      '9000-15000元', '南京·六合·龙池', '5-10年', '学历不限', '股份制企业', '20-99人', '咨询服务',
      ['安全管理', '注册安全工程师', 'EHS合规管理', '化工项目安全管控', '特种作业人员管理'],
      'http://www.zhaopin.com/jobdetail/CC628139980J40866505311.htm', outsource=True),
    j('CC527374224J00214731707', '网络与信息安全工程师',
      '中达宝通信息安全技术有限公司', 'https://www.zhaopin.com/companydetail/CZ527374220.htm',
      '5000-10000元', '郑州·管城·圃田', '经验不限', '本科', '民营', '20-99人', '检测/认证/计量',
      ['安全', '网络安全', '信息安全', '系统安全'],
      'http://www.zhaopin.com/jobdetail/CC527374224J00214731707.htm', has_cert=False),
    j('CC466965180J40878564505', '化工安全工程师',
      '山东省蓬渤安全环保服务有限公司', 'https://www.zhaopin.com/companydetail/CZ466965180.htm',
      '8000-10000元', '龙岩·长汀县·汀州镇', '5-10年', '本科', '国企', '100-299人', '石油/石化',
      ['安全管理', '注册安全工程师'],
      'http://www.zhaopin.com/jobdetail/CC466965180J40878564505.htm', first_seen=YESTERDAY),
    j('CC200640120J40823509316', '安全评价师/注册安全工程师（化工、工贸）',
      '兴达安全', 'https://www.zhaopin.com/companydetail/CZ200640120.htm',
      '1.2-2.4万', '绍兴·越城区·灵芝街道', '3-5年', '本科', '民营', '20-99人', '技术服务',
      [],
      'http://www.zhaopin.com/jobdetail/CC200640120J40823509316.htm', first_seen=YESTERDAY),
    # ---- 国聘样例（校招，国企） ----
    j('gp_1001', '安全管理岗（2026届校招）',
      '中国建筑第八工程局有限公司', 'https://www.iguopin.com/',
      '面议', '上海·浦东新区', '应届生', '本科', '国企', '10000人以上', '建筑',
      ['安全工程', '施工安全', '安全生产'],
      'https://www.iguopin.com/job/detail?id=1001', source='iguopin'),
    j('gp_1002', '安全环保专员（校园招聘）',
      '中国石油天然气股份有限公司', 'https://www.iguopin.com/',
      '面议', '北京·朝阳', '经验不限', '本科', '国企', '10000人以上', '石油/石化',
      ['安全工程', '职业健康', '环保'],
      'https://www.iguopin.com/job/detail?id=1002', source='iguopin'),
]

data = {
    'meta': {
        'updated_at': '2026-08-03 08:00:00',
        'updated_date': TODAY,
        'total': len(jobs),
        'new_today': sum(1 for x in jobs if x['first_seen'] == TODAY),
        'source': '智联招聘',
    },
    'jobs': jobs,
}

out = os.path.join(ROOT, 'data', 'jobs.json')
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
print('fixture written:', out, len(jobs), 'jobs')
for x in jobs:
    print(' -', x['title'], '|', x['city'], '|', salary_text_friendly(x['salary_text']),
          '| 新增' if x['first_seen'] == TODAY else '| 旧', '| 外派' if x['outsource'] else '')
