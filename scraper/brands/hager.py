import json
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup

from ..BrandScraper import BrandScraper
from ..utils import clean_text
from ..CanonicalMCCB import CanonicalMCCB


class HagerScraper(BrandScraper):
    """Scraper for Hager product pages at hager.com.

    Regional sitemaps are queried in the order defined by FALLBACK_REGIONS.
    The first region that contains the SKU is used.
    """

    FALLBACK_REGIONS = ["au", "uk", "nz"]
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # ------------------------------------------------------------------
    # BrandScraper interface
    # ------------------------------------------------------------------

    def get_soup(self, sku: str) -> BeautifulSoup | None:
        """Looks up the SKU across regional sitemaps and returns its page soup."""
        url = self._find_product_url(sku)
        if not url:
            return None
        try:
            res = requests.get(url, headers=self.HEADERS, timeout=10)
            res.raise_for_status()
            return BeautifulSoup(res.text, "html.parser")
        except Exception as e:
            print(f"Failed to fetch Hager page for '{sku}': {e}")
            return None

    def extract_product_info(self, soup: BeautifulSoup) -> dict:
        """Parses the Hager product page into a nested dict."""
        if not soup:
            return {}
        return {
            "General Information": self._extract_general_info(soup),
            **self._extract_specs(soup),
            "Documents": self._extract_documents(soup),
        }

    def to_dataframe(self, product_info: dict) -> pd.DataFrame:
        """Flattens the Hager dict, with special handling for the Documents section."""
        if not product_info:
            return pd.DataFrame(columns=["Attribute Group", "Attribute", "Attribute Value"])
        rows = []
        for group, attrs in product_info.items():
            if group == "Documents":
                for doc_cat, doc_list in attrs.items():
                    for doc in doc_list:
                        val = " | ".join(filter(None, [
                            doc.get("title", ""),
                            doc.get("file_type", ""),
                            doc.get("file_size", ""),
                            doc.get("url", ""),
                        ]))
                        rows.append({
                            "Attribute Group": f"Documents \u2013 {doc_cat}",
                            "Attribute": doc.get("title", ""),
                            "Attribute Value": val,
                        })
            else:
                for attr, val in attrs.items():
                    val_str = "\n".join(val) if isinstance(val, list) else str(val)
                    rows.append({
                        "Attribute Group": group,
                        "Attribute": attr,
                        "Attribute Value": val_str,
                    })
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Sitemap lookup
    # ------------------------------------------------------------------

    def _find_product_url(self, sku: str) -> str | None:
        """Iterates regional sitemaps in FALLBACK_REGIONS order, returning the
        first URL that matches the SKU, or None if not found in any region."""
        sku = sku.upper().strip()
        for region in self.FALLBACK_REGIONS:
            url = f"https://hager.com/{region}/products/media/sitemap_{region}.xml"
            try:
                res = requests.get(url, headers=self.HEADERS, timeout=15)
                res.raise_for_status()
                soup = BeautifulSoup(res.text, "xml")
                for loc in soup.find_all("loc"):
                    slug = loc.text.split("/")[-1]
                    match = re.match(r"^([a-z0-9]+)-", slug)
                    if match and match.group(1).upper() == sku:
                        print(f"Found '{sku}' in region '{region}': {loc.text}")
                        return loc.text
                print(f"'{sku}' not in region '{region}', trying next...")
            except Exception as e:
                print(f"Sitemap fetch failed for region '{region}': {e}")

        print(f"'{sku}' not found in any region: {self.FALLBACK_REGIONS}")
        return None

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    def _extract_general_info(self, soup: BeautifulSoup) -> dict:
        """Extracts name, SKU, description, URL, images, and categories."""
        info = {}

        # JSON-LD Product schema
        for script in soup.find_all("script", {"type": "application/ld+json"}):
            try:
                data = json.loads(script.string)
                if data.get("@type") == "Product":
                    info["Display Name"] = data.get("name", "")
                    info["SKU"] = data.get("sku", "")
                    info["Description"] = data.get("description", "")
                    info["Product URL"] = data.get("offers", {}).get("url", "")
                    ld_images = data.get("image", [])
                    info["Images"] = (
                        ld_images if len(ld_images) > 1 else (ld_images[0] if ld_images else "")
                    )
            except Exception:
                pass

        # Category hierarchy from GTM dataLayer
        for script in soup.find_all("script"):
            s = script.string or ""
            if "pageViewDataForGTM" in s and "JSON.parse" in s:
                match = re.search(
                    r"window\.pageViewDataForGTM\s*=\s*JSON\.parse\('(.+?)'\)", s
                )
                if match:
                    try:
                        gtm = json.loads(match.group(1).encode().decode("unicode_escape"))
                        info["Category 1"] = clean_text(gtm.get("productCategory", ""))
                        info["Category 2"] = clean_text(gtm.get("productCategory2", ""))
                        info["Category 3"] = clean_text(gtm.get("productCategory3", ""))
                    except Exception:
                        pass
                break

        # Full-resolution gallery images from Magento JS config
        for script in soup.find_all("script", {"type": "text/x-magento-init"}):
            s = script.string or ""
            if "fullGalleryImages" in s:
                try:
                    cfg = json.loads(s)
                    images_data = (
                        cfg.get("#gallery-container", {})
                        .get("Magento_Ui/js/core/app", {})
                        .get("components", {})
                        .get("product_main_gallery", {})
                        .get("config", {})
                        .get("fullGalleryImages", [])
                    )
                    full_images = [img["img"] for img in images_data if "img" in img]
                    if full_images:
                        info["Images"] = (
                            full_images if len(full_images) > 1 else full_images[0]
                        )
                except Exception:
                    pass
                break

        return info

    def _extract_specs(self, soup: BeautifulSoup) -> dict:
        """Parses the technical attribute groups into a nested dict."""
        specs = {}
        current_group = "Technical Properties"
        for el in soup.select(
            ".additional-attributes__header, .additional-attributes__product-specs__item"
        ):
            if "additional-attributes__header" in el.get("class", []):
                current_group = clean_text(el.text)
                specs.setdefault(current_group, {})
            else:
                lbl = el.select_one(".additional-attributes__product-specs__label")
                dat = el.select_one(".additional-attributes__product-specs__data")
                if lbl and dat:
                    specs.setdefault(current_group, {})[clean_text(lbl.text)] = clean_text(dat.text)
        return {g: attrs for g, attrs in specs.items() if attrs}

    def _extract_documents(self, soup: BeautifulSoup) -> dict:
        """Parses the Downloads section into a dict keyed by document category."""
        documents = {}
        for li in soup.select(".product-documents__table li"):
            heading_el = li.select_one(
                ".product-documents__subtitle, .product-documents__produktbild--subtitle"
            )
            cat = clean_text(heading_el.text) if heading_el else "Other"
            link_el = li.select_one("a.download-document")
            if not link_el:
                continue
            title_el = li.select_one(".table-product__name")
            desc_el = li.select_one("p.table-product__description")
            ext_el = li.select_one(".table-product__extension")
            size_el = li.select_one(".table-product__weight")
            documents.setdefault(cat, []).append({
                "title":       clean_text(title_el.text) if title_el else "",
                "description": clean_text(desc_el.text)  if desc_el  else "",
                "url":         link_el.get("href", ""),
                "file_type":   clean_text(ext_el.text)   if ext_el   else "",
                "file_size":   clean_text(size_el.text)  if size_el  else "",
            })
        return documents
    
