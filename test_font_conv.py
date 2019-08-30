# coding=utf-8
import base64
import sys
from io import BytesIO

import pymysql
import requests
import random
import re
from lxml import etree
from fontTools.ttLib import TTFont

reload(sys)
sys.setdefaultencoding('utf8')
conn = pymysql.connect(host='localhost', user='root', password='Scholl7fcb', database='house_spider')
rent_url = 'https://bj.zu.anjuke.com/?t=1&from=0&comm_exist=on&kw={}'
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 OPR/57.0.3098.116", }
proxies = []


def get_ip_from_db():
    cursor = conn.cursor()
    cursor.execute("select ip,port from ip_pool where is_active=1")
    results = cursor.fetchall()
    for row in results:
        ip = row[0]
        port = row[1]
        arr = dict()
        arr['http'] = "http://{}:{}".format(ip, port)
        proxies.append(arr)
    cursor.close()


def get_page_show_ret(mystr, bs64_str):
    '''
    :param mystr: 要转码的字符串
    :param bs64_str:  转码格式
    :return: 转码后的字符串
    '''
    font = TTFont(BytesIO(base64.decodestring(bs64_str.encode())))
    c = font['cmap'].tables[0].ttFont.tables['cmap'].tables[0].cmap
    ret_list = []
    for char in mystr:
        decode_num = ord(char)
        if decode_num in c:
            num = c[decode_num]
            num = int(num[-2:]) - 1
            ret_list.append(num)
        else:
            ret_list.append(char)
    ret_str_show = ''
    for num in ret_list:
        ret_str_show += str(num)
    return ret_str_show


if __name__ == '__main__':
    get_ip_from_db()
    html = requests.get(url=rent_url.format('领地OFFICE'), headers=headers, proxies=random.choice(proxies))
    bs64_str = re.findall("charset=utf-8;base64,(.*?)'\)", html.content)[0]
    selector = etree.HTML(html.content)
    price = selector.xpath('//*[@id="list-content"]/div[13]/div[2]/p/strong/b')
    res = get_page_show_ret(price[0].text, bs64_str)
    print res
