# -*- coding: utf-8 -*-
""" redis client
A String value can be at max 512 Megabytes in length.
"""
import  logging
import random
import json
from zope.interface import implementer
from redis.connection import BlockingConnectionPool
from redis import Redis

from interfaces import IDBClient

@implementer(IDBClient)
class RedisClient(object):
    """
    Redis client

    Redis中固定3个hash：;

    """
    def __init__(self, **kwargs):
        """
        kwargs: 'CONN_DB_INFO'配置信息
        """
        # CONN_DB_INFO配置结构如下
        # 'CONN_DB_INFO' : {'DBTYPE':'mysql',
        #                   'CONN': {'host':x, 'user':x,
        #                            'passwd':x, 'db':x, 'charset':'utf8'},},
        assert kwargs['DBTYPE'] == 'redis', (
            'DBtype error, {} Not `mysql`'.format(kwargs.get('DBTYPE')))
        cnn = kwargs['CONN']
        self.conn_info = {}
        if cnn.get('host'):
            self.conn_info['host'] = cnn.get('host')
        if cnn.get('port'):
            self.conn_info['port'] = cnn.get('port')
        if cnn.get('passwd'):
            self.conn_info['password'] = cnn.get('passwd')

        self.item_hash = 'tauction_item'
        self.item_url_scraped_hash = 'url_state1'  #已抓取,对应state==1
        self.item_url_scraping_hash = 'url_negativel'  #爬虫取正在抓取,对应state==-1
        self.item_url_hash = 'ur0'   #待传递给爬虫去抓取，对应state==0

        self.client = None
        self.state = None

    def  get_basic_infos(self):
        """
        about state, host, db
        return: {'host':, 'state': ,}
        """
        return {'host': self.conn_info['host'],
                'state': self.state}

    def  open(self):
        """open redis client"""
        if self.state == 'opened':
            return

        self.client = Redis(connection_pool=BlockingConnectionPool(**self.conn_info))
        if self.client:
            self.state = 'opened'

        logging.info("redis,host:%s, state:%s",
                     self.conn_info.get('host'), self.state)

    def close(self):
        """close redis client"""
        if self.state == 'closed':
            return

        self.state = 'closed'
        if self.client:
            logging.info("数据库连接关闭,host:%s", self.conn_info.get('host'))
            self.client.close()

    def escape_string(self, value, mapping=None)->str:
        """escape_string escapes *value* but not surround it with quotes."""
        return json.dumps(value)

    def insert_tauction_item(self, key, **kwargs)->int:
        """
        写标的详单，同时更新url状态为已抓取
        若成功，返回1
        params:
           key:
           dict keys: url, atten, rec, notice, intro, attachs,bian
            video, images, preferred, state, spidername
        """
        assert self.client
        #入库详单
        value = json.dumps(kwargs)
        self.put(self.item_hash, key, value)
        #改变状态
        if self.exists(self.item_url_hash, key):
            self.delete(self.item_url_hash, key)  #保险动作
        self.delete(self.item_url_scraping_hash, key)
        num = self.put(self.item_url_scraped_hash, key, value)
        return num


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
        assert self.client

        if (self.exists(self.item_url_scraped_hash, key) or
                self.exists(self.item_url_scraping_hash, key) or
                self.exists(self.item_url_hash, key)):
            return -1

        state = 0
        num = 0
        if kwargs.get('state'):
            # 如果状态不合法，则认为是0状态
            state = kwargs.get('state')
            if state == 1:
                num = self.put(self.item_url_scraped_hash, key, json.dumps(kwargs))
            elif state == -1:
                num = self.put(self.item_url_scraping_hash, key, json.dumps(kwargs))
            else:
                kwargs['state'] = 0
                num = self.put(self.item_url_hash, key, json.dumps(kwargs))
        else:
            kwargs['state'] = 0
            num = self.put(self.item_url_hash, key, json.dumps(kwargs))
        return num

    def fetch_auction_item_urls(self, spider, maxnum)->dict:
        """
        抓取最多max个未访问url,返回结构是{id:url}结构的字典

        params:
           spider: spider name
           maxnum: maximun urls got from db
        """
        assert maxnum > 0  and  self.client
        samples = {}
        all_sets = self.getall(self.item_url_hash)

        if all_sets:
            if len(all_sets) <= maxnum:
                samples = all_sets
            else:
                #随机获取指定数量
                sample_keys = random.sample(list(all_sets), maxnum)
                #
                samples = {k: v for k, v in all_sets.items() if k in sample_keys}
            #改变状态
            for  key, value in samples.items():
                self.delete(self.item_url_hash, key)
                self.put(self.item_url_scraping_hash, key, value)

            return {k: json.loads(v).get('url')   for k, v in samples.items()}


    def get(self, hashname, key)->str:
        """method"""
        #py3 redis.hget返回时byte类型
        data = self.client.hget(name=hashname, key=key)
        if data:
            return data.decode('utf-8')
        else:
            return None

    def put(self, hashname, key, value)->int:
        """method"""
        num = self.client.hset(hashname, key, value)
        return num

    def delete(self, hashname, *key):
        """delete        """
        self.client.hdel(hashname, *key)

    def exists(self, hashname, key):
        """method"""
        return self.client.hexists(hashname, key)

    def update(self, hashname, key, value):
        """method"""
        self.client.hset(hashname, key, value)

    def getall(self, hashname)->set:
        """method"""
        item_dict = self.client.hgetall(hashname)
        return {k.decode('utf-8'): v.decode('utf-8') for k, v in item_dict.items()}

    def clear(self, hashname):
        """method"""
        return self.client.delete(hashname)

    def getnumber(self, hashname):
        """method"""
        return self.client.hlen(hashname)
