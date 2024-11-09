# -*- coding: utf-8 -*-
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
import requests
from urllib.parse import urlparse
from openpyxl import Workbook
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


def get_webpage_metadata(url,option,driver):
    # Depending on the option this gets different metadata from the url 
    
    # Open the web page
    driver.get(url)
    
    # Swithc the different options
    if option == 1: # get the metadata "Title"
        return_value = driver.title
    elif option == 2: # get the metadata "keywords
        try:
            # Find the meta tag with the name 'keywords'
            meta_tags = driver.find_elements(By.TAG_NAME, "meta")
    
            keywords = None
            # Iterate through all meta tags to find one with name="keywords" (case-insensitive)
            for tag in meta_tags:
                name_attr = tag.get_attribute("name")
                if name_attr and name_attr.lower() == "keywords":
                    keywords = tag.get_attribute("content")
                    break
            
            #print("Keywords:", keywords)
            if keywords == None:
                return_value = "Inga Keywords specificerade för denna webbsida"
            else:
                return_value = keywords
        except Exception as e:
            print("Keywords meta tag not found or an error occurred:", e)
            return_value = "Inga Keywords specificerade för denna webbsida"
            
    elif option == 3: # get the metadata "Description"
        try:
            # Get all meta tags
            meta_tags = driver.find_elements(By.TAG_NAME, "meta")
            
            description = None
            # Iterate through all meta tags to find one with name="description" (case-insensitive)
            for tag in meta_tags:
                name_attr = tag.get_attribute("name")
                if name_attr and name_attr.lower() == "description":
                    description = tag.get_attribute("content")
                    break
            
            if description:
                return_value = description
            else:
                return_value = "Ingen beskrivning specificerad för denna webbsida"
        except Exception as e:
            print("An error occurred:", e)
            return_value = "Ingen beskrivning specificerad för denna webbsida"
    
    #return_value = re.sub('[&]', "_", return_value) 
    print("returnvalue is:", return_value)
    # Close the browser
    #driver.quit()
    return return_value

def get_site(url): # get the domain from the url ex. www.gislaved.se/somepage.html is www.gislaved.se
    parsed_url = urlparse(url)
    domain_with_subdomain = parsed_url.netloc
    print(f"domain is {domain_with_subdomain}")
    return domain_with_subdomain

