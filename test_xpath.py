# coding=utf-8
import requests, sys
from lxml import etree

reload(sys)
sys.setdefaultencoding('utf8')

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 OPR/57.0.3098.116", }

rent_url = 'https://bj.zu.anjuke.com/?t=1&from=0&comm_exist=on&kw={}'

html = requests.get(url=rent_url.format('中海枫丹公馆'), headers=headers)
selector = etree.HTML(html.content)

res = selector.xpath('//*[@id="list-content"]/div[{}]/div[1]/address/a/em'.format(29))
print len(res)