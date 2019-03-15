# _*_ coding: utf-8 _*_
# 2019/3/3 18:44
import copy
import re

import _thread
import requests
import MySQLdb
from scrapy.selector import Selector

__auther__ = "tanran"


conn = MySQLdb.connect(host="39.106.54.134", user="root", passwd="tr7625323", db="article_spider", charset="utf8")
cursor = conn.cursor()


def crawl_ips():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
    }
    for i in range(1,3614):
        if i == 1:
            res = requests.get("https://www.xicidaili.com/nn/", headers=headers)
        else:
            res = requests.get("https://www.xicidaili.com/nn/{0}".format(i), headers=headers)
        if res.status_code != 200:
            print("被识别")
            break
        selector = Selector(text=res.text)
        all_trs = selector.css('#ip_list tr')
        for tr in all_trs[1:]:
            speed_str = tr.css(".bar::attr(title)").extract()[0]
            if speed_str:
                speed = float(speed_str.split("秒")[0])
                all_text = tr.css("td::text").extract()
                time_str = all_text[10]
                if time_str:
                    match_re = re.match("\d+([\u4e00-\u9fa5]+)", time_str)
                    if match_re:
                        match_re = match_re.group(1)
                        if match_re == '分钟':
                            continue
                        ip = all_text[0]
                        port = all_text[1]
                        cursor.execute("""insert IGNORE INTO proxy_ip(ip, port, speed, proxy_type) 
                        VALUES('{0}', '{1}', '{2}', 'HTTP')
                        ON DUPLICATE KEY UPDATE port=VALUES (port)""".format(ip, port, speed))
                        conn.commit()


class GetIP():

    def judge_ip(self, ip, port):
        http_url = "https://www.baidu.com"
        proxy_url = "http://{0}:{1}".format(ip, port)
        try:
            proxy_dict = {
                "http":proxy_url
            }
            response = requests.get(http_url, proxies=proxy_dict, timeout=5)
        except Exception as e:
            print("invalid ip and port")
            self.delete_ip(ip)
            return False
        else:
            code = response.status_code
            if code >= 200 and code<=300:
                print("effective_ip")
                return True
            else:
                print("effective_ip")
                self.delete_ip(ip)
                return False

    def get_random_ip(self):
        sql = "SELECT ip, port FROM proxy_ip ORDER BY RAND() LIMIT 1"
        result = cursor.execute(sql)
        for ip_info in cursor.fetchall():
            ip = ip_info[0]
            port = ip_info[1]

            judge_ip = self.judge_ip(ip, port)
            if judge_ip:
                return "http://{0}:{1}".format(ip, port)
            else:
                return self.get_random_ip()

    def delete_ip(self, ip):
        delete_sql = """
            delete from proxy_ip where ip='{0}'
        """.format(ip)
        cursor.execute(delete_sql)
        conn.commit()


if __name__ == '__main__':
    # crawl_ips()
    GETIP = GetIP()
    GETIP.get_random_ip()
