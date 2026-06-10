from scraper import HagerScraper, AbbScraper

df = HagerScraper().scrape("HEC041H", export_csv=True)