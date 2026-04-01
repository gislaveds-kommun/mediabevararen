"""
Created on Thu Aug 29 16:19:39 2024
 < Archiving-of-web-and-social-media: Takes screenshots of webpages and social media
 and converts it to tiff images for the purpose of archiving.>
     Copyright (C) 2024 Gislaveds Kommun
     Author: Jerker Hubertus Bergman

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

import json
import sys
import re
import shutil
import traceback
import xml.etree.ElementTree as ET
import os
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
import pandas as pd
from PIL import Image
import lxml.etree as etree
from openpyxl import Workbook
from dotenv import load_dotenv

from constants import PATH_TO_IMAGE_TEMP
from constants import LOCAL_FACEBOOK_EXCEL_PATH
from constants import OUTPUT_DIR_EXTRACTED_DIVS
from constants import LOCAL_FACEBOOK_IMAGE_DIR
from constants import ORG_NUMBER
from constants import DELIVERY
from constants import CLI_STRINGS as cli
from webdriver_class import WebdriverClass
from exception import LoginException
from metadata import Metadata

DEBUG = False
SCRIPT_DIR = Path(__file__).resolve().parent
DEBUG_OUTPUT_DIR = SCRIPT_DIR / "tests"
XML_OUTPUT_ROOT_DIR_NAME = "folder xml merged"


def convert_png_to_tiff(input_path_png, output_path_tiff):
    image = Image.open(input_path_png)
    image.save(output_path_tiff, format='TIFF')


def replace_unwanted_chars(filename, replacement):
    return re.sub('[^a-zA-Z]', replacement, filename)


def get_part_of_string(input_string, split_by, index):
    print(input_string)
    if not split_by:
        raise ValueError("split_by cannot be empty.")
    try:
        return input_string.split(split_by)[index]
    except IndexError:
        raise IndexError(f"Index {index} is out of range for the split string.")


def create_file_name(url, type_of_web_extraction):
    filename_first_50_chars_in_url = str(url)[:50]
    if type_of_web_extraction == "local-facebook":
        filename = filename_first_50_chars_in_url
    else:
        second_part_of_filename = get_part_of_string(filename_first_50_chars_in_url, "//", 1)
        filename = second_part_of_filename

    cleaned_filename = replace_unwanted_chars(filename, "_")
    unique_filename_date_time = cleaned_filename + "_" + datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

    return unique_filename_date_time


def get_domain_from_url(url):
    return urlparse(url).netloc


def prepare_and_clean_columns_and_index(data):
    data.columns = data.columns.str.strip().str.lower()
    data.index = data.index.str.strip().str.lower()

    return data


def create_output_directories(output_base_dir, formatted_date_time):
    files_output_dir = output_base_dir / ("files for package creator " + formatted_date_time)
    xml_output_root_dir = output_base_dir / (XML_OUTPUT_ROOT_DIR_NAME + " " + formatted_date_time)

    files_output_dir.mkdir(parents=True, exist_ok=True)
    xml_output_root_dir.mkdir(parents=True, exist_ok=True)

    return files_output_dir, xml_output_root_dir


def create_combined_xml_file(xml_elements, xml_output_root_dir):
    root = ET.Element("root")
    for xml_element in xml_elements:
        root.append(xml_element)

    combined_xml_name = "combined_output.xml"
    Metadata.save_pretty_xml_to_file(root, xml_output_root_dir, combined_xml_name)
    print(f"Combined XML file created: {combined_xml_name}")
    return xml_output_root_dir / combined_xml_name


def create_xml_fgs(url_and_metadata_for_website, formatted_date, xml_file_name, tiff_image_name, folder_name,
                   basemetadata, type_of_web_extraction):
    url = url_and_metadata_for_website[0]
    title, keywords, description = WebdriverClass.get_webpage_metadata(url, type_of_web_extraction)

    metadata = basemetadata.to_dict()['value']
    additional_metadata = {
        "arkiveringsdatum": formatted_date,
        "site": get_domain_from_url(url),
        "webbsida": url_and_metadata_for_website[1],
        "webbadress": url,
        "webpagetitle": title,
        "webpagekeywords": keywords,
        "webpagedescription": description,
        "webpagecurrenturl": url,
        "informationsdatum": formatted_date,
        "dokumentfilnamn": tiff_image_name
    }
    metadata.update(additional_metadata)
    xml_file_path = Path(folder_name) / xml_file_name
    metadata_instance = Metadata(**metadata)
    metadata_instance.save_xml_to_file(xml_file_path)

    return metadata_instance.to_xml()


def is_valid_xml(xml_file):
    try:
        with open(xml_file, 'rb') as file:
            xml_doc = etree.parse(file, parser=etree.XMLParser(encoding='utf-8'))
        schema = etree.XMLSchema(file=config['xsd_file'])
        schema.assertValid(xml_doc)
        return True

    except Exception as e:
        print(f"Unexpected error: {e}")

    return False


def create_tiff_screenshot(url, package_creator_dir, xml_output_root_dir, type_of_web_extraction, image_temp_dir):
    filename = create_file_name(url, type_of_web_extraction)
    print(f"Processing {filename}")
    output_path_png = Path(image_temp_dir) / f"{filename}.png"
    tiff_image_name = filename + '.tif'
    output_path_tiff_package = Path(package_creator_dir) / tiff_image_name
    output_path_tiff_xml_output = Path(xml_output_root_dir) / tiff_image_name

    WebdriverClass.capture_full_page_screenshot_with_custom_width(str(output_path_png), type_of_web_extraction, url)

    convert_png_to_tiff(output_path_png, output_path_tiff_package)
    shutil.copy2(output_path_tiff_package, output_path_tiff_xml_output)

    return tiff_image_name


def create_package_creator_config(basemetadata, folder_name):
    arkivbildare = str(basemetadata['value']['arkivbildare'])
    first_part_of_arkivbildare = get_part_of_string(arkivbildare, "(", 0)
    arkivbildare_cleaned = replace_unwanted_chars(first_part_of_arkivbildare, '')

    ursprung = str(basemetadata['value']['ursprung'])
    systemnamn = config['systemnamn'] if config['systemnamn'].strip() else ursprung
    systemnamn_cleaned = replace_unwanted_chars(systemnamn, '')

    config_data = [("Agent 1 Namn", arkivbildare),
                   ("Agent 1 Kommentar", ORG_NUMBER),
                   ("Agent 2 Namn", systemnamn),
                   ("Agent 3 Namn", arkivbildare),
                   ("Leverans", DELIVERY),
                   ("Arkivbildare", arkivbildare_cleaned),
                   ("Systemnamn", systemnamn_cleaned),
                   ("Schema", config['xsd_file']),
                   ("Contract", config['contract'])]

    package_creator_workbook = Workbook()
    package_creator_active_sheet = package_creator_workbook.active
    for row in config_data:
        package_creator_active_sheet.append(row)

    config_file_path = folder_name / "Package-Creator-Metadata.xlsx"
    package_creator_workbook.save(config_file_path)


def run_web_extraction(type_of_web_extraction):
    pages_as_lists = pd.read_excel(config['pages_to_crawl_file'], sheet_name=0).fillna("").values.tolist()
    basemetadata = pd.read_excel(config['basemetadata_file'], sheet_name=0, index_col=0)
    basemetadata = prepare_and_clean_columns_and_index(basemetadata)

    now = datetime.now()
    formatted_date = now.strftime('%Y-%m-%d')
    formatted_date_time = now.strftime('%Y-%m-%d-%H-%M-%S')

    output_base_dir = DEBUG_OUTPUT_DIR if DEBUG else Path.cwd()
    output_base_dir.mkdir(parents=True, exist_ok=True)

    files_output_dir, xml_output_root_dir = create_output_directories(
        output_base_dir,
        formatted_date_time
    )

    image_temp_dir = (output_base_dir / PATH_TO_IMAGE_TEMP) if DEBUG else Path(PATH_TO_IMAGE_TEMP)
    image_temp_dir.mkdir(parents=True, exist_ok=True)

    match type_of_web_extraction.lower():
        case "facebook":
            WebdriverClass.login_to_facebook()
        case "linkedin":
            WebdriverClass.login_to_linkedin()
        case "instagram":
            WebdriverClass.login_to_instagram()

    xml_elements = []
    extraction_error = None

    try:
        for page_data in pages_as_lists:
            url = page_data[0]
            tiff_image_name = create_tiff_screenshot(
                url,
                files_output_dir,
                xml_output_root_dir,
                type_of_web_extraction,
                image_temp_dir
            )
            print(f"Converted to tiff: {tiff_image_name}")

            xml_file_name = get_part_of_string(tiff_image_name, ".", 0) + ".xml"
            xml_element = create_xml_fgs(
                page_data,
                formatted_date,
                xml_file_name,
                tiff_image_name,
                files_output_dir,
                basemetadata,
                type_of_web_extraction
            )
            xml_elements.append(xml_element)
            print(f"Created individual XML file: {xml_file_name}")
    except Exception as e:
        extraction_error = e
        print(f"Extraction interrupted due to error: {e}")
    finally:
        combined_xml_file_path = create_combined_xml_file(xml_elements, xml_output_root_dir)
        create_package_creator_config(basemetadata, files_output_dir)

        if xml_elements:
            convert_xml_to_csv(combined_xml_file_path, xml_output_root_dir)
        else:
            print("No XML entries were created; skipped CSV export.")

        shutil.rmtree(image_temp_dir, ignore_errors=True)

        if extraction_error is not None:
            raise extraction_error


def convert_xml_to_csv(xml_file_path, folder_name_merged):
    tree = etree.parse(xml_file_path)
    root = tree.getroot()

    data = []

    def local_name(tag_name):
        return tag_name.split("}", 1)[1] if "}" in tag_name else tag_name

    # merged XML contains default namespace "freda".
    leveransobjekt_list = [
        elem for elem in root.iter()
        if local_name(elem.tag) == "Leveransobjekt"
    ]

    for leveransobjekt in leveransobjekt_list:
        row_data = {}
        documents = [
            elem for elem in leveransobjekt
            if local_name(elem.tag) == "Dokument"
        ]

        for document in documents:
            for elem in document:
                if len(elem):
                    continue
                row_data[local_name(elem.tag)] = elem.text

            process_struct = next(
                (elem for elem in document if local_name(elem.tag) == "ProcessStrukturerat"),
                None
            )
            if process_struct is not None:
                level_values = {
                    local_name(child.tag): child.text
                    for child in process_struct
                }
                # creating fallback cause of encoding. å is encoded as Ã¥ sometimes
                # this will take å if it exists, otherwise it'll try to seawrch for Ã¥
                row_data["ProcessStrukturerat_niva1"] = level_values.get("nivå1", level_values.get("nivÃ¥1"))
                row_data["ProcessStrukturerat_niva2"] = level_values.get("nivå2", level_values.get("nivÃ¥2"))
                row_data["ProcessStrukturerat_niva3"] = level_values.get("nivå3", level_values.get("nivÃ¥3"))

            dokument_filnamn = next(
                (elem for elem in leveransobjekt if local_name(elem.tag) == "DokumentFilnamn"),
                None
            )
            if dokument_filnamn is not None:
                row_data["DokumentFilnamn"] = dokument_filnamn.text

        if row_data:
            data.append(row_data)

    df = pd.DataFrame(data)
    if not df.empty:
        process_columns = [
            "ProcessStrukturerat_niva1",
            "ProcessStrukturerat_niva2",
            "ProcessStrukturerat_niva3"
        ]
        target_candidates = [
            "KlassificeringsstrukturText",
            "klassificering",
            "Klassificering"
        ]
        column_lookup = {col.lower(): col for col in df.columns}
        target_column = next(
            (column_lookup[candidate.lower()] for candidate in target_candidates if candidate.lower() in column_lookup),
            None
        )

        if target_column is not None:
            columns_without_process = [col for col in df.columns if col not in process_columns]
            insert_index = columns_without_process.index(target_column) + 1
            process_present = [col for col in process_columns if col in df.columns]
            new_columns = (
                columns_without_process[:insert_index]
                + process_present
                + columns_without_process[insert_index:]
            )
            df = df.reindex(columns=new_columns)

    csv_file_path = Path(folder_name_merged) / "combined_output.csv"
    df.to_csv(csv_file_path, sep=';', index=False, encoding='utf-8')
    print(f"Combined CSV file created: {csv_file_path}")


def case_four_systemnamn():
    systemnamn_message = f"Your current Systemnamn is: {config['systemnamn']}"
    if not config['systemnamn']:
        systemnamn_message = cli['empty_systemnamn']

    print(systemnamn_message)
    print("************************************")
    print("You can choose one of the following actions:")
    print('1: to change Systemnamn')
    print('2: to clear it to choose the basemetadata "URSPRUNG" instead')
    print('Type any other key to exit this menu')
    print("************************************")

    answer_systemnamn_choice = input(cli['question_choice'])
    match answer_systemnamn_choice.lower():
        case "1":
            config['systemnamn'] = input(cli['question_systemnamn'])
            print(f"Your current Systemnamn is now: {config['systemnamn']}")
        case "2":
            config['systemnamn'] = ""
            print(cli['empty_systemnamn'])
        case _:
            print(cli['exit_systemnamn'])


def choose_new_file_input(file_type_name):
    print(f"\nYou are about to change which file to use as your {file_type_name.lower()}.")
    print("Write the new path to your file or write 'quit' to go back without making any changes.")

    while True:
        file_name = input(cli['question_path'])
        match file_name:
            case "quit":
                print(f'{file_type_name} was not changed.')
                return None
            case file_name if Path(file_name).is_file():
                print(f'{file_type_name} changed to {file_name}')
                return file_name
            case _:
                print(f'The path {file_name} is not valid, try again.')


def get_web_extraction_choice():
    print("************************************")
    print("The choices of web extraction are:")
    print("1: Website with a click on a banner")
    print("2: Website with no clicks")
    print("3: Facebook")
    print("4: LinkedIn")
    print("5: Instagram")
    print("6: Local Facebook")
    print("************************************")

    while True:
        user_input = input(cli['question_web_extraction'])
        match user_input:
            case "1":
                return "website-click"
            case "2":
                return "website-no-banner"
            case "3":
                return "facebook"
            case "4":
                return "linkedin"
            case "5":
                return "instagram"
            case "6":
                return "local-facebook"
            case _:
                print(cli['invalid_choice'])


def get_path_to_local_facebook():
    print(f"\nYour current 'path to local facebook' is: {config['path_to_local_facebook']}")
    answer_path_to_local_facebook = input(cli['question_local_facebook'])
    if answer_path_to_local_facebook.lower() == "y":
        new_path_local_facebook = input(cli['question_get_path_local_facebook'])
        config['path_to_local_facebook'] = new_path_local_facebook if new_path_local_facebook else config['path_to_local_facebook']


def get_custom_regexp():
    print(f"\nYour current 'divider regexp' is: {config['divider_regexp_pattern']}")
    answer_divider_regexp_pattern = input(cli['question_regexp_pattern'])
    if answer_divider_regexp_pattern.lower() == "y":
        new_divider_regexp = input(cli['question_get_new_regexp'])
        config['divider_regexp_pattern'] = new_divider_regexp if new_divider_regexp else config['divider_regexp_pattern']
        return config['divider_regexp_pattern']


def get_local_facebook_divide_choice():
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
                #return r'har lagt till .+ foto.?\.'
                return r'har\s+lagt\s+till\s+.+\s+foto.?\.'
            case "2":
                return r'har\s+lagt\s+till\s+en\s+ny\s+video\.?'
            case "3":
                return r'har\s+lagt\s+till\s+(.+foto.?|en\s+ny\s+video)\.?'
            case "4":
                return get_custom_regexp()
            case _:
                print(cli['invalid_choice'])


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


def extract_and_save_divs_with_images(html_content, divider_regexp_pattern, base_url, excel_path, lower_comparison_date, upper_comparison_date, is_date_comparison):
    cleanup_folders_and_files(excel_path)
    os.makedirs(OUTPUT_DIR_EXTRACTED_DIVS, exist_ok=True)
    image_dir = OUTPUT_DIR_EXTRACTED_DIVS + "/" + LOCAL_FACEBOOK_IMAGE_DIR
    os.makedirs(image_dir, exist_ok=True)

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
    date_pattern = re.compile('[a-z]{3,5} [0-9]{1,2}, [0-9]{4}')

    i = 0
    # Find all sections that look like posts
    posts = tag_div_main.find_all(['section', 'div'], class_='_a6-g')
    for post in posts:
        # Get the text JUST for this specific section
        post_text = post.get_text(separator=" ", strip=True)

        if re.search(divider_regexp_pattern, post_text):
            footer = post.find(class_='_a72d')
            if not footer:
                footer = post.find('footer')

            if footer:
                footer_text = footer.get_text(strip=True)
                date_match = date_pattern.search(footer_text)

                if date_match:
                    found_date = date_match.group(0).strip()
                    translated_date = translate_swedish_date(found_date)
                    date_obj = datetime.strptime(translated_date, "%b %d, %Y")

                    print("Extracted Date:", found_date)

                    if (date_obj > lower_comparison_date and date_obj < upper_comparison_date) or not is_date_comparison:
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
                                full_img_url = urljoin(base_url, img_url)
                                if full_img_url.startswith("file:///"):
                                    copy_local_image(full_img_url, image_dir)
                                else:
                                    download_image(full_img_url, img_url, image_dir)
                        i += 1
    save_extracted_data_to_file(extracted_file_paths, excel_path)


def divide_local_facebook_and_fill_excel():

    get_path_to_local_facebook()
    base_path = f"file:///{config['path_to_local_facebook']}/"
    file_path = os.path.join(config['path_to_local_facebook'], "this_profile's_activity_across_facebook/posts/profile_posts_1.html")

    config['divider_regexp_pattern'] = get_local_facebook_divide_choice()

    is_date_comparison = False
    lower_comparison_date = get_filter_date("lower")
    if lower_comparison_date:
        lower_comparison_date = transform_date(lower_comparison_date)
        is_date_comparison = True
    else:
        lower_comparison_date = datetime(1, 1, 1, 0, 0, 0)

    upper_comparison_date = get_filter_date("upper")
    if upper_comparison_date:
        upper_comparison_date = transform_date(upper_comparison_date)
        is_date_comparison = True
    else:
        lower_comparison_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    extract_and_save_divs_with_images(html_content, config['divider_regexp_pattern'], base_path, LOCAL_FACEBOOK_EXCEL_PATH, lower_comparison_date, upper_comparison_date, is_date_comparison)


def case_run():
    print(cli['run_program'])

    type_of_web_extraction = get_web_extraction_choice()

    if type_of_web_extraction == "local-facebook":
        pages_to_crawl_file_temp = config['pages_to_crawl_file']    
        divide_local_facebook_and_fill_excel()
        config['pages_to_crawl_file'] = LOCAL_FACEBOOK_EXCEL_PATH

    else:

        print(f"\nYour current 'pages-to-crawl-file' is: {config['pages_to_crawl_file']}")
        answer_change_pages_to_crawl = input(cli['question_change_file'])
        if answer_change_pages_to_crawl.lower() == "y":
            new_pages_to_crawl = choose_new_file_input('Pages-to-crawl-file')
            config['pages_to_crawl_file'] = new_pages_to_crawl if new_pages_to_crawl else config['pages_to_crawl_file']

    print(f"\nYour current basemetadata-file is: {config['basemetadata_file']}")
    answer_change_basemetadata = input(cli['question_change_file'])
    if answer_change_basemetadata.lower() == "y":
        new_basemetadata = choose_new_file_input('basemetadata-file')
        config['basemetadata_file'] = new_basemetadata if new_basemetadata else config['basemetadata_file']    

    try:
        print(cli['run_web_extraction'])
        run_web_extraction(type_of_web_extraction)
        if type_of_web_extraction == "local-facebook":
            config['pages_to_crawl_file'] = pages_to_crawl_file_temp
        print(cli['extraction completed'])
    except LoginException as e:
        print(f"Login failed: {e}")
    finally:
        WebdriverClass.quit_driver()


def case_one_headless():
    config['headless_for_full_height'] = not config['headless_for_full_height']
    print(f"Headless is set to {config['headless_for_full_height']}")


def case_two_xsd():
    print(f"\nYour current 'XSD-file' is: {config['xsd_file']}")
    answer_change_xsd = input(cli['question_change_file'])
    if answer_change_xsd.lower() == "y":
        new_xsd_file = choose_new_file_input('XSD-file')
        config['xsd_file'] = new_xsd_file if new_xsd_file else config['xsd_file']


def case_three_contract():
    if config['contract'] != "":
        print(f"Your current Contract-file is:  {config['contract']}")
    config['contract'] = input(cli['new_contract'])


def case_five_click_banner():
    print(f"Your current Click-Banner Xpath is:  {config['website_click_cookie_banner_xpath']}")
    config['website_click_cookie_banner_xpath'] = input(cli['new_click_banner_xpath'])


def exit_program():
    print(cli['exited_program'])
    print(cli['goodbye'])
    sys.exit()


def start_program():
    print(cli['welcome'])
    exit = False

    while not exit:

        print("************************************")
        print("You can choose one of the following actions:")
        print("'Exit' or ctrl+c to quit at any time.")
        print("'R' to run web extraction")
        print(f"1: to toggle Headless setting ({'ACTIVE' if config['headless_for_full_height'] else 'INACTIVE'})")
        print("2: to change XSD-file")
        print("3: to change Contract-file")
        print("4: to change Systemnamn")
        print("5: to change Click-Banner Xpath")
        print("************************************")

        user_input = input(cli['question_choice'])

        match user_input.lower():
            case "1":
                case_one_headless()
            case "2":
                case_two_xsd()
            case "3":
                case_three_contract()
            case "4":
                case_four_systemnamn()
            case "5":
                case_five_click_banner()
            case "exit":
                exit = True
            case "r":
                case_run()
            case _:
                print(cli['invalid_choice'])

        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":

    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: config.json file not found.")
        exit_program()
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in config.json.")
        exit_program()

    load_dotenv()
    try:
        start_program()
    except KeyboardInterrupt:
        print(cli['exit_ctrlc'])
    except Exception as e:
        print(f"Exited with error: {e}")
        traceback.print_exc()
    finally:
        exit_program()
