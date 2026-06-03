import json
from os.path import split

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
unique_brand_names = set([item.get('name').split()[0] for item in sorted_data_list])

def filter_data_list(**filter_items):
    new_list = [item for item in sorted_data_list
                if not (filter_items["cost_1"] and float(item["price_per_thousand_sheets"]) <= 2.30)
                and not (filter_items["cost_2"] and 2.30 < float(item["price_per_thousand_sheets"]) <= 3.50)
                and not (filter_items["cost_3"] and float(item["price_per_thousand_sheets"]) > 3.50)]

    if filter_items["f_brand"] != "default":
        new_list = [item for item in sorted_data_list
                    if item.get('name').split()[0] == filter_items["f_brand"]]

    return new_list

@app.route("/", methods=["GET", "POST"])
def index():
    page_number = request.args.get('page_num', default=1, type=int)

    def get_bool(key):
        return request.args.get(key, 'false').lower() == 'true'

    c1 = get_bool('cost_1')
    c2 = get_bool('cost_2')
    c3 = get_bool('cost_3')
    b1 = request.args.get('f_brand', 'default')

    filtered_item_list = filter_data_list(cost_1 = c1, cost_2 = c2, cost_3 = c3, f_brand = b1)
    # print(unique_brand_names)

    if htmx:
        html_filters = render_template("partials/filter-buttons.html", filter_cost_1=c1, filter_cost_2=c2, filter_cost_3=c3, f_brand=b1, unique_brand_names=unique_brand_names)
        html_cards = render_template("partials/stock.html", items=filtered_item_list, current_page=page_number)
        html_nav = render_template("partials/stock-page.html", items=filtered_item_list, current_page=page_number)
        return html_cards + html_nav + html_filters
    return render_template("index.html", items=filtered_item_list, current_page=page_number, filter_cost_1=c1, filter_cost_2=c2, filter_cost_3=c3, f_brand=b1, unique_brand_names=unique_brand_names)


@app.route("/FAQ")
def frequent_asked_questions():
    return render_template("FAQ.html")


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5001, debug=True)