# _*_ coding: utf-8 _*_
__auther__ = "tanran"
__date__ = "2019/1/12 21:49"

from selenium import webdriver

browser = webdriver.Chrome(executable_path="F:/scrapyproject/chromedriver.exe")

browser.get("https://www.zhihu.com/signup")

browser.find_element_by_css_selector(".SignContainer-switch span").click()

browser.find_element_by_css_selector('.SignFlow-accountInput.Input-wrapper input[name="username"]').send_keys("17138957451")

browser.find_element_by_css_selector('input[name="password"]').send_keys("lben5572")

browser.find_element_by_css_selector("button.Button SignFlow-submitButton.Button--primary.Button--blue").click()
print(browser.page_source)