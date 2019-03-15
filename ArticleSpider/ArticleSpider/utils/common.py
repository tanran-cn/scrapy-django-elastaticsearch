# _*_ coding: utf-8 _*_
import hashlib
import re

__auther__ = "tanran"
__date__ = "2019/1/11 13:40"



def get_md5(url):
    if isinstance(url, str):
        url = url.encode("utf-8")
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()


def extract_num(text):
    """
    从文本中提取数字
    :param text: 文本
    :return: nums 数字
    """
    match_re = re.match(".*?(\d+).*", text)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0

    return nums


if __name__ == "__main__":
    print(get_md5("http://jobbole.com"))