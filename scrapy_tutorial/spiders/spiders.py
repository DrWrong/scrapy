# -*- coding: utf-8 -*-
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
# from scrapy_tutorial.items import Project
from bs4 import BeautifulSoup
from urlparse import urlparse
from base64 import urlsafe_b64decode
from datetime import datetime
import re
import requests
from scrapy_tutorial.utils import remove_unuse_character
from scrapy_tutorial.utils import connection
from logging import getLogger

logger = getLogger(__file__)

class RongMofangSpider(CrawlSpider):


    name = "rongmofang"
    allowed_domains = ["www.rongmofang.com"]
    start_urls = ["https://www.rongmofang.com/project/list"]

    rules = [
        Rule(LinkExtractor(allow=(r'project/list(\?page=\d+)+',))),
        Rule(LinkExtractor(allow=(r"project/detail\?id=\d+")),
             callback="parse_project")
    ]

    def parse_project(self, response):
        print "start parseing"
        url  = response.url
        pid = int(urlparse(url).query.split("=")[1])
        project = connection.Project.one({"id": pid})
        if project is not None:
            return project
        # logger.debug("start parseing")
        soup = BeautifulSoup(response.body)
        project = connection.Project()

        # parse 头部信息
        financial_already = soup.find(
            "span", style="color: #e86e00;").text.strip()
        project["financial_already"] = remove_unuse_character(
            financial_already)
        financial_left = soup.find(
            "span", style="color: #3498DB;").text.strip()
        project["financial_left"] = remove_unuse_character(financial_left)
        project_header = soup.find("table", class_="project").find_all("tr")
        project["profit_method"] = project_header[
            1].find_all("td")[1].text.strip()

        project["time_limit"] = project_header[
            1].find_all("td")[3].text.strip()

        project["risk_management"] = project_header[
            2].find_all("td")[1].text.strip()

        project["expected_interest_date"] = datetime.strptime(
            project_header[2].find_all("td")[3].text.strip(),
            "%Y-%m-%d",
        )

        # parse 第一个table
        project_info = soup.find("div", id="fa-icon-1").table.find_all("tr")
        tr0 = project_info[0]
        project["project_name"] = tr0.find_all("td")[1].text.strip()
        tr1 = project_info[1]
        project["project_region"] = tr1.find_all("td")[1].text.strip()

        if tr1.find_all("td")[2].text.strip() == u"融资方：":
            project["project_type"] = u"融资"
            company_link_url = tr1.find_all("td")[3].a.attrs["href"]
            b64encodestr = urlparse(company_link_url).query.split("=")[1]
            b64encodestr = b64encodestr.replace("$", "=")
            try:
                company_id = urlsafe_b64decode(b64encodestr)
            except:
                company_id = b64encodestr
            company = connection.CompanyInfo.one({"company_id": company_id})
            if company is None:
                company = self.create_financial_company(soup, company_id)
        else:
            project["project_type"] = u"转让"
            company = self.create_transfer_company(soup)

        # logger.debug("till now everything is ok")
        print "till now everything is ok"
        project["company_id"] = company["_id"]

        tr2 = project_info[2]
        interest_per_year = tr2.find_all("td")[1].text.strip()
        project["interest_per_year"] = re.sub(
            r'\r\n|\s+', '', interest_per_year)
        project["payback_date"] = datetime.strptime(
            tr2.find_all("td")[3].text.strip(),
            "%Y-%m-%d",
        )
        try:
            tr3 = project_info[3]
            project["capitl_useage"] = tr3.find_all("td")[1].text.strip()
            tr4 = project_info[4]
            project["payback_source"] = tr4.find_all("td")[1].text.strip()
            if len(project_info) == 6:
                tr5 = project_info[5]
                project["additional"] = tr5.find_all("td")[1].text.strip()
            project["expected_profit"] = self.create_expected_profit(soup)
            project["invest_records"] = self.create_invest_records(response)
        except IndexError:
            pass

        # 风险控制信息
        # guarantee_link = soup.select("table.project td.filed a")[0]
        # href = guarantee_link.attrs["href"]
        trs = soup.find("div", id="fa-icon-2").table.find_all("tr")
        # tds = trs[0].find_all("td")
        guarantee_link = trs[0].a.attrs["href"]
        guarantee_id = int(guarantee_link.split("/")[-1])
        guarantee = connection.GuaranteeCompanyInfo.one({"id": guarantee_id})
        if guarantee is None:
            guarantee = self.create_guarantee(
                trs, project["project_type"], guarantee_id)
        project["guarantee_id"] = guarantee["_id"]
        project.save()
        company["projects"].append(project)
        company.save()
        guarantee["projects"].append(project)
        guarantee.save()
        # print project
        return project

    def create_guarantee(self, trs, project_type, guarantee_id):
        guarantee = connection.GuaranteeCompanyInfo()
        guarantee["id"] = guarantee_id
        if project_type == u"融资":
            guarantee = self.create_financial_guarantee(guarantee, trs)
        else:
            guarantee = self.create_transfer_guarantee(guarantee, trs)
        guarantee.save()
        return guarantee

    def create_financial_guarantee(self, guarantee, trs):
        guarantee["name"]  = trs[0].find_all("td")[1].text.strip()
        guarantee["balance"] = trs[1].find_all("td")[1].text.strip()
        guarantee["info"] = trs[2].find_all("td")[1].text.strip()
        return guarantee

    def create_transfer_guarantee(self, guarantee, trs):
        guarantee["name"] = trs[0].a.text.strip()
        guarantee["strategy"] = trs[0].find_all("td")[1].text.strip()
        guarantee["info"] = trs[1].find_all('td')[1].text.strip()
        return guarantee

    def create_invest_records(self, response):
        # sdfds()
        logger.debug("crete_invest_records start")
        parmas = {
            "projectId": urlparse(response.url).query.split("=")[1]}
        r = requests.get(
            "https://www.rongmofang.com/project/allinvester", parmas)
        logger.debug("successfully get invest")
        soup = BeautifulSoup(r.text)
        result = []
        for record in soup.find_all("tr")[1:]:
            tds = record.find_all("td")
            i = 0
            while i < 6:
                result.append({
                    "name": tds[0 + i].text.strip(),
                    "money": tds[1 + i].text.strip(),
                    "time": datetime.strptime(
                        tds[2+i].text.strip(),
                        "%Y-%m-%d %H:%M:%S"
                    )
                })
                i += 4
        return result

    def create_expected_profit(self, soup):
        records = soup.select(
            "div.wall table.table-bordered tbody")[0].find_all("tr")
        i = 0
        results = []
        while(i + 1 < len(records)):
            td1 = records[i].find_all("td")
            td2 = records[i + 1].find_all("td")
            temp_dict = {
                "expected_pay_time": datetime.strptime(
                    td1[0].text.strip(),
                    "%Y-%m-%d"),
                "details": [
                    {
                        "type": td1[1].text.strip(),
                        "amount": td1[2].text.strip(),
                    },
                    {
                        'type': td2[0].text.strip(),
                        "amount": td2[1].text.strip(),
                    }
                ]
            }
            results.append(temp_dict)
            i = i + 2
        return results

    # def create_company(self, soup, company_id, project_type):
    #     company = connection.CompanyInfo()
    #     # company_link = soup.select("table.project td.filed a")[0]
    #     # href = company_link.attrs["href"]
    #     # soup2 = BeautifulSoup(requests.get(href).text)
    #     # company["company_name"] = soup2.h3.text.srtip()
    #     # company["comany_description"] = soup2.find_all("p")[15].text.strip()
    #     company["company_id"] = company_id
    #     if project_type == u"融资":
    #         company = self.create_financial_company(company, soup)
    #     else:
    #         company = self.create_transfer_company(soup)
    #     company.save()
    #     return company

    def create_financial_company(self, soup, company_id):
        company = connection.CompanyInfo()
        company["company_id"] = company_id.decode()
        company_info = soup.find(
            "div", id="fa-icon-1").find_all("table")[1].find_all("tr")
        tr0 = company_info[0]
        company["register_time"] = datetime.strptime(
            tr0.find_all("td")[1].text.strip(),
            "%Y-%m-%d",
        )
        company["register_capital"] = tr0.find_all("td")[3].text.strip()
        try:
            tr1 = company_info[1]
            company["assets"] = tr1.find_all("td")[1].text.strip()
            company["property"] = tr1.find_all("td")[3].text.strip()
            company["industry"] = company_info[2].find_all("td")[1].text.strip()
            company["introduction"] = company_info[3].p.text.strip()
            company["assets_situation"] = company_info[4].p.text.strip()
            company["law_situation"] = company_info[5].p.text.strip()
            company['credit_situation'] = company_info[6].p.text.strip()
        except IndexError:
            pass
        company["financial_situation"] = []
        financial = soup.find(
            "div", id="fa-icon-1").find_all("table")[2]
        for tr in financial.find_all("tr")[1:]:
            tds = tr.find_all("td")
            temp_dict = {
                "year": int(tds[0].text.strip()),
                "main_income": float(tds[1].text.strip()),
                "profit": float(tds[2].text.strip()),
                "total_capital": float(tds[3].text.strip()),
                "pure_capital": float(tds[4].text.strip()),
                'balance_propery': float(tds[5].text.strip().split()[0]) / 100,
            }
            company["financial_situation"].append(temp_dict)
        company.save()
        return company

    def create_transfer_company(self, soup):
        company = connection.CompanyInfo()
        company_info = soup.find(
            "div", id="fa-icon-1").find_all("table")[1].find_all("tr")
        tds = company_info[0].find_all("td")
        company["profit_amount"] = tds[1].text.strip()
        company["profit_limit"] = tds[3].text.strip()
        company["profit_detial"] = company_info[1].p.text.strip()
        company["introduction"] = company_info[2].p.text.strip()
        company.save()
        return company
