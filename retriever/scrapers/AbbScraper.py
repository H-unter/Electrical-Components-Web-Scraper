import json
import re

from bs4 import BeautifulSoup
from typing import List, Optional, Dict, Any


from .BrandScraper import BrandScraper
from .utils import get_html_soup, write_json
from ..models.CanonicalMCCB import CanonicalMCCB
from ..models.CanonicalMCB import CanonicalMCB
from ..models.CanonicalContactor import CanonicalContactor
from ..models.CanonicalMotorOperator import CanonicalMotorOperator
from ..models.CanonicalIsolator import CanonicalIsolator
from ..models.CanonicalSpreader import CanonicalSpreader

class AbbScraper(BrandScraper):
    """Scraper for ABB product pages at new.abb.com/products."""

    def return_dictionary_content(self, data=None, url: str | None = None, export_json: bool = False, export_path: str | None = None) -> dict | None:
        source_data = data
        is_fetch_required = source_data is None and url is not None
        
        if is_fetch_required:
            source_data = self.return_html_content(url)
            
        if not source_data:
            return None

        viewmodel = source_data if isinstance(source_data, dict) else self._extract_viewmodel(source_data)
        if not viewmodel:
            return None
            
        result = self._parse_viewmodel(viewmodel)
        
        is_export_requested = export_json and export_path and result
        if is_export_requested:
            write_json(result, export_path)
            
        return result

    def _extract_viewmodel(self, soup: BeautifulSoup) -> dict | None:
        for script in soup.find_all("script"):
            if script.string and "var model =" in script.string:
                match = re.search(
                    r"var model\s*=\s*(\{.*?\}*?\});\s*jsLibs\.push",
                    script.string,
                    re.DOTALL,
                )
                if match:
                    try:
                        return json.loads(match.group(1))
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse ABB model JSON: {e}")
                        return None
        print("Could not find 'var model' block in ABB page HTML.")
        return None

    def _parse_viewmodel(self, model: dict) -> dict:
        product_info = model.get("ProductViewModel", {}).get("Product", {})
        image_list = (
            product_info.get("productDetails", {})
            .get("item", {})
            .get("images", [])
        )
        urls = [img["url"] for img in image_list if "url" in img]

        result = {
            "General Information": {
                "Display Name":       model.get("DisplayName", ""),
                "Short Name":         model.get("ShortName", ""),
                "Product URL Suffix": model.get("ProductURLSuffix", ""),
                "Meta Description":   model.get("MetaDescription", ""),
                "Global ID":          model.get("GlobalId", ""),
                "Images":             urls if len(urls) > 1 else (urls[0] if urls else ""),
            }
        }

        attribute_groups = product_info.get("attributeGroups", {}).get("items", [])
        for i, group in enumerate(attribute_groups):
            group_name = group.get("description", f"Group {i}")
            result[group_name] = {}
            for attr_key, attr_data in group.get("attributes", {}).items():
                attr_name = attr_data.get("attributeName", attr_key)
                values = [v["text"] for v in attr_data.get("values", []) if "text" in v]
                result[group_name][attr_name] = (
                    "" if not values else values[0] if len(values) == 1 else values
                )

        return result
    
