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
    
def map_hager_to_canonical(raw: dict|None) -> CanonicalMCCB|None:
    """Transforms raw parsed Hager dictionary structures into a CanonicalMCCB instance."""
    if not raw: return None  # Fast escape if raw data extraction was unsuccessful
    gen, elec, dims = raw.get("General Information", {}), raw.get("Electric current", {}), raw.get("Dimensions", {})

    def _num(val) -> float:
        s = val[0] if isinstance(val, list) and val else val
        return float(re.sub(r"[^\d.]", "", str(s).replace(",", "."))) if s else 0.0

    ics_dict, icu_dict = {}, {}
    for k, v in elec.items():
        v_str = v[0] if isinstance(v, list) and v else v
        v_cleaned = float(str(v_str).split()[0].replace(",", ".")) if v_str else 0.0
        if "Ics under" in k:
            m = re.search(r"under\s+(\d+\s*V\s*AC)", k)
            if m: ics_dict[m.group(1).replace(" ", "")] = v_cleaned
        elif "Icu under" in k:
            m = re.search(r"under\s+(\d+\s*V\s*AC)", k)
            if m: icu_dict[m.group(1).replace(" ", "")] = v_cleaned

    u_op_str = raw.get("Voltage", {}).get("Rated operational voltage Ue", "0")
    u_op_str_clean = u_op_str[0] if isinstance(u_op_str, list) and u_op_str else u_op_str
    u_op = _num(str(u_op_str_clean).split("-")[-1]) if "-" in str(u_op_str_clean) else _num(u_op_str_clean)
    
    freq_str = str(raw.get("Frequency", {}).get("Frequency", "50 - 60 Hz"))
    freq = [float(x) for x in re.findall(r"\d+", freq_str)] if "-" in freq_str else _num(freq_str)

    return CanonicalMCCB(
        sku=gen.get("SKU", ""),
        brand="Hager",
        display_name=gen.get("Display Name", ""),
        poles=int(str(raw.get("Architecture", {}).get("Number of poles", "3"))),
        rated_current_a=_num(elec.get("Rated current", "0")),
        rated_frequency_hz=freq,
        u_imp=_num(raw.get("Voltage", {}).get("Rated impulse withstand voltage Uimp", "0")) / 1000.0,
        u_insulation=_num(raw.get("Voltage", {}).get("Rated insulation voltage Ui", "0")),
        u_operational=u_op,
        trip_type=raw.get("Functions", {}).get("Trip unit", "TM"),
        voltage_to_short_circuit_breaking_capacity_ka=ics_dict,
        voltage_to_ultimate_short_circuit_breaking_capacity_ka=icu_dict,
        height_mm=_num(dims.get("Height", "0")),
        width_mm=_num(dims.get("Width", "0")),
        depth_mm=_num(dims.get("Depth", "0")),
        weight_kg=None
    )