def create_xml_fgs(row, formatted_date, xml_file_name, tiff_image_name, folder_name, basmetadata_as_lists, driver):
    # Create XML data for FGS Webbsidor
    url = row[0]
    webbsida_text = row[1]
    #clean_url = url.replace("&","")
    root = ET.Element("Leveransobjekt", attrib={"xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",  "xsi:noNamespaceSchemaLocation": "FREDA-GS-Webbsidor-v1_0.xsd",  "xmlns": "freda"})
    dokument = ET.SubElement(root, "Dokument")
    
    # Get the basmetadata from the excel list
    for basmetadata_row in basmetadata_as_lists:
        print(basmetadata_row[0])
        print(basmetadata_row[1])
        if basmetadata_row[0] == "Organisation":
            organisation_text = basmetadata_row[1]
        elif basmetadata_row[0] == "Arkivbildare":
            arkivbildare_text = basmetadata_row[1]
        elif basmetadata_row[0] == "Arkivbildarenhet":
            arkivbildareenhet_text= basmetadata_row[1]
        elif basmetadata_row[0] == "Arkiv":
            arkiv_text= basmetadata_row[1]
        elif basmetadata_row[0] == "Serie ":
            serie_text= basmetadata_row[1]
        elif basmetadata_row[0] == "Klassificeringsstruktur":
            klassificeringsstruktur_text= basmetadata_row[1]
        elif basmetadata_row[0] == "nivå1":
            niva1_text= str(basmetadata_row[1])
        elif basmetadata_row[0] == "nivå2":
            niva2_text= str(basmetadata_row[1])
        elif basmetadata_row[0] == "nivå3":
            niva3_text= str(basmetadata_row[1])
        elif basmetadata_row[0] == "Ursprung":
            ursprung_text= basmetadata_row[1]
        elif basmetadata_row[0] == "Sekretess":
            sekretess_text= str(basmetadata_row[1])
        elif basmetadata_row[0] == "Personuppgifter":
            personuppgifter_text= str(basmetadata_row[1])
        elif basmetadata_row[0] == "Forskningsdata":
            forskningsdata_text= str(basmetadata_row[1])
        elif basmetadata_row[0] == "Kommentar":
            kommentar_text= basmetadata_row[1]

    # Set all the nodes in the FGS XML
    organisation = ET.SubElement(dokument, "Organisation")
    organisation.text   = organisation_text
    
    arkivbildare = ET.SubElement(dokument, "Arkivbildare")
    arkivbildare.text = arkivbildare_text
    
    arkivbildarenhet = ET.SubElement(dokument, "Arkivbildarenhet")
    arkivbildarenhet.text = arkivbildareenhet_text
    
    arkiv = ET.SubElement(dokument, "Arkiv")
    arkiv.text = arkiv_text
    
    serie = ET.SubElement(dokument, "Serie")
    serie.text = serie_text
    
    klasstrukt = ET.SubElement(dokument, "KlassificeringsstrukturText")
    klasstrukt.text = klassificeringsstruktur_text
    
    process_strukturerat = ET.SubElement(dokument, "ProcessStrukturerat")

    niva1 = ET.SubElement(process_strukturerat, "nivå1")
    niva1.text = niva1_text  
    
    niva2 = ET.SubElement(process_strukturerat, "nivå2")
    niva2.text = niva2_text
    
    niva3 = ET.SubElement(process_strukturerat, "nivå3")
    niva3.text = niva3_text   
    
    ursprung = ET.SubElement(dokument, "Ursprung")
    ursprung.text = ursprung_text
    
       
    datum = ET.SubElement(dokument, "Arkiveringsdatum")
    datum.text = formatted_date
    
    sekretess = ET.SubElement(dokument, "Sekretess")
    sekretess.text = sekretess_text
        
    personuppgifter = ET.SubElement(dokument, "Personuppgifter")
    personuppgifter.text = personuppgifter_text
    
    forskningsdata = ET.SubElement(dokument, "Forskningsdata")
    forskningsdata.text = forskningsdata_text
    
    domain = get_site(url) # get the domain from the url ex. www.gislaved.se/somepage.html blir www. gislaved.se
    site = ET.SubElement(dokument, "Site")
    site.text = domain 
    
    print(webbsida_text)
    webbsida = ET.SubElement(dokument, "Webbsida")
    webbsida.text = webbsida_text
     
    webbadress = ET.SubElement(dokument, "Webbadress")
    webbadress.text =  url
    
    title = get_webpage_metadata(url,1,driver) # get the metadata "Title" from the HTML in the current webpage
    web_page_title = ET.SubElement(dokument, "WebPageTitle")
    web_page_title.text = title
    
    keywords = get_webpage_metadata(url,2,driver) # Get the metadata "Keywords" from the HTML in the current webpage
    web_page_keywords = ET.SubElement(dokument, "WebPageKeywords")
    web_page_keywords.text =  keywords
    
    description  = get_webpage_metadata(url,3,driver) # Get the metadata "Description" from the HTML in the current webpage
    web_page_description = ET.SubElement(dokument, "WebPageDescription")
    web_page_description.text = description
    
    web_page_current_url = ET.SubElement(dokument, "WebPageCurrentURL")
    web_page_current_url.text =  url
   
    informationsdatum = ET.SubElement(dokument, "Informationsdatum")
    informationsdatum.text = formatted_date
    
    kommentar = ET.SubElement(dokument, "Kommentar")
    kommentar.text = kommentar_text
    
    dokument_filnamn = ET.SubElement(root, "DokumentFilnamn")
    dokument_filnamn.text = tiff_image_name      
   
    # Create an ElementTree object with the XML declaration
    declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_string = declaration + ET.tostring(root, encoding="utf-8", method="xml").decode()
    
    dom = xml.dom.minidom.parseString(xml_string)
    
    formatted_xml = dom.toprettyxml(indent="  ", encoding="UTF-8").decode("UTF-8")
    # Create a string representation of the XML with formatting
    
    # Save the formatted XML to a file
    #file_path = output_folder.get()
    #file_path = f"{file_path}\{filename_new}.xml"
    xml_file_path = folder_name + "/" + xml_file_name
    with open(xml_file_path, "w", encoding="utf-8") as file:
        file.write(formatted_xml)    

