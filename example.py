from scraper import HagerScraper, AbbScraper
from scraper.brands.abb import map_abb_to_canonical_mcb, map_abb_to_canonical_mccb, map_abb_to_canonical_contactor
from scraper.brands.hager import map_hager_to_canonical_mccb, map_hager_to_canonical_contactor
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
abb_mcbs_of_interest = [
   'https://new.abb.com/products/2CDS273001R0164/s203m-c16',
   'https://new.abb.com/products/2CDS253001R0104/s203-c10',
   'https://new.abb.com/products/2CCG001232R0001/s803p-c80'
]

hager_contactors_of_interest = [
   'https://hager.com/au/products/product-information/esc464-contactor-63a-4nc-230v',
   'https://hager.com/au/products/product-information/esc125-contactor-25a-1no-230v',
   'https://hager.com/au/products/product-information/esc227-contactor-25a-1no-1nc-230v',
   'https://hager.com/au/products/product-information/esc080-auxiliary-contact-6a-1no-1nc'
]
hager_mccbs_of_interest = [ # sometimes really annoying due to their sitemap missing things.
      'HHS100DR',
      'HNW400JR',
      'HNJ400DR',
      'HHS100JR',
      'HHS160DR'
]
hager_mcbs_of_interest = [
   'HMC199T', # https://hager.com/au/products/product-information/hmc199t-mcb-1p-15ka-c-125a-1-5m
]
def main():
   for i, product in enumerate(abb_mcbs_of_interest):
      print(f"Processing ABB MCB: {product}")
      raw_dictionary = AbbScraper().scrape_to_dictionary(url=product, export_json=False, export_path=f"./output/abb_mcb_{i}_raw.json")
      canonical_mcb = map_abb_to_canonical_mcb(raw_dictionary)
      write_json(raw_dictionary, f"./output/abb_mcb_{i}_raw.json")
      write_json(canonical_mcb.to_dict(), f"./output/abb_mcb_{i}_canonical.json")

   # for i, product in enumerate(hager_contactors_of_interest):
   #    print(f"Processing Hager contactor: {product}")
   #    raw_dictionary = HagerScraper().scrape_to_dictionary(url=product, export_json=True, export_path=f"./output/hager_contactor_{i}_raw.json")
   #    canonical_contactor = map_hager_to_canonical_contactor(raw_dictionary)
   #    write_json(canonical_contactor.to_dict(), f"./output/hager_contactor_{i}_canonical.json")

if __name__ == "__main__":
    main()