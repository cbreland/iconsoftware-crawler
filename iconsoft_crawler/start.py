

import scrapy
from scrapy.utils.log import configure_logging
from twisted.internet import reactor, defer
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerRunner
from spiders.icon_crawl import IconSoftwareCrawl
import pendulum
date_format = 'MM-DD-YYYY'

SETTINGS = {
    "SPIDER_MIDDLEWARES": {'scrapy_splash.SplashDeduplicateArgsMiddleware': 100},
    "DOWNLOADER_MIDDLEWARES": {
        'scrapy_splash.SplashCookiesMiddleware': 723,
        'scrapy_splash.SplashMiddleware': 725,
        'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
    },
    "SPLASH_URL": 'http://0.0.0.0:8050',
    "ITEM_PIPELINES": {'pipelines.IconsoftCrawlerPipeline': 300}

}


class IconSoftwareRunner():
    """Class allows for inline callbacks without the need for a 
    reactor restart.

    Yields:
        runner.crawl(): New crawler Instance
    """

    def __init__(self, url,
                 username, password,
                 start_date, end_date,
                 filename, verbose):

        self.url = url
        self.username = username
        self.password = password
        self.filename = filename
        self.start_date = start_date
        self.end_date = end_date

        if end_date == None or start_date == None:
            end_date = pendulum.now()
            start_year = end_date.subtract(years=1)
            self.start_date = start_year.format(date_format)
            self.end_date = end_date.format(date_format)

        self.verbose = verbose

        self.initialize()

    @defer.inlineCallbacks
    def start(self):
        """Starts crawler settings to work with SPLASH middleware.

        ** Crawling multiple sites will only work if usernames and 
        passwords are the same for each site. If they are different, 
        each site will need to be crawled individually.

        Yields:
            CrawlRunner Object: Instance of a CrawlRunner Class in 
            a loop that enables multiple site to be crawled without
            needing to restart the reactor.
        """

        configure_logging()
        runner = CrawlerRunner(SETTINGS)

        for u in self.url:

            if self.verbose:
                print(f"CRAWLING >>> {self.url}")

            yield runner.crawl(IconSoftwareCrawl, url=u,
                               reactor=reactor,
                               username=self.username,
                               password=self.password,
                               start_date=self.start_date,
                               end_date=self.end_date,
                               verbose=self.verbose,
                               filename=self.filename)

        reactor.stop()

        if self.verbose:
            print('REACTOR HAS STOPPED ..........')

    def initialize(self):

        if self.verbose:
            print("STARTING REACTOR ..........")
        self.start()
        reactor.run()
