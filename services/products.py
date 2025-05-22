import requests 
from flask import Flask, jsonify, request, make_response
import jwt
from functools import wraps
import json
import os
# ✅ Removed DecodeError import
# from jwt.exceptions import DecodeError

app = Flask(__name__)
port = int(os.environ.get('PORT', 8000))
BASE_URL = "https://dummyjson.com"

app.config['SECRET_KEY'] = os.urandom(24)

with open('users.json', 'r') as f:
    users = json.load(f)

@app.route('/auth', methods=['POST'])
def authenticate_user():
    if request.headers['Content-Type'] != 'application/json':
        return jsonify({'error': 'Unsupported Media Type'}), 415
    username = request.json.get('username')
    password = request.json.get('password')
    for user in users:
        if user['username'] == username and user['password'] == password:
            token = jwt.encode({'user_id': user['id']}, app.config['SECRET_KEY'], algorithm="HS256")
            if isinstance(token, bytes):  # 🔧 Fix for PyJWT 2.x
                token = token.decode('utf-8')
            response = make_response(jsonify({'message': 'Authentication successful'}))
            response.set_cookie('token', token)
            return response, 200
    return jsonify({'error': 'Invalid username or password'}), 401

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return jsonify({'error': 'Authorization token is missing'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
        except jwt.InvalidTokenError:  # ✅ Updated to catch InvalidTokenError
            return jsonify({'error': 'Authorization token is invalid'}), 401
        return f(current_user_id, *args, **kwargs)
    return decorated

@app.route("/")
def home():
    return "Hello, this is a Flask Microservice"

@app.route('/products', methods=['GET'])
def get_products():
    response = requests.get(f"{BASE_URL}/products")
    if response.status_code != 200:
        return jsonify({'error': response.json().get('message', 'Failed to fetch products')}), response.status_code
    products = []
    for product in response.json().get('products', []):
        product_data = {
            'id': product.get('id'),
            'title': product.get('title'),
            'brand': product.get('brand'),
            'price': product.get('price'),
            'description': product.get('description')
        }
        products.append(product_data)
    return jsonify({'data': products}), 200 if products else 204

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    response = requests.get(f"{BASE_URL}/products/{id}")
    if response.status_code != 200:
        return jsonify({'error': response.json().get('message', 'Product not found')}), response.status_code
    product = response.json()
    product_data = {
        'id': product.get('id'),
        'title': product.get('title'),
        'brand': product.get('brand'),
        'price': product.get('price'),
        'description': product.get('description')
    }
    return jsonify({'data': product_data}), 200 if product_data else 204

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=port)
