"""Run crawler bound to Tracxn crawl queue only (Option B parallel: run this + go-crunchy-cb.py for parallel execution)."""
import os
os.environ["CRUNCHY_CRAWL_QUEUE"] = "tracxn"

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from CrunchyCrawler.spiders.crunchy import CrunchySpider

process = CrawlerProcess(get_project_settings())
process.crawl(CrunchySpider, name="crunchy_tracxn")
process.start()
