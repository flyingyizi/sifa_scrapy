# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from pathlib  import Path

class CcherePageItem(scrapy.Item):
    """
    代表一页
    """
    #
    url = scrapy.Field()
    articles = scrapy.Field() #存放CchereArticleItem list
    # 属于哪个专题
    topic = scrapy.Field()
    # 属于哪个分页
    page = scrapy.Field()


class CchereArticleItem(scrapy.Item):
    """
    代表一页中的一篇文章
    """
    url = scrapy.Field()
    # 是回复哪篇文章
    anstourl = scrapy.Field()
    title = scrapy.Field()
    # 文章正文
    c = scrapy.Field()
    # 在cchere全看方式下"/thread/xx"具备的层级信息
    lvl = scrapy.Field()
    
    auth = scrapy.Field()
    date = scrapy.Field()


def convertjsontomd(inputfile: str, outputpath: str):
    """
    输入是json文件格式是CcherePageItem list
    输出转换为markdown文件,输出仅指定路径文件名自动生成
    """
    from .utils import validateTitle

    with open(inputfile, encoding='utf-8') as f:
        import json
        result = json.load(f)
    # 收集topics
    topics = set()
    for t in result:
        topics.add(t['topic'])

    for topic in topics:
        a = filter(lambda x: x['topic'] == topic, result)
        # 按照page排序
        pages = sorted(a, key=lambda x: x['page'])

        # 输出markdown
        path = Path(outputpath).joinpath(validateTitle(topic)).with_suffix('.md')
        # 设置 buffer size 为 1024
        with path.open(mode='w', buffering=1024, encoding='utf-8') as f:
            # 写每一页
            for page in pages:
                #
                f.write('\n\n')
                f.write('# ' + str(page['page']))
                f.write('\n\n')
                # 写每一篇文章
                for article in page['articles']:
                    try:
                        lvl = 2 if article['lvl'] == '' else int(
                            article['lvl'])+1
                    except Exception:
                        lvl = 2

                    f.write('\n')
                    # 多于5级，markdown显示不了
                    lvl = 5 if lvl > 5 else lvl

                    a = ' [{}]({})\n'.format(article['title'], article['url'])
                    f.write('#' * lvl + a)
                    #f.write( ' '  + article['title']+'\n\n')
                    f.write('author: ' + article['auth'] +
                            ' '*4 + article['date'] + '\n\n')
                    f.write(article['c'])
                    f.write('\n')
            #写磁盘
            f.flush()
            print("生成文件 ：",path)

