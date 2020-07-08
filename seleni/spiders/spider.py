# from hashlib import md5
# from contextlib import contextmanager
# import time
import traceback
from urllib.parse import urljoin
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


class RmfysszcSpider(SeleniumSpider):
    """
    人民法院诉讼资产网 ，入口包括：
    动作'list'，与'list_result'入口：拍卖项目页（https://www1.rmfysszc.gov.cn/projects.shtml）带条件或不带条件的
    动作'result'入口：例如'https://www1.rmfysszc.gov.cn/Handle/110407.shtml'
    """
    name = 'rmfysszc'
    #

    # allowed_domains = ['https://www.talkcc.net/']
    # start_urls = ["..,"]

    def __init__(self, *args, **kwargs):
        """        """
        super().__init__(*args, **kwargs)

        #导航页(抽取标的url的页面)加载完判断
        self.nav_page_located_css = '#page'
        #标的详情页加载完判断
        self.detail_page_located_css = '.xmxx_main'
        self.h = html2text.HTML2Text()

    def parse(self, response):
        """
        通过selenium遍历分页，并对每个分页收集所有标的urls，对每个标的发起请求
        """
        self.logger.info("收集每页标的url,收集入口：{}".format(response.url))

        # collect
        for urls in self.collect_all_tagets(response.request.meta['driver'], response.url):
            # 持久化标的url
            item = GpaiPage(tag='pages', url=response.url,
                            items=urls, spidername=self.name)
            self.write_auction_item_urls(item)
            yield item

    def parse_result(self, response):
        """
        每个标的结果处理
        例如 "https://www.rmfysszc.gov.cn/statichtml/rm_obj/110358.shtml"
        """
        #保留html table，不转为markdown语法
        self.h.bypass_tables = True
        # 获取标题
        sel = '#Title *::text'
        item_title = response.css(sel).get()
        # 获取标的视频介绍
        item_video = None
        # 竞买须知
        sel = '#jmxz'
        item_atten = response.css(sel).get()
        item_atten = self.h.handle(item_atten)
        # 竞买公告
        sel = '#pmgg'
        item_notice = response.css(sel).get()
        item_notice = self.h.handle(item_notice)
        # 获取标的物介绍
        sel = '#bdjs11 table'
        item_intro = response.css(sel).get()
        item_intro = self.h.handle(item_intro)
        # 获取状态
        sel = '#time1 *::text'
        item_state = response.css(sel).getall()
        item_state = ''.join(item_state).strip()
        # 获取标的附件
        sel = '#pmgg a'
        sels = response.css(sel)
        item_attachs = dict()
        for i in sels:
            title = i.css('a::text').get()
            href = i.css('a::attr("href")').get()
            item_attachs[title] = urljoin(response.url, href)
        sel = '#bdjs11 table a'
        sels = response.css(sel)
        for i in sels:
            title = i.css('a::text').get()
            href = i.css('a::attr("href")').get()
            item_attachs[title] = href

        # 获取图片
        sel = '#bdjs11 img'
        item_images: list = response.css(sel+'::attr(src)').getall()
        # 获取优先购买人信息
        sel = '#yxgmq .yxq'
        item_preferred_buyers = response.css(sel).get()
        item_preferred_buyers = self.h.handle(item_preferred_buyers)

        # 获取竞买记录
        sel = '#jjjl1'
        item_rec = response.css(sel).get()
        item_rec = self.h.handle(item_rec)

        item = GpaiItem(tag='tagets', url=response.url, notice=item_notice, video=item_video,
                        intro=item_intro, attachs=item_attachs, atten=item_atten, rec=item_rec,
                        images=item_images, state=item_state, title=item_title,
                        preferred=item_preferred_buyers, spidername=self.name)
        # 入库
        self.write_auction_item(response.meta['key'], item)

        yield item

    def collect_all_tagets(self, driver, starturl: str) -> list:
        """
        从入口starturl开始，遍历每一页收集所有标的url，该函数执行前务必已经`driver.get(starturl)`

        适用"人民法院诉讼资产网中'拍卖项目'"，带条件或不带条件

        e.g. starturl is "https://www1.rmfysszc.gov.cn/projects.shtml"
        """

        # 分页信息分析

        # 首先跳转到尾页
        try:
            nav = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, '#page a'))
            )
            # 到尾页
            nav[len(nav)-1].click()
            driver.implicitly_wait(10)
        except TimeoutException:  # TimeoutException
            self.logger.debug("导航页有问题，初始跳转尾页失败：{}".format(starturl))

        max_page_num = 0
        # 通过在尾页查找最大页数
        try:
            nav = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, '#page .pagecur1'))
            )
            max_page_num = int(nav[len(nav)-1].text)
        except TimeoutException:  # TimeoutException
            self.logger.debug("导航页有问题，计算最大页数失败：{}".format(starturl))

        # 跳到到首页,以便后续开始遍历
        try:
            nav = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, '#page a'))
            )
            nav[0].click()
        except TimeoutException:  # TimeoutException
            self.logger.debug("导航页有问题，初始跳转首页失败：{}".format(starturl))

        # 从首页开始遍历每页，动作是收集所有标的，然后到下一页.
        for i in range(max_page_num):
            # 提示
            if i < max_page_num - 1 and i % 50 == 0:
                self.logger.info("第{}页开始收集".format(i))
            elif i == max_page_num - 1:
                self.logger.info(
                    "已收集{}页，starturl{}".format(i, starturl))

            try:
                goodlist = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#project_1 a')))
                #排重后yield
                yield list(set(map(lambda x: x.get_attribute('href'), goodlist)))

            except TimeoutException:
                self.logger.info("{} 页收集标的url失败".format(i))
            try:
                # ,通过点击倒数第二项,跳转到下一页
                nav = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#page a')))
                nav[len(nav)-2].click()
                # 不知道是否有用。担心点击下一页还没有取到的时候，'#project_1 a'还有数据
                driver.implicitly_wait(10)
            except TimeoutException:  # TimeoutException:
                self.logger.info("跳转 page:{}".format(i))


