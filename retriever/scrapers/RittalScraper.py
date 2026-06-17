import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import Optional, Any

from retriever.scrapers.utils import write_json
from .BrandScraper import BrandScraper

class RittalScraper(BrandScraper):
    """Scraper for Rittal Products."""

    def return_dictionary_content(self, data=None, url: str | None = None, export_json: bool = False, export_path: str | None = None) -> dict | None:
        is_soup_provided = isinstance(data, BeautifulSoup)
        if not is_soup_provided and url is not None:
            data = self.return_html_content(url)
            if data is None:
                return None
        
        dictionary_content = self._parse_html_to_dictionary(data)

        # Recursively sanitize out \xa0 characters and loose whitespaces from the entire payload
        if dictionary_content:
            dictionary_content = self._clean_whitespace_recursive(dictionary_content)

        is_export_required = export_json and export_path is not None
        if is_export_required:
            write_json(dictionary_content, export_path)
            
        return dictionary_content

    def _clean_whitespace_recursive(self, data: Any) -> Any:
        """
        Recursively traverses lists and dictionaries to clean up \xa0 and matching
        unwanted whitespace anomalies from all parsed textual values.
        """
        if isinstance(data, dict):
            return {self._clean_whitespace_recursive(k): self._clean_whitespace_recursive(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_whitespace_recursive(item) for item in data]
        elif isinstance(data, str):
            # Replace non-breaking spaces with standard space, then run a deep strip
            cleaned = data.replace('\xa0', ' ')
            return " ".join(cleaned.split()).strip()
        return data

    def _extract_technical_features(self, soup: BeautifulSoup) -> dict:
        """
        Dynamically extracts all technical attributes (Material, Color, Protection Category, 
        Dimensions, Weights, EAN, etc.) stored in <dt>/<dd> pairs on the page.
        """
        features = {}
        
        for dt in soup.find_all('dt'):
            label = dt.get_text(strip=True)
            if not label:
                continue
                
            values = []
            next_sibling = dt.find_next_sibling()
            
            while next_sibling and next_sibling.name == 'dd':
                if next_sibling.find('a', class_='download-link'):
                    next_sibling = next_sibling.find_next_sibling()
                    continue
                    
                val_text = next_sibling.get_text(" ", strip=True)
                if val_text:
                    values.append(val_text)
                next_sibling = next_sibling.find_next_sibling()
                
            if values:
                clean_label = label.rstrip(':').strip()
                features[clean_label] = values[0] if len(values) == 1 else values
                
        return features

    def _parse_html_to_dictionary(self, soup: BeautifulSoup) -> dict:
        """
        Parses the BeautifulSoup object and extracts product information into a structured dictionary.
        """
        product_data = {}

        # 1. Product Identification
        title_element = soup.find('h1')
        product_data["title"] = title_element.get_text(strip=True) if title_element else None

        article_element = soup.find(class_="value")
        product_data["article_no"] = article_element.get_text(strip=True) if article_element else None

        # 2. Product Description Section Extraction
        description_div = soup.find('div', class_='product-description')
        if description_div:
            product_data["description"] = description_div.get_text(strip=True)
        else:
            product_data["description"] = None

        # 3. Dynamic Technical Characteristics / Parameters Extraction
        technical_specs = self._extract_technical_features(soup)
        product_data.update(technical_specs)

        # 4. Downloads Section Extraction
        downloads = []
        download_links = soup.find_all('a', class_='download-link')
        
        for link in download_links:
            href = link.get('href')
            if not href:
                continue
                
            label_element = link.find('span', class_='label')
            label_text = label_element.get_text(strip=True) if label_element else link.get_text(strip=True)
            
            doc_type = None
            parent_dd = link.find_parent('dd')
            if parent_dd:
                doc_type = "".join([t for t in parent_dd.contents if isinstance(t, str)]).strip()
                if not doc_type:
                    prev_dt = parent_dd.find_previous('dt')
                    if prev_dt:
                        doc_type = prev_dt.get_text(strip=True)

            downloads.append({
                "document_name": doc_type if doc_type else "Download Link",
                "language_label": label_text,
                "url": href
            })
            
        product_data["downloads"] = downloads

        return product_data