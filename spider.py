import os
import re
import time

import pymysql
import requests
from bs4 import BeautifulSoup

from db_helper import DbHelper
from tools import UtilLogger


log = UtilLogger('SougouSpider',
                     os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log_SougouSpider.log'))
db = DbHelper()

def get_html(url):
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print('get type1 error:', e)
        log.error('get type1 error:', e)
        return -1


def get_category(url):
    cate1s = ['城市信息', '自然科学', '社会科学', '工程应用', '农林渔畜', '医学医药', '电子游戏', '艺术设计', '生活百科', '运动休闲', '人文科学', '娱乐休闲']
    # res = []
    html1 = get_html(url)
    soup1 = BeautifulSoup(html1, 'lxml')
    cate1_url = soup1.find('div', {'id': 'dict_nav_list'})
    a1_list = cate1_url.find_all('a')
    for i in range(len(a1_list)):
        html2 = get_html('https://pinyin.sogou.com' + a1_list[i]['href'])
        soup2 = BeautifulSoup(html2, 'lxml')
        cate2_no_child_list = soup2.find_all('div', {'class': 'cate_no_child no_select'})
        cate2_has_child_list = soup2.find_all('div', {'class': 'cate_has_child no_select'})
        cate2_list = cate2_no_child_list + cate2_has_child_list
        for cate2 in cate2_list:
            link = 'https://pinyin.sogou.com' + cate2.find('a')['href'] + '/default/'

            html3 = get_html(link)
            soup3 = BeautifulSoup(html3, 'lxml')
            page_list = soup3.find('div', {'id': 'dict_page_list'})
            li_list = page_list.find_all('li')
            try:
                page_num = li_list[-2].text
            except:
                page_num = 1


            yield link,page_num,cate1s[i],cate2.text.strip().replace('"', '')

            # print('url:{}\tpage:{}\tcate1:{}\tcate2:{}'.format(link,page_num,cate1s[i],cate2.text.strip().replace('"','')))
    #         res.append(
    #             {'url': link, 'page': page_num, 'cate1': cate1s[i], 'cate2': cate2.text.strip().replace('"', '')})
    # return res


def get_download(url):
    # titles = []
    # download_urls = []
    html = get_html(url)
    soup = BeautifulSoup(html, 'lxml')
    title_div_list = soup.find_all('div', {'class': 'detail_title'})
    download_div_list = soup.find_all('div', {'class': 'dict_dl_btn'})

    for i in range(len(title_div_list)):
        title = title_div_list[i].find('a').text
        download_url = download_div_list[i].find('a')['href']
        yield title,download_url


    # for title_div in title_div_list:
    #     title = title_div.find('a').text
    #     titles.append(title)
    # for download_div in download_div_list:
    #     download_url = download_div.find('a')['href']
    #     download_urls.append(download_url)
    # return titles, download_urls


def get_download_dir():
    base_dir = os.getcwd()
    download_dir = base_dir + '\\' + 'download'
    if not os.path.exists(download_dir):
        os.mkdir(download_dir)
    return download_dir


def strip(filename):
    str = ['\\', '/', ':', '*', '?', '<', '>', '|']
    res = ''
    for char in filename:
        if char not in str:
            res += char
    return res


def down_load(url, filename):
    try:
        r = requests.get(url)
        r.raise_for_status()
        content = r.content
        path = os.path.join(get_download_dir(), strip(filename))
        with open(path + '.scel', 'wb') as f:
            f.write(content)
            print('{} 词库文件保存完毕'.format(strip(filename)))
    except:
        return -1


if __name__ == '__main__':
    start = time.clock()
    total_download_num = 0

    configs = {'host': '127.0.0.1', 'user': 'root', 'password': 'admin', 'db': 'sogou'}
    db.connenct(configs)

    cate_info = get_category('https://pinyin.sogou.com/dict/cate/index/167')
    for link,page_num,cate1,cate2 in cate_info:
        for i in range(1, int(page_num) + 1):
            url = link + str(i)


            download_info = get_download(url)
            for title,download_url in download_info:
                filename = '{}_{}_{}'.format(cate1, cate2, title)
                data = {'url':download_url,'filename':filename,'cate1':cate1,'cate2':cate2}
                total_download_num += re.search(r'\d+',cate2).group()
                db.save_one_data_to_detail(data)

                log.debug('url:{}\tfilename:{}\tcate1:{}\tcate2:{}'.format(
                    download_url, filename, cate1,cate2))
                print('url:{}\tfilename:{}\tcate1:{}\tcate2:{}'.format(
                    download_url, filename, cate1,cate2))


            # titles, download_urls = get_download(url)
            # for j in range(len(titles)):
            #     filename = '{}_{}_{}'.format(cate['cate1'], cate['cate2'], titles[j])
            #     print('url:{}\tfilename:{}\tcate1:{}\tcate2:{}'.format(
            #           download_urls[j], filename, cate['cate1'],cate['cate2']))
    db.close()
    end = time.clock()
    print('总共需下载{}条词库'.format(total_download_num))
    print('耗时:', end - start)



    # down_load('http://download.pinyin.sogou.com/dict/download_cell.php?id=1316&name=%E6%9C%80%E8%AF%A6%E7%BB%86%E7%9A%84%E5%85%A8%E5%9B%BD%E5%9C%B0%E5%90%8D%E5%A4%A7%E5%85%A8','城市信息_行政区划地名(24)_最详细的全国地名大全')
