from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from CrunchyCrawler.spiders.crunchy import CrunchySpider


process = CrawlerProcess(get_project_settings())
process.crawl(CrunchySpider)
process.start()
