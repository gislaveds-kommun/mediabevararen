# About
A python script to harvest screenshots from **websites and social media** and prepare them for archiving in the **E-archive LTA**.

# Features
Takes screenshots of webpages or social media as **tiff** which is an archiveable image format.

Creates XML with metadata to each screenshot in **FGS archive XML** format.

The **FGS XML structure** is based on **FREDA which is an E-archive cooperation with municipalities in Jönköpings Län**.

Some of the **metadata** in the **FGS XML** comes from an **excel file (Basemetadata)** and others are extracted from **the current crawled website**.

Validates the FGS XML with .XSD file with the structure of **FREDA FGS XML for Websites**.

Creates a file **Package-Creator-Metadata.xlsx** that is to be used by another script or process to build the final package with LTA:s software **Package Creator**.

# Installation


## Prerequisites
The application needs to be run on a Windows machine capable of running Python 3.
 

#### Python Modules
The following modules needs to be installed.
 
Install them using pip by typing the following in the terminal.
 
See https://pip.pypa.io/en/stable/installation/ for help installing pip.
 
```python -m pip install Pillow```

```python -m pip install pandas```

```python -m pip install lxml```

```python -m pip install selenium```

```python -m pip install webdriver-manager```

```python -m pip install openpyxl```

```python -m pip pip install python-dotenv```

# Usage
In the **configuration** section below you can see what configuration is needed.

In order to start the program in command line you navigate to the folder with the downloaded files and

then write the command: 
 
```python3 .\archiving-of-web-and-social-media.py```

In the command line menu in the started program you can change many settings and input data and then run the webextraction.

# Configuration
There are already sample data and config settings that work out of the box, except the **.env** that
is needed for usernames and passwords for social media accounts.

Settings are in the files .env , config.py and constants.py, the files are explained further down. 

There are two excel files with sample data and you can change these while the program is running as long as you use the same 
structure as the sample files. The structure is explained further down.

## The three settings files will be explained here: ###
### Credentials in .env 
Create a file and name it .env, with this content below, and put it in the main folder of the program.

```
instagram_user = "your instagram user"

instagram_password = "your instagram password"

linkedin_user = "your linkedin user"

linkedin_password = "your linkedin password"

facebook_user = "your facebook user"

facebook_password = "your facebook password"
```
### Config settings in config.py
These are default settings that can be changed in the menu while the program is running.

They do not need to be changed in the file unless you want new default settings.

### Constants in constants.py
These are settings that are used in the program but they can not be changed when the program is running.
 
There can be situations when these settings need to be changed.


Example of change: 

The current Facebook cookie banner makes the constant look like this

FACEBOOK_COOKIE_BANNER = "//span[text()='Tillåt alla cookies']"

If the banner is changed, the constant might also need to be modified accordingly.

## The structure of the input data excel files is explained here ###
### Sample excel file for pages ###

The excel file default_sample_pages.xlsx needs to have the following information:

The first column named **Webbadress** containing the url to be crawled

The second column named **Webbsida** containing a short description of the url and the program puts it into the FGS node webbsida.

### Sample excel file for basemetadata ###

The excel file default_sample_metadata.xlsx contains two columns - the first one is for the names and the second is for the values.

The first coulmn needs to be exactly like the list below to match the default xsd file. 

***Default sample metadata rows***
>-Organisation
>
>-Arkivbildare
>
>-Arkivbildarenhet
>
>-Arkiv
>
>-Serie
>
>-Klassificeringsstruktur
>
>-nivå1
>
>-nivå2
>
>-nivå3
>
>-Ursprung
>
>-Sekretess
>
>-Personuppgifter
>
>-Forskningsdata
>
>-Kommentar


The values in the second column need to match the validation criteria in the default xsd file

You can change the default xsd file while the program is running but then the metadata excel indata has to match the new xsd. 

# License
This project is licensed under the GPL3 License. See the [LICENSE](LICENSE.txt) file for more information.  

# Contributing
Contributions are welcome! 


