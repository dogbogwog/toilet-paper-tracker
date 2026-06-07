import json
import requests
import os


def fetch_and_replace_prices():
    from main import TPItem, db, app

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
                "link_id": pull_data_from_path(product, dt.item_id),
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
                    new_item["link"] = store_link_format.get(new_item.get("store")) + new_item.get("link_id")
                    new_item["name"] = new_item["name"].split()[0]


                except ZeroDivisionError:
                    pass
                except TypeError:
                    pass
                else:
                    new_list.append(new_item)

        return new_list


    #############################################
    # get JSON and parse all useless data
    # with open("amazon.JSON", "r") as file:
    #     amazon_json = json.load(file)
    #
    # with open("walmart.JSON", "r") as file:
    #     walmart_json = json.load(file)
    #
    # with open("costco.JSON", "r") as file:
    #     costco_json = json.load(file)


    amazon_json = {}
    walmart_json = {}
    costco_json = {}

    amazon_data = {}
    walmart_data = {}
    costco_data = {}

    # AMAZON
    URL = "http://api.axesso.de/amz/amazon-search-by-keyword-asin"
    headers = {
        "axesso-api-key": (os.environ.get('amazon_key')),
        "Cache-Control": "no-cache",
    }
    params = {
        "domainCode": "ca",
        "keyword": "toilet paper",
        "page": 1,
    }
    amazon_json = requests.get(URL, params=params, headers=headers).json()
    #
    # # WALMART API
    params = {
        "api_key": (os.environ.get('walmart_key')),
        "type": "search",
        "search_term": "toilet paper",
        "walmart_domain": "walmart.ca"
    }
    walmart_json = requests.get('https://api.bluecartapi.com/request', params).json()

    # # COSTCO API
    url = "https://real-time-costco-data.p.rapidapi.com/search"
    querystring = {"query": "Toilet Paper", "country": "CA", "language": "en-CA", "start": "0"}
    headers = {
        "x-rapidapi-key": (os.environ.get('costco_key')),
        "x-rapidapi-host": "real-time-costco-data.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    costco_json = requests.get(url, headers=headers, params=querystring).json()


    try:
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
    except KeyError:
        print("Missing KeyError")

    list_of_amazon_products = extract_data(amazon_data)
    list_of_walmart_products = extract_data(walmart_data)
    list_of_costco_products = extract_data(costco_data)
    sorted_data_list = (sorted(list_of_walmart_products + list_of_amazon_products + list_of_costco_products, key=lambda d: d['price_per_sheet']))


    with app.app_context():
        db.create_all()

        db.session.query(TPItem).delete()
        db.session.commit()

    # Loop through the fresh list and add them to the database
    with app.app_context():
        for item in sorted_data_list:
            post = TPItem(
                store=item["store"],
                name=item["name"],
                price=item["price"],
                link_id=item["link_id"],
                number_of_rolls=item["number_of_rolls"],
                sheets_per_roll=item["sheets_per_roll"],
                price_per_sheet=item["price_per_sheet"],
                price_per_thousand_sheets=item["price_per_thousand_sheets"],
                link=item["link"],
            )
            db.session.add(post)
            db.session.commit()

