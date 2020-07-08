"""爬虫级别进行配置项配置，如果有相同配置，它会覆盖项目级配置"""
# -*- coding: utf-8 -*-


from shutil import which
from pathlib import Path
import os
# import random
#
output_path = Path(os.getcwd())

USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0',
    ('user-agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64) '
     'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.30 Safari/537.36 Edg/84.0.522.11'),
    ("Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) "
     "Chrome/22.0.1207.1 Safari/537.1"),
    ("Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) "
     "Chrome/20.0.1132.57 Safari/536.11"),
    ("Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) "
     "Chrome/20.0.1092.0 Safari/536.6"),
    ("Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) "
     "Chrome/20.0.1090.0 Safari/536.6"),
    ("Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) "
     "Chrome/19.77.34.5 Safari/537.1"),
    ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) "
     "Chrome/19.0.1084.9 Safari/536.5"),
    ("Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) "
     "Chrome/19.0.1084.36 Safari/536.5"),
    ("Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) "
     "Chrome/19.0.1063.0 Safari/536.3"),
    ("Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) "
     "Chrome/19.0.1063.0 Safari/536.3"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) "
     "Chrome/19.0.1063.0 Safari/536.3"),
    ("Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) "
     "Chrome/19.0.1062.0 Safari/536.3"),
    ("Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) "
     "Chrome/19.0.1062.0 Safari/536.3"),
    ("Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) "
     "Chrome/19.0.1061.1 Safari/536.3"),
    ("Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) "
     "Chrome/19.0.1061.1 Safari/536.3"),
    ("Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) "
     "Chrome/19.0.1061.1 Safari/536.3"),
    ("Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) "
     "Chrome/19.0.1061.0 Safari/536.3"),
    ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) "
     "Chrome/19.0.1055.1 Safari/535.24"),
    ("Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) "
     "Chrome/19.0.1055.1 Safari/535.24")
]


chrome_experimental_option = {
    # "prefs":  {"profile.managed_default_content_settings.images": 2},
    ## 通过这个实验方法掩盖chrome提示运行在selenium模式下
    'excludeSwitches': ['enable-automation'],
}


firefox_profiles = {
    # ref：google how-to-make-selenium-load-faster-with-firefox-in-python-ck7ncjyvw00sd8ss1v4i5xob1
    #所有选项见firefox输入`about:config`查看列表
    "network.http.pipelining": True,
    "network.http.proxy.pipelining": True,
    "network.http.pipelining.maxrequests": 8,
    "content.notify.interval": 500000,
    "content.notify.ontimer": True,
    "content.switch.threshold": 250000,
    "browser.cache.memory.capacity": 65536, # Increase the cache capacity.
    "browser.startup.homepage": "about:blank",
    "reader.parse-on-load.enabled": False, # Disable reader, we won't need that.
    "browser.pocket.enabled": False, # Duck pocket too!
    "loop.enabled": False,
    "browser.chrome.toolbar_style": 1, # Text on Toolbar instead of icons
    "browser.display.show_image_placeholders": False, # Don't show thumbnails on not loaded images.
    "browser.display.use_document_colors": False, # Don't show document colors.
    "browser.display.use_document_fonts": 0, # Don't load document fonts.
    "browser.display.use_system_colors": True, # Use system colors.
    "browser.formfill.enable": False, # Autofill on forms disabled.
    "browser.helperApps.deleteTempFileOnExit": True, # Delete temprorary files.
    "browser.shell.checkDefaultBrowser": False,
    "browser.startup.page": 0, # blank
    "browser.tabs.forceHide": True, # Disable tabs, We won't need that.
    "browser.urlbar.autoFill": False, # Disable autofill on URL bar.
    "browser.urlbar.autocomplete.enabled": False, # Disable autocomplete on URL bar.
    "browser.urlbar.showPopup": False, # Disable list of URLs when typing on URL bar.
    "browser.urlbar.showSearch": False, # Disable search bar.
    "extensions.checkCompatibility": False, # Addon update disabled
    "extensions.checkUpdateSecurity": False,
    "extensions.update.autoUpdateEnabled": False,
    "extensions.update.enabled": False,
    "general.startup.browser": False,
    "plugin.default_plugin_disabled": False,
    "permissions.default.image": 2, # Image load disabled again

        # 'javascript.enabled' : False,  #禁用js
        # 'dom.ipc.plugins.enabled.libflashplayer.so' : False, #禁用flash
}

