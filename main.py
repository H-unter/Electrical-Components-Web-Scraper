from scraper import HagerScraper, AbbScraper

def main():
   df1 = HagerScraper().scrape("HEC041H", export_csv=True)
   df2 = AbbScraper().scrape("1SDA068056R1", export_csv=True)
   print(df1)
   print(df2)

if __name__ == "__main__":
    main()