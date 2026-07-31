import os
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
import shutil
import requests
import pandas as pd

from bs4 import BeautifulSoup

from constants import LOCAL_FACEBOOK_EXCEL_PATH
from constants import OUTPUT_DIR_EXTRACTED_DIVS
from constants import LOCAL_FACEBOOK_IMAGE_DIR
from constants import CLI_STRINGS as cli


def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_filter_date(date_type):

    match date_type:
        case "lower":
            answer_filter_date = input(cli['question_lower_date'])
        case "upper":
            answer_filter_date = input(cli['question_upper_date'])

    if answer_filter_date.lower() == "y":
        while True:
            filter_date = input(cli['question_get_filter_date'])
            if is_valid_date(filter_date):
                return filter_date
            else:
                print(cli['invalid_date_format'])
    else:
        return False


def transform_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")


def get_path_to_local_facebook(config):
    from constants import CLI_STRINGS as cli
    print(f"\nYour current 'path to local facebook' is: {config['path_to_local_facebook']}")
    answer_path_to_local_facebook = input(cli['question_local_facebook'])
    if answer_path_to_local_facebook.lower() == "y":
        new_path_local_facebook = input(cli['question_get_path_local_facebook'])
        config['path_to_local_facebook'] = new_path_local_facebook if new_path_local_facebook else config['path_to_local_facebook']


def cleanup_folders_and_files(excel_path):
    if os.path.exists(OUTPUT_DIR_EXTRACTED_DIVS):
        # We delete the whole tree and recreate it to ensure it's empty
        shutil.rmtree(OUTPUT_DIR_EXTRACTED_DIVS)

    os.makedirs(OUTPUT_DIR_EXTRACTED_DIVS, exist_ok=True)

    # Delete the Excel file if it exists
    if os.path.exists(excel_path):
        os.remove(excel_path)
        print(f"Cleaned up existing Excel file: {excel_path}")

    # Recreate the image directory inside the fresh output folder
    image_dir = os.path.join(OUTPUT_DIR_EXTRACTED_DIVS, LOCAL_FACEBOOK_IMAGE_DIR)
    os.makedirs(image_dir, exist_ok=True)


def translate_swedish_date(date_str):
    date_str = date_str.lower()
    months = {
        "januari": "Jan", "februari": "Feb", "mars": "Mar",
        "april": "Apr", "maj": "May", "juni": "Jun",
        "juli": "Jul", "augusti": "Aug", "september": "Sep",
        "oktober": "Oct", "november": "Nov", "december": "Dec",
        # Also handle short versions if they exist in your data
        "jan": "Jan", "feb": "Feb", "mar": "Mar", "apr": "Apr",
        "okt": "Oct", "dec": "Dec"
    }

    for swedish, english in months.items():
        if swedish in date_str:
            date_str = date_str.replace(swedish, english)
            break

    return date_str


def save_html(html_soup, save_path):
    with open(save_path, 'w', encoding='utf-8') as file:
        file.write(str(html_soup.prettify()))


def copy_local_image(full_img_url, image_dir):
    local_path = urlparse(full_img_url).path

    if os.name == 'nt':
        local_path = local_path.lstrip('/')

    try:
        img_name = os.path.basename(local_path)
        img_path = os.path.join(image_dir, img_name)

        shutil.copy(local_path, img_path)
        print(f"Copied: {img_path}")

    except Exception as e:
        print(f"Failed to copy image {local_path}: {e}")


def download_image(full_img_url, img_url, image_dir):
    try:
        response = requests.get(full_img_url, stream=True)
        response.raise_for_status()

        img_name = os.path.basename(img_url)
        img_path = os.path.join(image_dir, img_name)

        with open(img_path, 'wb') as img_file:
            for chunk in response.iter_content(1024):
                img_file.write(chunk)

        print(f"Downloaded: {img_path}")

    except Exception as e:
        print(f"Failed to download image {full_img_url}: {e}")


def save_extracted_data_to_file(extracted_data, excel_path):
    df = pd.DataFrame(extracted_data, columns=['Webbadress', 'Webbsida'])
    df.to_excel(excel_path, index=False)


