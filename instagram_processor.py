import os
import re
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pathlib import Path

from base_processor import BaseLocalProcessor
from utils import (
    save_html,
    copy_local_image,
    download_image, 
    save_extracted_data_to_file,
    translate_swedish_date
)
from constants import CLI_STRINGS as cli


class LocalInstagramProcessor(BaseLocalProcessor):

    @property
    def relative_html_path(self):
        # Path inside local Instagram data export structure
        return "your_instagram_activity/media/posts_1.html"

    def get_divide_choice(self):
        """Prompt user to choose post filter rules for Instagram."""
        print("************************************")
        print("The choices for dividing local Instagram posts are:")
        print("1: All posts")
        print("2: Posts with images only")
        print("3: Posts with videos only")
        print("4: Posts WITHOUT images or videos (Text/Metadata only)")
        print("5: Custom regexp")
        print("************************************")

        while True:
            user_input = input("Enter choice (1-5): ")
            match user_input:
                case "1":
                    return r'.*'
                case "2":
                    return r'<img'
                case "3":
                    return r'<video|\.mp4|Klick\s+för\s+video:'
                case "4":
                    # Matches posts containing neither <img> nor <video>
                    return r'(?s)^(?!.*<img)(?!.*<video)'
                case "5":
                    return self.get_custom_regexp()
                case _:
                    print(cli.get('invalid_choice', 'Invalid choice, try again.'))

    def get_custom_regexp(self):
        print(f"\nYour current 'divider regexp' is: {self.config.get('divider_regexp_pattern')}")
        answer = input(cli.get('question_regexp_pattern', 'Change regex? (y/n): '))
        if answer.lower() == "y":
            new_regexp = input(cli.get('question_get_new_regexp', 'Enter pattern: '))
            if new_regexp:
                self.config['divider_regexp_pattern'] = new_regexp
        return self.config.get('divider_regexp_pattern', r'.*')

    def parse_instagram_date(self, date_text):
        """
        Parses dates like 'mars 17, 2026 5:17 em' or 'dec 09, 2025 2:39 em'
        """
        # Clean text
        date_text = date_text.strip().lower()

        # Handle Swedish time indicators (em = pm, fm = am)
        date_text = date_text.replace(" em", " pm").replace(" fm", " am")
        
        # Translate month name (e.g., 'mars' -> 'Mar', 'dec' -> 'Dec')
        translated_date_str = translate_swedish_date(date_text)

        # Parse string format: "Mar 17, 2026 5:17 pm"
        try:
            return datetime.strptime(translated_date_str, "%b %d, %Y %I:%M %p")
        except ValueError:
            # Fallback format if seconds or 24h format are used without am/pm
            try:
                date_part = date_text.split(" ")[0:3]
                date_only = translate_swedish_date(" ".join(date_part))
                return datetime.strptime(date_only, "%b %d, %Y")
            except Exception as e:
                print(f"Could not parse date '{date_text}': {e}")
                return None

    def extract_and_save_posts(self, html_content):
        """Instagram-specific DOM parsing and extraction logic."""
        soup = BeautifulSoup(html_content, 'html.parser')
        result_html = BeautifulSoup('<html></html>', 'html.parser')
        tag_html = result_html.html

        if soup.head:
            if soup.head.base:
                soup.head.base.decompose()
            tag_html.append(soup.head)

        tag_body = result_html.new_tag('body')
        tag_html.append(tag_body)

        # 1. Target Instagram's main content area
        tag_main = soup.find('main', role='main') or soup.find('div', class_='_a705')

        if not tag_main:
            print("No main content container found in Instagram HTML.")
            return

        extracted_file_paths = []
        MEDIA_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.mp4', '.mov', '.avi')
        root_export_dir = self.config.get(self.config_key, "")

        posts = tag_main.find_all('div', class_='_a6-g')
        print(f"Found {len(posts)} Instagram posts in file.")

        i = 0  
        for post in posts:
            post_html_str = str(post)

            if re.search(self.config.get('divider_regexp_pattern', r'.*'), post_html_str, re.IGNORECASE):

                footer = post.find('div', class_='_a6-o')
                date_obj = self.parse_instagram_date(footer.get_text(strip=True)) if footer else None

                if date_obj is None:
                    print("No date found.")
                    continue

                if not self.is_date_comparison or (self.lower_date <= date_obj <= self.upper_date):

                    media_elements = post.find_all(['img', 'video', 'a'])
                    root_export_dir = self.config.get(self.config_key, "")

                    for elem in media_elements:
                        attr_name = 'src' if elem.name in ['img', 'video'] else 'href'
                        media_url = elem.get(attr_name)

                        if media_url and media_url.lower().endswith(MEDIA_EXTENSIONS):
                            if 'Instagram-Logo' in media_url:
                                continue

                            img_name = os.path.basename(media_url)

                            clean_rel_path = media_url.replace('/', os.sep)
                            abs_file_path = os.path.join(root_export_dir, clean_rel_path)

                            if os.path.exists(abs_file_path):
                                full_media_url = Path(abs_file_path).as_uri()
                            else:
                                found_path = None
                                for root_dir, _, files in os.walk(root_export_dir):
                                    if img_name in files:
                                        found_path = os.path.join(root_dir, img_name)
                                        break

                                if found_path:
                                    full_media_url = Path(found_path).as_uri()
                                else:
                                    full_media_url = urljoin(self.base_path, media_url)

                            if full_media_url.startswith("file:///"):
                                copy_local_image(full_media_url, self.image_dir)
                            else:
                                download_image(full_media_url, media_url, self.image_dir)

                            rel_image_dir = os.path.relpath(self.image_dir, self.output_dir).replace('\\', '/')
                            elem[attr_name] = f"{rel_image_dir}/{img_name}"

                    tag_body.clear()
                    tag_body.append(post)
                    info_date = date_obj.strftime("%Y-%m-%d")
                    file_name = f'post_html_{i}--{info_date}.html'
                    file_path = os.path.join(self.output_dir, file_name)
                    save_html(result_html, file_path)
                    extracted_file_paths.append([file_path, "Lokal Instagram"])

                    i += 1  # Increment saved post counter

        save_extracted_data_to_file(extracted_file_paths, self.excel_path)
        print(f"Successfully extracted {i} Instagram posts to {self.excel_path}")