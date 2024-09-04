from scrapy.utils.reqser import request_to_dict, request_from_dict
import pickle
from scrapy import Request
from scrapy_playwright.page import PageMethod
from scrapy.spidermiddlewares.httperror import HttpError


headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',  # this is game changing header
}

def generateRequest(url, delivery_tag, queue="normal", callback = None, previousResult = {}):
        return Request(url,
                       headers=headers,
                       callback=callback,
                       meta={
                           "queue": queue,
                           "previousResult" : previousResult,
                           "delivery_tag": delivery_tag,
                           "playwright": True,
                           "playwright_page_methods": [
                               PageMethod(
                                   "wait_for_load_state", "networkidle")
                           ],
                       })