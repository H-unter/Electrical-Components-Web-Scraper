import json
import re

from bs4 import BeautifulSoup

from ..base import BrandScraper
from ..utils import get_html_soup


class AbbScraper(BrandScraper):
    """Scraper for ABB product pages at new.abb.com/products."""

    BASE_URL = "https://new.abb.com/products"

    # ------------------------------------------------------------------
    # BrandScraper interface
    # ------------------------------------------------------------------

    def get_soup(self, sku: str) -> BeautifulSoup | None:
        """Fetches the ABB product page for a given SKU."""
        url = f"{self.BASE_URL}/{sku.upper().strip()}"
        return get_html_soup(url)

    def extract_product_info(self, soup: BeautifulSoup) -> dict:
        """Parses the embedded JS `model` variable and returns a nested dict."""
        viewmodel = self._extract_viewmodel(soup)
        if not viewmodel:
            return {}
        return self._parse_viewmodel(viewmodel)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_viewmodel(self, soup: BeautifulSoup) -> dict | None:
        """Locates and parses the `var model = {...}` JS block in the page."""
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
        """Extracts general info and attribute groups from the viewmodel dict."""
        product_info = (
            model.get("ProductViewModel", {}).get("Product", {})
        )
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