def map_hager_to_canonical(raw_dictionary: dict|None) -> CanonicalMCCB|None:
    """Transforms raw parsed Hager dictionary structures into a CanonicalMCCB instance."""
    if not raw_dictionary: return None  # Fast escape if raw data extraction was unsuccessful

    general_info = raw_dictionary.get("General Information", {})  # Target general metadata blocks
    electric_current = raw_dictionary.get("Electric current", {})  # Target power performance attributes
    dimensions = raw_dictionary.get("Dimensions", {})  # Target layout sizing measurements
    documents = raw_dictionary.get("Documents", {})  # Extract the nested documents block safely

    def _num(value) -> float:
        string_value = value[0] if isinstance(value, list) and value else value  # Clean array layers down to string
        return float(re.sub(r"[^\d.]", "", str(string_value).replace(",", "."))) if string_value else 0.0  # Safe float cast

    short_circuit_breaking_capacity = {}  # Allocate mapping block for service capacities
    ultimate_short_circuit_breaking_capacity = {}  # Allocate mapping block for ultimate capacities
    for key, value in electric_current.items():
        string_value = value[0] if isinstance(value, list) and value else value  # Normalize lists down to single string element
        cleaned_value = float(str(string_value).split()[0].replace(",", ".")) if string_value else 0.0  # Snatch leading float digits
        if "Ics under" in key:  # Check pattern matches service criteria
            match = re.search(r"under\s+(\d+\s*V\s*AC)", key)  # Isolate specific voltage string token
            if match: short_circuit_breaking_capacity[match.group(1).replace(" ", "")] = cleaned_value  # Map voltage pair cleanly
        elif "Icu under" in key:  # Check pattern matches ultimate criteria
            match = re.search(r"under\s+(\d+\s*V\s*AC)", key)  # Isolate specific voltage string token
            if match: ultimate_short_circuit_breaking_capacity[match.group(1).replace(" ", "")] = cleaned_value  # Map voltage pair cleanly

    operational_voltage_string = raw_dictionary.get("Voltage", {}).get("Rated operational voltage Ue", "0")  # Extract baseline bounds
    operational_voltage_clean = operational_voltage_string[0] if isinstance(operational_voltage_string, list) and operational_voltage_string else operational_voltage_string  # Extract list item string safely
    operational_voltage = _num(str(operational_voltage_clean).split("-")[-1]) if "-" in str(operational_voltage_clean) else _num(operational_voltage_clean)  # Snatch the maximum range bound

    frequency_string = str(raw_dictionary.get("Frequency", {}).get("Frequency", "50 - 60 Hz"))  # Safe string conversion cast
    rated_frequency_hz = [float(extracted_number) for extracted_number in re.findall(r"\d+", frequency_string)] if "-" in frequency_string else _num(frequency_string)  # Capture frequency spans

    datasheet_list = []  # Initialize core file document stack array
    if isinstance(documents, dict): datasheet_list = documents.get("Product datasheet", []) or documents.get("Datasheet", [])  # Retrieve from direct subcategory keys
    if not datasheet_list and isinstance(documents, dict):  # Fallback: scan through inner document categories
        for key, value in documents.items():  # Loop keys looking for structural matches
            if "datasheet" in key.lower() and isinstance(value, list):  # If name fits structure
                datasheet_list = value  # Set target array layout
                break  # Exit traversal loop
    if not datasheet_list:  # Fallback: scan root keys directly
        for key, value in raw_dictionary.items():  # Traverse root dictionary structure
            if "datasheet" in key.lower() and isinstance(value, list):  # Check key pattern match criteria
                datasheet_list = value  # Set target array layout
                break  # Exit traversal loop
    datasheet_url = datasheet_list[0].get("url") if isinstance(datasheet_list, list) and datasheet_list else None  # Grab first available PDF asset link

    image_urls = []  # Allocate target listing placeholder array structure
    images_raw_value = general_info.get("Images", "")  # Pull general image asset strings
    if images_raw_value: image_urls = images_raw_value if isinstance(images_raw_value, list) else [images_raw_value]  # Push element natively or convert to single entry list
    if not image_urls and isinstance(documents, dict) and "Product image" in documents:  # Fallback to secondary asset gallery arrays
        product_images_documents = documents.get("Product image", [])  # Gather document lists
        if isinstance(product_images_documents, list): image_urls = [item.get("url") for item in product_images_documents if item.get("url")]  # Compile image URLs cleanly

    raw_impulse_voltage = _num(raw_dictionary.get("Voltage", {}).get("Rated impulse withstand voltage Uimp", "0"))  # Pull raw parameter metric
    u_imp = raw_impulse_voltage / 1000.0 if raw_impulse_voltage > 100.0 else raw_impulse_voltage  # Standardize thousands value string boundary directly down to kV scale units

    return CanonicalMCCB(
        sku=general_info.get("SKU", ""),
        brand="Hager",
        display_name=general_info.get("Display Name", ""),
        poles=int(str(raw_dictionary.get("Architecture", {}).get("Number of poles", "3"))),
        rated_current_a=_num(electric_current.get("Rated current", "0")),
        rated_frequency_hz=rated_frequency_hz,
        u_imp=u_imp,
        u_insulation=_num(raw_dictionary.get("Voltage", {}).get("Rated insulation voltage Ui", "0")),
        u_operational=operational_voltage,
        trip_type=raw_dictionary.get("Functions", {}).get("Trip unit", "TM"),
        voltage_to_short_circuit_breaking_capacity_ka=short_circuit_breaking_capacity,
        voltage_to_ultimate_short_circuit_breaking_capacity_ka=ultimate_short_circuit_breaking_capacity,
        height_mm=_num(dimensions.get("Height", "0")),
        width_mm=_num(dimensions.get("Width", "0")),
        depth_mm=_num(dimensions.get("Depth", "0")),
        weight_kg=None,
        datasheet_url=datasheet_url,
        image_urls=image_urls
    )