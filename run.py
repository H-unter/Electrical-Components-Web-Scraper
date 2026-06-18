import argparse
import sys
import json
import retriever.scrapers as scrapers
import retriever.mappers as mappers

def get_scrapers():
    return {name.replace("Scraper", "").lower(): getattr(scrapers, name) 
            for name in scrapers.__all__}

def main() -> None:
    SCRAPERS = get_scrapers()
    parser = argparse.ArgumentParser(description="Scrape and map product data.")
    parser.add_argument("brand", choices=SCRAPERS.keys(), help="Brand to scrape")
    parser.add_argument("url", help="Full URL of the product page")
    parser.add_argument("--canonical", action="store_true", help="Output canonical JSON")
    parser.add_argument("--type", help="Component type for mapping (e.g., mcb, mccb, isolator)", default="mcb")
    
    args = parser.parse_args()

    # 1. Scrape
    scraper = SCRAPERS[args.brand]()
    raw_data = scraper.return_dictionary_content(url=args.url)

    if raw_data is None:
        print("No data returned.")
        sys.exit(1)

    # 2. Handle Output
    if args.canonical:
        try:
            # Use the existing map_to function from your mappers package
            canonical_obj = mappers.map_to(args.brand, args.type, raw_data)
            print(json.dumps(canonical_obj.to_dict(), indent=4))
        except Exception as e:
            print(f"Mapping error: {e}")
            sys.exit(1)
    else:
        print(json.dumps(raw_data, indent=4))

if __name__ == "__main__":
    main()