import json

with open("./output/www.als.com_6_filtered.json") as file:
    products = json.load(file)

print(len(products))

# import random

# for i in range(3):
#     new_products = random.sample(products, 80)

#     with open(f"./input-old/www.als.com_{i}.json", "w") as file:
#         json.dump(new_products, file, indent=4)