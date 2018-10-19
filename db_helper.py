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

    def close(self):
        self.db.close()

    def save_one_data_to_detail(self,data):
        if len(data) == 0:
            return  -1
        with self.db.cursor() as cursor:
            sql = 'insert into detail(url,filename,cate1,cate2,create_time) values(%s,%s,%s,%s,now())'
            cursor.execute(sql,(data['url'],data['filename'],data['cate1'],data['cate2']))
            self.db.commit()
            print('{}\t{}\t{}\t{} insert into detail'.format(data['url'],data['filename'],data['cate1'],data['cate2']))

    def find_all_detail(self):
        with self.db.cursor() as cursor:
            sql = 'select * from detail'
            cursor.execute(sql)
            self.db.commit()