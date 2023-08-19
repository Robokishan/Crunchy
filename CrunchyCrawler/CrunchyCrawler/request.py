from scrapy.utils.reqser import request_to_dict, request_from_dict
import pickle
from scrapy import Request
from scrapy_playwright.page import PageMethod
# from scrapy.spidermiddlewares.httperror import HttpError
from scrapy_selenium import SeleniumRequest

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',  # this is game changing header
}


def generateRequest(url, delivery_tag, callback=None, previousResult={}):
    return SeleniumRequest(url=url, callback=callback, headers=headers, meta={
        "previousResult": previousResult,
        "delivery_tag": delivery_tag,
    })
    # return Request(url,
    #                headers=headers,
    #                callback=callback,
    #                meta={
    #                    "previousResult" : previousResult,
    #                    "delivery_tag": delivery_tag,
    #                    "playwright": True,
    #                    "playwright_page_methods": [
    #                        PageMethod(
    #                            "wait_for_load_state", "networkidle")
    #                    ],
    #                })
