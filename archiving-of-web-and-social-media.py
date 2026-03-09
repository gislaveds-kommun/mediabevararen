"""
Created on Thu Aug 29 16:19:39 2024

Experimentversion lö 22 mars 2025 med uppdaterade def create_xml_fgs och def run_web_extraction samt ny def convert_xml_to_csv.
Uppdateringarna innebär att xml-filerna slås ihop till en och att en csv-fil skapas baserad på den sammanslagna xml-filen.
Se #kommentarer.

Exp.version må 24 mars 2025: Fixat efter diskussion möte så att de kombinerade filerna sparas i separat, parallell mapp.
I def run_web_extraction:
    folder_name_merged = "files_for_merged_files " + formatted_date_time
    os.mkdir(folder_name_merged)
Samt byta från folder_name till folder_name_merged på förekommande ställen.

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
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from PIL import Image
import lxml.etree as etree
from openpyxl import Workbook
from dotenv import load_dotenv

from constants import PATH_TO_IMAGE_TEMP
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
    if not split_by:
        raise ValueError("split_by cannot be empty.")
    try:
        return input_string.split(split_by)[index]
    except IndexError:
        raise IndexError(f"Index {index} is out of range for the split string.")


def create_file_name(url):
    filename_first_50_chars_in_url = str(url)[:50]
    second_part_of_filename = get_part_of_string(filename_first_50_chars_in_url, "//", 1)
    cleaned_filename = replace_unwanted_chars(second_part_of_filename, "_")
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

def create_xml_fgs(url_and_metadata_for_website, formatted_date, xml_file_name, tiff_image_name, folder_name, basemetadata):
    url = url_and_metadata_for_website[0]
    title, keywords, description = WebdriverClass.get_webpage_metadata(url)

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
    filename = create_file_name(url)
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

    config_file_path = folder_name + "\\Package-Creator-Metadata.xlsx"
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
                basemetadata
            )
            xml_elements.append(xml_element)
            print(f"Created individual XML file: {xml_file_name}")
    except Exception as e:
        extraction_error = e
        print(f"Extraction interrupted due to error: {e}")
    finally:
        combined_xml_file_path = create_combined_xml_file(xml_elements, xml_output_root_dir)

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

    # Iterera leveransobjektet
    for leveransobjekt in root.findall("Leveransobjekt"):
        row_data = {}
        for document in leveransobjekt.findall("Dokument"):
            for elem in document:
                row_data[elem.tag] = elem.text
            
            # Extract values from ProcessStrukturerat
            #process_struct = document.find("ProcessStrukturerat")
            #if process_struct is not None:
                #for child in process_struct:
                    #row_data[child.tag] = child.text
                    
            # Fånga in nivå-värdena. Undviker framtida problem med csv:n genom att trolla bort bokstaven å. Borde kanske ha fixat detta redan i kombinerad xml
            process_struct = document.find("ProcessStrukturerat")
            if process_struct is not None:
                row_data["ProcessStrukturerat_niva1"] = process_struct.find(".//nivå1").text if process_struct.find(".//nivå1") is not None else None
                row_data["ProcessStrukturerat_niva2"] = process_struct.find(".//nivå2").text if process_struct.find(".//nivå2") is not None else None
                row_data["ProcessStrukturerat_niva3"] = process_struct.find(".//nivå3").text if process_struct.find(".//nivå3") is not None else None
            
            # DokumentFilnamn
            dokument_filnamn = leveransobjekt.find("DokumentFilnamn")
            if dokument_filnamn is not None:
                row_data["DokumentFilnamn"] = dokument_filnamn.text
        
        data.append(row_data)

    # Skapa df
    df = pd.DataFrame(data)

    # DataFrame till CSV
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
            case _:
                print(cli['invalid_choice'])


def case_run():
    print(cli['run_program'])

    type_of_web_extraction = get_web_extraction_choice()

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


