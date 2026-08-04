# -*- coding: utf-8 -*-
"""基于智联真实抓取数据的解析器单元测试"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parse import (parse_page, extract_card, normalize_salary,  # noqa: E402
                       parse_exp_level, salary_text_friendly)


def make_card(tokens):
    """把 token 列表包装成卡片 dict（模拟 parse_page 的分卡结果）"""
    return {'tokens': tokens, 'href': 'http://www.zhaopin.com/jobdetail/CC814231290J00495375603.htm'}


class TestCardExtraction(unittest.TestCase):

    def test_full_card(self):
        """完整字段卡片：连云港安评师岗位（真实数据）"""
        tokens = [
            ('link', 'http://www.zhaopin.com/jobdetail/CC814231290J00495375603.htm',
             '安全工程师（安评师）'),
            ('text', '8000-16000元'),
            ('text', '安全工程'),
            ('text', '安全生产'),
            ('text', '注册安全工程师'),
            ('text', '安全评价师证书'),
            ('text', '注册环评工程师'),
            ('text', '环境保护'),
            ('text', '连云港·海州区·新东街道'),
            ('text', '1-3年'),
            ('text', '大专'),
            ('link', 'https://www.zhaopin.com/companydetail/CZ814231290.htm',
             '连云港九九六注册安全工程师事务所有限公司'),
            ('text', '民营'),
            ('text', '20-99人'),
            ('text', '技术服务'),
            ('text', '3日内活跃'),
        ]
        j = extract_card(make_card(tokens))
        self.assertEqual(j['title'], '安全工程师（安评师）')
        self.assertEqual(j['job_id'], 'CC814231290J00495375603')
        self.assertEqual(j['salary'], (8000, 16000))
        self.assertEqual(j['salary_text'], '8000-16000元')
        self.assertEqual(j['education'], '大专')
        self.assertEqual(j['edu_level'], 3)
        self.assertEqual(j['experience'], '1-3年')
        self.assertEqual(j['exp_level'], 2)
        self.assertEqual(j['location'], '连云港·海州区·新东街道')
        self.assertEqual(j['city'], '连云港')
        self.assertEqual(j['district'], '海州区')
        self.assertEqual(j['company'], '连云港九九六注册安全工程师事务所有限公司')
        self.assertEqual(j['company_type'], '民营')
        self.assertEqual(j['company_size'], '20-99人')
        self.assertEqual(j['industry'], '技术服务')
        self.assertIn('注册安全工程师', j['tags'])
        self.assertIn('安全评价师证书', j['tags'])
        self.assertTrue(j['has_cert'])
        self.assertFalse(j['outsource'])

    def test_no_salary_and_limitless(self):
        """无薪资 + 经验不限 + 学历不限：台州沐安注册安全工程师（真实数据）"""
        tokens = [
            ('link', 'http://www.zhaopin.com/jobdetail/CCL1248467090J40178247503.htm',
             '注册安全工程师'),
            ('text', '8000-12000元'),
            ('text', '注册安全工程师'),
            ('text', '中级注册安全工程师'),
            ('text', '台州·玉环市·芦浦镇'),
            ('text', '经验不限'),
            ('text', '学历不限'),
            ('link', 'https://www.zhaopin.com/companydetail/CZL1248467090.htm', '台州沐安安全咨询有限公司'),
            ('text', '其它'),
            ('text', '20人以下'),
            ('text', '技术服务'),
        ]
        j = extract_card(make_card(tokens))
        self.assertEqual(j['salary'], (8000, 12000))
        self.assertEqual(j['experience'], '经验不限')
        self.assertEqual(j['exp_level'], 0)
        self.assertEqual(j['education'], '学历不限')
        self.assertEqual(j['edu_level'], 0)
        self.assertEqual(j['company_size'], '20人以下')

    def test_wan_salary_and_state_enterprise(self):
        """万单位薪资 + 国企：山东蓬渤化工安全工程师（真实数据）"""
        tokens = [
            ('link', 'http://www.zhaopin.com/jobdetail/CC466965180J40878564505.htm', '化工安全工程师'),
            ('text', '8000-10000元'),
            ('text', '安全管理'),
            ('text', '注册安全工程师'),
            ('text', '龙岩·长汀县·汀州镇'),
            ('text', '5-10年'),
            ('text', '本科'),
            ('link', 'https://www.zhaopin.com/companydetail/CZ466965180.htm',
             '山东省蓬渤安全环保服务有限公司'),
            ('text', '国企'),
            ('text', '100-299人'),
            ('text', '石油/石化'),
        ]
        j = extract_card(make_card(tokens))
        self.assertEqual(j['company_type'], '国企')
        self.assertEqual(j['company_size'], '100-299人')
        self.assertEqual(j['industry'], '石油/石化')
        self.assertEqual(j['exp_level'], 4)
        self.assertEqual(j['edu_level'], 4)

    def test_outsource_flag(self):
        """外派岗检测：南京周全 安全工程师（真实数据，含外派图标）"""
        tokens = [
            ('link', 'http://www.zhaopin.com/jobdetail/CC628139980J40866505311.htm', '安全工程师'),
            ('img', 'https://img09.zhaopin.com/2012/other/mobile/capp/position/ui24/tag_JD_waipai.png'),
            ('text', '9000-15000元'),
            ('text', '安全管理'),
            ('text', '注册安全工程师'),
            ('text', 'EHS合规管理'),
            ('text', '南京·六合·龙池'),
            ('text', '5-10年'),
            ('text', '学历不限'),
            ('link', 'https://www.zhaopin.com/companydetail/CZ628139980.htm', '南京周全安全咨询有限公司'),
            ('text', '股份制企业'),
            ('text', '20-99人'),
            ('text', '咨询服务'),
        ]
        j = extract_card(make_card(tokens))
        self.assertTrue(j['outsource'])

    def test_high_school(self):
        """高中学历 + 薪资 8k-10k：辽宁金帝消防（真实数据）"""
        tokens = [
            ('link', 'http://www.zhaopin.com/jobdetail/CC605158720J40784714706.htm', '安全工程师'),
            ('text', '8000-10000元'),
            ('text', '石油化工工程'),
            ('text', '安全员C本'),
            ('text', '中级注册安全工程师'),
            ('text', '一级动火'),
            ('text', '大连·金州·海青岛'),
            ('text', '1-3年'),
            ('text', '高中'),
            ('link', 'https://www.zhaopin.com/companydetail/CZ605158720.htm',
             '辽宁金帝消防安全工程有限公司'),
            ('text', '民营'),
            ('text', '20-99人'),
            ('text', '检测/认证/计量'),
        ]
        j = extract_card(make_card(tokens))
        self.assertEqual(j['education'], '高中')
        self.assertEqual(j['edu_level'], 1)
        self.assertTrue(j['has_cert'])  # 安全员C本

    def test_html_full_pipeline(self):
        """最小 HTML 全链路：HTML -> tokens -> 卡片 -> 字段"""
        html = '''
        <html><head><script>var x=1;</script></head><body>
        <div class="joblist-box__item">
          <a href="http://www.zhaopin.com/jobdetail/CC111111111J00000000001.htm">安全工程师</a>
          <span>6000-8000元</span>
          <span>注册安全工程师</span>
          <span>应急管理</span>
          <span>武汉·洪山</span>
          <span>3-5年</span>
          <span>本科</span>
          <a href="https://www.zhaopin.com/companydetail/CZ111111111.htm">武汉某某安全技术有限公司</a>
          <span>民营</span><span>100-299人</span><span>技术服务</span>
        </div>
        <div class="joblist-box__item">
          <img src="https://img09.zhaopin.com/2012/other/mobile/capp/position/ui24/tag_JD_waipai.png"/>
          <a href="http://www.zhaopin.com/jobdetail/CC222222222J00000000002.htm">驻点安全工程师</a>
          <span>1-1.5万</span>
          <span>消防管理</span>
          <span>深圳·福田·福田街道</span>
          <span>3-5年</span>
          <span>本科</span>
          <a href="https://www.zhaopin.com/companydetail/CZ222222222.htm">深圳市安慧安全技术咨询有限公司</a>
          <span>民营</span><span>20-99人</span><span>咨询服务</span>
        </div>
        </body></html>
        '''
        jobs = parse_page(html)
        self.assertEqual(len(jobs), 2)
        j0, j1 = jobs[0], jobs[1]
        self.assertEqual(j0['title'], '安全工程师')
        self.assertEqual(j0['salary'], (6000, 8000))
        self.assertEqual(j0['city'], '武汉')
        self.assertEqual(j1['title'], '驻点安全工程师')
        self.assertEqual(j1['salary'], (10000, 15000))
        self.assertTrue(j1['outsource'])
        # script 内容不应污染文本
        for j in jobs:
            self.assertNotIn('var x', ' '.join(j['tags']))


class TestSalary(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize_salary('8000-16000元'), (8000, 16000))
        self.assertEqual(normalize_salary('1-1.5万'), (10000, 15000))
        self.assertEqual(normalize_salary('1.2-2.4万'), (12000, 24000))
        self.assertEqual(normalize_salary('6-8千/月'), (6000, 8000))
        self.assertEqual(normalize_salary('10-20万/年'), (8333, 16667))
        self.assertIsNone(normalize_salary('面议'))
        self.assertIsNone(normalize_salary(''))

    def test_friendly(self):
        self.assertEqual(salary_text_friendly('8000-16000元'), '8k-16k')
        self.assertEqual(salary_text_friendly('1-1.5万'), '1万-1.5万')


class TestExpLevel(unittest.TestCase):
    def test_levels(self):
        self.assertEqual(parse_exp_level('经验不限'), 0)
        self.assertEqual(parse_exp_level('应届生'), 1)
        self.assertEqual(parse_exp_level('1-3年'), 2)
        self.assertEqual(parse_exp_level('3-5年'), 3)
        self.assertEqual(parse_exp_level('5-10年'), 4)
        self.assertEqual(parse_exp_level('10年以上'), 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
