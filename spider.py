import os
import re
import time
from queue import Queue
from threading import Thread

import requests
from bs4 import BeautifulSoup

from db_helper import DbHelper
from tools import UtilLogger


class SogouSpider(object):
    def __init__(self, start_url):
        # 记录日志
        self.log = UtilLogger('SougouSpider',
                              os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log_SougouSpider.log'))
        self.queue = Queue()  # 多线程通信队列
        self.start_url = start_url

    def get_html(self, url):
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print('get type1 error:', str(e))
            self.log.error('get type1 error:' + str(e))

    def get_category(self, url):
        # 这里一级分类的文字信息爬取不到，因为网页上一级分类名称是图片上的文字，所以直接就写死这十二类了
        cate1s = ['城市信息', '自然科学', '社会科学', '工程应用', '农林渔畜', '医学医药', '电子游戏', '艺术设计', '生活百科', '运动休闲', '人文科学', '娱乐休闲']
        html1 = self.get_html(url)
        soup1 = BeautifulSoup(html1, 'lxml')
        cate1_url = soup1.find('div', {'id': 'dict_nav_list'})
        a1_list = cate1_url.find_all('a')  # 十二个一级分类的标签列表
        for i in range(len(a1_list)):
            link = 'https://pinyin.sogou.com' + a1_list[i]['href']
            html2 = self.get_html(link)
            soup2 = BeautifulSoup(html2, 'lxml')
            # 没有再细化分的二级分类标签列表，例如:"自然科学"里的数学
            cate2_no_child_list = soup2.find_all('div', {'class': 'cate_no_child no_select'})
            # 有细化分的二级分类标签列表,例如:"自然科学"里的物理
            cate2_has_child_list = soup2.find_all('div', {'class': 'cate_has_child no_select'})
            cate2_list = cate2_no_child_list + cate2_has_child_list  # 每一个一级分类下总的二级分类的标签列表
            for cate2 in cate2_list:
                link = 'https://pinyin.sogou.com' + cate2.find('a')['href'] + '/default/'
                html3 = self.get_html(link)
                soup3 = BeautifulSoup(html3, 'lxml')
                page_list = soup3.find('div', {'id': 'dict_page_list'})
                li_list = page_list.find_all('li')  # 每一个二级分类的页数标签列表
                try:
                    page_num = li_list[-2].text  # li_list[-1]为下一页，[-2]即为总页数
                except:
                    page_num = 1  # 只有一页才会报数组越界异常
                yield link, page_num, cate1s[i], cate2.text.strip().replace('"', '')

    def get_download(self, url):
        html = self.get_html(url)
        soup = BeautifulSoup(html, 'lxml')
        title_div_list = soup.find_all('div', {'class': 'detail_title'})
        download_div_list = soup.find_all('div', {'class': 'dict_dl_btn'})

        for i in range(len(title_div_list)):
            title = title_div_list[i].find('a').text
            download_url = download_div_list[i].find('a')['href']
            yield title, download_url

    def ext_to_queue(self):
        global total_download_num  # 总共需下载的词库数
        total_download_num = 0
        cate_info = self.get_category(self.start_url)
        # yield返回的是生成器,只有for循环的时候,才能拿到数据
        for link, page_num, cate1, cate2 in cate_info:
            # 直接从二级分类括号中的数字拿到该二级分类的总词库数，例如:数学(27)
            total_download_num += int(re.search(r'\d+', cate2).group())
            for i in range(1, int(page_num) + 1):
                url = link + str(i)  # 二级分类中每一页的url
                download_info = self.get_download(url)
                for title, download_url in download_info:
                    filename = '{}_{}_{}'.format(cate1, cate2, title)
                    data = {'url': download_url, 'filename': filename, 'cate1': cate1, 'cate2': cate2}
                    self.queue.put_nowait(data)  # 放进队列

                    self.log.debug('put data into queue,url:{}\tfilename:{}\tcate1:{}\tcate2:{}'.format(
                        download_url, filename, cate1, cate2))
                    # print('url:{}\tfilename:{}\tcate1:{}\tcate2:{}'.format(
                    #     download_url, filename, cate1,cate2))

    def save_to_db(self, db):
        while True:
            try:
                data = self.queue.get_nowait()  # 取出数据
                db.save_one_data_to_detail(data)
                self.log.debug('{} insert into db'.format(data))
                self.queue.task_done()  # 标记该数据已完成操作
            except:
                print("queue is empty wait for a while")
                time.sleep(1)


if __name__ == '__main__':
    start = time.time()

    configs = {'host': '***', 'user': '***', 'password': '***', 'db': '***'}
    db = DbHelper()
    db.connenct(configs)

    # queue = Queue()

    spider = SogouSpider('https://pinyin.sogou.com/dict/cate/index/167')

    # 一个线程向队列存数据
    put_data_thread = Thread(target=spider.ext_to_queue)
    put_data_thread.setDaemon(True)  # 守护进程，主程序执行完，该线程自动结束
    put_data_thread.start()

    time.sleep(10)  # 让ext_to_queue先跑60秒,防止queue为空,join直接不阻塞了
    # 多个线程从队列取数据
    for i in range(3):
        get_data_thread = Thread(target=spider.save_to_db, args=(db,))
        get_data_thread.setDaemon(True)
        get_data_thread.start()

    # join()将主程序阻塞，直到queue里的所有数据都标记task_done，并且queue为空时才放通
    # 因为这里的模式是生产者速度慢，消费者速度快，有可能导致
    # 还没生产出来就已经消费完了，导致所有数据都被标记了task_done，而且queue为空了，这就
    # 使join()直接放通了，解决办法先让存数据的线程跑一段时间，queue里有初始数据量
    spider.queue.join()
    db.close()
    end = time.time()
    print('总共需下载{}条词库'.format(total_download_num))
    print('耗时:', end - start)