class JDSpider(SeleniumSpider):
    """
    京东拍卖-司法拍卖网，入口包括：
    1. 动作'list'，与'list_result'动作入口（starturl）是适用"京东拍卖-司法拍卖网"，
       带条件或不带条件，例如"https://auction.jd.com/sifa_list.html"

    2. 动作'result'动作入口（starturl）是适用标的详情页，例如'https://paimai.jd.com/115386844'
    """
    name = 'jdsifa'
    #

    def __init__(self, *args, **kwargs):
        """        """
        super().__init__(*args, **kwargs)

        #导航页(抽取标的url的页面)加载完判断
        self.nav_page_located_css = '.ui-pager'
        #标的详情页加载完判断
        self.detail_page_located_css = '#root'
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
        每个标的结果处理
        例如 "https://paimai.jd.com/115422046"
        """
        self.h.bypass_tables = True
        # 获取标题
        sel = '.pm-name *::text'
        item_title = response.css(sel).get()
        # 获取标的视频介绍
        item_video = None
        # 竞买公告
        sel = 'li.floor:nth-child(1)'
        item_notice = response.css(sel).get()
        item_notice = self.h.handle(item_notice)
        # 竞买须知
        sel = 'li.floor:nth-child(2)'
        item_atten = response.css(sel).get()
        item_atten = self.h.handle(item_atten)
        # 获取标的物介绍
        sel = 'li.floor:nth-child(3)'
        item_intro = response.css(sel).get()
        item_intro = self.h.handle(item_intro)
        # 获取图片
        sel = 'li.floor:nth-child(3) img ::attr(src)'
        item_images: list = response.css(sel).getall()
        item_images = list(
            map(lambda x: urljoin(response.url, x), item_images))
        # 获取状态
        sel = '.pm-summary .mt .state *::text '
        item_state = ''.join(response.css(sel).getall()).strip()
        sel = '.pm-summary .mt .startTime *::text '
        t_addi = ''.join(response.css(sel).getall()).strip()
        item_state = item_state + t_addi
        # 获取标的附件
        sel = '.attachFiles'
        sels = response.css(sel)
        item_attachs = dict()
        for i in sels:
            title = i.css('a::text').get()
            href = i.css('a::attr("href")').get()
            item_attachs[title] = href
        # 获取优先购买人信息
        sel = '.purchaserList'
        item_preferred_buyers = response.css(sel).get()
        item_preferred_buyers = self.h.handle(item_preferred_buyers)
        # 获取竞买记录
        sel = '.bidList'
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
            with wait_for_page_load(driver, '.goods-list li  a'):

                ele = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.ui-pager .ui-pager-next')))
                # ref google selenium-debugging-element-is-not-clickable-at-point-x-y
                driver.execute_script("arguments[0].click();", ele)
                return 1
        except TimeoutException:
            self.logger.info("跳转下一页失败 : %s", traceback.format_exc())
        return -1

    def collect_all_tagets(self, driver, starturl: str):
        """
        从入口starturl开始，遍历每一页收集所有标的url，该函数执行前务必已经`driver.get(starturl)`

        适用"京东拍卖-司法拍卖网"，带条件或不带条件

        e.g. starturl is "https://auction.jd.com/sifa_list.html"
        """
        try:
            nav = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, '.ui-pager a'))
            )
        except TimeoutException:  # TimeoutException
            self.logger.debug("导航页有问题，获取导航'.ui-pager'失败：{}".format(starturl))
            return
        # 分页信息分析
        if nav[len(nav)-1].get_attribute('class') == 'ui-pager-next':
            ##最后一项是next, 则倒数第二项为max_page_num
            max_page_num = int(nav[len(nav)-2].text)
        else:
            #最后一项是不是next, 则最后项为max_page_num
            max_page_num = int(nav[len(nav)-1].text)
        # 跳转到首页
        if nav[0].get_attribute('class') == 'ui-pager-prev':
            # nav[1].click()
            driver.execute_script("arguments[0].click();", nav[1])
        else:
            # nav[0].click()
            driver.execute_script("arguments[0].click();", nav[0])
        # 从首页开始遍历每页，动作是收集所有标的，然后到下一页.
        self.logger.info(
            "JDSpider.collect_all_tagets将收集{}页，starturl{}".format(max_page_num, starturl))

        max_retry_times = 5  # 尝试5次
        retrys = max_retry_times
        for i in range(max_page_num):
            # 提示
            if i < max_page_num - 1 and i % 50 == 0:
                self.logger.info("第{}页开始收集".format(i))
            elif i == max_page_num - 1:
                self.logger.info(
                    "已收集{}页，starturl{}".format(i, starturl))

            try:
                goodlist = WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.goods-list li >a')))
                #排重后yield
                yield list(set(map(lambda x: x.get_attribute('href'), goodlist)))
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


class SFCaaSpider(SeleniumSpider):
    """
    拍卖行业协会网 司法拍卖，入口包括：

    1.动作'list'，与'list_result'动作入口（starturl）是适用"拍卖行业协会网 司法拍卖"，
        带条件或不带条件，例如"https://sf.caa123.org.cn/pages/lots.html?lotMode=2"

    2.动作'result'动作入口（starturl）是适用标的详情页，例如''
    """
    name = 'sfcaa123'
    #

    # allowed_domains = ['https://www.talkcc.net/']
    # start_urls = ["..,"]

    def __init__(self, *args, **kwargs):
        """        """
        super().__init__(*args, **kwargs)

        #导航页(抽取标的url的页面)加载完判断
        self.nav_page_located_css = '.pagination'
        #标的详情页加载完判断
        self.detail_page_located_css = '#DetailTabMain'
        self.h = html2text.HTML2Text()

    def parse(self, response):
        """
        通过selenium遍历分页，并对每个分页收集所有标的urls，对每个标的发起请求
        """
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
        每个标的结果处理
        """
        self.h.bypass_tables = True
        # 标的标题
        sel = '.pm-main #bid_name::text'
        item_title = response.css(sel).get().strip()
        # 获取竞买公告
        sel = '.detail-main #NoticeDetail'
        item_notice = response.css(sel).get()
        item_notice = self.h.handle(item_notice)
        # 获取竞买须知
        sel = '.detail-main #ItemNotice'
        item_atten = response.css(sel).get()
        item_atten = self.h.handle(item_atten)
        # 获取标的物介绍
        sel = '.detail-main #RemindTip'
        item_intro = response.css(sel).get()
        item_intro = self.h.handle(item_intro)
        # 获取竞买记录
        sel = '#RecordContent table'
        item_rec = response.css(sel).get()
        item_rec = self.h.handle(item_rec)
        # 状态
        sel = '#sf-countdown .title ::text'
        item_state = response.css(sel).get()
        sel = '#sf-countdown .countdown *::text'
        t_addi = ''.join(response.css(sel).getall()).strip()
        item_state = item_state+' '+t_addi
        ####################
        # 获取标的附件
        sel = '#NoticeDetail .detail-adjunct a'
        sels = response.css(sel)
        item_attachs = dict()
        for i in sels:
            title = i.css('a::text').get()
            href = i.css('a::attr("href")').get()
            item_attachs[title] = href
        ####################
        # # 获取标的视频介绍TODO
        sel = '.detail-main #RemindTip .video-img .video_slide'
        item_video = dict()
        # try:
        #     item_video['src'] = response.css(sel+'::attr(src)').get().strip()
        #     item_video['poster'] = response.css(
        #         sel+'::attr(poster)').get().strip()
        # except Exception:
        #     pass
        # 获取图片
        sel = '.detail-main #RemindTip .video-img .sf-pic-slide img'
        item_images: list = response.css(sel+'::attr(src)').getall()
        # # 获取优先购买人信息TODO
        item_preferred_buyers = None
        # sel = ''
        # item_preferred_buyers = response.css(sel).get()
        # item_preferred_buyers = self.h.handle(item_preferred_buyers)

        item = GpaiItem(tag='tagets', url=response.url, notice=item_notice, video=item_video,
                        intro=item_intro, attachs=item_attachs, atten=item_atten, rec=item_rec,
                        images=item_images, state=item_state, title=item_title,
                        preferred=item_preferred_buyers, spidername=self.name)
        # 入库
        self.write_auction_item(response.meta['key'], item)
        yield item


    def _to_first_page(self, driver):
        """
        通过·到xx页· 输入框与 `确认`按钮进行跳转
        ret 1:代表成功调制
        ret -1: 代表跳转失败
        """
        try:
            # # 跳转到下一页
            with wait_for_page_load(driver, '.auction-list li  a'):
                # 第x页输入框
                inp = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.pagination .page-jump')))
                inp.clear()
                inp.send_keys('1')

                click_bt = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.pagination .page-skip  button')))
                click_bt.click()
                return 1
        except TimeoutException:
            self.logger.info("SFCaaSpider._to_first_page跳转失败")
        return -1

    def _to_next_page(self, driver):
        """
        通过 `next`按钮进行跳转
        ret 1:代表成功调制
        ret -1: 代表跳转失败
        """
        try:
            # # 跳转到下一页
            with wait_for_page_load(driver, '.auction-list li  a'):
                # next按钮
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.pagination .next')))
                # ref google selenium-debugging-element-is-not-clickable-at-point-x-y
                driver.execute_script("arguments[0].click();", next_button)
                return 1
        except TimeoutException:  # TimeoutException:
            self.logger.info("跳转下一页失败; %s", traceback.format_exc())
        return -1

    def collect_all_tagets(self, driver, starturl: str) -> set:
        """
        从入口starturl开始，遍历每一页收集所有标的url，该函数执行前务必已经`driver.get(starturl)`

        拍卖行业协会网 司法拍卖入口，带条件或不带条件

        e.g. starturl is "https://sf.caa123.org.cn/pages/lots.html?lotMode=2"
        """
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '.pagination .page-jump'))
            )
        except TimeoutException:
            self.logger.debug(
                "导航页有问题，获取导航'.pagination .page-jump'失败：{}".format(starturl))
            return

        # 跳转到首页
        self._to_first_page(driver)
        # 获取最大页数
        max_page_num = int(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '.pagination .page-total'))).text)

        # 从首页开始遍历每页，动作是收集所有标的，然后到下一页.
        self.logger.info(
            "SFCaaSpider.collect_all_tagets将收集{}页，starturl{}".format(max_page_num, starturl))
        for i in range(max_page_num-1):
            try:
                goodlist = WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.auction-list li  >a')))
                #排重后yield
                yield list(set(map(lambda x: urljoin(driver.current_url,
                                                     x.get_attribute('href')),
                                   goodlist)))

            except TimeoutException:  # TimeoutException:
                self.logger.info(
                    "SFCaaSpider.collect_all_tagets收集失败，page:{}".format(i))

            # 提示
            if i % 50 == 0:
                self.logger.info(
                    "SFCaaSpider.collect_all_tagets已收集{}页，starturl{}".format(i, starturl))
            # 跳转到下一页，如果跳转失败跳出循环结束
            if self._to_next_page(driver) == -1:
                break


