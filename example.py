from scraper import HagerScraper, AbbScraper, RittalScraper
from scraper.brands.abb import map_abb_to_canonical_mcb, map_abb_to_canonical_mccb, map_abb_to_canonical_contactor, map_abb_to_canonical_motor_operator, map_abb_to_canonical_isolator
from scraper.brands.hager import map_hager_to_canonical_mcb, map_hager_to_canonical_mccb, map_hager_to_canonical_contactor
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
abb_motor_operators_of_interest = [
   'https://new.abb.com/products/1SDA066460R1/mod-xt1-xt3-220-250v-ac-dc',
   'https://new.abb.com/products/1SDA104885R1/moe-xt5-220-250v-ac-dc-auto-reset',
   'https://new.abb.com/products/1SDA104895R1/moe-xt6-220-250v-ac-dc'
]
abb_isolators_of_interest = [
   'https://new.abb.com/products/2CDD272111R0063/shd202-63',
   'https://new.abb.com/products/2CDD273111R0063/shd203-63',
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
   'https://hager.com/au/products/product-information/hmc199t-mcb-1p-15ka-c-125a-1-5m', # https://hager.com/au/products/product-information/hmc199t-mcb-1p-15ka-c-125a-1-5m
   'https://hager.com/au/products/product-information/msn250-mcb-2p-6ka-c-50a-2m',
   'https://hager.com/au/products/product-information/hmc280t-mcb-2p-15ka-c-80a-3m'
]

rittal_urls_of_interest = [
    'https://www.rittal.com/au-en/products/PG20231215SCH101/PG20231512SCH301/PRO0023?variantId=1280500',
    'https://www.rittal.com/au-en/products/PG20231215SCH101/PG20240111SCH301/PRO70035?variantId=8004000',
    'https://www.rittal.com/au-en/products/PG20231215SCH101/PG20231512SCH301/PRO0023?variantId=1350500'
]


def main():
   for i, product in enumerate(abb_isolators_of_interest):
      print(f"Processing ABB Isolator: {product}")
      raw_dictionary = AbbScraper().return_dictionary_content(url=product, export_json=True, export_path=f"./output/abb_isolator_{i}_raw.json")
      # canonical_mcb = map_abb_to_canonical_mcb(raw_dictionary)
      # write_json(canonical_mcb.to_dict(), f"./output/abb_isolator_{i}_canonical.json")
      canonical_isolator = map_abb_to_canonical_isolator(raw_dictionary)
      write_json(canonical_isolator.to_dict(), f"./output/abb_isolator_{i}_canonical.json")

   # for i, product in enumerate(hager_mcbs_of_interest):
   #    print(f"Processing Hager MCB: {product}")
   #    raw_dictionary = HagerScraper().return_dictionary_content(url=product, export_json=True, export_path=f"./output/hager_mcb_{i}_raw.json")
   #    canonical_mcb = map_hager_to_canonical_mcb(raw_dictionary)
   #    write_json(canonical_mcb.to_dict(), f"./output/hager_mcb_{i}_canonical.json")

   # for i, product in enumerate(rittal_urls_of_interest):
   #    print(f"Processing Rittal Product: {product}")
   #    raw_dictionary = RittalScraper().return_dictionary_content(url=product, export_json=True, export_path=f"./output/rittal_product_{i}_raw.json")
   #    write_json(raw_dictionary, f"./output/rittal_product_{i}_raw.json")

if __name__ == "__main__":
    main()