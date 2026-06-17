# Electrical Components Web Scraper

A Python package for scraping technical specifications from manufacturer product pages. Given a SKU, it converts raw web data into a structured, canonical JSON format.

## Installation

Clone the repo and install in editable mode from the project root (where `pyproject.toml` lives):

```bash
pip install -e .
```

## Usage

### As a Python import

```python
from retriever.scrapers.AbbScraper import AbbScraper
from retriever.scrapers.HagerScraper import HagerScraper

# Scrape using the direct product URL
url = "https://new.abb.com/products/1SDA068056R1/xt1n-160-tmd-16-450-3p-ff"
raw_data = AbbScraper().return_dictionary_content(url=url) # this will be the 'brand specific' information which will have differing structure

mccb = map_to(brand, comp_type, raw_data)
json_data = mccb.to_dict() # this is the standardised format

# export
filename = f"./output/my_mccb.json"
write_json(json_data, filename)
```

### From the command line



```bash
python run.py --help
```

Run the scraper using `run.py` by providing the brand and the product URL:
```bash
python run.py abb https://new.abb.com/products/1SDA068056R1/xt3n-250-tmd-125-1250-3p-f-f
python run.py abb https://new.abb.com/products/1SDA068056R1/xt3n-250-tmd-125-1250-3p-f-f --canonical --type mccb
```

## Data Output

This project produces:

1. **Raw JSON:** The raw extracted data from the product page.
2. **Canonical JSON:** A standardized, unified data structure (e.g., `CanonicalMCB`, `CanonicalContactor`) mapped from the raw data.

## Supported Brands

| Brand | Approach |
|---|---|
| **ABB** | Extracts the embedded `var model` viewmodel JSON block from the product page script tag |
| **Hager** | Resolves the product URL from regional XML sitemaps, then parses the technical property grid via CSS selectors |
| **Rittal** | Only for enclosures |

## Adding a New Brand

1. Create a new scraper in `retriever/scrapers/` inheriting from `BrandScraper`.
2. Implement the `return_dictionary_content` method, ensuring it accepts a `url` parameter to fetch HTML via `self.return_html_content(url)`.
3. Create a corresponding mapper in `retriever/mappers/` to convert the raw data into one of the `Canonical` models located in `retriever/models/`.
4. Register the new scraper in `retriever/scrapers/__init__.py`.

## Project Structure

```
├── pyproject.toml
├── run.py                 # CLI entry point
└── retriever/
    ├── __init__.py
    ├── __main__.py
    ├── scrapers/          # Brand-specific extraction logic
    │   ├── BrandScraper.py# Abstract base class
    │   ├── AbbScraper.py
    │   └── HagerScraper.py
    ├── mappers/           # Logic to map raw data to canonical models
    └── models/            # Standardized Canonical classes (MCB, Contactor, etc.)
```
