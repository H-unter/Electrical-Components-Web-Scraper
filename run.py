"""CLI entry point: SKU + brand in, CSV out.

Usage
-----
    python run.py HEC041H hager
    python run.py HEC041H hager --csv
    python run.py HEC041H hager --csv --out my_output.csv
    python run.py 1SDA068056R1 abb --csv
"""

import argparse
import sys

from scraper.brands.abb import AbbScraper
from scraper.brands.hager import HagerScraper

BRANDS: dict = {
    "abb": AbbScraper,
    "hager": HagerScraper,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape a product page by SKU and brand."
    )
    parser.add_argument("sku", help="Product SKU (e.g. HEC041H, 1SDA068056R1)")
    parser.add_argument(
        "brand",
        choices=BRANDS.keys(),
        help="Brand to scrape",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Save output to a CSV file",
    )
    parser.add_argument(
        "--out",
        metavar="PATH",
        default=None,
        help="CSV output path (default: <SKU>.csv)",
    )
    args = parser.parse_args()

    scraper = BRANDS[args.brand]()
    df = scraper.scrape(args.sku, export_csv=args.csv, csv_path=args.out)

    if df is None:
        print("No data returned — SKU may not exist for this brand.")
        sys.exit(1)

    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
