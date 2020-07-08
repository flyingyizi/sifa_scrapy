"""
db 封装

爬虫使用db，通过‘DbClient’屏蔽各DB差异，具体后台使用哪个数据库，由
`cust_cfg/custcfg.py`配置中的`'CONN_DB_INFO'`节点的配置决定
"""
import sys
import os
from zope.interface import implementer
from ..cust_cfg.custcfg import cfg

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from interfaces import IDBClient

@implementer(IDBClient)
class DbClient:
    """ 抽象客户端，根据配置使用不同DB客户端 """

    def __init__(self, spider):
        """
        spider:  spider name
        """
        __type = None

        #获取数据库配置
        from_cfg = cfg[spider]    #配置是按照spider name分开配置
        self.db_info = from_cfg['scrapy_crawl']['CONN_DB_INFO']
        if self.db_info['DBTYPE'] == "mysql":
            __type = "MysqlClient"
        elif self.db_info['DBTYPE'] == "redis":
            __type = "RedisClient"
        # elif "SSDB" == config.db_type:
        #     __type = "SsdbClient"
        # elif "MONGODB" == config.db_type:
        #     __type = "MongodbClient"
        else:
            pass
        assert __type, (
            'type error, Not support DB type: {}'.format(self.db_info['DBTYPE']))
        self.client = getattr(__import__(__type), __type)(**self.db_info)

    def  get_basic_infos(self):
        """
        about state, host, db
        return: {'host':, 'db': , 'state': ,}
        """
        return self.client.get_basic_infos()


    def  open(self):
        """open db client"""
        self.client.open()


    def close(self):
        """close db client"""
        self.client.close()

    def escape_string(self, value, mapping=None)->str:
        """escape_string escapes *value* but not surround it with quotes."""
        self.client.escape_string(value, mapping)

    def insert_tauction_item(self, key, **kwargs)->int:
        """
        写标的详单，同时更新url状态为已抓取
        若成功，返回1
        params:
           key:
           dict keys: url, atten, rec, notice, intro, attachs,bian
            video, images, preferred, state, spidername
        """
        return self.client.insert_tauction_item(key, **kwargs)

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
        return self.client.insert_tauctionitem_url(key, **kwargs)

    def fetch_auction_item_urls(self, spider, maxnum)->dict:
        """
        抓取最多max个未访问url,返回结构是{id:url}结构的字典

        params:
           spider: spider name
           maxnum: maximun urls got from db
        """
        return self.client.fetch_auction_item_urls(spider, maxnum)
