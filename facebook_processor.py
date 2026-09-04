import re
import os
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from base_processor import BaseLocalProcessor
from utils import (
    save_html,
    copy_local_image,
    download_image,
    save_extracted_data_to_file,
    translate_swedish_date
)
from constants import CLI_STRINGS as cli


class LocalFacebookProcessor(BaseLocalProcessor):

    @property
    def relative_html_path(self):
        # Facebook's specific HTML profile export path
        return "this_profile's_activity_across_facebook/posts/profile_posts_1.html"

    def get_divide_choice(self):
        """Facebook-specific menu for post filter choices."""
        print("************************************")
        print("The choices for dividing local Facebook posts are:")
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

    def get_custom_regexp(self):
        print(f"\nYour current 'divider regexp' is: {self.config.get('divider_regexp_pattern')}")
        answer = input(cli['question_regexp_pattern'])
        if answer.lower() == "y":
            new_regexp = input(cli['question_get_new_regexp'])
            if new_regexp:
                self.config['divider_regexp_pattern'] = new_regexp
        return self.config.get('divider_regexp_pattern')

    def extract_and_save_posts(self, html_content):
        """Facebook-specific DOM parsing and extraction logic."""
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

        if not tag_div_main:
            print("No main content container found.")
            return

        posts = tag_div_main.find_all(['section', 'div'], class_='_a6-g')

        i = 0
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
                        

                        # Date filtering logic inherited from BaseLocalProcessor
                        if not self.is_date_comparison or (self.lower_date <= date_obj <= self.upper_date):
                            tag_body.clear()
                            tag_body.append(post)

                            info_date = date_obj.strftime("%Y-%m-%d")
                            file_name = f'post_html_{i}--{info_date}.html'    
                            file_path = os.path.join(self.output_dir, file_name)
                            save_html(result_html, file_path)
                            extracted_file_paths.append([file_path, "Lokal Facebook"])

                            images = post.find_all('img')
                            for img in images:
                                img_url = img.get('src')
                                if img_url:
                                    full_img_url = urljoin(self.base_path, img_url)
                                    if full_img_url.startswith("file:///"):
                                        if not copy_local_image(full_img_url, self.image_dir):
                                            print("Copy local image failed")
                                            continue
                                    else:
                                        download_image(full_img_url, img_url, self.image_dir)
                            i += 1
                    else:
                        print("No date found.")
                else:
                    print("No footer found.")
        save_extracted_data_to_file(extracted_file_paths, self.excel_path)