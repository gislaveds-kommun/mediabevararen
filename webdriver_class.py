from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

import constants as const
import config as conf


class WebdriverClass:
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
        options.add_argument(f"--window-size={const.WIDTH_Of_SCREENSHOT},{const.HEIGHT_Of_SCREENSHOT}")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        if conf.headless_for_full_height:
            options.add_argument("--headless")

        return options

    @classmethod
    def load_webpage(cls, url):
        cls.get_driver().get(url)
        cls._driver.implicitly_wait(const.TIMEOUT_SECONDS)

    @classmethod
    def quit_driver(cls):
        if cls._driver is not None:
            cls._driver.quit()
            cls._driver = None

    @classmethod
    def take_screenshot(cls, output_path):
        cls._driver.implicitly_wait(const.TIMEOUT_SECONDS)
        page_height = cls._driver.execute_script("return document.documentElement.scrollHeight")
        cls._driver.set_window_size(const.WIDTH_Of_SCREENSHOT, page_height)
        cls._driver.save_screenshot(output_path)
        print(f"Saved screenshot to {output_path}")
