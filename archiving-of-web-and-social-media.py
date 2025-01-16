"""
Created on Thu Aug 29 16:19:39 2024

 < Archiving-of-web-and-social-media: Takes screenshots of webpages and social media
 and converts it to tiff images for the purpose of archiving.>
    Copyright (C) <2024>  <Jerker Hubertus Bergman>

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
import os
import sys
import re
import traceback
import xml.etree.ElementTree as ET
import xml.dom.minidom
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from PIL import Image
from lxml import etree
from openpyxl import Workbook
from dotenv import load_dotenv

from constants import PATH_TO_IMAGE_TEMP
from constants import CLI_STRINGS as cli
from webdriver_class import WebdriverClass
from exception import LoginException


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


def save_pretty_xml_to_file(root, folder_name, xml_file_name):
    declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_string = declaration + ET.tostring(root, encoding="utf-8", method="xml").decode()

    dom = xml.dom.minidom.parseString(xml_string)
    formatted_xml = dom.toprettyxml(indent="  ", encoding="UTF-8").decode("UTF-8")

    xml_file_path = Path(folder_name) / xml_file_name
    with open(xml_file_path, "w", encoding="utf-8") as file:
        file.write(formatted_xml)


def create_xml_fgs(url_and_metadata_for_website, formatted_date, xml_file_name, tiff_image_name, folder_name, basemetadata):
    url = url_and_metadata_for_website[0]
    website = url_and_metadata_for_website[1]
    root = ET.Element(
        "Leveransobjekt",
        attrib={
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "FREDA-GS-Webbsidor-v1_0.xsd",
            "xmlns": "freda"
        }
    )

    # The order of the subelements is critical
    document = ET.SubElement(root, "Dokument")

    ET.SubElement(document, "Organisation").text = str(basemetadata['value']['organisation'])
    ET.SubElement(document, "Arkivbildare").text = str(basemetadata['value']['arkivbildare'])
    ET.SubElement(document, "Arkivbildarenhet").text = str(basemetadata['value']['arkivbildarenhet'])
    ET.SubElement(document, "Arkiv").text = str(basemetadata['value']['arkiv'])
    ET.SubElement(document, "Serie").text = str(basemetadata['value']['serie'])
    ET.SubElement(document, "KlassificeringsstrukturText").text = str(basemetadata['value']['klassificeringsstrukturtext'])

    process_struct = ET.SubElement(document, "ProcessStrukturerat")            
    ET.SubElement(process_struct, "nivå1").text = str(basemetadata['value']['nivå1'])
    ET.SubElement(process_struct, "nivå2").text = str(basemetadata['value']['nivå2'])
    ET.SubElement(process_struct, "nivå3").text = str(basemetadata['value']['nivå3'])

    ET.SubElement(document, "Ursprung").text = str(basemetadata['value']['ursprung'])
    ET.SubElement(document, "Arkiveringsdatum").text = formatted_date
    ET.SubElement(document, "Sekretess").text = str(basemetadata['value']['sekretess'])
    ET.SubElement(document, "Personuppgifter").text = str(basemetadata['value']['personuppgifter'])
    ET.SubElement(document, "Forskningsdata").text = str(basemetadata['value']['forskningsdata'])
    ET.SubElement(document, "Site").text = get_domain_from_url(url)
    ET.SubElement(document, "Webbsida").text = website
    ET.SubElement(document, "Webbadress").text = url

    title, keywords, description = WebdriverClass.get_webpage_metadata(url)
    ET.SubElement(document, "WebPageTitle").text = title
    ET.SubElement(document, "WebPageKeywords").text = keywords
    ET.SubElement(document, "WebPageDescription").text = description
    ET.SubElement(document, "WebPageCurrentURL").text = url
    ET.SubElement(document, "Informationsdatum").text = formatted_date
    ET.SubElement(document, "Kommentar").text = str(basemetadata['value']['kommentar'])

    ET.SubElement(root, "DokumentFilnamn").text = tiff_image_name

    save_pretty_xml_to_file(root, folder_name, xml_file_name)


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


def create_tiff_screenshot(url, folder_name, type_of_web_extraction):
    filename = create_file_name(url)
    print(f"Processing {filename}")
    output_path_png = "image_temp/" + filename + '.png'
    tiff_image_name = filename + '.tif'
    output_path_tiff = folder_name + "/" + tiff_image_name

    WebdriverClass.capture_full_page_screenshot_with_custom_width(output_path_png, type_of_web_extraction, url)

    convert_png_to_tiff(output_path_png, output_path_tiff)

    return tiff_image_name


def create_package_creator_config(basemetadata, folder_name):
    arkivbildare = str(basemetadata['value']['arkivbildare'])
    first_part_of_arkivbildare = get_part_of_string(arkivbildare, "(", 0)
    arkivbildare_cleaned = replace_unwanted_chars(first_part_of_arkivbildare, '')

    ursprung = str(basemetadata['value']['ursprung'])
    systemnamn = config['systemnamn'] if config['systemnamn'].strip() else ursprung
    systemnamn_cleaned = replace_unwanted_chars(systemnamn, '')

    config_data = [("Agent 1 Namn", arkivbildare),
                   ("Agent 1 Kommentar", "ORG:212000-0514"),
                   ("Agent 2 Namn", systemnamn),
                   ("Agent 3 Namn", arkivbildare),
                   ("Leverans", "Gislaved-webb-1"),
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

    today = datetime.now()
    formatted_date = today.strftime('%Y-%m-%d')
    formatted_date_time = today.strftime('%Y-%m-%d-%H-%M-%S')

    folder_name = "files for package creator " + formatted_date_time
    os.mkdir(folder_name)

    if not os.path.isdir(PATH_TO_IMAGE_TEMP):
        os.mkdir(PATH_TO_IMAGE_TEMP)

    match type_of_web_extraction.lower():
        case "facebook":
            WebdriverClass.login_to_facebook()
        case "linkedin":
            WebdriverClass.login_to_linkedin()
        case "instagram":
            WebdriverClass.login_to_instagram()

    for url_and_metadata_for_website in pages_as_lists:

        url = url_and_metadata_for_website[0]
        tiff_image_name = create_tiff_screenshot(url, folder_name, type_of_web_extraction)
        print(f"Converted to tiff: {tiff_image_name}")

        xml_file_name = get_part_of_string(tiff_image_name, ".", 0) + ".xml"
        create_xml_fgs(url_and_metadata_for_website, formatted_date, xml_file_name, tiff_image_name, folder_name, basemetadata)
        print(f"Created XML file: {xml_file_name}")

        xml_file_path = folder_name + "/" + xml_file_name

        if not is_valid_xml(xml_file_path):
            print(f"xml not valid: {xml_file_path}")
            break
        else:
            print("Validation successful.")

    create_package_creator_config(basemetadata, folder_name)


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
    print("1: gislaved.se")
    print("2: insidan.gislaved.se")
    print("3: Facebook")
    print("4: LinkedIn")
    print("5: Instagram")
    print("************************************")

    while True:
        user_input = input(cli['question_web_extraction'])
        match user_input:
            case "1":
                return "gislaved.se"
            case "2":
                return "insidan.gislaved.se"
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
        print("1: to toogle Headless setting")
        print("2: to change XSD-file")
        print("3: to change Contract-file")
        print("4: to change Systemnamn")
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
            case "exit":
                exit = True
            case "r":
                case_run()
            case _:
                print(cli['invalid_choice'])

        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)


if __name__ == "__main__":

    with open("config.json", "r") as f:
        config = json.load(f)

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
