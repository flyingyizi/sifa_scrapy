"""db client 接口定义"""
from zope.interface import Interface

# pylint:disable=inherit-non-class,no-method-argument,no-self-argument

class IDBClient(Interface):
    """db client interface"""
    def  open():
        """open db client"""

    def close():
        """close db client"""

    def  get_basic_infos(self):
        """
        about state, host, db
        return: {'host':, 'db': , 'state': ,}
        """

    def escape_string(value, mapping=None)->str:
        """escape_string escapes *value* but not surround it with quotes."""

    def insert_tauction_item(self, key, **kwargs)->int:
        """
        写标的详单，同时更新url状态为已抓取
        若成功，返回1
        params:
           key:
           dict keys: url, atten, rec, notice, intro, attachs,bian
            video, images, preferred, state, spidername
        """

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

    def fetch_auction_item_urls(self, spider, maxnum)->dict:
        """
        抓取最多max个未访问url,返回结构是{id:url}结构的字典

        params:
           spider: spider name
           maxnum: maximun urls got from db
        """
