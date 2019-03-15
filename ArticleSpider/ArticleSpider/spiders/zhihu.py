# -*- coding: utf-8 -*-
import json
import re
import time
from urllib import parse

import scrapy
from datetime import datetime
from scrapy.loader import ItemLoader
from ..items import ZhihuAnswerItem, ZhihuQuestionItem

from ..utils.zhihu_login.zhihu_login import ZhihuAccount

custom_settings = {
    "FEED_EXPORT_ENCODING" : 'utf-8'
 }


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['https://www.zhihu.com/']

    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cis_labeled%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%2A%5D.topics&limit={1}&offset={2}&platform=desktop&sort_by=default"

    zhihu_main_url = "https://www.zhihu.com/api/v3/feed/topstory/recommend?session_token={0}&desktop=true&page_number={1}&limit={2}&action=down&after_id={3}"

    headers = {
        'Host': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
    }

    custom_settings = {
        "FEED_EXPORT_ENCODING": 'utf-8'
    }

    def parse(self, response):
        """
        提取出页面中的所有url  并跟踪这些url进行进一步爬去
        如果提取的url中格式为/queston/xxx就下载之后直接进入解析函数
        :param response:知乎主页
        :return:问题详情页请求
        """
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls = filter(lambda x:True if x.startswith("https") else False, all_urls)
        for url in all_urls:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
            if match_obj:
                # 如果有question
                request_url = match_obj.group(1)
                question_id = match_obj.group(2)
                yield scrapy.Request(request_url, headers=self.headers,  meta={"question_id": question_id}, callback=self.parse_question)

        match_token = re.search(".*session_token=([a-zA-Z0-9]*)&desktop=true.*", response.text)
        match_arg = re.search(".*page_number=(\d)&limit=(\d)&action=down&after_id=(\d+)", response.text)
        token = match_token.group(1)
        page_number = match_arg.group(1)
        limit = match_arg.group(2)
        after_id = match_arg.group(3)
        if token and page_number and limit and after_id:
            yield scrapy.Request(self.zhihu_main_url.format(token, page_number, limit, after_id), headers=self.headers, callback=self.parse_more_question)

    def parse_question(self, response):
        # 处理question页面， 从页面中提取出具体的question item
        item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
        item_loader.add_css("title", "h1.QuestionHeader-title::text")
        item_loader.add_css("content", ".QuestionHeader-detail")
        item_loader.add_value("url", response.url)
        item_loader.add_value("zhihu_id", int(response.meta.get("question_id", "0")))
        item_loader.add_css("answer_num", ".List-headerText span::text")
        item_loader.add_css("comments_num", ".QuestionHeader-Comment button::text")
        item_loader.add_css("watch_user_num", ".NumberBoard-itemValue::text")
        item_loader.add_css("topics", ".QuestionHeader-topics .Popover div::text")

        question_item = item_loader.load_item()

        yield scrapy.Request(self.start_answer_url.format(response.meta.get("question_id", "0"), 5, 20), headers=self.headers, callback=self.parse_answer)

        yield question_item

    def parse_answer(self, response):
        # 处理回答
        ans_json = json.loads(response.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        # 提取anwser具体字段
        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else answer["excerpt"]
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]

            if answer_item:
                yield answer_item
            else:
                pass

        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)

    def parse_more_question(self, response):
        question_json = json.loads(response.text)
        for question in question_json["data"]:
            try:
                question_tag = question["target"]["question"]
                question_id = question_tag["id"]
            except:
                question_id = question["target"]["id"]
            if question_id:
                question_url = "https://www.zhihu.com/question/"
                yield scrapy.Request(question_url+str(question_id), headers=self.headers, meta={"question_id": question_id}, callback=self.parse_question)
        is_end = question_json["paging"]["is_end"]
        if not is_end:
            next_url = question_json["paging"]["next"]
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_more_question)

    def start_requests(self):
        account = ZhihuAccount('17138957451', 'lben5572')
        is_login = account.login(captcha_lang='en', load_cookies=True)
        if is_login:
            cookies = account.get_cookies()
            cookie_dict = {}
            for item in cookies:
                cookie_dict[item.name] = item.value
            return [scrapy.Request(
                url=self.start_urls[0],
                dont_filter=True,
                cookies=cookie_dict,
                headers=self.headers
            )]

