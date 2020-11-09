
from itemadapter import ItemAdapter
from spiders.base_vars import FIELDNAMES
import csv


class IconsoftCrawlerPipeline:

    def process_item(self, item, spider):
        writer = csv.DictWriter(
            open(f"crawl_saves/{item['filename']}.csv", mode='a+'),
            fieldnames=FIELDNAMES)

        return writer.writerow(item)
