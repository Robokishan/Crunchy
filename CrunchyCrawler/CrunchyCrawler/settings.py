# Scrapy settings for CrunchyCrawler project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import os
from decouple import config as DefaultConfig
from decouple import Config, RepositoryEnv

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

# playwright
SPIDER_MIDDLEWARES = { 
    'CrunchyCrawler.middlewares.RabbitMQSpiderMiddleware' : 100 
}


DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

DOWNLOADER_MIDDLEWARES = {
    'CrunchyCrawler.middlewares.CrunchyUserAgentMiddleware': 545,
    'CrunchyCrawler.middlewares.RabbitMQMiddleware': 546,
}

SCHEDULER = "CrunchyCrawler.rabbitmq.scheduler.Scheduler"

LOG_LEVEL = "INFO"
# LOG_LEVEL = "ERROR"


# KAFKA SETTINGS
KAFKA_USERNAME = config('KAFKA_USERNAME', cast=str)
KAFKA_PASSWORD = config('KAFKA_PASSWORD', cast=str)
KAFKA_SERVER = config('KAFKA_SERVER', cast=str)
KAFKA_SASL_MECHANISM = config('KAFKA_SASL_MECHANISM', cast=str)
KAFKA_GROUP_ID = config('KAFKA_GROUP_ID', cast=str)
KAFKA_CRUNCHBASE_DATABUCKET_TOPIC = config(
    'KAFKA_CRUNCHBASE_DATABUCKET_TOPIC', cast=str)


# rabbitMQ
RABBITMQ_URL = config('RABBITMQ_URL', cast=str)
RB_MAIN_EXCHANGE = config('RABBIT_MQ_MAIN_EXCHANGE', cast=str)
RB_MAIN_ROUTING_KEY = config('RABBIT_MQ_MAIN_ROUTING_KEY', cast=str)
RB_MAIN_QUEUE = config('RABBIT_MQ_MAIN_QUEUE', cast=str)

LOG_ENABLED = True

PLAYWRIGHT_BROWSER_TYPE = "firefox"

PLAYWRIGHT_PROCESS_REQUEST_HEADERS = None

PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "timeout": 50 * 1000,  # 20 seconds
}

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "CrunchyCrawler (+http://www.yourdomain.com)"

# Obey robots.txt rules
# ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

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
    "CrunchyCrawler.pipelines.KafkaPipeline": 301,
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
