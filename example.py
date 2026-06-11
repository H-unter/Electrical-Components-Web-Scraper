from scraper import HagerScraper, AbbScraper
from scraper.brands.abb import map_abb_to_canonical_mccb, map_abb_to_canonical_contactor
from scraper.brands.hager import map_hager_to_canonical
from scraper.utils import write_json

abb_mccbs_of_interest = [
   '1SDA067416R1',
   '1SDA068055R1',
   '1SDA067417R1',
   '1SDA068056R1',
   '1SDA067418R1'
]

abb_contactors_of_interest = [
   'AF52400013',
   'ESB63-22N-06',
]

hager_contactors_of_interest = [
   'ESC463',
   'ESC464',

]

hager_mccbs_of_interest = [
      'HHS100DR',
      'HNW400JR',
      'HNJ400DR',
      'HHS100JR',
      'HHS160DR'
]

def main():
   # for product in abb_contactors_of_interest:
   #    print(f"Processing ABB contactor: {product}")
   #    raw_dictionary = AbbScraper().scrape_to_dictionary(product, export_json=False, export_path=f"./output/abb_contactor_{product}_raw.json")
   #    canonical_contactor = map_abb_to_canonical_contactor(raw_dictionary)
   #    write_json(canonical_contactor.to_dict(), f"./output/abb_contactor_{product}_canonical.json")
      
   for product in hager_contactors_of_interest:
      print(f"Processing Hager contactor: {product}")
      raw_dictionary = HagerScraper().scrape_to_dictionary(product, export_json=True, export_path=f"./output/hager_contactor_{product}_raw.json")
      # canonical_contactor = map_hager_to_canonical_contactor(raw_dictionary, product_type="contactor")
      # write_json(canonical_contactor.to_dict(), f"./output/hager_contactor_{product}_canonical.json")

if __name__ == "__main__":
    main()