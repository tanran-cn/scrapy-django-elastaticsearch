# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import re
import time
import datetime

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from w3lib.html import remove_tags

from .models.es_types import ArticleType, ZhihuQuestionType, ZhihuAnswerType
from .utils.common import extract_num
from elasticsearch_dsl.connections import connections

es = connections.create_connection(ArticleType._doc_type.using)


class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


def date_convert(value):

    if isinstance(value, str):
        value = value.strip().replace("·","")
        try:
            create_data = datetime.datetime.strptime(value, "%Y/%m/%d ").date()
        except Exception as e:
            create_data = datetime.datetime.now().date()
        return create_data
    else:
        create_data = datetime.datetime.now().date()

        return create_data


def get_nums_convert(value):
    match_re = re.match(".*(\d+).*", value)
    if match_re:
        nums = match_re.group(1)
    else:
        nums = 0

    return nums


def gen_suggests(index, info_tuple):
    # 根据字符串生成搜索建议数组
    used_words = set()
    suggests = []
    for text, weight in info_tuple:
        if text:
            # 调用es的analyze接口分析字符串
            words = es.indices.analyze(index=index, analyzer="ik_max_word", params={'filter':["lowercase"]}, body=text)
            anylyzed_words = set(r["token"] for r in words["tokens"] if len(r["token"]) > 1)
            new_words = anylyzed_words - used_words
        else:
            new_words = set()

        if new_words:
            suggests.append({"input": list(new_words), "weight": weight})
    return suggests


def return_value(value):
    return value


class ArticleItemLoader(ItemLoader):
    # 自定义ItemLoader
    default_output_processor = TakeFirst()


