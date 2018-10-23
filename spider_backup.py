import os
import re
import time
from queue import Queue
from threading import Thread

import requests
from bs4 import BeautifulSoup

from db_helper import DbHelper
from tools import UtilLogger

class Sogou_spider():
    def __init__(self):
        self.log = UtilLogger('SougouSpider',
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log_SougouSpider.log'))
        self.queue = Queue()
        self.db = DbHelper()


    def get_html(self,url):
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print('get type1 error:', e)
            self.log.error('get type1 error:', e)
            return -1


    def get_category(self,url):
        cate1s = ['城市信息', '自然科学', '社会科学', '工程应用', '农林渔畜', '医学医药', '电子游戏', '艺术设计', '生活百科', '运动休闲', '人文科学', '娱乐休闲']
        html1 = self.get_html(url)
        soup1 = BeautifulSoup(html1, 'lxml')
        cate1_url = soup1.find('div', {'id': 'dict_nav_list'})
        a1_list = cate1_url.find_all('a')
        for i in range(len(a1_list)):
            html2 = self.get_html('https://pinyin.sogou.com' + a1_list[i]['href'])
            soup2 = BeautifulSoup(html2, 'lxml')
            cate2_no_child_list = soup2.find_all('div', {'class': 'cate_no_child no_select'})
            cate2_has_child_list = soup2.find_all('div', {'class': 'cate_has_child no_select'})
            cate2_list = cate2_no_child_list + cate2_has_child_list
            for cate2 in cate2_list:
                link = 'https://pinyin.sogou.com' + cate2.find('a')['href'] + '/default/'
                html3 = self.get_html(link)
                soup3 = BeautifulSoup(html3, 'lxml')
                page_list = soup3.find('div', {'id': 'dict_page_list'})
                li_list = page_list.find_all('li')
                try:
                    page_num = li_list[-2].text
                except:
                    page_num = 1
                yield link, page_num, cate1s[i], cate2.text.strip().replace('"', '')


    def get_download(self,url):
        html = self.get_html(url)
        soup = BeautifulSoup(html, 'lxml')
        title_div_list = soup.find_all('div', {'class': 'detail_title'})
        download_div_list = soup.find_all('div', {'class': 'dict_dl_btn'})

        for i in range(len(title_div_list)):
            title = title_div_list[i].find('a').text
            download_url = download_div_list[i].find('a')['href']
            yield title, download_url


    def ext_to_queue(self):
        global total_download_num
        total_download_num = 0
        cate_info = self.get_category('https://pinyin.sogou.com/dict/cate/index/167')
        for link, page_num, cate1, cate2 in cate_info:
            total_download_num += int(re.search(r'\d+', cate2).group())
            for i in range(1, int(page_num) + 1):
                url = link + str(i)
                download_info = self.get_download(url)
                for title, download_url in download_info:
                    filename = '{}_{}_{}'.format(cate1, cate2, title)
                    data = {'url': download_url, 'filename': filename, 'cate1': cate1, 'cate2': cate2}
                    self.queue.put_nowait(data)

                    self.log.debug('url:{}\tfilename:{}\tcate1:{}\tcate2:{}'.format(
                        download_url, filename, cate1, cate2))
                    # print('url:{}\tfilename:{}\tcate1:{}\tcate2:{}'.format(
                    #     download_url, filename, cate1,cate2))


    def save_to_db(self):
        while True:
            try:
                data = self.queue.get_nowait()
                self.db.save_one_data_to_detail(data)
                self.queue.task_done()
            except:
                print("queue is empty wait for a while")
                time.sleep(1)


if __name__ == '__main__':
    start = time.clock()

    configs = {'host': '127.0.0.1', 'user': 'root', 'password': 'admin', 'db': 'sogou'}
    db.connenct(configs)

    put_data_thread = Thread(target=ext_to_queue)
    put_data_thread.setDaemon(True)
    put_data_thread.start()

    time.sleep(10)  # 让ext_to_queue先跑10秒,防止queue为空,join直接不阻塞了
    for i in range(3):
        get_data_thread = Thread(target=save_to_db, args=(db,))
        get_data_thread.setDaemon(True)
        get_data_thread.start()

    queue.join()
    db.close()
    end = time.clock()
    print('总共需下载{}条词库'.format(total_download_num))
    print('耗时:', end - start)