def validate_xml(xml_file, xsd_file):
    try:
        # Parse XML
        with open(xml_file, 'rb') as file:
            xml_doc = etree.parse(file, parser=etree.XMLParser(encoding='utf-8'))
            
        # Load XSD schema
        schema = etree.XMLSchema(file=xsd_file)

        # Validate XML against the schema
        schema.assertValid(xml_doc)

        print("Validation successful.")
        return True

    except etree.XMLSyntaxError as e:
        print(f"XML syntax error: {e}")
        return False
    except etree.DocumentInvalid as e:
        print(f"Validation error: {e}")
        # return False


def login_to_instagram(driver, instagram_user, instagram_password):
    
    # Navigate to the webpage
    driver.get("https://www.instagram.com")  
    
    # Wait for the page to load (implicitly waits for 10 seconds)
    driver.implicitly_wait(10)
    
    try: # try to click the cookies button
        button = driver.find_element(By.XPATH, "//button[contains(@class, '_a9--') and text()='Tillåt alla cookies']")
        button.click()
    except Exception as e:
        print(f"Error click button cookies: {e}")
    
    # Locate the input field by its name or aria-label
    input_field = driver.find_element(By.NAME, "username")  # You can also use XPATH or other methods if necessary
    
    # Clear the input field (optional)
    input_field.clear()
    
    # Type the desired text into the input field
    input_field.send_keys(instagram_user)  
    
    password_field = driver.find_element(By.NAME, "password")  # You can use other attributes like XPath if needed

    # Clear the field (optional)
    password_field.clear()
    
    # Input the password
    password_field.send_keys(instagram_password)  
    
    login_button = driver.find_element(By.XPATH, "//div[contains(text(), 'Logga in')]")

    # Click the button
    login_button.click()

def login_to_linkedin(driver, linkedin_user, linkedin_password):
    
    # Navigate to the webpage
    driver.get("https://www.linkedin.com/login/sv?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin")  # Replace with the actual URL where the input field exists
    
    # Wait for the page to load (implicitly waits for 10 seconds)
    driver.implicitly_wait(10)
     
    try:
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[text()="Acceptera"]'))
        )
        accept_button.click()
    except Exception as e:
        print(f"Error: {e}")
    
    # Locate the input field by its name or aria-label
    input_field = driver.find_element(By.ID, "username")  # You can also use XPATH or other methods if necessary
    
    # Clear the input field
    input_field.clear()
    
    # set linkedin username
    input_field.send_keys(linkedin_user)  #

    password_field = driver.find_element(By.ID, "password")  # You can use other attributes like XPath if needed

    # Clear the field 
    password_field.clear()
    
    # Input the password
    password_field.send_keys(linkedin_password)  
    
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Logga in"]'))
    )

    # Click the button
    login_button.click()

    try:
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[text()="Acceptera"]'))
        )
        # Click on the parent button by clicking the span element
        accept_button.click()
    except Exception as e:
        print(f"Error: {e}")
        
