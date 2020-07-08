# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 22:44:43 2020

@author: tu_xu
"""

# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
#from pathlib  import Path

class GpaiPage(scrapy.Item):
    """
    代表一页
    """
    tag = scrapy.Field() #固定值为pages
    #页链接
    url = scrapy.Field()
    #哪个爬虫抓取的
    spidername = scrapy.Field()
    items = scrapy.Field() #存放标的 url list

    def quote():
        """对字段中url相关字段转义"""


class GpaiItem(scrapy.Item):
    """
    代表一页中的一个标的
    """
    tag = scrapy.Field() #固定值为tagets
    title = scrapy.Field()
    url = scrapy.Field()
    # 竞买须知
    atten=scrapy.Field()
    # 竞买记录
    rec=scrapy.Field()
    #公告
    notice = scrapy.Field()
    #标的物介绍
    intro = scrapy.Field()
    # 附件
    attachs = scrapy.Field()
    # 视频介绍
    video = scrapy.Field()
    #图片
    images = scrapy.Field()
    #优先购买人
    preferred = scrapy.Field()
    #状态
    state = scrapy.Field()

    #哪个爬虫抓取的
    spidername = scrapy.Field()

# def convertjsontomd(inputfile: str, outputpath: str):
#     """
#     输入是json文件格式是CcherePageItem list
#     输出转换为markdown文件,输出仅指定路径文件名自动生成
#     """
#     from .utils import validateTitle

#     with open(inputfile, encoding='utf-8') as f:
#         import json
#         result = json.load(f)
#     # 收集topics
#     topics = set()
#     for t in result:
#         topics.add(t['topic'])

#     for topic in topics:
#         a = filter(lambda x: x['topic'] == topic, result)
#         # 按照page排序
#         pages = sorted(a, key=lambda x: x['page'])

#         # 输出markdown
#         path = Path(outputpath).joinpath(validateTitle(topic)).with_suffix('.md')
#         # 设置 buffer size 为 1024
#         with path.open(mode='w', buffering=1024, encoding='utf-8') as f:
#             # 写每一页
#             for page in pages:
#                 #
#                 f.write('\n\n')
#                 f.write('# ' + str(page['page']))
#                 f.write('\n\n')
#                 # 写每一篇文章
#                 for article in page['articles']:
#                     try:
#                         lvl = 2 if article['lvl'] == '' else int(
#                             article['lvl'])+1
#                     except Exception:
#                         lvl = 2

#                     f.write('\n')
#                     # 多于5级，markdown显示不了
#                     lvl = 5 if lvl > 5 else lvl

#                     a = ' [{}]({})\n'.format(article['title'], article['url'])
#                     f.write('#' * lvl + a)
#                     #f.write( ' '  + article['title']+'\n\n')
#                     f.write('author: ' + article['auth'] +
#                             ' '*4 + article['date'] + '\n\n')
#                     f.write(article['c'])
#                     f.write('\n')
#             #写磁盘
#             f.flush()
#             print("生成文件 ：",path)

