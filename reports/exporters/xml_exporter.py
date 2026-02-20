# reports/exporters/xml_exporter.py
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd
from pathlib import Path
from core.logger import logger
from .base import Exporter

class XMLExporter(Exporter):
    def __init__(self, root_name="dados", encoding="utf-8"):
        self.root_name = root_name
        self.encoding = encoding

    def export(self, data: pd.DataFrame, output_path: Path, item_tag="registro", **kwargs) -> bool:
        try:
            root = ET.Element(self.root_name)
            for _, row in data.iterrows():
                item = ET.SubElement(root, item_tag)
                for col_name, value in row.items():
                    if pd.notna(value):
                        child = ET.SubElement(item, col_name)
                        child.text = str(value)

            xml_str = ET.tostring(root, encoding=self.encoding)
            parsed_xml = minidom.parseString(xml_str)
            pretty_xml = parsed_xml.toprettyxml(indent="  ", encoding=self.encoding)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(pretty_xml)

            logger.info(f"XML gerado: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao gerar XML: {e}", exc_info=True)
            return False