def login_to_facebook(driver, facebook_user, facebook_password):
    
    # Navigate to the webpage
    driver.get("https://www.facebook.com/")  
    
    driver.maximize_window()
    
    # Wait for the page to load (implicitly waits for 10 seconds)
    driver.implicitly_wait(20)
    
              
    try:
        # Use WebDriverWait to wait for the button to be present in the DOM
        wait = WebDriverWait(driver, 10)  # Wait for up to 10 seconds
        cookie_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//span[text()='Tillåt alla cookies']")
        ))
    
        # Create an instance of ActionChains
        actions = ActionChains(driver)
    
        # Move to the button and click it
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
        # Wait until the element is located in the DOM (can be hidden initially)
        wait = WebDriverWait(driver, 10)
        cookie_button = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//span[text()='Tillåt alla cookies']")
        ))
    
        # Create an ActionChains instance
        actions = ActionChains(driver)
    
        # Move to the element and click using ActionChains
        actions.move_to_element(cookie_button).click().perform()
    
        print("Cookies consent button clicked successfully using ActionChains!")
    
    except Exception as e:
        print(f"Error clicking the button: {e}")

def capture_full_page_screenshot_with_custom_width(output_path, width, driver, type_of_web_extraction):
    # capture fullscreen png screen shot
    # different buttons need to be clicked when making screenshoots of differnt webpages and social media 
    # when updates are made on the webpages the way buttons are clicked needs to be updated in this code
    
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
    except Exception as e:
        print(f"Error during page load: {e}")

    # 1 is External web gislaved.se 
    # 2 is Internal web insidan.gislaved.se
    # 3 is Facebook
    # 4 is LinkedIn
    # 5 is Instagram
    if type_of_web_extraction == 1:
        #1 is External web gislaved.se 
        try: # try to click the cookies button för gislaved.se
            button = driver.find_element(By.XPATH, "//button[contains(@class, 'env-button--primary') and text()='Godkänn alla kakor']")
            button.click()
        except Exception as e:
            print(f"Error click button cookies: {e}")
            
    #elif type_of_web_extraction ==2:
        #2 is Internal web insidan.gislaved.se
    #elif type_of_web_extraction ==3:
        # 3 is Facebook
    elif type_of_web_extraction == 4:
        try:
            # Wait for the button to be clickable (using aria-label)
            dismiss_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Avvisa"]'))
            )
            # Click the button
            dismiss_button.click()
        
        except Exception as e:
            print(f"Error: {e}")

    
    elif type_of_web_extraction ==5:
        #5 is Instagram
        try: # try to close the login bannar on instagram
            element = driver.find_element(By.XPATH, '//span[@aria-label="Stäng"]')
            
            # Use ActionChains to click
            actions = ActionChains(driver)
            actions.move_to_element(element).click().perform()
        except Exception as e:
            print(f"Error click  login button s: {e}")
        

    # Section with buttons the could be useful depending on changes in the user interface of the crawled sites
    """
    try:
        close_svg = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//svg[@aria-label="Stäng"]'))
        )
        # Click on the SVG element
        close_svg.click()
    except Exception as e:
        print(f"Error: {e}")
    """
    
    """
    try: # try to click the cookies button
        button = driver.find_element(By.XPATH, "//button[contains(@class, '_a9--') and text()='Tillåt alla cookies']")
        button.click()
    except Exception as e:
        print(f"Error click button cookies: {e}")
    """
    """
    try: # try to click the cookies button
        button = driver.find_element(By.XPATH, "//a[contains(text(), 'Logga in')]")
        button.click()
    except Exception as e:
        print(f"Error click  login button s: {e}")
    """

    driver.implicitly_wait(5)
    
    # Get the page's full height    
    page_height = driver.execute_script("return document.documentElement.scrollHeight")
    
    # Resize the window to the full page height
    driver.set_window_size(width, page_height)
    
    # Take a screenshot
    driver.save_screenshot(output_path)
    
    # Close the browser
    #driver.quit()
    print(f"Saved screenshot to {output_path}")

    
def convert_png_to_tiff(input_path_png, output_path_tiff):
    # Open the PNG image and convert it to TIFF
    image = Image.open(input_path_png)
    image.save(output_path_tiff, format='TIFF')

