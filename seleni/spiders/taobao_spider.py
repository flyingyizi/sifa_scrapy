# from hashlib import md5
# from contextlib import contextmanager
# import time
import traceback
# import scrapy
# from scrapy import signals
from scrapy.http.response.html import HtmlResponse
#from pathlib import Path
# from scrapy.http import Request

import html2text
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# from ..db.DbClient import DbClient # cust_cfg.custcfg import cfg
from .myselenium import SeleniumRequest

from .webdriver_spider import (
    SeleniumSpider,
    wait_for_page_load
)

from .items import(
    GpaiItem,
    GpaiPage
)



class TaobaoSpider(SeleniumSpider):
    """
    淘宝拍卖-司法拍卖网，入口包括：
    1. 动作'list'动作入口（starturl）是适用"京东拍卖-司法拍卖网"，
       带条件或不带条件，例如"https://sf.taobao.com/item_list.htm?spm=a213w.7398504.pagination.2.6e357ddatzTQlU&auction_source=0&st_param=-1&auction_start_seg=-1&page=1"

    2. 动作'result'动作入口（starturl）是适用标的详情页，例如'https://paimai.jd.com/115386844'
    """
    name = 'tbsifa'
    #

    def __init__(self, *args, **kwargs):
        """        """
        super().__init__(*args, **kwargs)

        #导航页(抽取标的url的页面)加载完判断
        self.nav_page_located_css = '.pagination.J_Pagination'
        #标的详情页加载完判断
        self.detail_page_located_css = "#J_DetailTabMain"
        self.h = html2text.HTML2Text()

    def parse(self, response):
        """
        通过selenium遍历分页，并对每个分页收集所有标的urls，对每个标的发起请求
        """
        self.logger.info("收集每页标的url,收集入口：{}".format(response.url))

        # 容忍次数
        tolerate_times = 50
        # collect
        for urls in self.collect_all_tagets(response.request.meta['driver'], response.url):
            # 持久化标的url
            item = GpaiPage(tag='pages', url=response.url,
                            items=urls, spidername=self.name)
            statistic = self.write_auction_item_urls(item)
            yield item
            # 从实践看京东页数非常多，但往往后面都是重复的，这里增加保护动作使得程序可以退出
            tolerate_times -= 1 if (statistic['fail_add'] == 0 and
                                    statistic['sucess_add'] == 0 and
                                    statistic['duplicate'] != 0)  else 0
            if tolerate_times <= 0:
                break

    def parse_result(self, response):
        """
        TODO
        每个标的结果处理
        例如 "https://sf-item.taobao.com/sf_item/620953479609.htm"
        """
        self.h.bypass_tables = True
        # 获取标题
        sel = '.pm-main > h1 ::text'
        item_title = response.css(sel).get().strip()
        # 获取标的视频介绍 TODO
        item_video = None
        # 竞买公告
        sel = '#NoticeDetail'
        item_notice = response.css(sel).get()
        item_notice = self.h.handle(item_notice)
        # 竞买须知
        sel = '#ItemNotice'
        item_atten = response.css(sel).get()
        item_atten = self.h.handle(item_atten)
        # 获取标的物介绍
        sel = '#J_DetailTabMain > .addition-desc.J_Content'
        item_intro = response.css(sel).getall()
        item_intro = ''.join(map(lambda x: self.h.handle(x), item_intro))
        # 获取图片
        sel = '.video-img img ::attr(src)'
        item_images: list = response.css(sel).getall()
        item_images = list(
            map(lambda x: response.urljoin(x), item_images))
        # 获取状态
        sel = '#sf-countdown *::text '
        item_state = ''.join(response.css(sel).getall()).strip()

        # 获取标的附件TODO
        # sel = '#J_DownLoadFirst .desc-att-item'
        # sels = response.css(sel)
        item_attachs = dict()
        # for i in sels:
        #     title = i.css('a *::text').get()
        #     href = i.css('a::attr("href")').get()
        #     item_attachs[title] = href
        # 获取优先购买人信息
        sel = '#J_ItemPriority'
        item_preferred_buyers = response.css(sel).get()
        item_preferred_buyers = self.h.handle(item_preferred_buyers)
        # 获取竞买记录
        sel = '#J_RecordContent #J_RecordList'
        item_rec = response.css(sel).get()
        item_rec = self.h.handle(item_rec)

        item = GpaiItem(tag='tagets', url=response.url, notice=item_notice, video=item_video,
                        intro=item_intro, attachs=item_attachs, atten=item_atten, rec=item_rec,
                        images=item_images, state=item_state, title=item_title,
                        preferred=item_preferred_buyers, spidername=self.name)
        # 入库
        self.write_auction_item(response.meta['key'], item)

        yield item

    def _to_next_page(self, driver):
        """
        通过·下一页·按钮进行跳转
        ret 1:代表成功跳转
        ret -1: 代表跳转失败
        """
        ele = None
        try:
            # # 跳转到下一页
            with wait_for_page_load(driver, ".sf-content .sf-item-list li a"):

                ele = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                '.pagination.J_Pagination .next')))
                # ref google selenium-debugging-element-is-not-clickable-at-point-x-y
                driver.execute_script("arguments[0].click();", ele)
                return 1
        except TimeoutException:
            self.logger.info("跳转下一页失败 : %s", traceback.format_exc())
        return -1

    def collect_all_tagets(self, driver, starturl: str):
        """
        从入口starturl开始，遍历每一页收集所有标的url，该函数执行前务必已经`driver.get(starturl)`
        """
        try:
            total = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div.pagination.J_Pagination  .page-total'))
            )
        except TimeoutException:  # TimeoutException
            self.logger.debug("导航页有问题，获取导航失败：{}".format(starturl))
            return
        # 分页信息分析
        max_page_num = int(total.text)

        try:
            nav = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'div.pagination.J_Pagination a'))
            )
        except TimeoutException:  # TimeoutException
            self.logger.debug("导航页有问题，获取导航失败：{}".format(starturl))
            return
        # 跳转到首页,第二个是第一页
        driver.execute_script("arguments[0].click();", nav[1])

        # 从首页开始遍历每页，动作是收集所有标的，然后到下一页.
        self.logger.info(
            "将收集{}页，starturl{}".format(max_page_num, starturl))

        max_retry_times = 5  # 尝试5次
        retrys = max_retry_times
        for i in range(max_page_num):
            # 提示
            if i < max_page_num - 1 and i % 50 == 0:
                self.logger.info("第{}页开始收集".format(i))
            elif i == max_page_num - 1:
                self.logger.info("已收集{}页".format(i))

            try:
                _ = WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR,
                                                         ".sf-content .sf-item-list li a")))
                #从实践看，网页会变化，所以采用保存下来再解析
                response = HtmlResponse(driver.current_url,
                                        body=str.encode(driver.page_source),
                                        encoding='utf-8')
                yield list(set(map(lambda x: response.urljoin(x),
                                   response.css(".sf-content .sf-item-list li a::attr(href)").getall())))

            except TimeoutException:
                self.logger.info("{} 页收集标的url失败".format(i))

            # 已经到了最后页，就不需要跳转下一页了
            if i < max_page_num - 1:
                # 跳转到下一页，
                if self._to_next_page(driver) == -1:
                    retrys -= 1
                    if retrys <= 0:
                        break  # 如果跳转失败跳出循环结束
                else:
                    retrys = max_retry_times
        # return urls
        return
