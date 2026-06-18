import dataclasses

from retriever import HagerScraper, AbbScraper, RittalScraper
from retriever.mappers import map_to
from retriever.scrapers.utils import write_json

abb_mccbs_of_interest = [
   'https://new.abb.com/products/1SDA067416R1/xt1n-160-tmd-100-1000-3p-f-f',
   'https://new.abb.com/products/1SDA068055R1/xt3n-250-tmd-100-1000-3p-f-f',
   'https://new.abb.com/products/1SDA067417R1/xt1n-160-tmd-125-1250-3p-f-f',
   'https://new.abb.com/products/1SDA068056R1/xt3n-250-tmd-125-1250-3p-f-f',
   'https://new.abb.com/products/1SDA067418R1/xt1n-160-tmd-160-1600-3p-f-f'
]
abb_contactors_of_interest = [
   'https://new.abb.com/products/1SBL367201R1300/af52-40-00-13',
   'https://new.abb.com/products/1SAE351111R0622/esb63-22n-06',
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
abb_spreaders_of_interest = [
   'https://new.abb.com/products/1SDA104738R1/kit-es-xt5-3pcs',
   'https://new.abb.com/products/1SDA066894R1/kit-es-xt2-4pcs',
   'https://new.abb.com/products/1SDA066897R1/kit-es-xt3-3pcs'
]

hager_contactors_of_interest = [
   'https://hager.com/au/products/product-information/esc464-contactor-63a-4nc-230v',
   'https://hager.com/au/products/product-information/esc125-contactor-25a-1no-230v',
   'https://hager.com/au/products/product-information/esc227-contactor-25a-1no-1nc-230v',
   'https://hager.com/au/products/product-information/esc080-auxiliary-contact-6a-1no-1nc'
]
hager_mccbs_of_interest = [ # sometimes really annoying due to their sitemap missing things.
   'https://hager.com/au/products/product-information/hhs100dr-mccb-h3-p160-tm-3x100a-25ka',
   'https://hager.com/au/products/product-information/hnw400jr-mccb-h3-p630-lsi-3x400a-40ka',
   'https://hager.com/au/products/product-information/hnw400jr-mccb-h3-p630-lsi-3x400a-40ka',
   'https://hager.com/au/products/product-information/hhs100jr-mccb-h3-p160-lsi-3x100a-25ka',
   'https://hager.com/au/products/product-information/hhs160dr-mccb-h3-p160-tm-3x160a-25ka'
]
hager_mcbs_of_interest = [
   'https://hager.com/au/products/product-information/hmc199t-mcb-1p-15ka-c-125a-1-5m', # https://hager.com/au/products/product-information/hmc199t-mcb-1p-15ka-c-125a-1-5m
   'https://hager.com/au/products/product-information/msn250-mcb-2p-6ka-c-50a-2m',
   'https://hager.com/au/products/product-information/hmc280t-mcb-2p-15ka-c-80a-3m'
]
hager_isolators_of_interest = [
   'https://hager.com/au/products/product-information/sbr180-1p-80a-switch-red-toggle', # switch disconnector, not an isolator
   'https://hager.com/au/products/product-information/jg220in-ip66-20a-2p-isolator'
]
hager_spreaders_of_interest = [
   'https://hager.com/au/products/product-information/hya014h-spreader-x160-3p-collar',
   'https://hager.com/au/products/product-information/hyb011h-spreader-x-p250-p250-3p',
   'https://hager.com/au/products/product-information/hyw011h-spread-term-extens-x630-p630-3p-400a'
]

rittal_urls_of_interest = [
    'https://www.rittal.com/au-en/products/PG20231215SCH101/PG20231512SCH301/PRO0023?variantId=1280500',
    'https://www.rittal.com/au-en/products/PG20231215SCH101/PG20240111SCH301/PRO70035?variantId=8004000',
    'https://www.rittal.com/au-en/products/PG20231215SCH101/PG20231512SCH301/PRO0023?variantId=1350500'
]

TEST_REGISTRY = [
   ("abb", "mccb", abb_mccbs_of_interest, AbbScraper),
   ("hager", "mccb", hager_mccbs_of_interest, HagerScraper),

   ("abb", "contactor", abb_contactors_of_interest, AbbScraper),
   ("hager", "contactor", hager_contactors_of_interest, HagerScraper),

   ("abb", "mcb", abb_mcbs_of_interest, AbbScraper),
   ("hager", "mcb", hager_mcbs_of_interest, HagerScraper),  

   ("abb", "motor_operator", abb_motor_operators_of_interest, AbbScraper),

   ("abb", "isolator", abb_isolators_of_interest, AbbScraper),
   ("hager", "isolator", hager_isolators_of_interest, HagerScraper),

   ("abb", "spreader", abb_spreaders_of_interest, AbbScraper),
   ("hager", "spreader", hager_spreaders_of_interest, HagerScraper),
]

def main():
   for brand, comp_type, url_list, ScraperClass in TEST_REGISTRY:
      print(f"\n>>> Starting batch: {brand.upper()} {comp_type.upper()}")

      for i, product_url in enumerate(url_list):
         print(f"Processing: {product_url}")
         raw_data = ScraperClass().return_dictionary_content(url=product_url)
         if not raw_data:
               print(f"FAILED: Could not fetch {product_url}")
               continue
         
         try:
               canonical_obj = map_to(brand, comp_type, raw_data)
               json_data = canonical_obj.to_dict()
               
               filename = f"./output/{brand}_{comp_type}_{i}_canonical.json"
               write_json(json_data, filename)
               print(f"SUCCESS: Exported {filename}")
               
         except NotImplementedError as e:
               print(f"SKIP: {e}")
         except Exception as e:
               print(f"ERROR: Mapping failed for {product_url}: {e}")

if __name__ == "__main__":
    rittal_scraper = RittalScraper()
    raw_data = rittal_scraper.return_dictionary_content(url=rittal_urls_of_interest[0], export_json=True, export_path="./output/rittal_raw.json")
    canonical_enclosure = map_to("rittal", "enclosure", raw_data)
    canonical_dict = canonical_enclosure.to_dict()
    write_json(canonical_dict, "./output/rittal_canonical.json")
    