def create_tiff_screenshot(url, formatted_date_file, folder_name, width, driver, type_of_web_extraction):
    print(url)
    filename = url[:50] if isinstance(url, str) else str(url)[:20] # get the 50 first chars from the web page url
    cleaned_filename = filename.split("//")[1] # clean the url from the first part
    cleaned_filename = re.sub('[^a-zA-Z]', "_", cleaned_filename)  # clean unwanted chars from the filename
    cleaned_filename = cleaned_filename + "_" + formatted_date_file # add the current date and time to get a unic filename
    
    print(f"Processing {cleaned_filename}")
    
    output_path_png = "image_temp/" + cleaned_filename + '.png' # set png in a temp folder
    tiff_image_name = cleaned_filename + '.tif'
    output_path_tiff = folder_name +"/" + tiff_image_name  # set the path form the tiff
    # Set desired width in pixels
    
    capture_full_page_screenshot_with_custom_width(output_path_png, width, driver, type_of_web_extraction) #t take the screenshot
    
    # Convert PNG to TIFF
    convert_png_to_tiff(output_path_png, output_path_tiff) # convert png to tiff
    return tiff_image_name

def create_package_creator_config(basmetadata_as_lists, folder_name,schema, contract):
    #This is used for creating a config file that the next process "Package creator" is using to creata zip file for the LTA archive
    for basmetadata_row in basmetadata_as_lists: # get some om the basmetadata to put in config file
        if basmetadata_row[0] == "Arkivbildare":
            arkivbildare_text = basmetadata_row[1]
        elif basmetadata_row[0] == "Ursprung":
            ursprung_text = basmetadata_row[1]
            
    arkivbildare_cleaned = arkivbildare_text.split("(")[0] # clean the arkivbildare from ending (aaa)
    arkivbildare_cleaned = re.sub('[^a-zA-Z]', '', arkivbildare_cleaned) # clean arkivbildare from everythhing but a-z
    
    systemnamn = "Webbsidor" # if you want the basmetadata "Ursprung" instead set this to ""
    if systemnamn:           #  "systemnamn" can be whatever you set it here if that is aproriate for package creator
        systemnamn_config = systemnamn 
    else:   
        systemnamn_config = ursprung_text  # otherwise it is from variable "Ursprung" if it is from a system like Castor
    
    systemnamn_config_cleaned = re.sub('[^a-zA-Z]', '', systemnamn_config)
    
    # List with config data
    data = [("Agent 1 Namn", arkivbildare_text), ("Agent 1 Kommentar", "ORG:212000-0514"), ("Agent 2 Namn", systemnamn_config), ("Agent 3 Namn", arkivbildare_text), ("Leverans", "Gislaved-webb-1"), ("Arkivbildare", arkivbildare_cleaned), ("Systemnamn", systemnamn_config_cleaned), ("Schema", schema),("Contract", contract)]
    
    # Create a workbook and select the active worksheet
    wb = Workbook()
    ws = wb.active
    
    # Write config data to the worksheet
    for row in data:
        ws.append(row)
    
    config_file_path = folder_name + "\Package-Creator-Metadata.xlsx"
    # Save the workbook
    wb.save(config_file_path)

