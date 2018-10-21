import os
import time
from multiprocessing.dummy import Pool as ThreadPool

import requests

from db_helper import DbHelper
from tools import UtilLogger


log = UtilLogger('SougouDownload',
                     os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log_SougouDownload.log'))
db = DbHelper()
pool = ThreadPool(20)

def get_content(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        content = r.content
        return content
    except Exception as e:
        log.error('get_content error, ' + str(e))
        print('get_content error,',str(e))

def download(data):
    url,filename = data
    basedir = os.getcwd()
    download_dir = os.path.join(basedir, 'download\\')
    path = os.path.join(download_dir, filename)
    content = get_content(url)
    with open(path + '.scel','wb') as f:
        f.write(content)
        log.debug('{}词库下载完成'.format(filename))
        print('{}词库下载完成'.format(filename))

if __name__ == '__main__':
    start = time.time()
    configs = {'host': '127.0.0.1', 'user': 'root', 'password': 'admin', 'db': 'sogou'}
    db.connenct(configs)

    basedir = os.getcwd()
    download_dir = os.path.join(basedir, 'download\\')
    # print(download_dir)
    if not os.path.exists(download_dir):
        os.mkdir(download_dir)

    datas = db.find_all_detail()
    pool.map(download, datas)

    # datas = db.find_all_detail()
    # for data in datas:
    #     download(data)

    end = time.time()
    print('耗时:', end - start)