# -*- coding: utf-8 -*-
import re
from pathlib import Path
import logging
from urllib.parse import urljoin
import scrapy
#
# from urllib import parse
from scrapy.http.response.html import HtmlResponse
from scrapy.selector import Selector
from scrapy.http import Request

import html2text
from .items import  (
    CchereArticleItem,
    CcherePageItem
)

from .utils import (
    zJ_PE,
    getContentInSep
)

#
# scrapy  crawl cchere -a start_urls="https://www.talkcc.net/thread/4519373,https://www.talkcc.net/topic/4519373/7"


class CchereSpider(scrapy.Spider):
    """
    支持全看模式“/thread/XXX”与主题模式“/topic/XXX”的爬取，这两种模式的特点是有分页信息
    e.g： scrapy crawl cchere -a start_urls="https://www.talkcc.net/thread/4519373,"
    """
    name = 'cchere'
    # allowed_domains = ['https://www.talkcc.net/']
    # start_urls = ["https://www.talkcc.net/thread/4519373"]

    # def __init__(self, *args, **kwargs):
    #     """
    #     支持命令行传递starturl
    #     e.g： scrapy crawl my_spider -a start_urls="http://example1.com,http://example2.com"
    #     """
    #     super().__init__(*args, **kwargs)
    #
    h = html2text.HTML2Text()

    def parse(self, response):
        """
        处理start_urls响应,仅仅做翻页处理
        """
        # 从scrapy response获得解码后html snippet
        body = self._getls_cchereLS(response)

        # 得到翻页urls
        pages = self._getPages(body)
        for i, page in pages.items():
            absloute = urljoin(response.url, page)
            logging.info('翻页:%s', absloute)
            yield Request(absloute, meta={"page": i}, callback=self.parse_articles)

    def parse_articles(self, response):
        """
        处理每个翻页链接的内容,
        """
        output_p = CcherePageItem()
        output_p['url'] = response.url

        # 获取所属页信息
        output_p['page'] = response.meta['page']
        # 从scrapy response获得解码后html snippet
        body = self._getls_cchereLS(response)
        linkpart = self._getls_cchereRS(response)

        # article title 与 relative ul的字典
        maps = self._getLinks(linkpart)

        # 获取专题名称
        output_p['topic'] = self._getTopic(body)

        # 存放导出的文章
        output_articles = []

        for orig in self._getArticles(body):
            s = Selector(text=orig)
            # 获取文章层级
            lev = s.css("article .sPACont >small::text").get(default='')
            # 获取文章是回复哪篇文章
            anstourl = s.css(
                "article div:nth-child(1) a[href^='/article/']::attr(href)").get(default='')
            anstourl = urljoin(response.url, anstourl)

            # 获取作者，第一个div中的<a>元素查找
            author = s.css(
                "article div:nth-child(1) a[href^='/user/']::text").get(default='')
            # 获取标题，取第一个<b>元素
            title = s.css(
                "article .sPACont b:first-of-type::text").get(default='')

            # 获得文章链接
            url = maps.get(title, None)
            if url != None:
                url = urljoin(response.url, url)

            # 获取发布时间
            date = s.css("article .sPACont .sPMc *::text").get(default='')

            # 获取正文,
            content = s.css("article .sPACont").get()
            rubbish = s.css(
                "article .sPACont   .sHFixedA, .sPMc, .sForPER , a[onclick]").getall()
            # 排除
            for rb in rubbish:
                content = content.replace(rb, "")
            # 将正文中的图片链接转成绝对地址
            images = Selector(text=content).css(" .sPACont img").getall()
            # 将正文中的引用链接转成绝对地址
            anchors = Selector(text=content).css(" .sPACont a").getall()
            conv = []
            # 构造替换映射-img
            for i in images:
                t = Selector(text=i)
                old = t.css("img::attr(src)").get()
                new = urljoin(response.url, old)
                i_new = i.replace(old, new)
                conv.append((i, i_new))
            # 构造替换映射-anchor
            for i in anchors:
                t = Selector(text=i)
                old = t.css("a::attr(href)").get()
                new = urljoin(response.url, old)
                i_new = i.replace(old, new)
                conv.append((i, i_new))
            # 替换
            for o, n in dict(conv).items():
                content = content.replace(o, n)
            #美化
            content=self.h.handle(content)

            article = CchereArticleItem(lvl=lev, title=title, date=date,
                                        c=content, auth=author,
                                        anstourl=anstourl, url=url)
            output_articles.append(article)

        output_p['articles'] = output_articles
        yield output_p


    def _getls_cchereLS(self, response: HtmlResponse):
        """
        获取页面解码后文章部分的html代码，解析var ls=xxx得到
        """
        output = None
        for s in response.css("script").getall():
            # 该语句依赖js语句是分行
            ex = re.search(r'var[\t ]+ls[\t ]*=[\t ]*(.*)',
                           s, flags=re.IGNORECASE)
            if ex != None:
                # 见上面正则，只定义了一个group
                output = ex.groups()[0]
                break

        # 去掉外层双引号
        o1 = getContentInSep(output)
        # 解码
        o2 = zJ_PE(o1)
        return o2

    def _getls_cchereRS(self, response: HtmlResponse):
        """
        获取页面解码后关联链接部分的html代码，解析var rs=xxx得到
        """
        output = None
        for s in response.css("script").getall():
            # 该语句依赖js语句是分行
            ex = re.search(r'var[\t ]+rs[\t ]*=[\t ]*(.*)',
                           s, flags=re.IGNORECASE)
            if ex != None:
                # 见上面正则，只定义了一个group
                output = ex.groups()[0]
                break

        # 去掉外层双引号
        o1 = getContentInSep(output)
        # 解码
        o2 = zJ_PE(o1)
        return o2

    def _getLinks(self, linkpart: str):
        """
        从网页中提取出文章链接字典表 key是title，value是相对链接
        """
        s = Selector(text=linkpart)
        out = []
        for a in s.css(".s_Sec .s_SecC a").getall():
            t = Selector(text=a)
            link = t.css("a::attr(href) ").get()
            title = t.css("a::text ").get()
            out.append((title, link))

        return dict(out)
    def _getArticles(self, body: str) -> list:
        """
        从网页中提取出文章list
        """
        s = Selector(text=body)
        articles = s.css("#D_GT_L article").getall()
        return articles

    def _getTopic(self, body: str):
        """
        从网页中提取出文章所在主题，<h3 class="sTAC sNoWrap">
        """
        s = Selector(text=body)
        topic = ''.join(s.css(".sTAC *::text").getall()
                        ).replace('\n', '').strip()
        return topic

    def _getPages(self, body: str):
        """
        从网页中提取出翻页relative url dict,如果无则返回None
        """
        s = Selector(text=body)

        # 返回类似  ['/thread/4519373', '/thread/4519373/2', '/thread/4519373/6']
        pages = s.css(".s_PGNav .s_FW_R  a::attr(href)").getall()
        if len(pages) == 0:
            return None

        # 获取最大页,认为最后一项是最后页
        endp = pages[-1]
        maxp = int(Path(endp).name)

        output = list()
        for i in range(1, maxp+1):
            a = urljoin(endp, str(i))
            output.append((i, a))

        return dict(output)
