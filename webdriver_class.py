import os
import json
import time
import base64

from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

import constants as const
from exception import LoginException


class WebdriverClass:
    _driver = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            cls._driver = cls._create_driver()
        return cls._driver

    @classmethod
    def _create_driver(cls):
        options = cls.get_options()
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()

        return driver

    @staticmethod
    def get_options():
        with open("config.json", "r") as f:
            config = json.load(f)
        options = Options()
        options.add_argument(f"--window-size={const.WIDTH_Of_SCREENSHOT},{const.HEIGHT_Of_SCREENSHOT}")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        if config['headless_for_full_height']:
            options.add_argument("--headless")

        return options

    @classmethod
    def load_local_html(cls, relative_path):
        # Get absolute path and format for browser
        absolute_path = os.path.abspath(relative_path)
        file_url = f"file:///{absolute_path.replace(os.sep, '/')}"

        cls.load_webpage(file_url)

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

        # 1. Force all WOW.js animated elements to be 100% visible immediately
        try:
            driver.execute_script("""
                // Force visible on WOW.js / animate.css elements
                document.querySelectorAll('.wow').forEach(function(el) {
                    el.style.visibility = 'visible';
                    el.style.opacity = '1';
                    el.style.animationName = 'none';
                });
                // Trigger window scroll event to kickstart lazy scripts
                window.dispatchEvent(new Event('scroll'));
            """)
        except Exception as e:
            print(f"Warning: Could not reveal WOW elements: {e}")

        # 2. Wait for images to render
        try:
            WebDriverWait(driver, const.TIMEOUT_SECONDS).until(
                lambda d: d.execute_script(
                    "return Array.from(document.images).every(img => img.complete && img.naturalWidth !== 0);"
                )
            )
        except Exception as e:
            print(f"Warning: Timed out waiting for images: {e}")

        time.sleep(1)

        # 3. Capture exact layout dimensions
        try:
            target_width = int(const.WIDTH_Of_SCREENSHOT)

            content_height = driver.execute_script(
                "return Math.max("
                "document.body.scrollHeight, document.documentElement.scrollHeight, "
                "document.body.offsetHeight, document.documentElement.offsetHeight, "
                "document.body.clientHeight, document.documentElement.clientHeight);"
            )

            driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
                "width": target_width,
                "height": int(content_height),
                "deviceScaleFactor": 1,
                "mobile": False
            })

            screenshot_data = driver.execute_cdp_cmd("Page.captureScreenshot", {
                "format": "png",
                "captureBeyondViewport": True
            })

            with open(output_path, "wb") as f:
                f.write(base64.b64decode(screenshot_data["data"]))

            # Cleanup viewport overrides & reset window dimensions
            driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
            driver.set_window_size(const.WIDTH_Of_SCREENSHOT, const.HEIGHT_Of_SCREENSHOT)

            print(f"Saved full-page screenshot to {output_path}")

        except Exception as e:
            print(f"CDP capture failed, falling back: {e}")
            page_height = driver.execute_script(
                "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);"
            )
            driver.set_window_size(const.WIDTH_Of_SCREENSHOT, page_height)
            driver.save_screenshot(output_path)

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
    def get_webpage_metadata(cls, url, type_of_web_extraction):
        if type_of_web_extraction.startswith("local-"):
            cls.load_local_html(url)
        else:
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
        if type_of_web_extraction.startswith("local-"):
            cls.load_local_html(url)
        else:
            cls.load_webpage(url)
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        try:
            WebDriverWait(driver, const.TIMEOUT_SECONDS).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )

        except Exception as e:
            print(f"Error during page load: {e}")

        match type_of_web_extraction.lower():
            case "website-click":
                try:
                    WebDriverWait(driver, const.TIMEOUT_SECONDS).until(
                        EC.element_to_be_clickable((By.XPATH, config['website_click_cookie_banner_xpath']))).click()

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
