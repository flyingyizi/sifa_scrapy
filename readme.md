

# 一. 

## 需求

对中国主流司法拍卖网站的拍卖标的支持抓取。

## 配置

可以按照`scrapy project`项目级配置，这也是scrapy默认模板提供的方式，配置文件位于`selni/settings.py`. 

也可以按照spider级别配置，配置文件位于`seleni/cust_cfg/settings.py`。

这两个不同级别的配置项相同。 配置在spider级别的优先级高，如果在两处都有相同配置项配置，spider级配置会覆盖项目级配置。

注：  对spider级别的配置，scrapy默认提供 spider cls 属性 `custom_settings`。通过它也可以进行spider级别的配置。本例中没有使用这种方式，因为本例是希望将这个个性化配置统一维护，不是散布在各个spider class中。 下面是使用这种官方方式的例子

    ```python
    class DemoSpider(scrapy.Spider):
        name = 'demo'
        start_urls = ['http://domain']
        custom_settings = {
            'DOWNLOADER_MIDDLEWARES': {
                'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            },
            'DOWNLOAD_DELAY': 1,  
        }
        def parse(self, response):
        ...
    ```

在scrapy 标准配置项基础上，新增以下自定义配置项，所谓自定义配置，就是不是`scrapy 定义的配置`，而是本程序新增的配置项

### 自定义配置
#### 数据库配置

- `'CONN_DB_INFO'`: 数据库连接信息，如果有该配置项目， 则爬取结果会入库，入库结构见`auction_items_tbl`与`auction_items_url_tbl`；该配置项目与scrapy配置项`'FEEDS'`之间是并存关系。`'FEEDS'`是对爬取结果生成文件,导出文件的结构见`items.py`中对数据结构定义

#### selenium配置

如果需要使用`selenium webdriver`引擎来爬取网页，则需要设置以下的配置。否则就采用原始的`GET html source `爬取网页。

- `'SELENIUM_DRIVER_xx'`：使用selenium需要的信息，包括：

    - `'SELENIUM_DRIVER_NAME': 'firefox', ` , 必须
    - `'SELENIUM_DRIVER_EXECUTABLE_PATH': which('geckodriver'),`  必须
    - `'SELENIUM_DRIVER_ARGUMENTS': ['-headless'],`  可选
    - `'SELENIUM_DRIVER_PROFILES': xxx `  可选，对firefox是去填充firefox_profile, 对chrome是去填充experimental_option
    - `'SELENIUM_DRIVER_PAGE_LOADTIMEOUT'：xx` 可选，selenium web加载页面超时时间 单位秒

使用`selenium webdriver`引擎还有个前提是安装对应的驱动，这里只列出浏览器chrome/firefox的信息，它们下载路径与说明如下：

