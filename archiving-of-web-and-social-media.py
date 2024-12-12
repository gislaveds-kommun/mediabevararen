"""
Created on Thu Aug 29 16:19:39 2024

 < Archiving-of-web-and-social-media: Takes screenshots of webpages and social media
 and converts it to tiff images for the purpose of archiving.>
    Copyright (C) <2024>  <Jerker Hubertus Bergman>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,P
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

from PIL import Image
import pandas as pd
import re
import xml.etree.ElementTree as ET
import xml.dom.minidom
from lxml import etree
from datetime import datetime
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
from openpyxl import Workbook
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
import constants as const
load_dotenv()


def convert_png_to_tiff(input_path_png, output_path_tiff):
    image = Image.open(input_path_png)
    image.save(output_path_tiff, format='TIFF')


def replace_unwanted_chars(filename, replacement):
    return re.sub('[^a-zA-Z]', replacement, filename)  


def get_part_of_string(input_string, split_by, part):
    return input_string.split(split_by)[part]


def create_file_name(url):
    filename_first_50_chars_in_url = str(url)[:50]
    second_part_of_filename = get_part_of_string(filename_first_50_chars_in_url, "//", 1)
    cleaned_filename = replace_unwanted_chars(second_part_of_filename, "_")
    unique_filename_date_time = cleaned_filename + "_" + datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    return unique_filename_date_time


def tag_has_key_value(tag, key, value=None):
    if value:
        return tag.get_attribute(key) and tag.get_attribute(key).lower().strip() == value
    return tag.get_attribute(key) and tag.get_attribute(key).strip()


def has_keywords_with_content(tag):
    return tag_has_key_value(tag, "name", "keywords") and tag_has_key_value(tag, "content")


def has_description_with_content(tag):
    return tag_has_key_value(tag, "name", "description") and tag_has_key_value(tag, "content")


def get_domain_from_url(url):
    return urlparse(url).netloc


def prepare_and_clean_columns_and_index(data):
    data.columns = data.columns.str.strip()
    data.index = data.index.str.strip()
    data.columns = data.columns.str.lower()
    data.index = data.index.str.lower()
    return data


def get_webpage_metadata(url, driver):
    driver.get(url)
    title = driver.title
    try:
        all_meta_tags = driver.find_elements(By.TAG_NAME, "meta")

        generator = (tag.get_attribute("content") for tag in all_meta_tags if has_keywords_with_content(tag))

        keywords = next(generator, const.NO_KEYWORDS_TEXT)

    except Exception as e:
        keywords = const.NO_KEYWORDS_TEXT
        print("Error occurred trying to get Keywords data: :", e)

    try:
        all_meta_tags = driver.find_elements(By.TAG_NAME, "meta")

        generator = (tag.get_attribute("content") for tag in all_meta_tags if has_description_with_content(tag))

        description = next(generator, const.NO_DESCRIPTION_TEXT)

    except Exception as e:
        description = const.NO_DESCRIPTION_TEXT
        print("Error occurred trying to get description data: :", e)
    return title, keywords, description


def create_xml_fgs(url_and_metadata_for_website, formatted_date, xml_file_name, tiff_image_name, folder_name, basmetadata, driver):
    url = url_and_metadata_for_website[0]
    webbsida = url_and_metadata_for_website[1]
    root = ET.Element("Leveransobjekt", attrib={"xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance", "xsi:noNamespaceSchemaLocation": "FREDA-GS-Webbsidor-v1_0.xsd", "xmlns": "freda"})
    dokument = ET.SubElement(root, "Dokument")

    ET.SubElement(dokument, "Organisation").text = str(basmetadata['value']['organisation'])
    ET.SubElement(dokument, "Arkivbildare").text = str(basmetadata['value']['arkivbildare'])
    ET.SubElement(dokument, "Arkivbildarenhet").text = str(basmetadata['value']['arkivbildarenhet'])
    ET.SubElement(dokument, "Arkiv").text = str(basmetadata['value']['arkiv'])
    ET.SubElement(dokument, "Serie").text = str(basmetadata['value']['serie'])
    ET.SubElement(dokument, "KlassificeringsstrukturText").text = str(basmetadata['value']['klassificeringsstrukturtext'])
    process_strukturerat = ET.SubElement(dokument, "ProcessStrukturerat")            
    ET.SubElement(process_strukturerat, "nivå1").text = str(basmetadata['value']['nivå1'])
    ET.SubElement(process_strukturerat, "nivå2").text = str(basmetadata['value']['nivå2'])
    ET.SubElement(process_strukturerat, "nivå3").text = str(basmetadata['value']['nivå3'])
    ET.SubElement(dokument, "Ursprung").text = str(basmetadata['value']['ursprung'])
    ET.SubElement(dokument, "Arkiveringsdatum").text = formatted_date
    ET.SubElement(dokument, "Sekretess").text = str(basmetadata['value']['sekretess'])
    ET.SubElement(dokument, "Personuppgifter").text = str(basmetadata['value']['personuppgifter'])
    ET.SubElement(dokument, "Forskningsdata").text = str(basmetadata['value']['forskningsdata'])
    ET.SubElement(dokument, "Site").text = get_domain_from_url(url)
    ET.SubElement(dokument, "Webbsida").text = webbsida
    ET.SubElement(dokument, "Webbadress").text = url
    title, keywords, description = get_webpage_metadata(url, driver)
    ET.SubElement(dokument, "WebPageTitle").text = title
    ET.SubElement(dokument, "WebPageKeywords").text = keywords
    ET.SubElement(dokument, "WebPageDescription").text = description
    ET.SubElement(dokument, "WebPageCurrentURL").text = url
    ET.SubElement(dokument, "Informationsdatum").text = formatted_date
    ET.SubElement(dokument, "Kommentar").text = str(basmetadata['value']['kommentar'])
    ET.SubElement(root, "DokumentFilnamn").text = tiff_image_name

    declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_string = declaration + ET.tostring(root, encoding="utf-8", method="xml").decode()

    dom = xml.dom.minidom.parseString(xml_string)

    formatted_xml = dom.toprettyxml(indent="  ", encoding="UTF-8").decode("UTF-8")

    xml_file_path = folder_name + "/" + xml_file_name
    with open(xml_file_path, "w", encoding="utf-8") as file:
        file.write(formatted_xml)


def validate_xml(xml_file, xsd_file):
    try:
        with open(xml_file, 'rb') as file:
            xml_doc = etree.parse(file, parser=etree.XMLParser(encoding='utf-8'))
        schema = etree.XMLSchema(file=xsd_file)
        schema.assertValid(xml_doc)
        print("Validation successful.")
        return True

    except etree.XMLSyntaxError as e:
        print(f"XML syntax error: {e}")
    except etree.DocumentInvalid as e:
        print(f"Validation error: {e}")
    return False


def login_to_instagram(driver):
    instagram_user = os.getenv("instagram_user")
    instagram_password = os.getenv("instagram_password")
    driver.get(const.PATH_TO_INSTAGRAM)
    seconds_to_wait_for_page_to_load = 10
    driver.implicitly_wait(seconds_to_wait_for_page_to_load)

    try:
        driver.find_element(By.XPATH, const.INSTAGRAM_COOKIE_BANNER).click()
    except Exception as e:
        print(f"Error click button cookies: {e}")

    input_field = driver.find_element(By.NAME, "username")
    input_field.clear()
    input_field.send_keys(instagram_user)

    password_field = driver.find_element(By.NAME, "password")
    password_field.clear()
    password_field.send_keys(instagram_password)

    driver.find_element(By.XPATH, const.INSTAGRAM_LOGIN_BUTTON).click()


def login_to_linkedin(driver):
    linkedin_user = os.getenv("linkedin_user")
    linkedin_password = os.getenv("linkedin_password")
    driver.get(const.PATH_TO_LINKEDIN)
    seconds_to_wait_for_page_to_load = 10
    seconds_to_wait_item_present = 10
    driver.implicitly_wait(seconds_to_wait_for_page_to_load)

    try:
        accept_button = WebDriverWait(driver, seconds_to_wait_item_present).until(
            EC.element_to_be_clickable((By.XPATH, const.LINKEDIN_ACCEPT_BUTTON1))
        )
        accept_button.click()
    except Exception as e:
        print(f"Error: {e}")

    input_field = driver.find_element(By.ID, "username")
    input_field.clear()
    input_field.send_keys(linkedin_user)

    password_field = driver.find_element(By.ID, "password")
    password_field.clear()
    password_field.send_keys(linkedin_password)

    login_button = WebDriverWait(driver, seconds_to_wait_item_present).until(
        EC.element_to_be_clickable((By.XPATH, const.LINKEDIN_LOGIN_BUTTON))
    )
    login_button.click()

    try:
        accept_button = WebDriverWait(driver, seconds_to_wait_item_present).until(
            EC.element_to_be_clickable((By.XPATH, const.LINKEDIN_ACCEPT_BUTTON2))
        )
        accept_button.click()
    except Exception as e:
        print(f"Error: {e}")


def login_to_facebook(driver):
    facebook_user = os.getenv("facebook_user")
    facebook_password = os.getenv("facebook_password")
    driver.get(const.PATH_TO_FACEBOOK)
    driver.maximize_window()
    seconds_to_wait_for_page_to_load = 20
    seconds_to_wait_item_present = 10
    driver.implicitly_wait(seconds_to_wait_for_page_to_load)

    try:
        wait = WebDriverWait(driver, seconds_to_wait_item_present)
        cookie_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, const.FACEBBOK_COOKIE_BANNER)
        ))

        actions = ActionChains(driver)
        actions.move_to_element(cookie_button).click().perform()
        print("Cookies consent button clicked successfully using ActionChains!")

    except Exception as e:
        print(f"Error clicking the button: {e}")

    try:
        email_input = driver.find_element(By.ID, "email")
        email_input.clear()
        email_input.send_keys(facebook_user)

        password_input = driver.find_element(By.ID, "pass")
        password_input.send_keys(facebook_password)

        password_input.send_keys(Keys.RETURN)

    except Exception as e:
        print(f"Error: {e}")

    try:
        wait = WebDriverWait(driver, seconds_to_wait_item_present)
        cookie_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, const.FACEBBOK_COOKIE_BANNER)
        ))
        actions = ActionChains(driver)
        actions.move_to_element(cookie_button).click().perform()
        print("Cookies consent button clicked successfully using ActionChains!")

    except Exception as e:
        print(f"Error clicking the button: {e}")


def capture_full_page_screenshot_with_custom_width(output_path, width_of_screenshot, driver, type_of_web_extraction):
    seconds_to_wait_for_page_to_load = 5
    seconds_to_wait_item_present = 10
    try:
        WebDriverWait(driver, seconds_to_wait_item_present).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
    except Exception as e:
        print(f"Error during page load: {e}")

    match type_of_web_extraction.lower():
        case "gislaved.se":
            try:
                driver.find_element(By.XPATH, const.GISLAVED_SE_COOKIE_BUTTON).click()
            except Exception as e:
                print(f"Error click button cookies: {e}")
        case "linkedin":
            try:
                dismiss_button = WebDriverWait(driver, seconds_to_wait_item_present).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, const.LINKEDIN_REJECT_BUTTON))
                )
                dismiss_button.click()

            except Exception as e:
                print(f"Error: {e}")
        case "instagram":
            try:
                element = driver.find_element(By.XPATH, const.INSTAGRAM_LOGIN_BANNER)
                actions = ActionChains(driver)
                actions.move_to_element(element).click().perform()
            except Exception as e:
                print(f"Error click  login button s: {e}")

    driver.implicitly_wait(seconds_to_wait_for_page_to_load)
    page_height = driver.execute_script("return document.documentElement.scrollHeight")
    driver.set_window_size(width_of_screenshot, page_height)
    driver.save_screenshot(output_path)
    print(f"Saved screenshot to {output_path}")


def create_tiff_screenshot(url, folder_name, width_of_screenshot, driver, type_of_web_extraction):
    filename = create_file_name(url)
    print(f"Processing {filename}")
    output_path_png = "image_temp/" + filename + '.png'
    tiff_image_name = filename + '.tif'
    output_path_tiff = folder_name + "/" + tiff_image_name

    capture_full_page_screenshot_with_custom_width(output_path_png, width_of_screenshot, driver, type_of_web_extraction)

    convert_png_to_tiff(output_path_png, output_path_tiff)
    return tiff_image_name


def create_package_creator_config(basmetadata, folder_name, schema, contract, systemnamn):
    arkivbildare = str(basmetadata['value']['arkivbildare'])
    first_part_of_arkivbildare = get_part_of_string(arkivbildare, "(", 0)
    arkivbildare_cleaned = replace_unwanted_chars(first_part_of_arkivbildare, '')

    ursprung = str(basmetadata['value']['ursprung'])
    systemnamn = systemnamn if systemnamn.strip() else ursprung
    systemnamn_cleaned = replace_unwanted_chars(systemnamn, '')

    config_data = [("Agent 1 Namn", arkivbildare),
                   ("Agent 1 Kommentar", "ORG:212000-0514"),
                   ("Agent 2 Namn", systemnamn),
                   ("Agent 3 Namn", arkivbildare),
                   ("Leverans", "Gislaved-webb-1"),
                   ("Arkivbildare", arkivbildare_cleaned),
                   ("Systemnamn", systemnamn_cleaned),
                   ("Schema", schema),
                   ("Contract", contract)]

    package_creator_workbook = Workbook()
    package_creator_active_sheet = package_creator_workbook.active
    for row in config_data:
        package_creator_active_sheet.append(row)

    config_file_path = folder_name + "\\Package-Creator-Metadata.xlsx"
    package_creator_workbook.save(config_file_path)


def run_web_extraction(pages_to_crawl_file, basmetadata_file, width_of_screenshot, headless_for_full_height, type_of_web_extraction, xsd_file, contract, systemnamn):
    pages_as_lists = pd.read_excel(pages_to_crawl_file, sheet_name=0).fillna("").values.tolist()

    basmetadata = pd.read_excel(basmetadata_file, sheet_name=0, index_col=0)
    basmetadata = prepare_and_clean_columns_and_index(basmetadata)

    today = datetime.now()
    formatted_date = today.strftime('%Y-%m-%d')
    formatted_date_time = today.strftime('%Y-%m-%d-%H-%M-%S')

    folder_name = "files for package creator " + formatted_date_time
    os.mkdir(folder_name)

    if not os.path.isdir(const.PATH_TO_IMAGE_TEMP):
        os.mkdir(const.PATH_TO_IMAGE_TEMP)

    options = Options()
    options.add_argument(f"--window-size={width_of_screenshot},1080")
    options.add_argument("--disable-gpu")  # Disable GPU acceleration for stability
    options.add_argument("--no-sandbox")   # Required for some environments like Docker

    if headless_for_full_height:
        options.add_argument("--headless")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.maximize_window()

    match type_of_web_extraction.lower():
        case "facebook":
            login_to_facebook(driver)
        case "linkedin":
            login_to_linkedin(driver)
        case "instagram":
            login_to_instagram(driver)

    xml_valid = True
    for url_and_metadata_for_website in pages_as_lists:
        if xml_valid:
            url = url_and_metadata_for_website[0]
            driver.get(url)
            tiff_image_name = create_tiff_screenshot(url, folder_name, width_of_screenshot, driver, type_of_web_extraction)
            print(f"converted to tif {tiff_image_name}")

            xml_file_name = get_part_of_string(tiff_image_name, ".", 0) + ".xml"
            create_xml_fgs(url_and_metadata_for_website, formatted_date, xml_file_name, tiff_image_name, folder_name, basmetadata, driver)

            print(xml_file_name)
            xml_file_path = folder_name + "/" + xml_file_name
            xml_valid = validate_xml(xml_file_path, xsd_file)

        else:
            print(f"xml not valid {xml_file_path}")

    driver.quit()
    create_package_creator_config(basmetadata, folder_name, xsd_file, contract, systemnamn)


if __name__ == "__main__":
    # Config section ###################################################################

    # Create a .env file and put your social media usernamnes and password there.
    # load_dotenv()
    # instagram_user = os.getenv("instagram_user")
    # instagram_password = os.getenv("instagram_password")
    # linkedin_user = os.getenv("linkedin_user")
    # linkedin_password = os.getenv("linkedin_password")
    # facebook_user = os.getenv("facebook_user")
    # facebook_password = os.getenv("facebook_password")

    # type_of_web_extraction = "gislaved.se"
    # gislaved.se
    # insidan.gislaved.se
    # Facebook
    # LinkedIn
    # Instagram

    width_of_screenshot = 1920
    headless_for_full_height = True  # Adjust this to true to get full height. False för debugging to see how buttons are clicked
    xsd_file = "FREDA-GS-Webbsidor-v1_0.xsd"  # XSD file for validation of FGS. Change to your own XSD.
    contract = "Contract_2020-02-24-13-03-23-WEB.xml"  # contract file for LTA upload
    systemnamn = "Webbsidor"  # If you want package creator systemnamn to be the basmetadata "Ursprung" instead set this to empty string ("")

    # Load the Excel file with a list of web pages for the current run
    pages_to_crawl_file = 'pages_gislaved_se_extern_webb.xlsx'
    # The following is the the two columns of the pages excel.
    # Webbadress	Webbsida
    # The first is the url to be crawled
    # The second is a short description of the url that goes in the FGS node webbsida

    basmetadata_file = 'basmetadata_extern_webb.xlsx'
    # The following is the first column of the excel with basmetadata. The second column is for the values
    # Basmetadata
    # Organisation
    # Arkivbildare
    # Arkivbildarenhet
    # Arkiv
    # Serie
    # Klassificeringsstruktur
    # nivå1
    # nivå2
    # nivå3
    # Ursprung
    # Sekretess
    # Personuppgifter
    # Forskningsdata
    # Kommentar

    # End config section #############################################################

    print("Welcome to Mediahanteraren")

    while True:
        print("************************************")
        print("Type 'Exit' to quit at any time.")
        print("Type 'Run' to run the program")
        print("Type 1 to toogle Headless setting")
        print("************************************")
        user_input = input("Enter a chooise:")

        match user_input.lower():
            case "1":
                headless_for_full_height = not headless_for_full_height
                print(f"Headless = {headless_for_full_height}")
            case "exit":
                print("Goodbye!")
                break
            case "run":
                print("************************************")
                print("Type 1 for gislaved.se")
                print("Type 2 for insidan.gislaved.se")
                print("Type 3 for Facebook")
                print("Type 4 for LinkedIn")
                print("Type 5 for Instagram")
                print("************************************")
                type_of_web_extraction_input = input("What typ of webextraction do you want run?")
                match type_of_web_extraction_input:
                    case "1":
                        type_of_web_extraction = "gislaved.se"
                    case "2":
                        type_of_web_extraction = "insidan.gislaved.se"
                    case _:
                        type_of_web_extraction = "Not a correct chooise"
                
                if type_of_web_extraction != "Not a correct chooise":
                    print(f"Your current pages to crawl file is: {pages_to_crawl_file}")
                    answer_pages_to_crawl = input("do you want to change it y/n?")
                    if answer_pages_to_crawl == "y":
                        pages_to_crawl_file = input("Enter your new file?")
                    run_web_extraction(pages_to_crawl_file, basmetadata_file, width_of_screenshot, headless_for_full_height, type_of_web_extraction, xsd_file, contract, systemnamn)
                else:
                    print("You did not choose a correct webextraction type")