def main():
    
    #Config section ###################################################################
    width = 1920 # width of the screenshot
    instagram_user = "your instagram user"
    instagram_password = "your instagram password"
    linkedin_user = "your linkin user"
    linkedin_password = "your linkedin password"
    facebook_user = "your facebook user"
    facebook_password = "your facebook password"
    type_of_web_extraction = 1  # 1 is External web gislaved.se 
                                # 2 is Internal web insidan.gislaved.se
                                # 3 is Facebook
                                # 4 is LinkedIn
                                # 5 is Instagram
                        
    headless = False # adjust this to true to get full height. False för debugging to see how buttons are clicked
    
    xsd_file = "FREDA-GS-Webbsidor-v1_0.xsd" #xsd file for validation of FGS change to your own 
    contract = "Contract_2020-02-24-13-03-23-WEB.xml" #contract file for LTA upload
 
    # Load the Excel file with a list of web pages for the current run
    pages = pd.read_excel('pages_gislaved_se_extern_webb.xlsx', sheet_name='webpage')
    # The following is the the two columns of the pages excel. 
    #Webbadress	Webbsida
    # The first is the url to be crawled
    # The second is a short descritio n of the url that goes in the FGS node webbsida
    
    # Convert the DataFrame to a list of lists (each list corresponds to a row)
    pages_as_lists = pages.values.tolist()

    # load the excel file with a list of basmetadata for the  current run
    basmetadata = pd.read_excel('basmetadata_extern_webb.xlsx', sheet_name='basmetadata')
    #The following is the first column of the excel with basmetadata. The second column is for the values 
    #Basmetadata
    #Organisation
    #Arkivbildare
    #Arkivbildarenhet
    #Arkiv
    #Serie 
    #Klassificeringsstruktur
    #nivå1
    #nivå2
    #nivå3
    #Ursprung
    #Sekretess
    #Personuppgifter
    #Forskningsdata
    #Kommentar

    # Convert the DataFrame to a list of lists (each list corresponds to a row)
    basmetadata_as_lists = basmetadata.values.tolist()

    #End config section #############################################################  
    

    today = datetime.now()
    # Format the date as 'YYYY-MM-DD'
    formatted_date = today.strftime('%Y-%m-%d')
    formatted_date_time = today.strftime('%Y %m %d %H %M') 
    
    # Directory name for the folder for the current run with the current date and time
    folder_name = "files for package creator " + formatted_date_time
    os.mkdir(folder_name) # Create the directory used for saving the images and xmls
    
    if os.path.isdir("image_temp"):
        print("Image temp folder exists.")
    else:
        print("Image temp folder does not exist. Creating the folder")
        os.mkdir("image_temp") # Create the folder for holding temporary image
    
    options = Options()
    options.add_argument(f"--window-size={width},1080")
    options.add_argument("--disable-gpu")  # Disable GPU acceleration for stability
    options.add_argument("--no-sandbox")   # Required for some environments like Docker
    #choose headless=false when testing the script to se that login and clicking buttons work
    #when running the real run use headlees=true otherwise the screenshoots will not be full height
    if headless:
        options.add_argument("--headless")      # Run Chrome in headless mode
    
    # Start Chrome WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.maximize_window()
    
    if type_of_web_extraction == 3:
        login_to_facebook(driver, facebook_user, facebook_password)   #use only when login to facebokk is nedded
    elif type_of_web_extraction == 4:
        login_to_linkedin(driver, linkedin_user, linkedin_password)   #use only when logim to linkedIn is nedded
    elif type_of_web_extraction == 5:
        login_to_instagram(driver, instagram_user, instagram_password)  #use only when login to instagram is needed
    
    xml_valid = True;
    for row in pages_as_lists: # loop all the web pages and create screenshots and FGS XML:s
        if xml_valid: # continue if last XML vas valid
            url= row[0]
            
            # create tiff file
            today = datetime.now()
            formatted_date_file = today.strftime('%Y-%m-%d-%H-%M-%S') # set the date to for the file name ending to create a unic name
            print(f"file date {formatted_date_file}")
            driver.get(url)
            tiff_image_name = create_tiff_screenshot(url, formatted_date_file, folder_name, width, driver, type_of_web_extraction)
            print(f"converted to tif {tiff_image_name}")
            
            # creat FGS XML
            name_splitted = tiff_image_name.split(".") # split the tiff name to get the first part
            xml_file_name = name_splitted[0] + ".xml" # get the first part of the tiff name to set the xml file name
            create_xml_fgs(row,formatted_date, xml_file_name, tiff_image_name, folder_name, basmetadata_as_lists, driver)
            
            # validate the XML against schema
            print(xml_file_name)
            xml_file_path = folder_name + "/" + xml_file_name
            xml_valid=validate_xml(xml_file_path, xsd_file)
            
        else:
            print(f"xml not valid {xml_file_path}")
    
    # create the config file for package creator
    driver.quit()
    create_package_creator_config(basmetadata_as_lists, folder_name, xsd_file, contract)


# Run the main function
main()



