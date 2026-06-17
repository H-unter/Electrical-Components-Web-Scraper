from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
import pandas as pd

from scraper.utils import write_json, get_html_soup

class BrandScraper(ABC):
    """Abstract base class for all brand-specific scrapers."""

    def return_html_content(self, url: str) -> BeautifulSoup | None:
        """
        Fetches the raw HTML data for a given URL.
        Returns a BeautifulSoup object.
        """
        return get_html_soup(url)

    @abstractmethod
    def return_dictionary_content(self, data = None, url: str | None = None, export_json: bool = False, export_path: str | None = None) -> dict | None:
        """
        Parses the raw source data (e.g., a BeautifulSoup object or JSON dict)
        and extracts the product information into a structured dictionary.
        """
        pass