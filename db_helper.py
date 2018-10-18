import pymysql


class DbHelper(object):
    def connenct(self, configs):
        self.db = pymysql.connect(
            host=configs['host'],
            user=configs['user'],
            password=configs['password'],
            db=configs['db'],
            charset='utf8mb4'
        )
        return self.db
