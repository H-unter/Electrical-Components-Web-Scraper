from abc import ABC, abstractmethod

import pandas as pd


class BrandScraper(ABC):
    """Abstract base class defining the interface every brand scraper must implement.

    Subclasses override `get_soup` and `extract_product_info` with brand-specific
    logic. The `scrape` method owns the full pipeline and should not be overridden
    unless absolutely necessary. `to_dataframe` has a sensible default but can be
    overridden when a brand's dict structure differs (e.g. Hager's Documents section).
    """

    @abstractmethod
    def get_soup(self, sku: str):
        """Fetch and return a BeautifulSoup object for the given SKU, or None."""

    @abstractmethod
    def extract_product_info(self, soup) -> dict:
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

    def scrape(self, sku: str, export_csv: bool = False, csv_path: str = None) -> pd.DataFrame:
        """Full pipeline: SKU in, DataFrame out. This is the public API.

        Parameters
        ----------
        sku : str
            The product SKU to look up.
        export_csv : bool
            If True, saves the DataFrame to a CSV file.
        csv_path : str, optional
            Output path for the CSV. Defaults to `<SKU>.csv` in the working directory.

        Returns
        -------
        pd.DataFrame or None if the SKU could not be found.
        """
        soup = self.get_soup(sku)
        if soup is None:
            print(f"Could not retrieve page for SKU '{sku}'.")
            return None

        product_info = self.extract_product_info(soup)
        df = self.to_dataframe(product_info)

        if export_csv:
            path = csv_path or f"{sku.upper()}.csv"
            df.to_csv(path, index=False, encoding="utf-8-sig")
            print(f"CSV saved to: {path}")

        return df
