  # -*- coding: utf-8 -*-
import scrapy
from pydispatch import dispatcher
from scrapy import signals
from scrapy.http import Request
from urllib import parse

from ..items import JobboleArticleItem, ArticleItemLoader
from  ..utils.common import get_md5


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    # 收集伯乐在线所有404的url 以及404页面
    handle_httpstatus_list = [404]

    def __init__(self):
        self.fail_urls = []
        dispatcher.connect(self.handle_spider_closed, signals.spider_closed)

    def handle_spider_closed(self, spider, reason):
        self.crawler.stats.set_value("failed_urls", ",".join(self.fail_urls))

    def parse(self, response):
        '''
        1、获取文章列表页，并交给下载器下载
        2、获取下一页的url,并交给下载器
        :param response:
        :return:
        '''
        if response.status == 404:
            self.fail_urls.append(response.url)
            self.crawler.stats.inc_value("failed_url")

        post_nodes = response.css("#archive .floated-thumb")
        for post_node in post_nodes:
            image_url = post_node.css(".post-thumb img::attr(src)").extract_first("")
            post_url = post_node.css(".post-meta a::attr(href)").extract_first("")
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url":image_url}, callback=self.parse_detail)

        # 提取下一页
        next_urls = response.css(".next.page-numbers::attr(href)").extract_first("")
        if next_urls:
            yield Request(url=parse.urljoin(response.url, next_urls), callback=self.parse)

    def parse_detail(self, response):

        front_image_url = response.meta.get("front_image_url", "")

        # 通过item loader加载item
        item_loader = ArticleItemLoader(item=JobboleArticleItem(), response=response)
        item_loader.add_css("title", ".entry-header h1::text")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_value("front_image_url", [front_image_url])
        item_loader.add_css("create_data", "p.entry-meta-hide-on-mobile::text")
        item_loader.add_css("fav_nums", "span.bookmark-btn::text")
        item_loader.add_css("content", ".entry")
        item_loader.add_css("tag", "p.entry-meta-hide-on-mobile a::text")
        item_loader.add_css("comment_nums", "a[href='#article-comment'] span::text")
        item_loader.add_css("praise_num", ".vote-post-up h10::text")

        article_item = item_loader.load_item()

        yield article_item