- geckodriver: 对应浏览器是firefox，[WebDriver for Firefox 下载路径](https://github.com/mozilla/geckodriver),需要将`geckodriver`放置在PATH可执行路径中. firefox 命令行参数完整列表，见[Command_Line_Options官网](https://developer.mozilla.org/en-US/docs/Mozilla/Command_Line_Options)

- chromedriver: 对应浏览器是chrome, [WebDriver for Chrome 下载路径 ](https://sites.google.com/a/chromium.org/chromedriver/downloads) . [linux chrome下载路径](https://www.ubuntuupdates.org/ppas). 下载的驱动需要与chrome的版本对应，可以通过`chrome://version/`查找chrome安装路径与chrome版本.需要将`chromedriver.exe`放置在PATH可执行路径中. chrome命令行参数见[chrome参数说明参考](https://peter.sh/experiments/chromium-command-line-switches/),与[chrome-flags-for-tools.md#--enable-automation](https://github.com/GoogleChrome/chrome-launcher/blob/master/docs/chrome-flags-for-tools.md#--enable-automation)


## 运行

对`seleni/cust_cfg/custcfg.py`配置文件进行修改，比如适配DB的信息。修改之后，可以采用下面两种方式运行爬虫

- 方式1：将`seleni/cli/start.sh`方式在任意可执行的地方，修改该文件中的`script`变量，指向`runspider.py`实际存在的位置

- 方式2：运行`python runspider.py`。可以在任意工作目录执行，例如`~/temp$python ~/work/a/ab/spider-demo/selni/cli/runspider.py`

如果使用edge browser，需要`pip3 install msedge-selenium-tools selenium==3.141`


# 二. scrapy 源码解读

运行scrapy爬虫有几种方式，命令行方式，以及脚本方式。 本次以脚本方式来解读下scrapy框架源码。 [脚本方式启动scrapy](https://docs.scrapy.org/en/latest/topics/practices.html?highlight=script%20run%20%20#run-scrapy-from-a-script)又有几种方式, 本次以下面的入口来尝试解读

```python
from scrapy.crawler import CrawlerProcess
process = CrawlerProcess(...)
process.crawl(spider_cls, *args, **kwargs)
process.start()
```

`scrapy.crawler.CrawlerProcess`类 位于`scrapy-master\scrapy\crawler.py`，定义是`class CrawlerProcess(CrawlerRunner):`,它是一个辅助类，核心其实是`CrawlerRunner`.

## 1. 启动： `process = CrawlerProcess(...)`解读

`process = CrawlerProcess(...)`生成CrawlerProcess object，主要的工作就是执行`CrawlerRunner.__init__`

```python
class CrawlerRunner:
    def __init__(self, settings=None):
        if isinstance(settings, dict) or settings is None:
            settings = Settings(settings)
        self.settings = settings
        # 'SPIDER_LOADER_CLASS'配置的'scrapy.spiderloader.SpiderLoader'，
        # 属于辅助方法，主要作用是将spider模块加载进入进程空间
        self.spider_loader = self._get_spider_loader(settings)
        # 维护crawler列表，意思就是字面的含义，每调用process.crawl（核心是CrawlerRunner.crawl）就生成一个crawler
        #对象放入_crawlers列表，对应对象的deferred放入 _active列表。
        self._crawlers = set()
        self._active = set()
        self.bootstrap_failed = False
        # 如果通过`TWISTED_REACTOR`配置项配置了指定reator实现，就加载指定的reactor实现
        # 例如在linux下指定使用"twisted.internet.pollreactor.PollReactor"
        self._handle_twisted_reactor()
```

## 2. 启动：`process.crawl`解读

`process.crawl` 执行的是`CrawlerRunner.crawl` 该方法返回该crawler对象对应的callback deferred，本次入口解读的样例代码中没有使用返回的deferred. 

```python
class CrawlerRunner:
    def crawl(self, crawler_or_spidercls, *args, **kwargs):
        """
        Run a crawler with the provided arguments.
        Returns a deferred that is fired when the crawling is finished.
        """
        ...
        # 生成`scrapy.crawler.Crawler object`对象，最核心的是执行`Crawler.__init__`
        crawler = self.create_crawler(crawler_or_spidercls)
        # 这个_crawl method是重点
        return self._crawl(crawler, *args, **kwargs)

```

### 2.1. `CrawlerRunner._crawl`解读

```python
class CrawlerRunner:
    def _crawl(self, crawler, *args, **kwargs):
        # crawlers就是CrawlerRunner._crawlers的别名
        self.crawlers.add(crawler)
        #执行`Crawler.crawl`方法，该方法是逻辑重点,它生成 `crawler：spider, engine ` 组合
        #并返回该crawler对应的deferred
        d = crawler.crawl(*args, **kwargs)
        self._active.add(d)

        def _done(result):
            self.crawlers.discard(crawler)
            self._active.discard(d)
            self.bootstrap_failed |= not getattr(crawler, 'spider', None)
            return result
        # 
        return d.addBoth(_done)
```

#### 2.1.1 `Crawler.crawl`解读

从下面的代码片段可以看到，它生成了  `crawler：spider, engine ` 组合

显然这个方法是`@defer.inlineCallbacks`修饰的，可以参考“http://krondo.com/just-another-way-to-spell-callback/”，看看这种方式书写callback

deferred的好处

```python
class Crawler:
    @defer.inlineCallbacks
    def crawl(self, *args, **kwargs):
        if self.crawling:
            raise RuntimeError("Crawling already taking place")
        self.crawling = True

        try:
            # 生成spider object
            self.spider = self._create_spider(*args, **kwargs)
            # 生成engine 对象
            self.engine = self._create_engine()
            start_requests = iter(self.spider.start_requests())
            #
            yield self.engine.open_spider(self.spider, start_requests)
            yield defer.maybeDeferred(self.engine.start)
        except Exception:
            self.crawling = False
            if self.engine is not None:
                yield self.engine.close()
            raise
```

下面是在同一个process运行多个spider的脚本示例，演示了多次

```python
runner = CrawlerRunner()
runner.crawl(MySpider1)
runner.crawl(MySpider2)
d = runner.join()
d.addBoth(lambda _: reactor.stop())
reactor.run() # the script will block here until all crawling jobs are finished
```

##### 2.1.1.1 `Crawler._create_engine()`

就是调用`ExecutionEngine.__init__`, 生成了  `engine：scheduler, downloader, scraper ` 组合

```python
class ExecutionEngine:
    def __init__(self, crawler, spider_closed_callback):
        self.crawler = crawler
        self.settings = crawler.settings
        self.signals = crawler.signals
        self.logformatter = crawler.logformatter
        self.slot = None
        self.spider = None
        self.running = False
        self.paused = False
        self.scheduler_cls = load_object(self.settings['SCHEDULER'])
        downloader_cls = load_object(self.settings['DOWNLOADER'])
        # 生成downloader（包括downloadmiddleware）
        self.downloader = downloader_cls(crawler)
        #
        self.scraper = Scraper(crawler)
        self._spider_closed_callback = spider_closed_callback
```

##### 2.1.1.2 `ExecutionEngine.open_spider` 解读


```python
class ExecutionEngine:
    @defer.inlineCallbacks
    def open_spider(self, spider, start_requests=(), close_if_idle=True):
        if not self.has_capacity():
            raise RuntimeError("No free spider slot when opening %r" % spider.name)
        logger.info("Spider opened", extra={'spider': spider})
        #生成callback nextcall，当_next_request被调用时，会去执行ExecutionEngine.crawl
        nextcall = CallLaterOnce(self._next_request, spider)
        scheduler = self.scheduler_cls.from_crawler(self.crawler)
        # 让各个middleware的process_start_requests方法对原始start_requst处理得到最终的start_requests(Request对象)
        start_requests = yield self.scraper.spidermw.process_start_requests(start_requests, spider)
        #构建slot engine
        slot = Slot(start_requests, close_if_idle, nextcall, scheduler)
        self.slot = slot
        self.spider = spider
        yield scheduler.open(spider)
        yield self.scraper.open_spider(spider)
        self.crawler.stats.open_spider(spider)
        yield self.signals.send_catch_log_deferred(signals.spider_opened, spider=spider)
        # 将callback nextcall放入reactor的执行队列中
        slot.nextcall.schedule()
        #设置heartbeat deferred每5秒执行一次
        slot.heartbeat.start(5)
```

## 3. 启动：`process.start()`

从下面可以看出，这个方法最核心的是执行`reactor.run`，从而将event loop运行起来。 而在其他的地方，是将要执行的逻辑作为callback加入到event loop逻辑中，例如engine，downloader，scraper...要执行的逻辑。

```python
class CrawlerProcess(CrawlerRunner):
    def start(self, stop_after_crawl=True):
        """
        This method starts a :mod:`~twisted.internet.reactor`, adjusts its pool
        size to :setting:`REACTOR_THREADPOOL_MAXSIZE`, and installs a DNS cache
        based on :setting:`DNSCACHE_ENABLED` and :setting:`DNSCACHE_SIZE`.

        If ``stop_after_crawl`` is True, the reactor will be stopped after all
        crawlers have finished, using :meth:`join`.

        :param boolean stop_after_crawl: stop or not the reactor when all
            crawlers have finished
        """
        from twisted.internet import reactor
        if stop_after_crawl:
            d = self.join()
            # Don't start the reactor if the deferreds are already fired
            if d.called:
                return
            d.addBoth(self._stop_reactor)
        #使用twisted内置的域名解析
        resolver_class = load_object(self.settings["DNS_RESOLVER"])
        resolver = create_instance(resolver_class, self.settings, self, reactor=reactor)
        resolver.install_on_reactor()
        tp = reactor.getThreadPool()
        tp.adjustPoolsize(maxthreads=self.settings.getint('REACTOR_THREADPOOL_MAXSIZE'))
        reactor.addSystemEventTrigger('before', 'shutdown', self.stop)
        # 启动
        reactor.run(installSignalHandlers=False)  # blocking call
```

## 4. 引擎

从前面的介绍可以看出， 在 `Crawler.crawl`中生成了engine object，这个object是 `engine：scheduler, downloader, scraper ` 组合。


然后通过 `ExecutionEngine.open_spider` 进入引擎的工作逻辑中。根据前面对`ExecutionEngine.open_spider` 分析，`ExecutionEngine._next_request`这个方法是request流转的关键函数，

在open_spider中为它构建了nextcall封装，并在reactor中加入callbacks队列。 

对`ExecutionEngine._next_request`方法，这个可以任务是engine的的核心流程了，由于代码相对较长，这里不列出，关键作用包括：

- 从scheduler取request交给`ExecutionEngine._download`, 并且安排之后执行`ExecutionEngine._handle_downloader_output`
- 通过`request = next(slot.start_requests)`获取下一个reuqest，交给`ExecutionEngine.crawl`


### 4.1.1 `ExecutionEngine._next_request`

这个函数是request在引擎中被处理的入口

#### 4.1.1.1 `ExecutionEngine.crawl` 

下面看下`ExecutionEngine.crawl` 执行：

从下面可以看出，它的主要作用就是从将获取下一个start_reuqest放入scheduler，并再次安排nextcall deferred

```python
class ExecutionEngine:
    def crawl(self, request, spider):
        if spider not in self.open_spiders:
            raise RuntimeError("Spider %r not opened when crawling: %s" % (spider.name, request))
        #将requst放入scheduler，并信号发送
        self.schedule(request, spider)
        #即ExecutionEngine._next_request defered封装再次放入callback队列
        self.slot.nextcall.schedule()

    def schedule(self, request, spider):
        #以sender是Anonymous身份，向所有receivers发送signals.request_scheduled信号
        self.signals.send_catch_log(signals.request_scheduled, request=request, spider=spider)
        #将request放入scheduler
        if not self.slot.scheduler.enqueue_request(request):
            self.signals.send_catch_log(signals.request_dropped, request=request, spider=spider)
```

#### 4.1.1.2`ExecutionEngine._download`

它的核心逻辑就是执行`self.downloader.fetch(request, spider)`，以及按照当下载完毕之后再次调用`slot.nextcall.schedule()`使得ExecutionEngine._next_request defered封装再次放入reactor callback队列

engine 成员downloader，如前面`Crawler._create_engine()`解读中介绍的，是通过DOWNLOADER 配置项（'scrapy.core.downloader.Downloader'）生成。对它的解释见下一部分

#### 4.1.1.3 `ExecutionEngine._handle_downloader_output`

它是安排在`__download`后面执行的，它其中会执行`self.scraper.enqueue_scrape(response, request, spider)`, enqueue_scrape将会执行 spider request的`'callback'`，以及piple item的`'process_item'`.所以也可以称它是scraper模块的入口

```python
    def _handle_downloader_output(self, response, request, spider):
        if not isinstance(response, (Request, Response, Failure)):
            raise TypeError(
                "Incorrect type: expected Request, Response or Failure, got %s: %r"
                % (type(response), response)
            )
        # downloader middleware can return requests (for example, redirects)
        if isinstance(response, Request):
            self.crawl(response, spider)
            return
        # response is a Response or Failure
        d = self.scraper.enqueue_scrape(response, request, spider)
        d.addErrback(lambda f: logger.error('Error while enqueuing downloader output',
                                            exc_info=failure_to_exc_info(f),
                                            extra={'spider': spider}))
        return d
```

## 5. downloader

Downloader类实现文件见`scrapy-master\scrapy\core\downloader\__init__.py`

#### 5.1 对象生成

在前面`Crawler._create_engine()`中我们提到了它生成了生成了  `engine：scheduler, downloader, scraper ` 组合。这里就看下downloader的生成

```python
class Downloader:
    def __init__(self, crawler):
        self.settings = crawler.settings
        self.signals = crawler.signals
        self.slots = {}
        self.active = set()
        #加载不同协议对应的下载处理器
        self.handlers = DownloadHandlers(crawler)
        self.total_concurrency = self.settings.getint('CONCURRENT_REQUESTS')
        self.domain_concurrency = self.settings.getint('CONCURRENT_REQUESTS_PER_DOMAIN')
        self.ip_concurrency = self.settings.getint('CONCURRENT_REQUESTS_PER_IP')
        self.randomize_delay = self.settings.getbool('RANDOMIZE_DOWNLOAD_DELAY')
        # 根据'DOWNLOADER_MIDDLEWARES'，'DOWNLOADER_MIDDLEWARES_BASE'配置，将所有相关dlmw 模块生成
        self.middleware = DownloaderMiddlewareManager.from_crawler(crawler)
        self._slot_gc_loop = task.LoopingCall(self._slot_gc)
        self._slot_gc_loop.start(60)
```

下面是默认配置,来自`scrapy-master\scrapy\settings\default_settings.py`



```python
DOWNLOADER_MIDDLEWARES = {}

DOWNLOADER_MIDDLEWARES_BASE = {
    # Engine side
    'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': 100,
    'scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware': 300,
    'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 350,
    'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': 400,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 500,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
    'scrapy.downloadermiddlewares.ajaxcrawl.AjaxCrawlMiddleware': 560,
    'scrapy.downloadermiddlewares.redirect.MetaRefreshMiddleware': 580,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 590,
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 600,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750,
    'scrapy.downloadermiddlewares.stats.DownloaderStats': 850,
    'scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware': 900,
    # Downloader side
}
```

这里注意，以`DOWNLOADER_MIDDLEWARES`,`DOWNLOADER_MIDDLEWARES_BASE`为例, 是“scrapy.settings” 提供的`getwithbase   '''Get a composition of a dictionary-like setting and its _BASE'''`方法写死了,

在代码中直接搜索`DOWNLOADER_MIDDLEWARES_BASE`关键字看是在哪里加载是搜不到的

#### 5.2 下载

下载的入口就是`Downloader.fetch`， 下面的是对它的说明

```python
class Downloader:
    def fetch(self, request, spider):
        def _deactivate(response):
            self.active.remove(request)
            return response

        self.active.add(request)
        # 执行下载，细节见下一小节的说明
        dfd = self.middleware.download(self._enqueue_request, request, spider)
        return dfd.addBoth(_deactivate)
```
对前面`dfd = self.middleware.download(self._enqueue_request, request, spider)`语句的说明。

显然从中可以看出类似我们自己实现了SeleniumMiddleware 下载中间件，并且返回了response的场景，是不会使用系统默认下载handle进行下载的。

```python
class Downloader:
    def download(self, download_func, request, spider):
        @defer.inlineCallbacks
        def process_request(request):
            for method in self.methods['process_request']:
                response = yield deferred_from_coro(method(request=request, spider=spider))
                if response is not None and not isinstance(response, (Response, Request)):
                    raise _InvalidOutput(
                        "Middleware %s.process_request must return None, Response or Request, got %s"
                        % (method.__self__.__class__.__name__, response.__class__.__name__)
                    )
                #这意味着只要其中一个dlmw的process_request返回了响应（非None），就不会执行后续的
                if response:
                    return response
            #只要任意一个dlmw的process_request返回了响应（非None），就不会执行了，
            # download_func是Downloader._enqueue_request,它使用系统的各协议下载器（见Downloader.handlers）进行下载
            return (yield download_func(request=request, spider=spider))

        @defer.inlineCallbacks
        def process_response(response):
            ....
        ....

        deferred = mustbe_deferred(process_request, request)
        deferred.addErrback(process_exception)
        deferred.addCallback(process_response)
        return deferred
```

## 6. scraper

scraper模块是处理download结果， 包括pipline  process_item与spider Request响应的callback都是在这个模块中被执行。

#### 6.1 对象生成

在前面`Crawler._create_engine()`中我们提到了它生成了生成了  `engine：scheduler, downloader, scraper ` 组合。这里就看下scraper的生成

scrapy-master\scrapy\core\scraper.py

```python
class Scraper:
    def __init__(self, crawler):
        self.slot = None
        self.spidermw = SpiderMiddlewareManager.from_crawler(crawler)
        itemproc_cls = load_object(crawler.settings['ITEM_PROCESSOR'])
        self.itemproc = itemproc_cls.from_crawler(crawler)
        self.concurrent_items = crawler.settings.getint('CONCURRENT_ITEMS')
        self.crawler = crawler
        self.signals = crawler.signals
        self.logformatter = crawler.logformatter
```

#### 6.2 处理入口与逻辑

在前面解读`ExecutionEngine._handle_downloader_output`时已经提到，该方法是scraper模块中api被调用的入口，从而使得spider request的`'callback'`，以及piple item的`'process_item'`得到执行

