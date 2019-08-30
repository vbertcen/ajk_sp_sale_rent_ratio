# coding=utf-8
import sys

import pymysql
import requests
import datetime
from lxml import etree

reload(sys)
sys.setdefaultencoding('utf8')
now_str = datetime.datetime.now().strftime('%Y-%m-%d')
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 OPR/57.0.3098.116", }


def init_ip_pool():
    conn = pymysql.connect(host='localhost', user='root', password='Scholl7fcb', database='house_spider')
    cursor = conn.cursor()
    cursor.execute("truncate ip_pool")
    conn.commit()
    cursor.close()
    index = 1
    while True:
        print "当前查询到第{}页".format(index)
        url = 'http://www.66ip.cn/{}.html'.format(index)
        html = requests.get(url=url, headers=headers)
        selector = etree.HTML(html.content)

        page_count = len(selector.xpath('//*[@id="main"]/div/div[1]/table/tr'))
        if page_count == 0:
            break
        print page_count

        ip = '//*[@id="main"]/div/div[1]/table/tr[{}]/td[1]'
        port = '//*[@id="main"]/div/div[1]/table/tr[{}]/td[2]'
        location = '//*[@id="main"]/div/div[1]/table/tr[{}]/td[3]'

        for i in range(2, page_count):
            ip_text = selector.xpath(ip.format(i))[0].text
            port_text = selector.xpath(port.format(i))[0].text
            location_text = selector.xpath(location.format(i))[0].text

            cursor = conn.cursor()
            if verify_available(ip_text, port_text):
                cursor.execute(
                    "insert into ip_pool values(null,'{}','{}','{}',1,'{}')".format(ip_text, port_text, location_text,
                                                                                    now_str))
                print "ip={},available={}".format(ip_text, "true")
            else:
                cursor.execute(
                    "insert into ip_pool values(null,'{}','{}','{}',0,'{}')".format(ip_text, port_text, location_text,
                                                                                    now_str))
                print "ip={},available={}".format(ip_text, "false")

            cursor.close()
            conn.commit()
        index += 1

    conn.close()


def verify_available(ip, port):
    pro = dict()
    pro['http'] = "http://{}:{}".format(ip, port)
    try:
        html = requests.get(url='http://www.baidu.com', headers=headers, proxies=pro, timeout=2)
    except Exception:
        return False
    else:
        return html.content.count('百度') > 0


if __name__ == '__main__':
    init_ip_pool()
