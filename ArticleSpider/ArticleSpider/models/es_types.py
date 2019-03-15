# _*_ coding: utf-8 _*_
# 2019/3/13 22:25
from datetime import datetime
from elasticsearch_dsl import DocType, Date, Keyword, Text, Integer, Completion
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

__auther__ = "tanran"

connections.create_connection(hosts=["localhost"])


class CustomAnalyzer(_CustomAnalyzer):

    def get_analysis_definition(self):
        return []


ik_analyzer = CustomAnalyzer("ik_max_word", filter=["lowercase"])


class ArticleType(DocType):
    # 伯乐在线文章类型
    suggest = Completion(analyzer=ik_analyzer)
    title = Text(analyzer="ik_max_word")
    create_data = Date()
    url = Keyword()
    url_object_id = Keyword()
    praise_num = Keyword()
    fav_nums = Integer()
    comment_nums = Integer()
    content = Text(analyzer="ik_max_word")
    tag = Text(analyzer="ik_max_word")
    front_image_url = Keyword()
    front_image_path = Keyword()

    class Meta:
        index = "jobbole"
        doc_type = "article"


class ZhihuQuestionType(DocType):
    # 知乎问题类型
    suggest = Completion(analyzer=ik_analyzer)
    zhihu_id = Keyword()
    topics = Text(analyzer="ik_max_word")
    url = Keyword()
    title = Text(analyzer="ik_max_word")
    content = Text(analyzer="ik_max_word")
    answer_num = Integer()
    comments_num = Integer()
    watch_user_num = Integer()
    click_num = Integer()
    crawl_time = Date()

    class Meta:
        index = "zhihuquestion"
        doc_type = "zhihuq"


class ZhihuAnswerType(DocType):
    zhihu_id = Keyword()
    url = Keyword()
    question_id = Keyword()
    author_id = Keyword()
    content = Text(analyzer="ik_max_word")
    praise_num = Integer()
    comments_num = Integer()
    create_time = Date()
    update_time = Date()
    crawl_time = Date()

    class Meta:
        index = "zhihuanswer"
        doc_type = "zhihua"


if __name__ == '__main__':
    # ArticleType.init()
    # ZhihuQuestionType.init()
    ZhihuAnswerType.init()