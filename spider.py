import os
import time
from queue import Queue
from threading import Thread

import pymysql
import requests
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool as ThreadPool

from db_helper import DbHelper

queue1 = Queue()
queue2 = Queue()
queue3 = Queue()

pool1 = ThreadPool(5)
pool2 = ThreadPool(5)
pool3 = ThreadPool(5)

flag1 = 0
flag2 = 0
flag3 = 0

def get_html(url):
    try:
        r = requests.get(url,timeout=5)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print('get type1 error:', e)
        return -1


def get_cate1(url):
    cate1s = ['城市信息','自然科学','社会科学','工程应用','农林渔畜','医学医药','电子游戏','艺术设计','生活百科','运动休闲','人文科学','娱乐休闲']
    res = []
    html1 = get_html(url)
    soup1 = BeautifulSoup(html1, 'lxml')
    cate1_url = soup1.find('div', {'id': 'dict_nav_list'})
    a1_list = cate1_url.find_all('a')
    for i in range(len(a1_list)):


        url = 'https://pinyin.sogou.com' + a1_list[i]['href']
        queue1.put_nowait(url)
        # print('queue1 put data')
    # flag1 = 1

    #     html2 = get_html('https://pinyin.sogou.com' + a1_list[i]['href'])
    #     soup2 = BeautifulSoup(html2,'lxml')
    #     cate2_no_child_list = soup2.find_all('div',{'class':'cate_no_child no_select'})
    #     cate2_has_child_list = soup2.find_all('div',{'class':'cate_has_child no_select'})
    #     cate2_list = cate2_no_child_list + cate2_has_child_list
    #     for cate2 in cate2_list:
    #         link = 'https://pinyin.sogou.com' + cate2.find('a')['href'] + '/default/'
    #
    #         html3 = get_html(link)
    #         soup3 = BeautifulSoup(html3,'lxml')
    #         page_list = soup3.find('div',{'id':'dict_page_list'})
    #         li_list = page_list.find_all('li')
    #         try:
    #             page_num = li_list[-2].text
    #         except:
    #             page_num = 1
    #
    #         # print('url:{}\tpage:{}\tcate1:{}\tcate2:{}'.format(link,page_num,cate1s[i],cate2.text.strip().replace('"','')))
    #         res.append({'url':link,'page':page_num,'cate1':cate1s[i],'cate2':cate2.text.strip().replace('"','')})
    # return res


def get_cate2():
    start = time.time()
    end = time.time()
    while True:
        if end - start > 20:
            break
        else:
            try:
                url = queue1.get_nowait()
                # print('queue1 get data')
                start = time.time()
                html2 = get_html(url)
                soup2 = BeautifulSoup(html2,'lxml')
                cate2_no_child_list = soup2.find_all('div',{'class':'cate_no_child no_select'})
                cate2_has_child_list = soup2.find_all('div',{'class':'cate_has_child no_select'})
                cate2_list = cate2_no_child_list + cate2_has_child_list
                for cate2 in cate2_list:
                    link = 'https://pinyin.sogou.com' + cate2.find('a')['href'] + '/default/'
                    queue2.put_nowait(link)
                    print('queue2 put data')
            except:
                print("queue1 is empty wait for a while")
                time.sleep(1)
                end = time.time()

def get_cate3():
    start = time.time()
    end = time.time()
    while True:
        if end - start > 20:
            break
        else:
            try:
                link = queue2.get_nowait()
                print('queue2 get data')
                html3 = get_html(link)
                soup3 = BeautifulSoup(html3,'lxml')
                page_list = soup3.find('div',{'id':'dict_page_list'})
                li_list = page_list.find_all('li')
                try:
                    page_num = li_list[-2].text
                except:
                    page_num = 1
                for i in range(1,page_num + 1):
                    url = link + str(i)
                    queue3.put_nowait(url)
            except:
                print("queue2 is empty wait for a while")
                time.sleep(1)
                end = time.time()

def get_download():
    start = time.time()
    end = time.time()
    while True:
        if end - start > 20:
            break
        else:
            try:
                url = queue3.get_nowait()
                html = get_html(url)
                soup = BeautifulSoup(html,'lxml')
                title_div_list = soup.find_all('div',{'class':'detail_title'})
                download_div_list = soup.find_all('div',{'class':'dict_dl_btn'})


                for i in range(len(title_div_list)):
                    title = title_div_list[i].find('a').text
                    download_url = download_div_list[i].find('a')['href']
                    print('url:{}\ttitle:{}'.format(download_url,title))


                # for title_div in title_div_list:
                #     title = title_div.find('a').text
                    # titles.append(title)
                # for download_div in download_div_list:
                    # download_url = download_div.find('a')['href']
                    # download_urls.append(download_url)
                # return titles,download_urls
            except:
                print("queue3 is empty wait for a while")
                time.sleep(1)
                end = time.time()

# def get_download(url):
#     titles = []
#     download_urls = []
#     html = get_html(url)
#     soup = BeautifulSoup(html,'lxml')
#     title_div_list = soup.find_all('div',{'class':'detail_title'})
#     download_div_list = soup.find_all('div',{'class':'dict_dl_btn'})
#     for title_div in title_div_list:
#         title = title_div.find('a').text
#         titles.append(title)
#     for download_div in download_div_list:
#         download_url = download_div.find('a')['href']
#         download_urls.append(download_url)
#     return titles,download_urls

def get_download_dir():
    base_dir = os.getcwd()
    download_dir = base_dir + '\\' + 'download'
    if not os.path.exists(download_dir):
        os.mkdir(download_dir)
    return download_dir

def strip(filename):
    str = ['\\','/',':','*','?','<','>','|']
    res = ''
    for char in filename:
        if char not in str:
            res += char
    return res

def down_load(url,filename):
    try:
        r = requests.get(url)
        r.raise_for_status()
        content = r.content
        path = os.path.join(get_download_dir(),strip(filename))
        with open(path + '.scel','wb') as f:
            f.write(content)
            print('{} 词库文件保存完毕'.format(strip(filename)))
    except:
        return -1

if __name__ == '__main__':
    start = time.clock()
    # cates = get_category('https://pinyin.sogou.com/dict/cate/index/167')
    # for cate in cates:
    #     for i in range(1,int(cate['page']) + 1):
    #         url = cate['url'] + str(i)
    #         titles,download_urls = get_download(url)
    #         for j in range(len(titles)):
    #             filename = '{}_{}_{}'.format(cate['cate1'],cate['cate2'],titles[j])
    #             print('url:{}\tfilename:{}\tcate1:{}\tcate2:{}'.format(download_urls[j],filename,cate['cate1'],cate['cate2']))
    #
    # end = time.clock()
    # print('耗时:',end - start)


    Thread(target=get_cate1('https://pinyin.sogou.com/dict/cate/index/167')).start()
    Thread(target=get_cate2).start()
    Thread(target=get_cate3).start()
    Thread(target=get_download).start()

    # pool1.map(get_cate2())
    # pool2.map(get_cate3())
    # pool3.map(get_download())


    end = time.clock()
    print('耗时:',end - start)

    # configs = {'host': '127.0.0.1', 'user': 'root', 'password': 'admin', 'db': 'sogou'}
    # db = DbHelper().connenct(configs)

    # down_load('http://download.pinyin.sogou.com/dict/download_cell.php?id=1316&name=%E6%9C%80%E8%AF%A6%E7%BB%86%E7%9A%84%E5%85%A8%E5%9B%BD%E5%9C%B0%E5%90%8D%E5%A4%A7%E5%85%A8','城市信息_行政区划地名(24)_最详细的全国地名大全')
