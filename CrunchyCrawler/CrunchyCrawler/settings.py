# Scrapy settings for CrunchyCrawler project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import sys
import json
import inspect
import os
from decouple import config as DefaultConfig
from decouple import Config, RepositoryEnv
from loguru import logger
import logging


# Configure Loguru


DEV_ENV_FILE = "../.env.dev"
PROD_ENV_FILE = "../.env.prod"

# default env file
DOTENV_FILE = os.environ.get("DOTENV_FILE", DEV_ENV_FILE)

config: Config = DefaultConfig

ENVIORNMENT = os.environ.get('PYTHON_ENV', "dev")

if ENVIORNMENT == "dev":
    config = Config(RepositoryEnv(DEV_ENV_FILE))

BOT_NAME = "CrunchyCrawler"

SPIDER_MODULES = ["CrunchyCrawler.spiders"]
NEWSPIDER_MODULE = "CrunchyCrawler.spiders"

'''
Not sure why but i have put 1000 to put custom middleware at bottom
of all scrapy default middleware
because of same process_exception running multiple times
'''
# playwright
SPIDER_MIDDLEWARES = {
    'CrunchyCrawler.middlewares.RabbitMQSpiderMiddleware': 1000,
    'CrunchyCrawler.middlewares.TestSpiderMiddleware1': 1002,
}


# Use stealth-enabled Playwright handler to reduce Cloudflare detection
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright_stealth.handler.ScrapyPlaywrightStealthDownloadHandler",
    "https": "scrapy_playwright_stealth.handler.ScrapyPlaywrightStealthDownloadHandler",
}

# Enable stealth mode for Playwright
PLAYWRIGHT_USE_STEALTH = True

DOWNLOADER_MIDDLEWARES = {
    'CrunchyCrawler.middlewares.CrunchyUserAgentMiddleware': 545,
    'CrunchyCrawler.middlewares.RabbitMQMiddleware': 546,
}

SCHEDULER = "CrunchyCrawler.rabbitmq.scheduler.Scheduler"

LOG_LEVEL = "INFO"
# LOG_LEVEL = "ERROR"


# rabbitMQ (crawl queues + databucket queues)
RABBITMQ_URL = config('RABBITMQ_URL', cast=str)
RB_MAIN_EXCHANGE = config('RABBIT_MQ_MAIN_EXCHANGE', cast=str)
RB_MAIN_ROUTING_KEY = config('RABBIT_MQ_MAIN_ROUTING_KEY', cast=str)
RB_MAIN_QUEUE = config('RABBIT_MQ_MAIN_QUEUE', cast=str)

RABBIT_MQ_PRIORITY_EXCHANGE = config('RABBIT_MQ_PRIORITY_EXCHANGE', cast=str)
RABBIT_MQ_PRIORITY_ROUTING_KEY = config(
    'RABBIT_MQ_PRIORITY_ROUTING_KEY', cast=str)
RABBIT_MQ_PRIORITY_QUEUE = config('RABBIT_MQ_PRIORITY_QUEUE', cast=str)

# Databucket exchange: scraped items (Crunchbase/Tracxn) go to these queues for Django consumers
RB_DATABUCKET_EXCHANGE = config('RB_DATABUCKET_EXCHANGE', cast=str, default='databucket_exchange')
RB_DATABUCKET_CRUNCHBASE_RK = config('RB_DATABUCKET_CRUNCHBASE_RK', cast=str, default='crunchbase_databucket')
RB_DATABUCKET_TRACXN_RK = config('RB_DATABUCKET_TRACXN_RK', cast=str, default='tracxn_databucket')

# FlareSolverr settings for Cloudflare bypass (free, open-source)
FLARESOLVERR_URL = config('FLARESOLVERR_URL', cast=str, default='http://localhost:8191/v1')
CLOUDFLARE_SOLVE_TIMEOUT = 60000  # milliseconds to wait for FlareSolverr solution

# Dump raw scraped HTML + parsed item to <company_name>.json for testing extractors (test_crunchy_extractor.py, test_tracxy_extractor.py)
DUMP_RAW_SCRAPED_DATA = config('DUMP_RAW_SCRAPED_DATA', default=False, cast=bool)
DUMP_RAW_SCRAPED_DIR = config('DUMP_RAW_SCRAPED_DIR', default='./raw_scraped_dumps')

LOG_ENABLED = False

PLAYWRIGHT_BROWSER_TYPE = "firefox"

# PLAYWRIGHT_PROCESS_REQUEST_HEADERS = None

PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": False,
    "timeout": 50 * 1000,  # 20 seconds
}

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "CrunchyCrawler (+http://www.yourdomain.com)"

# Obey robots.txt rules
# ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 2

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 5  # 2 seconds of delay
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    'Referer': 'http://crunchbase.com/companies'
    #    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    #    "Accept-Language": "en",
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "CrunchyCrawler.middlewares.CrunchycrawlerSpiderMiddleware": 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    "CrunchyCrawler.middlewares.CrunchycrawlerDownloaderMiddleware": 543,
# }

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "CrunchyCrawler.pipelines.RabbitMQPipeline": 300,
    "CrunchyCrawler.pipelines.DatabucketPipeline": 301,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage())


# Configure Loguru to handle all logs
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


def flatten_loguru_log(message):
    # https://github.com/Delgan/loguru/issues/1006
    message_json = json.loads(message)
    message_json = json.loads(message)
    message_json = message_json["record"]
    message_json["level"] = message_json["level"]["name"]
    message_json['timestamp'] = message_json['time']['repr']
    message_json["time"] = message_json["time"]["timestamp"]
    serialized = json.dumps(message_json, default=str, ensure_ascii=False)
    sys.stderr.write(serialized + "\n")


if ENVIORNMENT == "prod":
    logger.remove(0)
    logger.add(
        flatten_loguru_log,  # Custom sink function
        format="{time} | {level} | {message}| ",
        serialize=True
    )
