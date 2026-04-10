import json
from flask import Flask, request, render_template, url_for
from operator import index
import requests
from bs4 import BeautifulSoup
from werkzeug.utils import redirect
from flask_htmx import HTMX

app = Flask(__name__)
htmx = HTMX(app)

store_link_format = {
    "Walmart" : "https://www.walmart.ca/en/ip/",
    "Amazon" : "https://www.amazon.ca/dp/",
    "Costco" : "https://www.costco.ca/p/-/",
}

# gets number of "item" in a string (looks in order, item_name: "1|2|3").
# usage: find_number_of_items("45 mega rolls", "rolls", "equal|equals|rolls") --> returns 45
def find_number_of_items(item_description: str, item_name:str):
    if item_description:
        item_description = item_description.lower().replace("ply sheets", "")
        start_pos = ""
        for item in item_name.split("|"):
            start_pos = item_description.find(item)
            if start_pos != -1: break

        words = item_description[0:start_pos].split()

        for i in range(len(words)-1, -1, -1):
            try:
                float(words[i])
            except ValueError:
                pass
            else:
                return float(words[i])
    return None

# For paths you can use dot notation as a string to navigate json (e.g. "store.product.price")
class Data:
    def __init__(self, data_list:list, store_name:str, name_path:str, id_path:str, img_url_path:str, price_path:str):
        self.data = data_list
        self.store_name = store_name
        self.item_name = name_path
        self.item_id = id_path
        self.item_img_url = img_url_path
        self.item_price = price_path

def pull_data_from_path(data, path : str):
    for item in path.split("."):
        if data:
            data = data.get(item)
    return data

def extract_data(dt : Data):
    new_list = []
    for product in dt.data:
        new_item = {
            "store": dt.store_name,
            "name": pull_data_from_path(product, dt.item_name),
            "id": pull_data_from_path(product, dt.item_id),
            "img_url": pull_data_from_path(product, dt.item_img_url),
            "price": pull_data_from_path(product, dt.item_price),
            "number_of_rolls": None,
            "sheets_per_roll": None,
            "price_per_sheet": None,
            "price_per_thousand_sheets": None,
            "link": None,
        }

        if new_item.get("name") and new_item.get("price"):
            try:
                number_of_rolls = find_number_of_items(new_item.get("name"), "×| x |equal|equals|rolls|")
                sheets_per_roll = find_number_of_items(new_item.get("name"), "sheets|")
                new_item["number_of_rolls"] = number_of_rolls
                new_item["sheets_per_roll"] = sheets_per_roll
                new_item["price_per_sheet"] = float(new_item.get("price")) / (number_of_rolls * sheets_per_roll)
                new_item["price_per_thousand_sheets"] = "{:.2f}". format(new_item["price_per_sheet"] * 1000)
                new_item["link"] = store_link_format.get(new_item.get("store")) + new_item.get("id")

            except ZeroDivisionError:
                pass
            except TypeError:
                pass
            else:
                new_list.append(new_item)

    return new_list


#############################################
# get JSON and parse all useless data
with open("amazon.JSON", "r") as file:
    amazon_json = json.load(file)

with open("walmart.JSON", "r") as file:
    walmart_json = json.load(file)

with open("costco.JSON", "r") as file:
    costco_json = json.load(file)

amazon_data = Data(amazon_json["searchProductDetails"],
             "Amazon",
             "productDescription",
             "asin",
             "imgUrl",
             "price")

walmart_data = Data(walmart_json["search_results"],
             "Walmart",
             "product.title",
             "product.item_id",
             "images.main_image",
             "offers.primary.price")

costco_data = Data(costco_json["data"]["products"],
             "Costco",
             "item_short_description",
             "item_number",
             "image",
             "item_location_pricing_pricePerUnit_price")

list_of_amazon_products = extract_data(amazon_data)
list_of_walmart_products = extract_data(walmart_data)
list_of_costco_products = extract_data(costco_data)
sorted_data_list = (sorted(list_of_walmart_products + list_of_amazon_products + list_of_costco_products, key=lambda d: d['price_per_sheet']))



@app.route("/", methods=["GET", "POST"])
def index():
    return redirect(url_for("home", page_number=1))

@app.route("/<int:page_number>", methods=["GET", "POST"])
def home(page_number):
    if htmx:
        return render_template("partials/stock.html", items=sorted_data_list, current_page=page_number) + render_template("partials/stock-page.html", items=sorted_data_list, current_page=page_number)
    return render_template("index.html", items=sorted_data_list, current_page=page_number)

if __name__ == "__main__":
    app.run(debug=True)