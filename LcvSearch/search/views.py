import json
from django.shortcuts import render
from django.views.generic.base import View
from search.models import ArticleType
from django.http import HttpResponse
from elasticsearch import Elasticsearch
from datetime import datetime

client = Elasticsearch(hosts=["127.0.0.1"])


# Create your views here.
class SearchSuggest(View):
    def get(self, request):
        key_words = request.GET.get('s', '')
        re_datas = []
        if key_words:
            s = ArticleType.search()
            s = s.suggest('my_suggest', key_words, completion={
                "field": "suggest", "fuzzy": {
                    "fuzziness": 2
                },
                "size": 10
            })
            suggestions = s.execute_suggest()
            for match in suggestions.my_suggest[0].options:
                source = match._source
                re_datas.append(source["title"])
        return HttpResponse(json.dumps(re_datas), content_type="application/json")


class SearchView(View):
    def get(self, request):
        start_time = datetime.now()
        key_words = request.GET.get("q", "")
        page = request.GET.get("p", "1")
        try:
            page = int(page)
        except:
            page = 1

        s_type = request.GET.get("s_type", "")
        if s_type == 'article':
            response = client.search(
                index= "jobbole",
                body={
                    "query":{
                        "multi_match": {
                            "query": key_words,
                            "fields":["tags", "title", "content"]
                        }
                    },
                    "from": (page-1)*10,
                    "size": 10,
                    "highlight": {
                        "pre_tags": ["<span class='keyWord'>"],
                        "post_tags": ["</span>"],
                        "fields": {
                            "title": {},
                            "content": {}
                        }
                    }
                }
            )

            total_nums = response["hits"]["total"]
            hit_list = []
            for hit in response["hits"]["hits"]:
                hit_dict = {}
                if "title" in hit["highlight"] :
                    hit_dict["title"] = "".join(hit["highlight"]["title"])
                else:
                    hit_dict["title"] = hit["_source"]["title"]

                hit_dict["content"] = hit["_source"]["content"][:500]

                hit_dict["create_date"] = hit["_source"]["create_data"]
                hit_dict["url"] = hit["_source"]["url"]
                hit_dict["score"] = hit["_score"]

                hit_list.append(hit_dict)
            end_time = datetime.now()
            last_time = (end_time - start_time).total_seconds()
            return render(request, "result.html", {"all_hits": hit_list, "key_words": key_words,
                                                   "total_nums": total_nums, "s_type": s_type,
                                                   "last_time":last_time})
        elif s_type == 'question':
            response = client.search(
                index="zhihuquestion",
                body={
                    "query": {
                        "multi_match": {
                            "query": key_words,
                            "fields": ["topics", "title", "content"]
                        }
                    },
                    "from": (page-1)*5,
                    "size": 5,
                    "highlight": {
                        "pre_tags": ["<span class='keyWord'>"],
                        "post_tags": ["</span>"],
                        "fields": {
                            "title": {},
                            "content": {}
                        }
                    }
                }
            )

            total_nums = response["hits"]["total"]
            hit_list = []
            for hit in response["hits"]["hits"]:
                hit_dict = {}
                if 'highlight' in hit.keys():
                    if "title" in hit["highlight"]:
                        hit_dict["title"] = "".join(hit["highlight"]["title"])
                    else:hit_dict["title"] = hit["_source"]["title"]
                else:
                    hit_dict["title"] = hit["_source"]["title"]
                hit_dict["content"] = hit["_source"]["content"][:500]

                hit_dict["create_date"] = hit["_source"]["crawl_time"]
                hit_dict["url"] = hit["_source"]["url"]
                hit_dict["score"] = hit["_score"]

                hit_list.append(hit_dict)

            response = client.search(
                index="zhihuanswer",
                body={
                    "query": {
                        "multi_match": {
                            "query": key_words,
                            "fields": ["content"]
                        }
                    },
                    "from": (page-1)*5,
                    "size": 5,
                }
            )
            total_nums = total_nums + response["hits"]["total"]
            for hit in response["hits"]["hits"]:
                hit_dict = {}
                question_id = hit["_source"]["question_id"]
                repo = client.search(
                        index="zhihuquestion",
                        body={
                            "query": {
                                "multi_match": {
                                    "query": question_id,
                                    "fields": ["zhihu_id"]
                                }
                            },
                            "from": 0,
                            "size": 1,
                        }
                    )
                if repo["hits"]["hits"]:
                    hit_dict["title"] = repo["hits"]["hits"][0]["_source"]["title"]
                    hit_dict["url"] = repo["hits"]["hits"][0]["_source"]["url"]
                else:
                    hit_dict["title"] = ""
                    hit_dict["url"] = hit["_source"]["url"]

                hit_dict["content"] = hit["_source"]["content"][:500]

                hit_dict["create_date"] = hit["_source"]["crawl_time"]
                hit_dict["score"] = hit["_score"]

                hit_list.append(hit_dict)
            end_time = datetime.now()
            last_time = (end_time-start_time).total_seconds()
            return render(request, "result.html", {"page":page, "all_hits": hit_list,
                                                   "key_words": key_words, "total_nums": total_nums, "s_type": s_type,
                                                   "last_time": last_time})

