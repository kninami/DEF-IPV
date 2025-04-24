import sys
import base64
from PIL import Image, ExifTags
import xml.etree.ElementTree as ET

class MetadataExtractor:
    def __init__(self, image_path=None):
        self.image_path = image_path
        self.img = None
        
    def load_image(self, image_path=None):
        if image_path:
            self.image_path = image_path
        
        if not self.image_path:
            raise ValueError("Image path not provided")
            
        self.img = Image.open(self.image_path)
        return self
        
    def extract_metadata(self):
        if not self.img:
            self.load_image()
            
        width, height = self.img.size

        root = ET.Element('ImageMetadata')
        size_elem = ET.SubElement(root, 'Size')
        ET.SubElement(size_elem, 'Width').text = str(width)
        ET.SubElement(size_elem, 'Height').text = str(height)

        # DPI
        if 'dpi' in self.img.info:
            dpi_elem = ET.SubElement(root, 'DPI')
            dpi = self.img.info['dpi']
            ET.SubElement(dpi_elem, 'X').text = str(dpi[0])
            ET.SubElement(dpi_elem, 'Y').text = str(dpi[1])

        # ICC profile
        if 'icc_profile' in self.img.info:
            icc_elem = ET.SubElement(root, 'ICCProfile')
            icc_elem.text = base64.b64encode(self.img.info['icc_profile']).decode('ascii')

        # XMP
        if 'xmp' in self.img.info:
            xmp_elem = ET.SubElement(root, 'XMP')
            xmp_elem.text = self.img.info['xmp'].decode('utf-8', errors='replace')
        if 'XML:com.adobe.xmp' in self.img.info:
            adxmp = self.img.info['XML:com.adobe.xmp']
            text = adxmp if isinstance(adxmp, str) else adxmp.decode('utf-8', errors='replace')
            ET.SubElement(root, 'AdobeXMP').text = text

        # EXIF
        exif_data = self.img._getexif() or {}
        if exif_data:
            exif_elem = ET.SubElement(root, 'EXIF')
            for tag_id, val in exif_data.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                ET.SubElement(exif_elem, str(tag)).text = str(val)

        # return XML string
        return ET.tostring(root, encoding='utf-8', xml_declaration=True)

    def save_metadata_to_file(self, output_path=None):
        if not output_path:
            output_path = self.image_path.rsplit('.', 1)[0] + '_metadata.xml'
        
        xml_bytes = self.extract_metadata()
        xml_string = xml_bytes.decode('utf-8')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_string)
            
        return output_path