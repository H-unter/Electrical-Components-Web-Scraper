import json
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any

from retriever.models import CanonicalSpreader

from .BrandScraper import BrandScraper
from .utils import clean_text, write_json

class HagerScraper(BrandScraper):
    """Scraper for Hager product pages at hager.com."""
    
    def return_dictionary_content(self, data=None, url: str | None = None, export_json: bool = False, export_path: str | None = None) -> dict | None:
        source_data = data
        is_fetch_required = source_data is None and url is not None
        
        if is_fetch_required:
            source_data = self.return_html_content(url)
            
        if not source_data:
            return None
            
        result = {
            "General Information": self._extract_general_info(source_data),
            **self._extract_specs(source_data),
            "Documents": self._extract_documents(source_data),
            # Add the extracted list as a new key
            "Compatible Products": self._extract_compatible_products(source_data) if source_data else []
        }
        
        is_export_requested = export_json and export_path and result
        if is_export_requested:
            write_json(result, export_path)
            
        return result
    
    def _extract_compatible_products(self, soup: BeautifulSoup) -> list:
        """Helper to extract .product-list__name tags."""
        return [item.get_text(strip=True) for item in soup.select(".product-list__name")]
   
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
