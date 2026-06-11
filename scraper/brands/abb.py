import json
import re

from bs4 import BeautifulSoup


from ..BrandScraper import BrandScraper
from ..utils import get_html_soup
from ..CanonicalMCCB import CanonicalMCCB

class AbbScraper(BrandScraper):
    """Scraper for ABB product pages at new.abb.com/products."""

    BASE_URL = "https://new.abb.com/products"

    # ------------------------------------------------------------------
    # BrandScraper interface
    # ------------------------------------------------------------------

    def get_soup(self, sku: str) -> BeautifulSoup | None:
        """Fetches the ABB product page for a given SKU."""
        url = f"{self.BASE_URL}/{sku.upper().strip()}"
        soup = get_html_soup(url)
        if not soup:
            url = f"{self.BASE_URL}/{sku.lower().strip()}"
            soup = get_html_soup(url)
        return soup if soup else None

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
    
def map_abb_to_canonical(raw: dict|None) -> CanonicalMCCB|None:
    """Transforms raw parsed ABB dictionary structures into a CanonicalMCCB instance."""
    if not raw: return None
    gen, tech, dims = raw.get("General Information", {}), raw.get("Technical", {}), raw.get("Dimensions", {})
    certs = raw.get("Certificates and Declarations", {}) # Extract certificates section

    def _num(val) -> float:
        s = val[0] if isinstance(val, list) and val else val
        return (
            float(re.sub(r"[^\d.]", "", str(s).replace(",", "."))) if s else 0.0
        )

    # 1. Helper function to find a value by evaluating text patterns inside the keys dynamically
    def _find_val(d: dict, pattern: str):
        return next((v for k, v in d.items() if pattern in k), None)

    # 2. Helper function to isolate voltage levels and numeric capacities from array lists safely
    def _parse_capacity(raw_val) -> dict[str, float]:
        lines = (
            raw_val
            if isinstance(raw_val, list)
            else [raw_val]
            if raw_val
            else []
        )
        pairs = [
            re.search(r"\((.*?)\)\s*([\d.]+)", str(line))
            for line in lines
            if "(" in str(line)
        ]
        return {
            m.group(1).replace(" ", ""): float(m.group(2)) for m in pairs if m
        }

    freq_str = tech.get("Rated Frequency (f)", "50 / 60 Hz")
    freq = (
        [float(x) for x in re.findall(r"\d+", str(freq_str))]
        if "/" in str(freq_str) or "-" in str(freq_str)
        else _num(freq_str)
    )

    u_op_str = _find_val(tech, "Rated Operational Voltage") or ""
    u_op_clean = u_op_str[0] if isinstance(u_op_str, list) and u_op_str else u_op_str
    u_op = (
        _num(str(u_op_clean).split("V AC")[0])
        if "V AC" in str(u_op_clean)
        else _num(u_op_clean)
    )
    doc_list = certs.get("Data Sheet, Technical Information", [])
    doc_id = doc_list[0] if isinstance(doc_list, list) and doc_list else None

    return CanonicalMCCB(
        sku=gen.get("Global ID", ""),
        brand="ABB",
        display_name=gen.get("Display Name", ""),
        datasheet_url=f"https://search.abb.com/library/Download.aspx?DocumentID={doc_id}&LanguageCode=en&DocumentPartId=&Action=Launch" if doc_id else None,
        image_urls=gen.get("Images", []) if isinstance(gen.get("Images"), list) else [],
        poles=int(
            str(_find_val(tech, "Number of Poles") or "3").replace("P", "")
        ),
        rated_current_a=_num(_find_val(tech, "Rated Current")),
        rated_frequency_hz=freq,
        u_imp=_num(_find_val(tech, "Rated Impulse Withstand")),
        u_insulation=_num(_find_val(tech, "Rated Insulation Voltage")),
        u_operational=u_op,
        trip_type=tech.get("Release Type", "TM"),
        voltage_to_short_circuit_breaking_capacity_ka=_parse_capacity(
            _find_val(tech, "Rated Service Short-Circuit")
        ),
        voltage_to_ultimate_short_circuit_breaking_capacity_ka=_parse_capacity(
            _find_val(tech, "Rated Ultimate Short-Circuit")
        ),
        height_mm=_num(dims.get("Product Net Height", "0")),
        width_mm=_num(dims.get("Product Net Width", "0")),
        depth_mm=_num(dims.get("Product Net Depth / Length", "0")),
        weight_kg=_num(dims.get("Product Net Weight", "0")) or None,
    )