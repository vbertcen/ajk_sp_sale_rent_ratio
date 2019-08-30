# coding=utf-8
import base64
import datetime
import random
import re
import sys
import time
from decimal import Decimal
from io import BytesIO

import numpy
import pymysql
import requests
import math
from fontTools.ttLib import TTFont
from lxml import etree

import get_ip_pool

reload(sys)
sys.setdefaultencoding('utf8')

"""
爬取安居客二手房、租房信息，计算租售比
1.获取ip池，入库
2.读取ip池加载缓存
3.获取二手房信息
4.加工二手房统计信息
5.获取租房信息
6.脱敏租房加密金额
by cenhz 20190825
"""

now_str = datetime.datetime.now().strftime('%Y-%m-%d')
sale_url = 'https://beijing.anjuke.com/sale/chaoyang/p{}'
rent_url = 'https://bj.zu.anjuke.com/?t=1&from=0&comm_exist=on&kw={}'
conn = pymysql.connect(host='localhost', user='root', password='Scholl7fcb', database='house_spider')
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 OPR/57.0.3098.116", }
proxies = []


def get_ip_from_db():
    """
    读取数据库中的ip池信息
    """
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


def load_ajk_sh_info():
    """
    获取安居客二手房信息，入库ajk_sh
    TODO:内层循环判断是否还是当前小区，目前有bug
    """
    cursor = conn.cursor()
    cursor.execute("delete from ajk_sh where dt='{}'".format(now_str))
    conn.commit()
    cursor.close()

    for j in range(1, 10):
        pro = random.choice(proxies)
        print "外层循环第{}次，代理为{}".format(j, pro)
        html = requests.get(url=sale_url.format(j), headers=headers, proxies=pro)
        selector = etree.HTML(html.content)
        if len(selector.xpath('//*[@id="houselist-mod-new"]/li')) == 0:
            print "代理有问题，跳出"
            continue
        location_path = '//*[@id="houselist-mod-new"]/li[{}]/div[2]/div[3]/span'
        price_path = '//*[@id="houselist-mod-new"]/li[{}]/div[3]/span[2]/text()'
        for i in range(1, 60):
            print "内层循环第{}次".format(i)
            location_text = selector.xpath(location_path.format(i))[0].attrib.get('title').replace(u'\xa0', ' ')
            ll = location_text.split(' ')[0]
            price_text = selector.xpath(price_path.format(i))[0].replace(u'元/m²', '')
            cursor = conn.cursor()
            sql = "insert into house_spider.ajk_sh(addr,unit_price,dt) values('{}','{}','{}')".format(ll, price_text,
                                                                                                      now_str)
            cursor.execute(sql)
            conn.commit()
            cursor.close()
        time.sleep(2)


def generate_statistic_table():
    """
    根据ajk_sh生成ajk_rent_sale_ratio
    :return:
    """
    cursor = conn.cursor()
    cursor.execute("select addr,avg(unit_price) as avg_sale from ajk_sh where dt='{}' group by addr".format(now_str))
    results = cursor.fetchall()
    for row in results:
        addr = row[0]
        avg_sale = row[1]
        cursor.execute(
            "insert into ajk_rent_sale_ratio(addr,avg_sale,dt) values('{}',{},'{}')".format(addr, avg_sale, now_str))
    conn.commit()
    cursor.close()


def load_ajk_rent_info():
    """
    获取安居客租房信息，入库ajk_rent
    :return:
    """
    cursor = conn.cursor()
    cursor.execute("select id,addr,avg_sale from ajk_rent_sale_ratio where rent_sale_ratio is null and dt='{}'".format(now_str))
    results = cursor.fetchall()
    for row in results:
        id = row[0]
        addr = row[1]
        avg_sale = row[2]

        print "-----开始分析'{}'小区-----".format(addr)

        html = requests.get(url=rent_url.format(addr), headers=headers, proxies=random.choice(proxies))
        selector = etree.HTML(html.content)
        bs64_str = re.findall("charset=utf-8;base64,(.*?)'\)", html.content)[0]
        div_lens = len(selector.xpath('//*[@id="list-content"]/div'))
        rent_price_mon_sqr_arr = []
        for i in range(3, div_lens):
            print "总共{}条记录，当前第{}条".format(div_lens, i)
            res = selector.xpath('//*[@id="list-content"]/div[{}]/div[1]/address/a/em'.format(i))

            if len(res) == 0:
                print '---不属于此小区数据---'
                break

            label = res[0].text

            # 判断是否是要搜索的小区
            if label != addr:
                break

            rent_price_mon = get_page_show_ret(
                selector.xpath('//*[@id="list-content"]/div[{}]/div[2]/p/strong/b'.format(i))[0].text, bs64_str)
            square_metres = get_page_show_ret(
                selector.xpath('//*[@id="list-content"]/div[{}]/div[1]/p[1]/b[3]'.format(i))[0].text, bs64_str)

            rent_price_mon_sqr = Decimal(Decimal(rent_price_mon) / Decimal(square_metres)).quantize(Decimal('0.0000'))

            rent_price_mon_sqr_arr.append(rent_price_mon_sqr)

        avg_rent = numpy.mean(rent_price_mon_sqr_arr)
        if math.isnan(avg_rent):
            print '{}小区信息不全，无法统计'.format(addr)
            continue
        rent_sale_ratio = Decimal(Decimal(avg_rent) / Decimal(avg_sale)).quantize(Decimal('0.0000'))

        cursor.execute(
            "update ajk_rent_sale_ratio set avg_rent = {}, rent_sale_ratio={} where id={}".format(avg_rent,
                                                                                                  rent_sale_ratio, id))
        conn.commit()
    cursor.close()
    conn.close()


def get_page_show_ret(mystr, bs64_str):
    """
    :param mystr: 要转码的字符串
    :param bs64_str:  转码格式
    :return: 转码后的字符串
    """
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


def test():
    pro = {'http': 'http://221.122.91.60:80'}
    html = requests.get(url='http://www.baidu.com', headers=headers, proxies=pro)
    print html.content


if __name__ == '__main__':
    # get_ip_pool.init_ip_pool()
    get_ip_from_db()
    # load_ajk_sh_info()
    # generate_statistic_table()
    load_ajk_rent_info()
    # test()
