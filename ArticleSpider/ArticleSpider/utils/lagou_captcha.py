# _*_ coding: utf-8 _*_
# 2019/3/6 21:30
import base64
import json
import random
import re

import requests
from PIL import Image

__auther__ = "tanran"


class lagou_captcha:
    def __init__(self):
        self.captcha_url = "https://www.lagou.com/utrack/verify.jpg?{0}"
        self.session = requests.session()

    def _get_captcha(self, lang: str):
        """
        请求验证码的 API 接口，无论是否需要验证码都需要请求一次
        如果需要验证码会返回图片的 base64 编码
        根据 lang 参数匹配验证码，需要人工输入
        :param lang: 返回验证码的语言(en/cn)
        :return: 验证码的 POST 参数
        """
        captcha_random = random()
        api = self.captcha_url.format(captcha_random)
        resp = self.session.get(api)
        show_captcha = re.search(r'true', resp.text)

        if show_captcha:
            put_resp = self.session.put(api)
            json_data = json.loads(put_resp.text)
            img_base64 = json_data['img_base64'].replace(r'\n', '')
            with open('./lagou_captcha.jpg', 'wb') as f:
                f.write(base64.b64decode(img_base64))
            img = Image.open('./captcha.jpg')
            img.show()
            capt = input('请输入图片里的验证码：')
            # 这里必须先把参数 POST 验证码接口
            self.session.post(api, data={'input_text': capt})

