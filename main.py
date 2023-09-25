import os
import re
import json
import dataclasses
import configparser
from typing import Optional

import pandas as pd

from utils import Logger

config = configparser.ConfigParser()

with open("./settings/settings.ini", "r") as file:
    config.read_file(file)

OUTPUT_PATH = config.get("paths", "output_path")

INPUT_NEW_FILES_PATH = config.get("paths", "new_json_files_path")

INPUT_OLD_FILES_PATH = config.get("paths", "old_json_files_path")

@dataclasses.dataclass
class FileDesc:
    """Store file descriptions i.e. file name, products before and products after"""
    file_name: str
    products_count_before: int
    products_count_after: int = 0

@dataclasses.dataclass
class Product:
    product: dict[str, str|int|list[dict]]

    def __post_init__(self) -> None:
        self.name = self.product["name"]

        try:
            self.price = self.product["offers"][0].get("price")
        except:
            self.price = None

class JsonProcessor:
    """Matches the products in the new json files to those in the old json files and remove matches"""
    def __init__(self) -> None:
        self.logger = Logger(__class__.__name__)
        self.logger.info("*****JsonProcessor started*****")

        self.products = []
        self.files_processed = []
        self.status: list[FileDesc] = []

        self.new_files = self.__read_files(INPUT_NEW_FILES_PATH)
        self.old_files = self.__read_files(INPUT_OLD_FILES_PATH)

        self.product_threads_num = 500

    def __read_files(self, path: str) -> list[str]:
        """Reads all the json files in the given directory"""
        return [f"{path}{filename}" for filename in os.listdir(path) if filename.endswith(".json")]

    def __read_json(self, file_path: str) -> Optional[list[dict[str, str|int|dict]]]:
        """Read products from the given json file path"""
        try:
            with open(file_path) as file:
                return json.load(file)
        except:
            self.logger.error("Error encountered while reading {}".format(file_path))
    
    def __match_filename_to_old_filenames(self, file_path: str) -> list[str]:
        """Matches the new filename to other filenames in the old files"""
        file_matches = []

        file_slugs = file_path.split("/")[-1].replace(".json", "").split(".")

        file_domain = file_slugs[1] if len(file_slugs) == 3 else file_slugs[0]
        
        [file_matches.append(file) for file in self.old_files if re.search(rf"{file_domain}", file, re.I)]
        
        return file_matches
    
    def __save(self, products: list[dict[str, str|int|dict]], file_name: str) -> None:
        """Saves the products remaining after processing"""
        self.logger.info("Saving filtered assets...")

        file_name = file_name.replace('.json', '_filtered.json')

        with open(f"{OUTPUT_PATH}{file_name}", "w") as file:
            json.dump(products, file, indent=4)

        self.logger.info("Filtered assets saved to {}".format(file_name))
    
    def __save_status(self) -> None:
        """Saves the status"""
        self.logger.info("Saving status...")

        file_status = [dataclasses.asdict(status) for status in self.status]

        df = pd.DataFrame(file_status)

        df.to_excel("./status/status.xlsx", index=False)

        self.logger.info("Status saved.")

    def run(self) -> None:
        """Entry point to the json processor"""
        self.logger.info("Processing files...")

        for index, file in enumerate(self.new_files):
            self.logger.info("Processing file > {}".format(file.split("/")[-1]))

            self.products = self.__read_json(file_path=file)

            if self.products is None: continue

            status = FileDesc(file_name=file.split("/")[-1], products_count_before=len(self.products))

            matching_files = self.__match_filename_to_old_filenames(file_path=file)

            for old_file in matching_files:
                self.logger.info("Comparing to {}".format(old_file.split("/")[-1]))

                products_before = len(self.products)

                old_products = self.__read_json(file_path=old_file)

                duplicated_products = []

                for new_product in self.products:
                    product = Product(new_product)

                    for old_product in old_products:
                        _old_product = Product(old_product)

                        if product.name == _old_product.name and product.price == _old_product.price:
                            duplicated_products.append(product.product)

                [self.products.remove(product) for product in duplicated_products if product in self.products]

                self.logger.info("Products before: %s || Products after: %s" % (products_before, len(self.products)))
            
            if not len(matching_files):
                self.logger.info("No matching files found for {}".format(file.split("/")[-1]))
            
            self.__save(self.products, file_name=file.split("/")[-1])

            status.products_count_after = len(self.products)

            self.status.append(status)
 
            if index % 10 == 0 and index > 0:
                self.__save_status()
        
        self.__save_status()

        self.logger.info("Done")


if __name__ == "__main__":
    app = JsonProcessor()
    app.run()