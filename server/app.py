from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import joinedload
from models import db, Restaurant, Pizza, RestaurantPizza
import os
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)

@app.route("/")
def index():
    app.logger.info("Index route was accessed.")
    return "<h1>Code challenge</h1>"

# Get all restaurants
@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    restaurants = Restaurant.query.all()
    response = [
        {
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
        }
        for restaurant in restaurants
    ]
    return jsonify(response)

# Get restaurant by ID
@app.route("/restaurants/<int:id>", methods=["GET"])
def get_restaurant_by_id(id):
    try:
        # Fetch restaurant with related pizzas using correct class-bound attribute
        restaurant = db.session.get(Restaurant, id, options=[joinedload(Restaurant.restaurant_pizzas)])

        
        # Handle restaurant not found
        if not restaurant:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)
        
        # Build response
        response = {
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
            "restaurant_pizzas": [
                {"pizza_id": rp.pizza_id, "price": rp.price} for rp in restaurant.restaurant_pizzas
            ],
        }
        return jsonify(response)
    except Exception as e:
        # Log and return a 500 error for debugging
        app.logger.error(f"Error retrieving restaurant by ID: {e}")
        return make_response(jsonify({"error": "Internal server error"}), 500)

# Delete restaurant by ID
@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = db.session.get(Restaurant, id)

    if restaurant:
        db.session.delete(restaurant)
        db.session.commit()
        return "", 204
    else:
        return make_response(jsonify({"error": "Restaurant not found"}), 404)

# Get all pizzas
@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    pizzas = Pizza.query.all()
    response = [
        {
            "id": pizza.id,
            "name": pizza.name,
            "ingredients": pizza.ingredients,
        }
        for pizza in pizzas
    ]
    return jsonify(response)

# Create a restaurant_pizza entry
@app.route("/restaurant_pizzas", methods=["POST"])
def create_restaurant_pizza():
    data = request.get_json()
    pizza_id = data.get("pizza_id")
    restaurant_id = data.get("restaurant_id")
    price = data.get("price")

    # Validate that pizza and restaurant exist
    pizza = db.session.get(Pizza, pizza_id)

    restaurant = db.session.get(Restaurant, restaurant_id)
    if not pizza or not restaurant:
        return make_response(jsonify({"error": "Pizza or Restaurant not found"}), 404)

    # Validate price range
    if not (1 <= price <= 30):
        return make_response(jsonify({"errors": ["validation errors"]}), 400)

    # Create the new entry in RestaurantPizza
    restaurant_pizza = RestaurantPizza(
        pizza_id=pizza_id, restaurant_id=restaurant_id, price=price
    )
    db.session.add(restaurant_pizza)
    db.session.commit()

    response = {
        "id": restaurant_pizza.id,
        "price": restaurant_pizza.price,
        "pizza_id": restaurant_pizza.pizza_id,
        "restaurant_id": restaurant_pizza.restaurant_id,
        "pizza": {
            "id": pizza.id,
            "name": pizza.name,
            "ingredients": pizza.ingredients,
        },
        "restaurant": {
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
        },
    }

    return jsonify(response), 201

# Error handler for 404
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({"error": "Not found"}), 404)

# Error handler for 400
@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({"error": "Bad request"}), 400)

if __name__ == "__main__":
    app.run(port=5555, debug=True)