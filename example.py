from scraper import HagerScraper, AbbScraper
from scraper.brands.abb import map_abb_to_canonical
from scraper.brands.hager import map_hager_to_canonical
from scraper.utils import write_json

def main():
   abb_products_of_interest = [
      '1SDA067416R1',
      '1SDA068055R1',
      '1SDA067417R1',
      '1SDA068056R1',
      '1SDA067418R1'
   ]
   hager_products_of_interest = [
       'HHS100DR',
       'HNW400JR',
       'HNJ400DR',
       'HHS100JR',
       'HHS160DR'
   ]
   for product in abb_products_of_interest:
      # AbbScraper().scrape_to_df(product, export_csv=True, csv_path=f"./output/abb_{product}.csv")
      # AbbScraper().scrape_to_dictionary(product, export_json=True, export_path=f"./output/abb_{product}.json")
      raw_dictionary = AbbScraper().scrape_to_dictionary(product, export_json=False)
      mccb = map_abb_to_canonical(raw_dictionary)
      if mccb:
         write_json(mccb.to_dict(), f"./output/abb_{product}_canonical.json")
   for product in hager_products_of_interest:
      # HagerScraper().scrape_to_df(product, export_csv=True, csv_path=f"./output/hager_{product}.csv")
      # HagerScraper().scrape_to_dictionary(product, export_json=True, export_path=f"./output/hager_{product}.json")
      raw_dictionary = HagerScraper().scrape_to_dictionary(product, export_json=False)
      mccb = map_hager_to_canonical(raw_dictionary)
      if mccb:
         write_json(mccb.to_dict(), f"./output/hager_{product}_canonical.json")

if __name__ == "__main__":
    main()