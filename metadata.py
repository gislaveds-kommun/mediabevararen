from dataclasses import dataclass


@dataclass
class Metadata:
    organisation: str

    def to_xml(self):
        root = ET.Element(......)

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

        ET.SubElement(document, "Organisation").text = self.organisaton
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
        return root
    

    def save_xml_to_file(self, filepath):
        tree = etree.ElementTree(self.to_xml())
        tree.write(xml_file_path, encoding='UTF-8', xml_declaration=True, pretty_print=True)