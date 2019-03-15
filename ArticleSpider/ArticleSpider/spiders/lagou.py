# -*- coding: utf-8 -*-
import re
from datetime import datetime

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from ..tools.crawl_xici_ip import GetIP
from ..items import LagouJobItemLoader, LagouJobItem
from ..utils.common import get_md5


class LagouSpider(CrawlSpider):
    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['https://www.lagou.com']

    proxy_url = ''

    # headers = {
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
    # }

    custom_settings = {
        "COOKIES_ENABLED": False,  # 防止被重定向
        }


    rules = (
        # Rule(LinkExtractor(allow=('zhaopin/.*',)), follow=True),
        # Rule(LinkExtractor(allow=('gongsi/j\d+.html',)), follow=True),
        Rule(LinkExtractor(allow=r'jobs/\d+.html'), callback='parse_job', follow=True),
    )

    handle_httpstatus_list = [302]

    # def parse_start_url(self, response):
    #     return [scrapy.Request('https://passport.lagou.com/login/login.html', headers=self.headers)]
    #
    # def process_results(self, response, results):
    #     return results

    def parse_job(self, response):

        if response.status == 302:
            pass
            # get_ip = GetIP()
            # url = response.url
            # return scrapy.Request(url, meta={"proxy": get_ip})
            # url = response.url
            # url_id = re.findall(r"\d*", url)
            # while '' in url_id:
            #     url_id.remove('')
            # url_id = url_id[0]
            # sort_ps = re.match(".*job.*", url)
            # if sort_ps:
            #     sort = 'jobs'
            # else:
            #     sort = 'gongsi'
            # url_302 = "https://www.lagou.com/utrack/verify.html?t=1&f=https%3A%2F%2Fwww.lagou.com%2F{0}%2F{1}.html".format(sort, url_id)
            # return scrapy.Request(url_302, callback=self.parse_img)

        # 解析拉勾网的职位
        item_loader = LagouJobItemLoader(item=LagouJobItem(), response=response)
        item_loader.add_css("title", ".job-name::attr(title)")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        salary = response.css(".job_request .salary::text").extract()
        if salary:
            salary = salary[0]
            salary_list = salary.split("-")
            if len(salary_list) == 2:
                salary_min = salary_list[0].replace('k', '')
                salary_max = salary_list[1].replace('k', '')
                item_loader.add_value('salary_min', salary_min)
                item_loader.add_value('salary_max', salary_max)
        """
        crawl_time =scrapy.Field()
        crawl_update_time =scrapy.Field()
        """
        item_loader.add_xpath('job_city', '//*[@class="job_request"]/p/span[2]/text()')
        item_loader.add_xpath('work_years', '//*[@class="job_request"]/p/span[3]/text()')
        item_loader.add_xpath('degree_need', '//*[@class="job_request"]/p/span[4]/text()')
        item_loader.add_xpath('job_type', '//*[@class="job_request"]/p/span[5]/text()')
        # item_loader.add_css('tag', '.position-label li::text')
        item_loader.add_css('pulish_time', 'p.publish_time::text')
        item_loader.add_css('job_advantage', '.job-advantage p::text')
        item_loader.add_css('job_desc', '.job_bt .job-detail')
        item_loader.add_css('job_addr', '.job-address .work_addr')
        item_loader.add_css('company_name', '#job_company dt a img::attr(alt)')
        item_loader.add_css('company_url', '#job_company dt a::attr(href)')
        item_loader.add_value('crawl_time', datetime.now())

        job_item = item_loader.load_item()

        return job_item

    def parse_img(self, response):
        pass




