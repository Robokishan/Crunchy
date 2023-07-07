import pika
from scrapy.exceptions import NotConfigured
from CrunchyCrawler.agents import AGENTS
import random
from scrapy import Request
from scrapy_playwright.page import PageMethod

'''
PROXY SERVERS TBD
'''


class CrunchyHttpProxyMiddleware(object):
    def process_request(self, request, spider):
        ip = "119.8.10.18:7890"

        request.meta['playwright_context_kwargs'] = {
            "proxy": {
                "server": "https://"+ip,
            }}


class CrunchyUserAgentMiddleware(object):
    def process_request(self, request, spider):
        agent = random.choice(AGENTS)
        request.headers['User-Agent'] = agent
