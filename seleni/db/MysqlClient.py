""" 数据库客户端mysql实现"""
import logging
import datetime
import pymysql as pq
from  pymysql import escape_string  as es

from zope.interface import implementer
from interfaces import IDBClient

@implementer(IDBClient)
class MysqlClient(object):
    """mysql client"""

    def __init__(self, **kwargs):
        """
        kwargs: 'CONN_DB_INFO'配置信息
        """
        # CONN_DB_INFO配置结构如下
        # 'CONN_DB_INFO' : {'DBTYPE':'mysql',
        #                   'CONN': {'host':x, 'user':x,
        #                            'passwd':x, 'db':x, 'charset':'utf8'},},
        assert kwargs['DBTYPE'] == 'mysql', (
            'DBtype error, {} Not `mysql`'.format(kwargs.get('DBTYPE')))
        self.conn_info = kwargs['CONN']
        self.client = None
        self.cursor = None
        self.state = None

    def  get_basic_infos(self):
        """
        about state, host, db
        return: {'host':, 'db': , 'state': ,}
        """
        return {'host': self.conn_info['host'],
                'db':self.conn_info['db'],
                'state': self.state}

    def  open(self):
        """open mysql client"""
        # open database
        if self.state == 'opened':
            return
        self.client = pq.connect(**self.conn_info)
        self.cursor = self.client.cursor()
        if self.cursor:
            self.state = 'opened'

    def close(self):
        """close mysql client"""
        # close database
        if self.state == 'closed':
            return

        self.state = 'closed'
        if self.cursor:
            self.cursor.close()
        if self.client:
            self.client.close()

    def escape_string(self, value, mapping=None):
        """escape_string escapes *value* but not surround it with quotes."""
        return es(str(value), mapping)

    def insert_tauction_item(self, key, **kwargs)->int:
        """
        写标的详单，同时更新url状态为已抓取
        若成功，返回1

        params:
           key:
           dict keys: url, atten, rec, notice, intro, attachs,
            video, images, preferred, state, spidername
        """
        assert self.client is not None and self.cursor is not None

        args = (key, self.escape_string(kwargs['title']), self.escape_string(kwargs['url']),
                self.escape_string(kwargs['atten']), self.escape_string(kwargs['rec']),
                self.escape_string(kwargs['notice']), self.escape_string(kwargs['intro']),
                self.escape_string(kwargs['attachs']), self.escape_string(kwargs['video']),
                self.escape_string(kwargs['images']), self.escape_string(kwargs['preferred']),
                self.escape_string(kwargs['state'][:32]), self.escape_string(kwargs['spidername']),
                0)  #di

        success = 0
        # 写详单
        self.cursor.callproc("""insert_auction_item""", args)
        self.cursor.execute(
            'SELECT @_insert_auction_item_13')  # `_procname_n`，out参数是第13个, 从0开始
        ret = self.cursor.fetchone()
        if ret:
            success = int(ret[0])  # [0]与select语句只取一个对应

        return success

    def insert_tauctionitem_url(self, key, **kwargs)->int:
        """
        写标的url, 如果不提供状态state，写入均按照初始状态<0>写入

        返回值：
        -1  如果标的url已经历史入库过
        0   历史库没有，但入库失败
        1   入库成功
        params:
            key:
            kwargs keys: url, spidername, state
        """
        assert self.client is not None and self.cursor is not None

        #判断是否已经存储过
        self.cursor.execute(("select * from auction_items_url_tbl "
                             "where `id` = %s"), key)
        ret = self.cursor.fetchone()
        if ret:
            return -1

        _url = self.escape_string(kwargs['url'])
        state = 0
        if kwargs.get('state'):
            state = kwargs.get('state')

        # 后续如果从db中读出datetime到python中建议直接CAST(date AS CHAR)，或json loads自定义转换
        insert_time = datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")
        num = self.cursor.execute(("insert into auction_items_url_tbl "
                                   "(`id`,`spider`, `url`, `datetime`,`state`) "
                                   "VALUES (%s,%s,%s, %s, %s) "),
                                  (key, kwargs['spidername'], _url, insert_time, state))
        self.client.commit()
        return num

    def fetch_auction_item_urls(self, spider, maxnum)->dict:
        """
        抓取最多max个未访问url,返回

        params:
           spider: spider name
           maxnum: maximun urls got from db
        """
        assert maxnum > 0  and  self.state == 'opened'
        # 先爬取db库中的urls，再爬取命令传递过来的urls
        args = (maxnum, spider, 0)
        self.cursor.callproc("""getauctionitemurls""", args)
        ret = self.cursor.fetchall()
        return {x[0]: x[1] for x in ret}
