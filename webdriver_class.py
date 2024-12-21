from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

import constants as const
import config as conf


class Webdriver_class:
    _driver = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            cls._driver = cls.create_driver()
        return cls._driver

    @classmethod
    def create_driver(cls):
        options = cls.get_options()
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()

        return driver

    @staticmethod
    def get_options():
        options = Options()
        options.add_argument(f"--window-size={const.WIDTH_Of_SCREENSHOT},1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        if conf.headless_for_full_height:
            options.add_argument("--headless")

        return options
