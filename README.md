# Electrical Components Web Scraper

An awesome web scraping engine built using Python to extract technical specifications from manufacturer product catalogs. Attempts to keep it relatively consistent in terms of csv formatting

## Current Brands

* **ABB**: Extracts raw viewmodel JSON components natively out of script layouts.
* **Hager**: Resolves absolute URLs via global sitemaps and parses specific technical property grids natively using clean CSS selectors.

Example use case in `main.py`:
```python
from scraper import HagerScraper, AbbScraper

def main():
   df1 = HagerScraper().scrape("HEC041H", export_csv=True)
   df2 = AbbScraper().scrape("1SDA068056R1", export_csv=True)
   print(df1)
   print(df2)

if __name__ == "__main__":
    main()
```