cfg = {
    # 公拍网爬虫
    'gpai': {
        'additional': {
        },
        'scrapy_crawl': {
            #数据库
            # 'CONN_DB_INFO' : {'DBTYPE':'redis',
            #                   'CONN': {'host':'192.168.1.8',
            #                            'passwd':'123456', 'port':6379},},
            'CONN_DB_INFO' : {'DBTYPE':'mysql',
                              'CONN': {'host':'192.168.1.8', 'user':'yyyyuser',
                                       'passwd':'xxxx', 'db':'yyyy', 'charset':'utf8'},},
            # 可配置参数： 所有可配置的scrapy crawl系统参数
            'FEEDS': {output_path.joinpath("gpai.json").absolute().as_uri() :
                      {"format": "json", 'encoding': 'utf8'}, },
            'LOG_LEVEL': 'INFO',
            'LOG_FILE': 'gai_logs.log',
            # 使用selenium firefox
            'SELENIUM_DRIVER_NAME': 'firefox',
            'SELENIUM_DRIVER_EXECUTABLE_PATH': which('geckodriver'),
            #firefox ref https://developer.mozilla.org/en-US/docs/Mozilla/Command_Line_Options
            'SELENIUM_DRIVER_ARGUMENTS': ['-headless'],
            'SELENIUM_DRIVER_PROFILES' : firefox_profiles,

            # # 使用selenium chrome
            # 'SELENIUM_DRIVER_NAME': 'chrome',
            # 'SELENIUM_DRIVER_EXECUTABLE_PATH': which('chromedriver'),
            # 'SELENIUM_DRIVER_ARGUMENTS': ['--headless', 'blink-settings=imagesEnabled=false',
            #chrome headless的UA会很特别，所以需要  掩盖下
            # 'user-agent=' + random.choice(spider.settings['USER_AGENT_LIST']],
            # 'SELENIUM_DRIVER_PROFILES' : chrome_experimental_option,

            # # 使用selenium edge  chromium
            # 'SELENIUM_DRIVER_NAME': 'edge',
            # 'SELENIUM_DRIVER_EXECUTABLE_PATH': which('msedgedriver'),
            # 'SELENIUM_DRIVER_ARGUMENTS': ['headless',],
            'DOWNLOADER_MIDDLEWARES': {'seleni.spiders.myselenium.SeleniumMiddleware': 800, },
        },
    },
    # 京东网爬虫
    'jdsifa': {
        'additional': {

        },
        'scrapy_crawl': {
            #数据库
            'CONN_DB_INFO' : {'DBTYPE':'mysql',
                              'CONN': {'host':'192.168.1.8', 'user':'yyyyuser',
                                       'passwd':'xxxx', 'db':'yyyy', 'charset':'utf8'},},
            'FEEDS': {output_path.joinpath("jd.json").absolute().as_uri() :
                      {"format": "json", 'encoding': 'utf8'}, },
            'LOG_LEVEL': 'INFO',
            'LOG_FILE': 'jd_logs.log',
            # 使用selenium
            'SELENIUM_DRIVER_NAME': 'firefox',
            'SELENIUM_DRIVER_EXECUTABLE_PATH': which('geckodriver'),
            'SELENIUM_DRIVER_ARGUMENTS': ['-headless'],
            'SELENIUM_DRIVER_PROFILES' : firefox_profiles,
            'DOWNLOADER_MIDDLEWARES': {'seleni.spiders.myselenium.SeleniumMiddleware': 800, },
            # # 后处理,
            # 'ITEM_PIPELINES':{'seleni.pipelines.PaimaiPipeline': 300,},
        },
    },
    # 人民法院司法资产网
    'rmfysszc': {
        'additional': {
        },
        'scrapy_crawl': {
            'CONN_DB_INFO' : {'DBTYPE':'mysql',
                              'CONN': {'host':'192.168.1.8', 'user':'yyyyuser',
                                       'passwd':'xxxx', 'db':'yyyy', 'charset':'utf8'},},

            'FEEDS': {output_path.joinpath("rmsfsszzc.json").absolute().as_uri() :
                      {"format": "json", 'encoding': 'utf8'}, },
            'LOG_LEVEL': 'INFO',
            'LOG_FILE': 'rmsfsszzc_logs.log',
            # 使用selenium firefox
            'SELENIUM_DRIVER_NAME': 'firefox',
            'SELENIUM_DRIVER_EXECUTABLE_PATH': which('geckodriver'),
            'SELENIUM_DRIVER_ARGUMENTS': ['-headless'],
            'SELENIUM_DRIVER_PROFILES' : firefox_profiles,

            # # 使用selenium chrome
            # 'SELENIUM_DRIVER_NAME': 'chrome',
            # 'SELENIUM_DRIVER_EXECUTABLE_PATH': which('chromedriver'),
            # 'SELENIUM_DRIVER_ARGUMENTS': ['--headless', '–incognito',
            #                               ('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            #                                'AppleWebKit/537.36 (KHTML, like Gecko) '
            #                                'Chrome/83.0.4103.106 Safari/537.36'),],
            # 'SELENIUM_DRIVER_PROFILES' : chrome_experimental_option,

            'DOWNLOADER_MIDDLEWARES': {'seleni.spiders.myselenium.SeleniumMiddleware': 800, },
        },
    },
    # 'blink-settings=imagesEnabled=false',
    # 拍卖行业协会网 司法拍卖
    'sfcaa123': {
        'additional': {
        },
        'scrapy_crawl': {
            'CONN_DB_INFO' : {'DBTYPE':'mysql',
                              'CONN': {'host':'192.168.1.8', 'user':'yyyyuser',
                                       'passwd':'xxxx', 'db':'yyyy', 'charset':'utf8'},},
            'FEEDS': {"sfcaa123.json": {"format": "json", 'encoding': 'utf8'}, },
            'LOG_LEVEL': 'INFO',
            'LOG_FILE': 'sfcaa123_logs.log',
            # 使用selenium
            'SELENIUM_DRIVER_NAME': 'firefox',
            'SELENIUM_DRIVER_EXECUTABLE_PATH': which('geckodriver'),
            'SELENIUM_DRIVER_ARGUMENTS': ['-headless'],
            'DOWNLOADER_MIDDLEWARES': {'seleni.spiders.myselenium.SeleniumMiddleware': 800, },
        },
    },

    # 淘宝网 司法拍卖
    'tbsifa': {
        'additional': {
        },
        'scrapy_crawl': {
            'CONN_DB_INFO' : {'DBTYPE':'mysql',
                              'CONN': {'host':'192.168.1.8', 'user':'yyyyuser',
                                       'passwd':'xxxx', 'db':'yyyy', 'charset':'utf8'},},
            'FEEDS': {"tbsifa.json": {"format": "json", 'encoding': 'utf8'}, },
            'LOG_LEVEL': 'INFO',
            'LOG_FILE': 'tbsifa_logs.log',
            # # 使用selenium
            # 'SELENIUM_DRIVER_NAME': 'firefox',
            # 'SELENIUM_DRIVER_EXECUTABLE_PATH': which('geckodriver'),
            # 'SELENIUM_DRIVER_ARGUMENTS': ['-headless'],
            'DOWNLOADER_MIDDLEWARES': {'seleni.spiders.myselenium.SeleniumMiddleware': 800, },
            # 使用selenium chrome
            'SELENIUM_DRIVER_NAME': 'chrome',
            'SELENIUM_DRIVER_EXECUTABLE_PATH': which('chromedriver'),
            'SELENIUM_DRIVER_ARGUMENTS': ['--headless', '–incognito',
                                          ('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                                           'Chrome/83.0.4103.106 Safari/537.36'),],
            'SELENIUM_DRIVER_PROFILES' : chrome_experimental_option,

        },
    },

    # cchere爬虫
    'cchere': {
        'additional': {
        },
        'scrapy_crawl': {
            # 可配置参数： 所有可配置的scrapy crawl系统参数
            'FEEDS': {output_path.joinpath("cchere.json").absolute().as_uri():
                      {"format": "json", 'encoding': 'utf8'}, },
            'LOG_LEVEL': 'INFO',
            'LOG_FILE': 'cchere_logs.log',
        },
    },
}
