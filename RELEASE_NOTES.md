'''

Release notes

================================================================================

v1.0.0 Initial Release

* A python script to harvest screenshots from **websites and social media** and prepare them for archiving in the **E-archive LTA**.


* Takes screenshots of webpages or social media as **tiff** which is an archiveable image format.

* Creates XML with metadata to each screenshot in **FGS archive XML** format.

* The **FGS XML structure** is based on **FREDA which is an E-archive cooperation with municipalities in Jönköpings Län**.

* Some of the **metadata** in the **FGS XML** comes from an **excel file (Basemetadata)** and others are extracted from **the current crawled website**.

* Validates the FGS XML with .XSD file with the structure of **FREDA FGS XML for Websites**.

* Creates a file **Package-Creator-Metadata.xlsx** that is to be used by another script or process to build the final package with 
LTA:s software **Package Creator**.

* See README.md for installation and usage

* Future Enhancements: add extraction from Facebook from local downloaded files instad of online.



'''
