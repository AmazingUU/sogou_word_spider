import os
import time
from multiprocessing.dummy import Pool as ThreadPool

import requests

from db_helper import DbHelper
from tools import UtilLogger


class Downloader(object):
    def __init__(self):
        self.log = UtilLogger('SougouDownload',
                              os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log_SougouDownload.log'))
        self.pool = ThreadPool(20)  # 线程池

    def get_content(self, url):
        try:
            r = requests.get(url)
            r.raise_for_status()
            content = r.content
            return content
        except Exception as e:
            self.log.error('get_content error, ' + str(e))
            print('get_content error,', str(e))

    def download(self, data):
        url = data['url']
        filename = data['filename']
        basedir = os.getcwd()
        download_dir = os.path.join(basedir, 'download\\')
        path = os.path.join(download_dir, filename)
        content = self.get_content(url)
        with open(path + '.scel', 'wb') as f:
            f.write(content)
            self.log.debug('{}词库下载完成'.format(filename))
            print('{}词库下载完成'.format(filename))

    def start(self, datas):
        self.pool.map(self.download, datas)
        # 一行代码实现多线程,大致相当于下面的代码，这种使用线程池的多线程的优势在于编写简单，
        # 但是只适用于所有需要处理的数据都已经生成，而且相对于正常写线程来说不够灵活
        # for data in datas:
        #   download(data)


if __name__ == '__main__':
    start = time.time()
    configs = {'host': '***', 'user': '***', 'password': '***', 'db': '***'}
    db = DbHelper()
    db.connenct(configs)

    basedir = os.getcwd()
    download_dir = os.path.join(basedir, 'download\\')
    # print(download_dir)
    if not os.path.exists(download_dir):
        os.mkdir(download_dir)

    datas = db.find_all_detail()
    downloader = Downloader()
    downloader.start(datas)
    db.close()
    end = time.time()
    print('耗时:', end - start)