class JobboleArticleItem(scrapy.Item):
    title = scrapy.Field()
    create_data = scrapy.Field(
        input_processor=MapCompose(date_convert),
    )
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    praise_num = scrapy.Field(
        input_processor=MapCompose(get_nums_convert),
    )
    fav_nums = scrapy.Field(
        input_processor=MapCompose(get_nums_convert),
    )

    comment_nums = scrapy.Field(
        input_processor=MapCompose(get_nums_convert),
    )
    content = scrapy.Field()
    tag = scrapy.Field(
        output_processor=Join(",")
    )
    front_image_url = scrapy.Field(
        output_processor=MapCompose(return_value),
    )
    front_image_path = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                           insert into article(title, url, create_date, fav_nums, url_object_id, content, front_image_url, fornt_image_path, comment_nums, praise_nums, tags)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                             ON DUPLICATE KEY UPDATE fav_nums=VALUES (fav_nums)
                       """
        params = (self["title"], self["url"], self["create_data"], self["fav_nums"], self["url_object_id"], self["content"], self["front_image_url"], self["front_image_path"], self["comment_nums"], self["praise_num"], self["tag"])

        return insert_sql, params

    def save_to_es(self):
        article = ArticleType()
        article.title = self["title"]
        article.create_data = self["create_data"]
        article.content = remove_tags(self["content"])
        article.front_image_url = self["front_image_url"]
        if "front_image_path" in self:
            article.front_image_path = self["front_image_path"]
        article.praise_num = self["praise_num"]
        article.fav_nums = self["fav_nums"]
        article.comment_nums = self["comment_nums"]
        article.url = self["url"]
        article.tag = self["tag"]
        article.meta.id = self["url_object_id"]

        article.suggest = gen_suggests(ArticleType._doc_type.index, ((article.title, 10), (article.tag, 7)))

        article.save()


def remove_splash(value):
    return value.replace("/", "")


def remove_tags_addr(value):
    value = remove_tags(value)
    value = value.replace(" ", "")
    value = value.replace("查看地图", "")
    value = "".join(value.split())
    return value


class LagouJobItem(scrapy.Item):
    # 拉钩网职位信息
    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    salary_min = scrapy.Field()
    job_city = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    salary_max = scrapy.Field()
    work_years = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    degree_need = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    job_type =scrapy.Field()
    pulish_time = scrapy.Field()
    # tag标签有错误
    # tag = scrapy.Field(
    #     input_processor=MapCompose(Join(","))
    # )
    job_advantage = scrapy.Field()
    job_desc =scrapy.Field()
    job_addr =scrapy.Field(
        input_processor=MapCompose(remove_tags_addr),
    )
    company_url =scrapy.Field()
    company_name =scrapy.Field()
    crawl_time =scrapy.Field()
    crawl_update_time =scrapy.Field()

    def get_insert_sql(self):
        """

        :return:
        """
        insert_sql = """
            insert into lagou_job(title, url, url_object_id, salary_min, job_city, salary_max, work_years, degree_need,
            job_type, pulish_time, job_advantage, job_desc, job_addr, company_url, company_name, crawl_time) 
            VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE salary_min=VALUES (salary_min), salary_max=VALUES(salary_max), 
            degree_need=VALUES(degree_need)
        """
        params = (self["title"], self["url"], self["url_object_id"], self["salary_min"], self["job_city"],
                  self["salary_max"], self["work_years"], self["degree_need"], self["job_type"], self["pulish_time"],
                  self["job_advantage"], self["job_desc"], self["job_addr"], self["company_url"],
                  self["company_name"], self["crawl_time"].strftime("%Y-%m-%d %H:%M:%S")
                  )

        return insert_sql, params


class LagouJobItemLoader(ItemLoader):
    # 自定义ItemLoader
    default_output_processor = TakeFirst()


class ZhihuQuestionItem(scrapy.Item):
    # 知乎的问题 item
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field(
        input_processor=MapCompose(date_convert),
    )
    crawl_update_time = scrapy.Field()

    def get_insert_sql(self):
        """
        插入知乎question表的sql语句
        :return: sql语句与字段名组成的元组
        """
        insert_sql = """insert into zhihu_question(zhihu_id, topics, url, title, content, answer_num, comments_num, watch_user_num, crawl_time)
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                   ON DUPLICATE KEY UPDATE answer_num=VALUES (answer_num), comments_num=VALUES (comments_num), watch_user_num=VALUES (watch_user_num)
                                   
                    """
        zhihu_id = self["zhihu_id"][0]
        topics = ",".join(self["topics"])
        url = "".join(self["url"])
        title = "".join(self["title"])
        content = "".join(self["content"])
        # timeArray = time.localtime(self["create_time"])
        # create_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        # timeArray = time.localtime(self["update_time"])
        # update_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        answer_num = extract_num("".join(self["answer_num"]))
        comments_num = extract_num("".join(self["comments_num"]))
        watch_user_num = extract_num("".join(self["watch_user_num"]))
        crawl_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        params = (zhihu_id, topics, url, title, content, answer_num, comments_num, watch_user_num, crawl_time)

        return insert_sql, params

    def save_to_es(self):
        zhihuq = ZhihuQuestionType()
        zhihuq.zhihu_id = self["zhihu_id"][0]
        zhihuq.topics = ",".join(self["topics"])
        zhihuq.url = "".join(self["url"])
        zhihuq.title = "".join(self["title"])
        zhihuq.content = remove_tags(self["content"][0])
        zhihuq.answer_num = extract_num(str(self["answer_num"][0]))
        zhihuq.comments_num = extract_num(str(self["comments_num"][0]))
        zhihuq.watch_user_num = extract_num(str(self["watch_user_num"][0]))
        zhihuq.crawl_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        zhihuq.suggest = gen_suggests(ZhihuQuestionType._doc_type.index, ((zhihuq.title, 10), (zhihuq.topics, 7)))

        zhihuq.save()


class ZhihuAnswerItem(scrapy.Item):
    # 知乎的问题回答item
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    praise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()
    crawl_update_time = scrapy.Field()

    def get_insert_sql(self):
        """
        插入知乎answer表的sql语句
        :return: sql语句与字段名组成的元组
        """
        insert_sql = """insert into zhihu_answer(zhihu_id, url, question_id, author_id, content, praise_num, comments_num, create_time, update_time, crawl_time)
                                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                           ON DUPLICATE KEY UPDATE content=VALUES (content), comments_num=VALUES(comments_num), praise_num=VALUES(praise_num), update_time=VALUES(update_time)
                            """
        zhihu_id = self["zhihu_id"]
        url = "".join(self["url"])
        question_id = self["question_id"]
        author_id = self["author_id"]
        content = "".join(self["content"])
        praise_num = self["praise_num"]
        comments_num = self["comments_num"]
        # create_time = datetime.datetime.fromtimestamp(self["create_time"]).strftime("%Y-%m-%d %H:%M:%S") 也可以这样用
        timeArray = time.localtime(self["create_time"])
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        timeArray = time.localtime(self["update_time"])
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        crawl_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        params = (zhihu_id, url, question_id, author_id, content, praise_num, comments_num, create_time, update_time, crawl_time)

        return insert_sql, params

    def save_to_es(self):
        zhihua = ZhihuAnswerType()
        zhihua.zhihu_id = self["zhihu_id"]
        zhihua.url = "".join(self["url"])
        zhihua.question_id = self["question_id"]
        if self["author_id"] != "0":
            zhihua.author_id = self["author_id"]
        zhihua.content = remove_tags(self["content"])
        zhihua.praise_num = self["praise_num"]
        zhihua.comments_num = self["comments_num"]
        timeArray = time.localtime(self["create_time"])
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        timeArray = time.localtime(self["update_time"])
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        crawl_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        zhihua.create_time = create_time
        zhihua.update_time = update_time
        zhihua.crawl_time = crawl_time

        zhihua.save()









