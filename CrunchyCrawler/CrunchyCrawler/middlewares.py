from CrunchyCrawler.rabbitmq.connection import from_settings
from CrunchyCrawler.agents import AGENTS
import random
from scrapy.exceptions import IgnoreRequest
from importlib import import_module

from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium import webdriver

import undetected_chromedriver as uc
from .http import SeleniumRequest

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
        print(f"Selected agent: {agent}")

class RabbitMQMiddleware(object):
    def __init__(self, channel):
        self.channel = channel

    @classmethod
    def from_crawler(cls, crawler):
        channel = from_settings()
        return cls(channel)
    
    # only send ack or nack incase of final result
    def process_response(self, request, response, spider):
        print("process_response" , request.meta, response, response.status)
        if response.status != 200:
            delivery_tag = request.meta.get('delivery_tag')
            print(f"Fail Response: {delivery_tag}", request.meta, response)
            self.nack(delivery_tag)
            raise IgnoreRequest
        else:
            print("Success Response:" , request.meta, response, response.status)
            return response

    def process_exception(self, request, exception, spider):
        delivery_tag = request.meta.get('delivery_tag')
        print(f"process_exception: {delivery_tag}", request.meta, exception)
        self.nack(delivery_tag)
        return None

    def nack(self, delivery_tag):
        print("RQ:DownloadMiddleware:Sending nack for", delivery_tag)
        self.channel.basic_nack(delivery_tag=delivery_tag, requeue=True)

class RabbitMQSpiderMiddleware:
    def __init__(self, channel):
        self.channel = channel

    @classmethod
    def from_crawler(cls, crawler):
        channel = from_settings()
        return cls(channel)
    
    def nack(self, delivery_tag):
        print("RQSpider Middleware:Sending nack for", delivery_tag)
        self.channel.basic_nack(delivery_tag=delivery_tag, requeue=True)

    def process_spider_exception(self, response, exception, spider):
        delivery_tag = response.meta.get('delivery_tag', None)
        print(f"process_spider_exception {delivery_tag}", response.meta, exception, spider)
        if delivery_tag:
            self.nack(delivery_tag)

class SeleniumMiddleware:
    """Scrapy middleware handling the requests using selenium"""

    def __init__(self, driver_name, driver_executable_path,
        browser_executable_path, command_executor, driver_arguments):
        """Initialize the selenium webdriver

        Parameters
        ----------
        driver_name: str
            The selenium ``WebDriver`` to use
        driver_executable_path: str
            The path of the executable binary of the driver
        driver_arguments: list
            A list of arguments to initialize the driver
        browser_executable_path: str
            The path of the executable binary of the browser
        command_executor: str
            Selenium remote server endpoint
        """

        webdriver_base_path = f'selenium.webdriver.{driver_name}'

        driver_klass_module = import_module(f'{webdriver_base_path}.webdriver')
        self.driver_klass = getattr(driver_klass_module, 'WebDriver')

        driver_options_module = import_module(f'{webdriver_base_path}.options')
        driver_options_klass = getattr(driver_options_module, 'Options')

        driver_options = driver_options_klass()
        self.driver_executable_path = driver_executable_path

        if browser_executable_path:
            driver_options.binary_location = browser_executable_path
            self.browser_executable_path = browser_executable_path
        for argument in driver_arguments:
            driver_options.add_argument(argument)

        self.driver_kwargs = {
            'executable_path': driver_executable_path,
            f'{driver_name}_options': driver_options
        }

        # locally installed driver
        if driver_executable_path is not None:
            self.driver_kwargs = {
                'executable_path': driver_executable_path,
                f'options': driver_options
            }
            # self.driver = driver_klass(**self.driver_kwargs)
            # self.driver = uc.Chrome(headless=False,use_subprocess=False, browser_executable_path=browser_executable_path)

        # remote driver
        elif command_executor is not None:
            from selenium import webdriver
            capabilities = driver_options.to_capabilities()
            self.driver = webdriver.Remote(command_executor=command_executor,
                                           desired_capabilities=capabilities)

    @classmethod
    def from_crawler(cls, crawler):
        """Initialize the middleware with the crawler settings"""

        driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME')
        driver_executable_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        browser_executable_path = crawler.settings.get('SELENIUM_BROWSER_EXECUTABLE_PATH')
        command_executor = crawler.settings.get('SELENIUM_COMMAND_EXECUTOR')
        driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS')

        if browser_executable_path is None:
            raise NotConfigured('SELENIUM_BROWSER_EXECUTABLE_PATH')

        if driver_name is None:
            raise NotConfigured('SELENIUM_DRIVER_NAME must be set')

        if driver_executable_path is None and command_executor is None:
            raise NotConfigured('Either SELENIUM_DRIVER_EXECUTABLE_PATH '
                                'or SELENIUM_COMMAND_EXECUTOR must be set')

        middleware = cls(
            driver_name=driver_name,
            driver_executable_path=driver_executable_path,
            browser_executable_path=browser_executable_path,
            command_executor=command_executor,
            driver_arguments=driver_arguments
        )

        crawler.signals.connect(middleware.spider_closed, signals.response_received)

        return middleware

    def process_request(self, request, spider):
        """Process a request using the selenium driver if applicable"""
        print("Requesting through selenium")
        # self.driver = uc.Chrome(headless=True, use_subprocess=False, browser_executable_path=self.browser_executable_path)
        service = Service(executable_path=self.driver_executable_path)
        options = webdriver.ChromeOptions()
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(service=service, options=options)
        # self.driver = self.driver_klass(**self.driver_kwargs)
        if not isinstance(request, SeleniumRequest):
            return None
        self.driver.get(request.url)

        for cookie_name, cookie_value in request.cookies.items():
            self.driver.add_cookie(
                {
                    'name': cookie_name,
                    'value': cookie_value
                }
            )
        try:
            if request.wait_until:
                print("Now waiting for selenium")
                WebDriverWait(self.driver, request.wait_time).until(
                    request.wait_until
                )
        except Exception as e:
            print("Driver wait error",e)

        if request.screenshot:
            request.meta['screenshot'] = self.driver.get_screenshot_as_png()

        if request.script:
            self.driver.execute_script(request.script)

        body = str.encode(self.driver.page_source)

        # Expose the driver via the "meta" attribute
        request.meta.update({'driver': self.driver})

        self.driver.delete_all_cookies()

        print("Response Downloaded", body)

        # self.driver.close()

        return HtmlResponse(
            self.driver.current_url,
            body=body,
            encoding='utf-8',
            request=request
        )

    def spider_closed(self):
        """Shutdown the driver when spider is closed"""
        print("Driver quiting")
        self.driver.quit()