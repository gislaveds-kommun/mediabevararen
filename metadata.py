import xml.etree.ElementTree as ET
import xml.dom.minidom
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Metadata:
    organisation: str
    arkivbildare: str
    arkivbildarenhet: str
    arkiv: str
    serie: str
    klassificeringsstrukturtext: str
    nivå1: str
    nivå2: str
    nivå3: str
    ursprung: str
    sekretess: str
    personuppgifter: str
    forskningsdata: str
    kommentar: str
    arkiveringsdatum: datetime
    site: str
    webbsida: str
    webbadress: str
    webpagetitle: str
    webpagekeywords: str
    webpagedescription: str
    webpagecurrenturl: str
    informationsdatum: datetime
    dokumentfilnamn: str

    def to_xml(self):
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

        ET.SubElement(document, "Organisation").text = str(self.organisation)
        ET.SubElement(document, "Arkivbildare").text = str(self.arkivbildare)
        ET.SubElement(document, "Arkivbildarenhet").text = str(self.arkivbildarenhet)
        ET.SubElement(document, "Arkiv").text = str(self.arkiv)
        ET.SubElement(document, "Serie").text = str(self.serie)
        ET.SubElement(document, "KlassificeringsstrukturText").text = str(self.klassificeringsstrukturtext)

        process_struct = ET.SubElement(document, "ProcessStrukturerat")
        ET.SubElement(process_struct, "nivå1").text = str(self.nivå1)
        ET.SubElement(process_struct, "nivå2").text = str(self.nivå2)
        ET.SubElement(process_struct, "nivå3").text = str(self.nivå3)

        ET.SubElement(document, "Ursprung").text = str(self.ursprung)
        ET.SubElement(document, "Arkiveringsdatum").text = self.arkiveringsdatum
        ET.SubElement(document, "Sekretess").text = str(self.sekretess)
        ET.SubElement(document, "Personuppgifter").text = str(self.personuppgifter)
        ET.SubElement(document, "Forskningsdata").text = str(self.forskningsdata)
        ET.SubElement(document, "Site").text = str(self.site)
        ET.SubElement(document, "Webbsida").text = str(self.webbsida)
        ET.SubElement(document, "Webbadress").text = str(self.webbadress)

        ET.SubElement(document, "WebPageTitle").text = str(self.webpagetitle)
        ET.SubElement(document, "WebPageKeywords").text = str(self.webpagekeywords)
        ET.SubElement(document, "WebPageDescription").text = str(self.webpagedescription)
        ET.SubElement(document, "WebPageCurrentURL").text = str(self.webpagecurrenturl)
        ET.SubElement(document, "Informationsdatum").text = self.informationsdatum
        ET.SubElement(document, "Kommentar").text = str(self.kommentar)

        ET.SubElement(root, "DokumentFilnamn").text = str(self.dokumentfilnamn)

        return root

    def save_xml_to_file(self, filepath):
        declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        root = self.to_xml()
        xml_string = declaration + ET.tostring(root, encoding="utf-8", method="xml").decode()

        dom = xml.dom.minidom.parseString(xml_string)
        formatted_xml = dom.toprettyxml(indent="  ", encoding="UTF-8").decode("UTF-8")

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(formatted_xml)
