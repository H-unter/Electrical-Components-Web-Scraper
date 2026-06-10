# Electrical Components Web Scraper

A Python package for scraping technical specifications from manufacturer product pages. Given a SKU, it returns a structured pandas DataFrame (and optionally a CSV) with consistent column formatting across brands.

## Installation

Clone the repo and install in editable mode from the **project root** (where `pyproject.toml` lives):

```bash
pip install -e .
```

## Usage

### As a Python import

```python
from scraper import HagerScraper, AbbScraper

df = HagerScraper().scrape("HEC041H", export_csv=True)
df = AbbScraper().scrape("1SDA068056R1", export_csv=True)
```

### From the command line

```bash
scraper HEC041H hager --csv
scraper 1SDA068056R1 abb --csv
scraper HEC041H hager --csv --out my_output.csv  # custom output path
```

### Output format

Every brand returns a DataFrame with three columns:

| Attribute Group | Attribute | Attribute Value |
|---|---|---|
| General Information | Display Name | HEC041H |
| Electric current | Rated current | 40 A |
| ... | ... | ... |

## Supported Brands

| Brand | Approach |
|---|---|
| **ABB** | Extracts the embedded `var model` viewmodel JSON block from the product page script tag |
| **Hager** | Resolves the product URL from regional XML sitemaps, then parses the technical property grid via CSS selectors |

## Adding a New Brand

1. Create `scraper/brands/newbrand.py` subclassing `BrandScraper`
2. Implement `get_soup(sku)` and `extract_product_info(soup)`
3. Register it in `scraper/brands/__init__.py` and `scraper/__main__.py`

```python
from ..base import BrandScraper

class NewBrandScraper(BrandScraper):

    def get_soup(self, sku: str):
        # fetch and return BeautifulSoup for this SKU
        ...

    def extract_product_info(self, soup) -> dict:
        # parse and return nested dict
        ...
```

## Project Structure

```
├── pyproject.toml
├── requirements.txt
├── main.py
└── scraper/
    ├── __init__.py        # exports all scrapers
    ├── __main__.py        # CLI entry point
    ├── base.py            # BrandScraper abstract base class
    ├── utils.py           # shared helpers
    └── brands/
        ├── abb.py
        └── hager.py
```
