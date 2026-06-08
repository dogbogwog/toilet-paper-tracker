from dbm import sqlite3
# from sqlite3 import OperationalError

from flask_htmx import HTMX
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask import Flask, render_template, request
import price_updater
import os

app = Flask(__name__)
htmx = HTMX(app)

# CREATE DATABASE
class Base(DeclarativeBase):
    pass

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///items.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///posts.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class TPItem(db.Model):
    __tablename__ = "tp_item_list"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    price: Mapped[str] = mapped_column(Float, nullable=False)
    number_of_rolls: Mapped[str] = mapped_column(Integer, nullable=False)
    sheets_per_roll: Mapped[str] = mapped_column(Integer, nullable=False)
    price_per_thousand_sheets: Mapped[str] = mapped_column(Float, nullable=False)
    link: Mapped[str] = mapped_column(String(250), nullable=False)
    link_id: Mapped[str] = mapped_column(String(250), nullable=False)
    price_per_sheet: Mapped[str] = mapped_column(Float, nullable=False)

with app.app_context():
    db.create_all()

def filter_data_list(sorted_data_list, **filter_items):
    new_list = [item for item in sorted_data_list
                if not (filter_items["cost_1"] and float(item["price_per_thousand_sheets"]) <= 2.00)
                and not (filter_items["cost_2"] and 2.0 < float(item["price_per_thousand_sheets"]) <= 3.50)
                and not (filter_items["cost_3"] and float(item["price_per_thousand_sheets"]) > 3.50)]

    if filter_items["f_brand"] != "default":
        new_list = [item for item in sorted_data_list
                    if item.get('name').split()[0] == filter_items["f_brand"]]

    return new_list

@app.route("/", methods=["GET", "POST"])
def index():

    sorted_data_list = []
    item_list = {}

    try:
        db_list = db.session.execute(db.select(TPItem)).scalars().all()
        for item in db_list:
            sorted_data_list.append({
                "store": item.store,
                "name": item.name,
                "link_id": item.link_id,
                "price": item.price,
                "number_of_rolls": item.number_of_rolls,
                "sheets_per_roll": item.sheets_per_roll,
                "price_per_sheet": item.price_per_sheet,
                "price_per_thousand_sheets": item.price_per_thousand_sheets,
                "link": item.link,
            })

        item_list = db.session.execute(db.select(TPItem)).scalars().all()

    except OperationalError as e:
        print(f"error: no database {e}")


    unique_brand_names = set([item.get('name').split()[0] for item in sorted_data_list])
    page_number = request.args.get('page_num', default=1, type=int)

    def get_bool(key):
        return request.args.get(key, 'false').lower() == 'true'

    c1 = get_bool('cost_1')
    c2 = get_bool('cost_2')
    c3 = get_bool('cost_3')
    b1 = request.args.get('f_brand', 'default')


    filtered_item_list = filter_data_list(sorted_data_list, cost_1 = c1, cost_2 = c2, cost_3 = c3, f_brand = b1)

    if htmx:
        html_filters = render_template("partials/filter-buttons.html", filter_cost_1=c1, filter_cost_2=c2, filter_cost_3=c3, f_brand=b1, unique_brand_names=unique_brand_names)
        html_cards = render_template("partials/stock.html", items=filtered_item_list, current_page=page_number)
        html_nav = render_template("partials/stock-page.html", items=filtered_item_list, current_page=page_number)
        return html_cards + html_nav + html_filters
    return render_template("index.html", items=filtered_item_list, current_page=page_number, filter_cost_1=c1, filter_cost_2=c2, filter_cost_3=c3, f_brand=b1, unique_brand_names=unique_brand_names)


@app.route("/FAQ")
def frequent_asked_questions():
    return render_template("FAQ.html")


@app.route('/tasks/update-prices', methods=['POST'])
def trigger_price_update():
    # Security check: Make sure the cron job sends the password
    # (Matches the password you will put in cron-job.org)
    SECRET_TOKEN = os.environ.get('cron-job-key')

    provided_token = request.headers.get("Authorization")
    if provided_token != f"Bearer {SECRET_TOKEN}":
        return {"error": "Unauthorized"}, 401

    try:
        # Move the script execution INSIDE the route
        price_updater.fetch_and_replace_prices()
        return {"status": "success", "message": "Prices updated successfully!"}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


# if __name__ == "__main__":
#     app.run(host='127.0.0.1', port=5001, debug=True)

if __name__ == "__main__":
    app.run(debug=False, port=5001)