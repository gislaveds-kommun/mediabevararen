import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

import constants as const
import config as conf
from exception import LoginException


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
        driver = cls.get_driver()
        driver.implicitly_wait(const.TIMEOUT_SECONDS)
        page_height = cls._driver.execute_script("return document.documentElement.scrollHeight")
        driver.set_window_size(const.WIDTH_Of_SCREENSHOT, page_height)
        driver.save_screenshot(output_path)
        print(f"Saved screenshot to {output_path}")

    @classmethod
    def find_element_by_id(cls, name):
        return cls.get_driver().find_element(By.ID, name)

    @classmethod
    def find_element_by_name(cls, name):
        return cls.get_driver().find_element(By.NAME, name)

    @classmethod
    def find_element_by_tag_name(cls, tag_name):
        return cls.get_driver().find_elements(By.TAG_NAME, tag_name)

    @classmethod
    def find_element_by_xpath(cls, xpath):
        return cls.get_driver().find_element(By.XPATH, xpath)

    @classmethod
    def get_title(cls):
        return cls.get_driver().title

    @classmethod
    def send_input_name(cls, name, value):
        name_field = cls.find_element_by_name(name)
        name_field.clear()
        name_field.send_keys(value)

    @classmethod
    def send_input_id(cls, name, value, keys_return=False):
        name_field = cls.find_element_by_id(name)
        name_field.clear()
        name_field.send_keys(value)
        if keys_return:
            name_field.send_keys(Keys.RETURN)

    @classmethod
    def tag_has_key_value(cls, tag, key, value=None):
        if value:
            return tag.get_attribute(key) and tag.get_attribute(key).lower().strip() == value
        return tag.get_attribute(key) and tag.get_attribute(key).strip()

    @classmethod
    def has_keywords_with_content(cls, tag):
        return cls.tag_has_key_value(tag, "name", "keywords") and cls.tag_has_key_value(tag, "content")

    @classmethod
    def has_description_with_content(cls, tag):
        return cls.tag_has_key_value(tag, "name", "description") and cls.tag_has_key_value(tag, "content")

    @classmethod
    def get_webpage_metadata(cls, url):
        cls.load_webpage(url)
        title = cls.get_title()
        try:
            all_meta_tags = cls.find_element_by_tag_name("meta")

            generator = (tag.get_attribute("content") for tag in all_meta_tags if cls.has_keywords_with_content(tag))

            keywords = next(generator, const.NO_KEYWORDS_TEXT)

        except Exception as e:
            keywords = const.NO_KEYWORDS_TEXT
            print("Error occurred trying to get Keywords data: :", e)

        try:
            all_meta_tags = cls.find_element_by_tag_name("meta")

            generator = (tag.get_attribute("content") for tag in all_meta_tags if cls.has_description_with_content(tag))

            description = next(generator, const.NO_DESCRIPTION_TEXT)

        except Exception as e:
            description = const.NO_DESCRIPTION_TEXT
            print("Error occurred trying to get description data: :", e)

        return title, keywords, description

    @classmethod
    def capture_full_page_screenshot_with_custom_width(cls, output_path, type_of_web_extraction, url):
        driver = cls.get_driver()
        cls.load_webpage(url)
        try:
            WebDriverWait(driver, const.TIMEOUT_SECONDS).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )

        except Exception as e:
            print(f"Error during page load: {e}")

        match type_of_web_extraction.lower():
            case "gislaved.se":
                try:
                    WebDriverWait(driver, const.TIMEOUT_SECONDS).until(
                        EC.element_to_be_clickable((By.XPATH, const.GISLAVED_SE_COOKIE_BUTTON))).click()

                except Exception as e:
                    print(f"Error click button cookies: {e}")
            case "linkedin":
                try:
                    WebDriverWait(driver, const.TIMEOUT_SECONDS).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, const.LINKEDIN_REJECT_BUTTON))).click()

                except Exception as e:
                    print(f"Error: {e}")
            case "instagram":
                try:
                    ActionChains(driver).move_to_element(WebDriverWait(driver, const.TIMEOUT_SECONDS).until(
                        EC.element_to_be_clickable((By.XPATH, const.INSTAGRAM_LOGIN_BANNER)))).click().perform()

                except Exception as e:
                    print(f"Error click  login button s: {e}")

        cls.take_screenshot(output_path)

    @classmethod
    def login_to_facebook(cls):
        username = os.getenv("facebook_user")
        password = os.getenv("facebook_password")
        driver = cls.get_driver()
        WebdriverClass.load_webpage(const.PATH_TO_FACEBOOK)

        try:
            wait = WebDriverWait(driver, const.TIMEOUT_SECONDS)
            cookie_button = wait.until(EC.presence_of_element_located(
                (By.XPATH, const.FACEBOOK_COOKIE_BANNER)
            ))

            ActionChains(driver).move_to_element(cookie_button).click().perform()
            print("Cookies consent button clicked successfully using ActionChains!")

        except Exception as e:
            print(f"Error clicking the button: {e}")

        try:
            cls.send_input_id("email", username)
            cls.send_input_id("pass", password, True)

        except Exception as e:
            print(f"Error: {e}")
            raise LoginException

        try:
            wait = WebDriverWait(driver, const.TIMEOUT_SECONDS)
            cookie_button = wait.until(EC.presence_of_element_located(
                (By.XPATH, const.FACEBOOK_COOKIE_BANNER)
            ))
            ActionChains(driver).move_to_element(cookie_button).click().perform()
            print("Cookies consent button clicked successfully using ActionChains!")

        except Exception as e:
            print(f"Error clicking the button: {e}")

    @classmethod
    def login_to_linkedin(cls):
        username = os.getenv("linkedin_user")
        password = os.getenv("linkedin_password")
        driver = cls.get_driver()
        cls.load_webpage(const.PATH_TO_LINKEDIN)

        try:
            WebDriverWait(driver, const.TIMEOUT_SECONDS).until(
                EC.element_to_be_clickable((By.XPATH, const.LINKEDIN_ACCEPT_BUTTON1))).click()

        except Exception as e:
            print(f"Error: {e}")

        try:
            cls.send_input_id("username", username)
            cls.send_input_id("password", password)

            WebDriverWait(driver, const.TIMEOUT_SECONDS).until(
                EC.element_to_be_clickable((By.XPATH, const.LINKEDIN_LOGIN_BUTTON))).click()

        except Exception as e:
            print(f"Error on linkedin login {e}")
            raise LoginException

        try:
            WebDriverWait(driver, const.TIMEOUT_SECONDS).until(
                EC.element_to_be_clickable((By.XPATH, const.LINKEDIN_ACCEPT_BUTTON2))).click()

        except Exception as e:
            print(f"Error: {e}")

    @classmethod
    def login_to_instagram(cls):
        username = os.getenv("instagram_user")
        password = os.getenv("instagram_password")

        cls.load_webpage(const.PATH_TO_INSTAGRAM)

        try:
            cls.find_element_by_xpath(const.INSTAGRAM_COOKIE_BANNER).click()

        except Exception as e:
            print(f"Error click button cookies: {e}")

        try:
            cls.send_input_name("username", username)
            cls.send_input_name("password", password)
            cls.find_element_by_xpath(const.INSTAGRAM_LOGIN_BUTTON).click()

        except Exception as e:
            print(f"Error on instagram login {e}")
            raise LoginException
