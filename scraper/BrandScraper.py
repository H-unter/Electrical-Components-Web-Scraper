from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
import pandas as pd

from scraper.utils import write_json, get_html_soup


class BrandScraper(ABC):
    """Abstract base class defining the interface every brand scraper must implement.

    Subclasses override `get_soup` and `extract_product_info` with brand-specific
    logic. The `scrape_to_df` method owns the full pipeline and should not be overridden
    unless absolutely necessary. `to_dataframe` has a sensible default but can be
    overridden when a brand's dict structure differs (e.g. Hager's Documents section).
    """

    @abstractmethod
    def get_soup(self, sku: str) -> BeautifulSoup | None:
        """Fetch and return a BeautifulSoup object for the given SKU, or None."""

    @abstractmethod
    def extract_product_info(self, soup: BeautifulSoup) -> dict:
        """Parse the soup into a nested product info dict.

        Expected structure:
            {
                "General Information": { "Display Name": ..., "SKU": ..., ... },
                "<Attribute Group>":   { "<Attribute>": "<Value>", ... },
                ...
            }
        """
    
    def to_dataframe(self, product_info: dict) -> pd.DataFrame:
        """Flatten the nested product dict into a three-column DataFrame.

        Columns: Attribute Group | Attribute | Attribute Value

        Override this method in a brand subclass only when the dict contains
        non-flat values (e.g. lists of dicts) that need special handling.
        """
        if not product_info:
            return pd.DataFrame(columns=["Attribute Group", "Attribute", "Attribute Value"])
        rows = []
        for group, attrs in product_info.items():
            for attr, val in attrs.items():
                val_str = "\n".join(val) if isinstance(val, list) else str(val)
                rows.append({
                    "Attribute Group": group,
                    "Attribute": attr,
                    "Attribute Value": val_str,
                })
        return pd.DataFrame(rows)


    def scrape_to_dictionary(self, sku: str | None = None, url: str | None = None, export_json: bool = False, export_path: str | None = None) -> dict | None:
        """Executes the full pipeline to extract product information into a dictionary.
        
        This method retrieves the page source using either a direct URL or by 
        looking up the provided SKU, and then extracts the brand-specific 
        product data into a nested dictionary structure.

        Parameters
        ----------
        sku : str, optional
            The product SKU to look up. 
        url : str, optional
            A direct URL to the product page. If provided, this bypasses the 
            SKU sitemap lookup process.
        export_json : bool, default False
            If True, saves the resulting dictionary to a JSON file.
        export_path : str, optional
            The output file path for the JSON file. Required if `export_json` is True.

        Returns
        -------
        dict or None
            A nested dictionary containing the parsed product attributes, or 
            None if neither an identifier is provided nor the page could be retrieved.
        """
        if not sku and not url:
            print("Error: You must provide either an 'sku' or a 'url'.")
            return None

        soup = get_html_soup(url) if url else self.get_soup(sku)
            
        if not soup:
            target = f"URL '{url}'" if url else f"SKU '{sku}'"
            print(f"Failed to retrieve page for {target}.")
            return None

        product_info = self.extract_product_info(soup)
        
        if export_json and export_path:
            write_json(product_info, export_path)
            
        return product_info


    def scrape_to_df(self, sku: str | None = None, url: str | None = None, export_csv: bool = False, csv_path: str | None = None) -> pd.DataFrame | None:
        """Executes the full pipeline to extract and flatten product info into a DataFrame.
        
        This method retrieves the page source using either a direct URL or by 
        looking up the provided SKU, extracts the product data, and then flattens 
        the nested dictionary into a three-column pandas DataFrame.

        Parameters
        ----------
        sku : str, optional
            The product SKU to look up.
        url : str, optional
            A direct URL to the product page. If provided, this bypasses the 
            SKU sitemap lookup process.
        export_csv : bool, default False
            If True, saves the resulting DataFrame to a CSV file.
        csv_path : str, optional
            Output path for the CSV. Defaults to `<SKU>.csv` in the working directory 
            (or `PRODUCT.csv` if only a URL is provided).

        Returns
        -------
        pd.DataFrame or None
            A DataFrame with columns ['Attribute Group', 'Attribute', 'Attribute Value'], 
            or None if neither an identifier is provided nor the page could be retrieved.
        """
        if not sku and not url:
            print("Error: You must provide either an 'sku' or a 'url'.")
            return None

        soup = get_html_soup(url) if url else self.get_soup(sku)

        if not soup:
            target = f"URL '{url}'" if url else f"SKU '{sku}'"
            print(f"Failed to retrieve page for {target}.")
            return None

        product_info = self.extract_product_info(soup)
        df = self.to_dataframe(product_info)

        if export_csv:
            path = csv_path or f"{(sku or 'product').upper()}.csv"
            df.to_csv(path, index=False, encoding="utf-8-sig")
            print(f"CSV saved to: {path}")

        return df
