"""启动爬虫入口"""
# pylint: disable=no-value-for-parameter
import sys
import os
from pathlib import Path
import click
# import platform

sys.path.append(str(Path(__file__).parent.parent))
#pylint: disable=wrong-import-position
# print(sys.path)
from cust_cfg.custcfg import cfg


def _get_spider_cls(spider, settings):
    """
    通过spider name查找对应spider cls,通过返回project settings
    """
    # SPIDER_MODULES setting in settings.py
    from scrapy.utils.misc import walk_modules
    import inspect
    import scrapy
    import traceback
    import warnings

    tem = None
    # SPIDER_MODULES setting in settings.py
    for name in settings['SPIDER_MODULES']:
        try:
            all_modules = walk_modules(name)
            for module in all_modules:
                for obj in vars(module).values():
                    if (inspect.isclass(obj) and
                            issubclass(obj, scrapy.spiders.Spider) and
                            obj.__module__ == module.__name__  and
                            getattr(obj, 'name', None) == spider):
                        tem = obj
                        return tem
        except ImportError:
            msg = ("\n{tb}Could not load spiders from module '{modname}'. "
                   "See above traceback for details.".format(
                       modname=name, tb=traceback.format_exc()))
            warnings.warn(msg, RuntimeWarning)
    return tem

def run_spider(spider, *args, **kwargs):
    """
    :param spider:    run the spider
    :param list args: arguments to initialize the spider

    :param dict kwargs: keyword arguments to initialize the spider
            1.  if include custom 'conn_db_info' string, it means the spider connect to db.
                it shoud be a dict, and format is {'host':'x.x.x.x', 'user':'xx',
                                                   'passwd':'xxx', 'db':'xx',
                                                   'charset':'utf8'}
            2.  if include custom 'grab_action', it should be 'list' or 'result' or 'list_result'.

                动作'list'，与'list_result'动作入口（starturl）是适用类似"京东拍卖-司法拍卖网"，
                带条件或不带条件，例如"https://auction.jd.com/sifa_list.html"

                动作'result'动作入口（starturl）是适用标的详情页，例如'https://paimai.jd.com/115386844'
    """
    from scrapy.utils.project import get_project_settings

    #使用了scrapy的get_project_settings，它依赖'scrapy.cfg'对当前目录有要求，因此临时切换下
    #backup
    backup_cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))   # to current file's dir
    project_settings = get_project_settings()
    #recover
    os.chdir(backup_cwd)

    #######
    loader_cls = _get_spider_cls(spider, project_settings)
    #######

    #1
    from_cfg = cfg[spider]    #配置是按照spider name分开配置
    scrapy_crawl = from_cfg['scrapy_crawl']
    # add and override custom settings to project settings
    project_settings.update(scrapy_crawl)
    project_settings.update(kwargs)

    from scrapy.crawler import CrawlerProcess

    process = CrawlerProcess(project_settings)
    # add and override cmd line input settings to project settings
    final = project_settings
    # final.update(kwargs)

    process.crawl(loader_cls, *args, **final)  #**kwargs)
    process.start()




@click.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.option('-name', '--spider', required=True,
              type=click.Choice(['rmfysszc', 'jdsifa', 'gpai', 'sfcaa123', 'tbsifa']),
              help='run which spider')
@click.option('-c', '--action', 'cmd', required=True,
              type=click.Choice(['list', 'result'], case_sensitive=False),
              help='list: to grab auction item urls; result: to grab auction items')
@click.option('-s', '--set', 'settings', multiple=True, type=(str, str),
              help='<k v> settings for spider/crawl,you can do mutil set. for example, '
              '"-s k1 v1 -s k2 v2" ')
@click.argument('urls', nargs=-1, type=click.UNPROCESSED)
def cli(spider, cmd, settings, urls):
    """cmd line wrapper"""
    # click.echo(cmd.lower())
    # click.echo(settings)
    # click.echo(spider)
    kwargs = dict(settings)

    urls_from_cmd = list()
    for item in urls:
        urls_from_cmd.extend(item.split(','))

    run_spider(spider, grab_action=cmd.lower(), start_urls=urls_from_cmd, **kwargs)


if __name__ == '__main__':
    cli()