class GPSpider(SeleniumSpider):
    """
    公拍网，入口包括：
    1.动作'list'动作入口（starturl）是适用"公拍网, 法院自主拍卖"，
      带条件或不带条件，例如"http://s.gpai.net/sf/search.do?action=court"

    2.动作'result'动作入口（starturl）是适用标的详情页，
      例如'https://www1.rmfysszc.gov.cn/Handle/110407.shtml'
    """
    name = 'gpai'
    #
    h = html2text.HTML2Text()

    # allowed_domains = ['https://www.talkcc.net/']
    # start_urls = ["..,"]

    def __init__(self, *args, **kwargs):
        """        """
        super().__init__(*args, **kwargs)

        #导航页(抽取标的url的页面)加载完判断
        self.nav_page_located_css = 'body .page-bar'
        #标的详情页加载完判断
        self.detail_page_located_css = '.bottom'
        self.h = html2text.HTML2Text()

    def parse(self, response):
        """
        获取所有分页urls，对每个分页发起请求
        """
        # 获取分页链接list
        sel = 'body .page-bar'
        pages = response.css(f'{sel}'+' ' + 'a::attr("href")').getall()
        # 结果类似下面，需要从中分析max page
        # ['http://s.gpai.net/sf/search.do?action=court&cityNum=310109&Page=0',
        # ...
        #  'http://s.gpai.net/sf/search.do?action=court&cityNum=310109&Page=2']

        # # 得到翻页urls
        for page in pages:
            absloute = urljoin(response.url, page)
            self.logger.info('翻页: %s', absloute)
            yield SeleniumRequest(url=absloute,
                                  wait_time=10,
                                  wait_until=lambda driver: driver.find_element_by_css_selector(
                                      '.bottom'),
                                  callback=self.parse_targets)

    def parse_targets(self, response):
        """
        对特定分页，解析出其中的标的
        """
        # 获取页面每项标的link
        sel = '.main-col-list .list-item .item-tit a::attr("href")'
        urls = response.css(sel).getall()
        # 结果类似下面
        # ['http://www.gpai.net/sf/item2.do?Web_Item_ID=28120',
        # ...
        #  'http://www.gpai.net/sf/item2.do?Web_Item_ID=28562']
        # collect
        item = GpaiPage(tag='pages', url=response.url,
                        items=urls, spidername=self.name)
        self.write_auction_item_urls(item)
        yield item



    def parse_result(self, response: HtmlResponse):
        """
        每个标的结果处理
        """
        # 标的标题
        sel = '.d-m-title'
        item_title = response.css(sel).get()
        item_title = self.h.handle(item_title)
        # 获取竞买公告
        sel = '#menuid1 + .d-title + .d-article'
        item_notice = response.css(sel).get()
        item_notice = self.h.handle(item_notice)
        # 获取竞买须知
        sel = '#menuid2 + .d-title + .d-article'
        item_atten = response.css(sel).get()
        item_atten = self.h.handle(item_atten)
        # 获取标的物介绍
        sel = '#menuid3 + .d-title + .d-block'
        item_intro = response.css(sel).get()
        item_intro = self.h.handle(item_intro)
        # 获取竞买记录
        sel = '#menuid4 + .d-title + .d-article'
        item_rec = response.css(sel).get()
        item_rec = self.h.handle(item_rec)

        # 状态
        sel = '#ItemArea .d-m-time .fl::text'
        item_state = response.css(sel).get()

        # 获取标的附件
        sel = '.d-block-download a'
        sels = response.css(sel)
        item_attachs = dict()
        for i in sels:
            title = i.css('a::text').get()
            href = i.css('a::attr("href")').get()
            item_attachs[title] = href
        # 获取标的视频介绍
        sel = '.d-block > .d-article video'
        item_video = dict()
        if response.css(sel+'::attr(src)').get():
            item_video['src'] = response.css(sel+'::attr(src)').get().strip()
            item_video['poster'] = response.css(
                sel+'::attr(poster)').get().strip()

        # 获取图片
        sel = '.ItemImgAll img'
        item_images: list = response.css(sel+'::attr(src)').getall()
        # 获取优先购买人信息
        sel = '.d-block .d-block-tb table'
        item_preferred_buyers = response.css(sel).get()
        item_preferred_buyers = self.h.handle(item_preferred_buyers)

        item = GpaiItem(tag='tagets', url=response.url, notice=item_notice, video=item_video,
                        intro=item_intro, attachs=item_attachs, atten=item_atten, rec=item_rec,
                        images=item_images, state=item_state, title=item_title,
                        preferred=item_preferred_buyers, spidername=self.name)

        # 入库
        self.write_auction_item(response.meta['key'], item)
        yield item
