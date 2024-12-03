# About
> A python script to harvest screenshoots from **websites and social media** and prepare them for archiving in the **E-archive LTA**.
> 
# Features
>Takes screenshoots of webpages or social media as **tiff** which is a archiveable image format.
>
>Creates XML with metadata to each screenshoot in **FGS archive XML** format.
>
>The **FGS XML structure** is based on **FREDA which is an E-archive cooperation with municipalities in Jönkpings Län**.
>
>Some of the **metadata** in the **FGS XML** comes from an **excel file (Basmetadata)** and others are extracted from **the current crawled website**.
>
>Validates the FGS XML with .XSD file whith the structur of **FREDA FGS XML for Websites**.
>
>Creates a file **Package-Creator-Metadata.xlsx** that is to be used by another script or process to build the final package with LTA:s software **Package Creator**.
>
# Installation


# Prerequisites
The application needs to be run on a Windows machine capable of running Python 3.
 

#### Python Modules
The following modules needs to be installed.
 
Install them using pip by typing the following in the terminal.
 
See https://pip.pypa.io/en/stable/installation/ for help installing pip.
 
>python -m pip install Pillow
>python -m pip install pandas
>python -m pip install lxml
>python -m pip install selenium
>python -m pip install webdriver-manager
>python -m pip install openpyxl

# Usage
>Open **Spyder** (comes with **Anaconda**)
>
>Open the python file **archiving-of-web-and-social-media.py** in **Spyder**
>
>Set the data in the **config section** in the python file **archiving-of-web-and-social-media.py**
>
>There is already **sample data and a config setting** that works out of the box
>but you need to put **your own settings** in the config section for your purpose.
>See the configuration section in this readme for more information about the settings.
>
>Run the python script in **Spyder**
>
# Configuration
>There is already sample data and a config setting that works out of the box but you need to put your own settings in the config section which is found in the main function in the python script.
>
>**width** = 1920 # width of the screenshot
>
>**instagram_user** = "your instagram user"
>
>**instagram_password** = "your instagram password"
>
>**linkedin_user** = "your linkin user"
>
>**linkedin_password** = "your linkedin password"
>
>**facebook_user** = "your facebook user"
>
>**facebook_password** = "your facebook password"
>
>**type_of_web_extraction** = 1  Select 1-5 for different types of web extractions.
>
>You probably have to adjust the button clicks in the code to adjust to the webpage you are crawling.
>The button clicks on these types is set for example to the current cookie banner that needs to be clicked. This might change over time when websites are uppdated. That requieres changes in the code not in the configuration settings.
>
>1 is External web gislaved.se   
>
>2 is Internal web insidan.gislaved.se
>
>3 is Facebook
>
>4 is LinkedIn
>
>5 is Instagram
>
>**headless** = True or False : Adjust this to true to get full height. False för debugging to see how buttons are clicked but then full height is not saved in the screenshoot.
>
>**xsd_file** = "FREDA-GS-Webbsidor-v1_0.xsd" XSD file for validation of FGS change to your own.
>
>**contract** = "Contract_2020-02-24-13-03-23-WEB.xml" contract file for LTA upload.
>
>Load the Excel file with a list of web pages for the current run.
>
>**pages** = pd.read_excel('**pages_gislaved_se_extern_webb.xlsx**', sheet_name='webpage')
>
>The following is the two columns of the pages excel.
>
>**Webbadress	Webbsida**
>
>The first is the url to be crawled.
>The second is a short description of the url that goes in the FGS node webbsida.
>
>load the excel file with a list of basmetadata for the  current run.
>
>**basmetadata** = pd.read_excel('**basmetadata_extern_webb.xlsx**', sheet_name='basmetadata')
>
>The following is the first column of the excel with basmetadata. The second column is for the values.
>
>**Basmetadata**
>
>Organisation
>
>Arkivbildare
>
>Arkivbildarenhet
>
>Arkiv
>
>Serie
>
>Klassificeringsstruktur
>
>nivå1
>
>nivå2
>
>nivå3
>
>Ursprung
>
>Sekretess
>
>Personuppgifter
>
>Forskningsdata
>
>Kommentar
 
# License
This project is licensed under the GPL3 License. See the [LICENSE](LICENSE.txt) file for more information.  

# Contributing
Contributions are welcome! 