class LocalFacebookProcessor:
    def __init__(self, config):
        self.config = config
        self.base_path = f"file:///{self.config['path_to_local_facebook']}/"
        self.html_file_path = os.path.join(
            self.config['path_to_local_facebook'],
            "this_profile's_activity_across_facebook/posts/profile_posts_1.html"
        )
        self.image_dir = os.path.join(OUTPUT_DIR_EXTRACTED_DIVS, LOCAL_FACEBOOK_IMAGE_DIR)

        self.is_date_comparison = False
        self.lower_date = datetime(1, 1, 1)
        self.upper_date = datetime.now()

    def get_local_facebook_divide_choice(self):
        """Internal method to determine how to split the HTML posts."""
        print("************************************")
        print("The choices for dividing the local facebook are:")
        print("1: Divs with images")
        print("2: Divs with movies")
        print("3: Divs with images and movies")
        print("4: Custom regexp")
        print("************************************")

        while True:
            user_input = input(cli['question_local_fb_divide'])
            match user_input:
                case "1":
                    return r'har\s+lagt\s+till\s+.+\s+foto.?\.'
                case "2":
                    return r'har\s+lagt\s+till\s+en\s+ny\s+video\.?'
                case "3":
                    return r'har\s+lagt\s+till\s+(.+foto.?|en\s+ny\s+video)\.?'
                case "4":
                    return self.get_custom_regexp()
                case _:
                    print(cli['invalid_choice'])

    def extract_and_save_divs_with_images(self, html_content, excel_path):
        """Logic for parsing the HTML and downloading associated media."""
        cleanup_folders_and_files(excel_path)
        os.makedirs(OUTPUT_DIR_EXTRACTED_DIVS, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)

        soup = BeautifulSoup(html_content, 'html.parser')
        result_html = BeautifulSoup('<html></html>', 'html.parser')
        tag_html = result_html.html

        if soup.head:
            if soup.head.base:
                soup.head.base.decompose()
            tag_html.append(soup.head)

        tag_body = result_html.new_tag('body')
        tag_html.append(tag_body)

        tag_div_main = soup.find(True, {"role": "main"})
        extracted_file_paths = []
        date_pattern = re.compile(r'[a-z]{3,10} [0-9]{1,2}, [0-9]{4}', re.IGNORECASE)

        i = 0
        posts = tag_div_main.find_all(['section', 'div'], class_='_a6-g')

        for post in posts:
            post_text = post.get_text(separator=" ", strip=True)

            if re.search(self.config['divider_regexp_pattern'], post_text):
                footer = post.find(class_='_a72d') or post.find('footer')

                if footer:
                    footer_text = footer.get_text(strip=True)
                    date_match = date_pattern.search(footer_text)

                    if date_match:
                        found_date = date_match.group(0).strip()
                        translated_date = translate_swedish_date(found_date)
                        date_obj = datetime.strptime(translated_date, "%b %d, %Y")

                        if not self.is_date_comparison or (self.lower_date <= date_obj <= self.upper_date):
                            tag_body.clear()
                            tag_body.append(post)

                            file_name = f'post_html_{i}.html'
                            file_path = os.path.join(OUTPUT_DIR_EXTRACTED_DIVS, file_name)
                            save_html(result_html, file_path)
                            extracted_file_paths.append([file_path, "Lokal Facebook"])

                            images = post.find_all('img')
                            for img in images:
                                img_url = img.get('src')
                                if img_url:
                                    full_img_url = urljoin(self.base_path, img_url)
                                    if full_img_url.startswith("file:///"):
                                        copy_local_image(full_img_url, self.image_dir)
                                    else:
                                        download_image(full_img_url, img_url, self.image_dir)
                            i += 1

        save_extracted_data_to_file(extracted_file_paths, excel_path)

    def get_custom_regexp(self):
        print(f"\nYour current 'divider regexp' is: {self.config['divider_regexp_pattern']}")
        answer_divider_regexp_pattern = input(cli['question_regexp_pattern'])
        if answer_divider_regexp_pattern.lower() == "y":
            new_divider_regexp = input(cli['question_get_new_regexp'])
            self.config['divider_regexp_pattern'] = new_divider_regexp if new_divider_regexp else self.config['divider_regexp_pattern']
        return self.config['divider_regexp_pattern']

    def process(self):
        """Main entry point for the class."""
        get_path_to_local_facebook(self.config)
        self.base_path = f"file:///{self.config['path_to_local_facebook']}/"
        self.html_file_path = os.path.join(
            self.config['path_to_local_facebook'],
            "this_profile's_activity_across_facebook/posts/profile_posts_1.html"
        )
        self.config['divider_regexp_pattern'] = self.get_local_facebook_divide_choice()

        lower = get_filter_date("lower")
        if lower:
            self.lower_date = transform_date(lower)
            self.is_date_comparison = True

        upper = get_filter_date("upper")
        if upper:
            self.upper_date = transform_date(upper)
            self.is_date_comparison = True
        else:
            self.upper_date = datetime.today().replace(hour=23, minute=59, second=59)

        if not os.path.exists(self.html_file_path):
            print(f"Error: HTML file not found at {self.html_file_path}")
            return

        with open(self.html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        self.extract_and_save_divs_with_images(html_content, LOCAL_FACEBOOK_EXCEL_PATH)
