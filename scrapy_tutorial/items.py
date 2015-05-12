# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from mongokit import Document, IS, OR
from scrapy.item import BaseItem
from bson.objectid import ObjectId
from datetime import datetime
from scrapy_tutorial.utils import connection


class MongoBaseItem(Document, BaseItem):
    pass


@connection.register
class Project(MongoBaseItem):
    __database__ = "rongmofang"
    __collection__ = "project"
    structure = {
        "id": int,
        "project_type": IS(u"融资", u"转让"),
        "financial_already": unicode,  # 项目融资金额
        "financial_left": unicode,  # 还需融资额
        'project_name': unicode,
        'project_region': unicode,
        "company_id": ObjectId,
        "guarantee_id": ObjectId,
        "profit_method": unicode,  # 获取收益方式
        "time_limit": unicode,  # 融资期限
        "risk_management": unicode,  # 风险措施
        "expected_interest_date": datetime,  # 预计起息日
        'interest_per_year': unicode,
        'payback_date': datetime,
        'capitl_useage': unicode,
        'payback_source': unicode,
        'additional': unicode,
        'expected_profit': [{
            "expected_pay_time": datetime,
            'details': [{
                "type": unicode,
                "amount": unicode,
            }],
        }],
        'invest_records': [{
            'name': unicode,
            'money': unicode,
            'time': datetime,
        }]
    }


@connection.register
class CompanyInfo(MongoBaseItem):

    __database__ = "rongmofang"
    __collection__ = "companyinfo"

    use_autorefs = True
    structure = {
        # "cid": int,
        "company_id": OR(unicode, basestring),
        # "company_name": unicode,
        # "compnay_description": unicode,
        "register_time": datetime,
        "register_capital": unicode,  # 注册资本
        "assets": unicode,  # 净资产
        "property": unicode,  # 公司性质
        "industry": unicode,  # 所在行业
        "introduction": unicode,  # 企业简介
        "assets_situation": unicode,
        "law_situation": unicode,  # 涉诉情况
        "credit_situation": unicode,  # 征信情况
        "financial_situation": [{
            'year': int,
            'main_income': float,  # 主营收入
            'profit': float,  # 净利润
            'total_capital': float,  # 总资产
            'pure_capital': float,  # 净资产
            "balance_propery": float,  # 资产负债率
        }],
        # 转让类企业信息
        "profit_amount": unicode,  # 收益权金额
        "profit_limit": unicode,  # 收益权期限
        "profit_detial": unicode,  # 收益权详情
        "projects": [Project]
    }


@connection.register
class GuaranteeCompanyInfo(MongoBaseItem):
    __database__ = "rongmofang"
    __collection__ = "guarantee_company_info"
    use_autorefs = True
    structure = {
        "id": int,
        # "description": unicode,
        "name": unicode,
        "balance": unicode,
        "info": unicode,
        "strategy": unicode,

        "projects": [Project],
    }
