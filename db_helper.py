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
        try:
            with self.db.cursor() as cursor:
                sql = 'insert into detail(url,filename,cate1,cate2,create_time) values(%s,%s,%s,%s,now())'
                cursor.execute(sql,(data['url'],data['filename'],data['cate1'],data['cate2']))
                self.db.commit()
                print('{}\t{}\t{}\t{} insert into detail'.format(data['url'],data['filename'],data['cate1'],data['cate2']))
        except Exception as e:
            print(str(e))

    def save_one_data_to_keyword(self,data):
        if len(data) == 0:
            return -1
        try:
            with self.db.cursor() as cursor:
                sql = 'insert into keyword(keyword,pinyin,cate1,cate2,cate3,create_time) values(%s,%s,%s,%s,%s,now())'
                cursor.execute(sql, (data['keyword'], data['pinyin'], data['cate1'], data['cate2'],data['cate3']))
                self.db.commit()
                print('{}\t{}\t{}\t{}\t{} insert into keyword'.format(data['keyword'], data['pinyin'], data['cate1'], data['cate2'],data['cate3']))
        except Exception as e:
            print(str(e))

    def find_all_detail(self):
        with self.db.cursor() as cursor:
            sql = 'select url,filename from detail limit 50'
            cursor.execute(sql)
            res = cursor.fetchall()
            return res