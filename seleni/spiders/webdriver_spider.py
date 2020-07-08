"""
该基类用于提供以下能力

1. 结合 selenium  middleware进行网页抓取
2. 标的url，与标的内容 在数据库的存储
"""
# -*- coding: utf-8 -*-
# pylint:disable=inherit-non-class,no-method-argument,no-self-argument,too-many-lines

from hashlib import md5
from contextlib import contextmanager
import time
# import traceback
# from urllib.parse import urljoin
import scrapy
from scrapy import signals
# from scrapy.http.response.html import HtmlResponse
#from pathlib import Path
# from scrapy.http import Request

# import html2text
# from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from ..db.DbClient import DbClient # cust_cfg.custcfg import cfg
from .myselenium import SeleniumRequest

from .items import(
    GpaiItem,
    GpaiPage
)


class SeleniumSpider(scrapy.Spider):
    """
    1.支持自定义action
    2.支持数据库，ref https://docs.scrapy.org/en/latest/topics/signals.html
    """
    # 指示爬取动作
    # 'list'动作入口（starturl）是使用starturl作为入口爬取标的详单url
    # 'result'动作入口（starturl）是适用标的详情页，例如'https://www1.rmfysszc.gov.cn/Handle/110407.shtml'
    grab_action = 'list'
    valid_grab_action = {'list', 'result', }

    debug_total = 0

    def __init__(self, *args, **kwargs):
        """解析定制参数        """
        super().__init__(*args, **kwargs)
        if kwargs.get('grab_action') is not None:
            if {kwargs['grab_action'], }.issubset(self.valid_grab_action):
                self.grab_action = kwargs['grab_action']
                kwargs.pop('grab_action')
            else:
                raise Exception("爬取动作'grab_action'非法:{}".format(
                    kwargs.get('grab_action')))
        self.db_client = DbClient(self.name)

        #导航页(抽取标的url的页面)加载完判断，必须由子类设置
        self.nav_page_located_css = None
        #标的详情页加载完判断，必须由子类设置
        self.detail_page_located_css = None

    def start_requests(self):
        """override"""
        if not self.nav_page_located_css or not self.detail_page_located_css:
            raise AttributeError("not found located css ")

        if self.grab_action == 'list':
            if not self.start_urls:
                raise AttributeError(
                    "Crawling could not start: 'start_urls' not found ")
            for url in self.start_urls:
                # 等待分页导航出现
                self.logger.info("等待分页导航出现:{}".format(url))
                yield SeleniumRequest(url=url,
                                      wait_time=50,
                                      wait_until=EC.presence_of_all_elements_located(
                                          (By.CSS_SELECTOR, self.nav_page_located_css)),
                                      callback=self.parse)

        elif self.grab_action == 'result':
            grab_max_pages_onetime = 1200    # 该分支中 1200,50这两个数字当前都硬编码
            maxtimes = grab_max_pages_onetime / 50
            # for url in self.start_urls:
            for urls in self.getauction_item_urls(50):
                for key, url in urls.items():
                    # self.logger.info(("请求url: {} {}").format(key, url))
                    try:
                        req = SeleniumRequest(url=url,
                                              wait_time=10,
                                              wait_until=EC.presence_of_element_located(
                                                  (By.CSS_SELECTOR, self.detail_page_located_css)),
                                              #wait_until=lambda driver:
                                              #driver.find_element_by_css_selector(
                                              #    self.detail_page_located_css),
                                              callback=self.parse_result)
                        req.meta['key'] = key
                        yield req
                    except ValueError:
                        self.logger.info("标的url不合法:%s", url)
                maxtimes -= 1
                if maxtimes <= 0:
                    break

    def parse(self, response):
        raise NotImplementedError(('{}.parse callback '
                                   'is not defined').format(self.__class__.__name__))

    def parse_result(self, response):
        raise NotImplementedError(('{}.parse callback '
                                   'is not defined').format(self.__class__.__name__))

    def spider_opened(self, spider):
        """处理spider open event"""
        # open database
        self.db_client.open()
        spider.logger.info("db连接:{}".format(self.db_client.get_basic_infos()))

    def spider_closed(self, spider):
        """处理spider close event"""
        spider.logger.info('-Spider closed: %s', spider.name)
        self.db_client.close()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """overrider"""
        spider = super(SeleniumSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed,
                                signal=signals.spider_closed)
        crawler.signals.connect(spider.spider_opened,
                                signal=signals.spider_opened)
        return spider

    def write_auction_item(self, key, item: GpaiItem):
        """写标的详单，同时更新url状态"""

        temp = dict(item)
        result = self.db_client.insert_tauction_item(key, **temp)
        if result != 1:
            self.logger.info("写详单失败{}".format(temp))

    def write_auction_item_urls(self, item: GpaiPage)->dict:
        """
        写标的url

        返回: 返回统计项 {'fail_add': x, 'sucess_add': x, 'duplicate': x}
        """
        num = 0

        statistic = {'fail_add': 0, 'sucess_add': 0, 'duplicate': 0}
        for url in item['items']:
            #skip invalid url
            if url and ('://' not in url) and (not url.startswith('data:')):
                continue

            key = md5(url.strip().encode('utf-8')).hexdigest()
            num = self.db_client.insert_tauctionitem_url(key, url=url,
                                                         spidername=item['spidername'])
            if num == -1:
                statistic['duplicate'] = statistic['duplicate'] + 1
            elif num == 0:
                statistic['fail_add'] = statistic['fail_add'] + 1
            else:
                statistic['sucess_add'] = statistic['sucess_add'] + 1
        self.logger.info("入库标的url统计：{}".format(statistic))
        return statistic



    def getauction_item_urls(self, maxnum)->dict:
        """
        生成器：抓取最多max个未访问urls, 返回结构是“{id:url}”字典数据
        """
        assert maxnum > 0

        # 先爬取db库中的urls，再爬取命令传递过来的urls
        urls = self.db_client.fetch_auction_item_urls(self.name, maxnum)
        if urls:
            while  urls and len(urls) > 0:
                yield urls
                urls = self.db_client.fetch_auction_item_urls(self.name, maxnum)
        self.logger.info("-----数据库中已经没有待抓取标的url-----")

        if self.start_urls and len(self.start_urls) > 0:
            yield {md5(url.strip().encode('utf-8')).hexdigest():url  for url in self.start_urls}



def wait_for(condition_function):
    """为识别网页更新加载完成的辅助函数"""
    start_time = time.time()
    while time.time() < start_time + 3:
        if condition_function():
            return True
        else:
            time.sleep(0.1)
    raise Exception('Timeout waiting for {}'.format(
        condition_function.__name__))


@contextmanager
def wait_for_page_load(browser, css_sel):
    """
    css_sel: 用来识别网页已经更新加载的选择器
    """
    old_page = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css_sel)))
    yield

    def page_has_loaded():
        new_page = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_sel)))
        return new_page.id != old_page.id
    wait_for(page_has_loaded)
