# sogou_word_spider
搜狗词库爬虫


Scrapy-sogou
1、一级分类标题文字为图片形式，获取不到
	写死
2、下载url太长，写不进数据库
	下载url保存到Mysql时报错 1406, "Data too long for column 'songlist_url' at row 1"
	参考如下文章解决
	http://huanyouchen.github.io/2018/05/22/mysql-error-1406-Data-too-long-for-column/
3、文件下载
	项目里还涉及到文件下载，查资料了解到scrapy的文件下载是通过FilesPipeline实现的
	官方文档（https://scrapy-chs.readthedocs.io/zh_CN/1.0/topics/media-pipeline.html）说的很详细
	需要注意的有三点
	1、get_media_requests()在不重写的情况下，处理的url固定为item['file_urls'],且要求传递过来的为一系列url列表。
	所以没有其他要求的话，直接在item中定义该字段，pipeline中创建类继承下FilesPipeline即可。
	本项目中传递的url为单个，不是列表，所以重写了该方法
	2、下载的默认文件名为文件的SHA1值，需要重命名，file_path()返回文件的绝对路径，需要在这里将文件重命名，但是这个方法里并没有item参数，如何拿到filename呢？
	仔细看file_path()参数里有一个request，这个request就是get_media_requests()里返回的，只需要将filename给request的meta即可
	3、setting里的FILES_STORE为绝对路径。这是文件的下载目录，需要设为绝对路径
利用scrapy框架的好处就是不用自己考虑多线程的问题了，而且也有专门的日志记录，所以框架是挺方便的。下片文章讲讲直接直接用requests实现。

Requests-sogou
利用requests实现搜狗词库爬虫，就是原文里提供的方法了，参考原文，我做了些小的改变。但就是这一些小的变化，遇到些问题。
思路
因为后面对词库关键词的解析不属于爬虫，而且cate表只是作为中转，我就没有存储，所以我只建了一个表detail。
1、建表detail，字段url、filename、cate1、cate2、create_time
2、从初始url中解析全部一级分类url
3、从一级分类url中解析二级分类url
4、从二级分类url中解析出每一个二级分类的页数
5、将二级分类url和每一个的页数拼接成新的url
6、从新的url中解析出下载地址和标题，和一级分类和二级分类一并存入detail表
7、从detail表中取出所有下载url，下载文件到本地
问题
前面一篇文章已经将问题说的差不多了，这里只重点讲讲多线程的问题，这也是我为什么要用requests再实现一遍的原因，要研究一下Python的多线程
1、python的多线程常用的有两种：
(1)正常的启动多个thread，每个线程跑一个任务，进程间用队列queue通信。具体实现如下;
def put_to_queue(arg1,arg2):
	......
	# queue有两种存数据的方法，一种是put(),这种方法在队列满的时，会一直等待，直到队列有
	# 空位置可以放数据。另一种是put_nowait(),这种方法会在队列满时，抛出异常。同样取数据
	# 也有get()和get_nowait()，get_nowait()会在队列空时，抛出异常。
	queue.put_nowait(data)
	
def get_from_queue(arg1):
	......
	while True:
		try:
			data = queue.get_nowait() # 循环取出数据，如果队列为空，则抛出异常
			......
			queue.task_done() # 操作完成，标记该数据已从队列取出
		except:
			print('queue is empty wait for a while')

if __name__ == '__main__':
	......
	put_thread = Thread(target=put_to_queue,args=(arg1,arg2))
	put_thread.setDaemon(True) # 守护进程，当主程序执行完，该线程自动结束
	put_thread.start()

	time.sleep(10) # 队列存数据线程先跑10秒，让队列里有初始数据量，防止队列里没数据，join()直接不阻塞了
	
	for i in range(3):
		get_thread = Thread(target=get_from_queue,args=(arg1,)) # 注意单个参数的使用形式
		get_thread.setDaemon(True)
		get_thread.start()

	# join()将主程序阻塞，直到queue里的所有数据都标记task_done，并且queue为空时才放通
	# 因为这里的模式是生产者速度慢，消费者速度快，有可能导致
	# 还没生产出来就已经消费完了，导致所有数据都被标记了task_done，而且queue为空了，这就
	# 使join()直接放通了，解决办法先让存数据的线程跑一段时间，queue里有足够的初始数据量
	queue.join()
	......
相关的说明和注意事项都在注释中，这种多线程方式还是最适合生产者速度快，消费者速度慢，并且queue有一定的初始数据量的情况下，这样join()就不会误放通了。

(2)使用multiprocessing.dummy中的Pool线程池
	from multiprocessing.dummy import Pool as ThreadPool
	pool = ThreadPool(10) # 线程池中最大线程数
	pool.map(download, datas) # download为每个线程中跑的任务，datas为所有需要处理的数据

        # 一行代码实现多线程,大致相当于下面的代码
        # for data in datas:
        #   Thread(target=download,args=(data,)).start()
这种使用线程池的多线程的优势在于编写简单，但是只适用于所有需要处理的数据都已经生成，而且相对于正常写线程来说不够灵活

2、因为涉及到多线程的数据库存储问题，那么就必须提到锁。因为一个connection在同一时间只能被一个线程占用，其他线程没办法读取。一个解决办法就是
开启多个connection,每个线程使用一个，但是这样的话就太浪费资源，因为一个线程不可能总是占用connect读取数据库，最好的办法就是多个线程共用一个
connect。当一个线程读取数据后，将connect给下一个线程使用，这就需要锁来实现了。简单来说，锁就是在数据库读写时加个标志，当需要读取数据库时，
先锁定，读取完成后再解锁，然后另一个线程要读取数据库之前，先判断锁的状态，如果是锁定状态，就先等待，等到解锁后再读取数据库。具体实现如下：
def save_data_to_db(self, data):	
	while self.mutex == 1:  # connetion正在被其他线程使用，需要等待
            time.sleep(1)
            print('db connect is using...')
        self.mutex = 1  # 锁定
        try:
            with self.db.cursor() as cursor:
                sql = '...'
                cursor.execute(sql)
                self.db.commit()
                self.mutex = 0  # 解锁
        except Exception as e:
            print('save_data_to_db fail,error:' + str(e))