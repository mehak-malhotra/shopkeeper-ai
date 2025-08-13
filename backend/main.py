import os
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import uuid
import requests as ext_requests
import certifi
import re
from difflib import get_close_matches
from datetime import datetime
import hashlib
import secrets
from functools import wraps
import base64
import io
from PIL import Image
import pytesseract
from rapidfuzz import fuzz, process
import json

from flask import Flask
from flask_cors import CORS
import os

app = Flask(__name__)

# Allow specific origin + credentials + methods + headers
CORS(
    app,
    resources={r"/api/*": {"origins": "https://shopkeeper-ai.vercel.app"}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"]
)

@app.route("/")
def home():
    return "Server is running ✅"


# # MongoDB connection
# try:
#     load_dotenv()
#     MONGO_URI = os.getenv("MONGO_URI")
#     GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
#     GEMINI_API_URL = os.getenv("GEMINI_API_URL")
#     client = MongoClient(
#         MONGO_URI,
#         tls=True,
#         tlsCAFile=certifi.where(),
#         serverSelectionTimeoutMS=5000
#     )
#     client.server_info()
#     print("MongoDB connection successful!")
# except Exception as e:
#     print(f"MongoDB connection failed: {e}")
#     raise
MONGO_URI = os.getenv("MONGO_URI")
JWT_SECRET = os.getenv("JWT_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = os.getenv("GEMINI_API_URL")

if not all([MONGO_URI, JWT_SECRET, GEMINI_API_KEY, GEMINI_API_URL]):
    raise ValueError("One or more essential environment variables are missing.")
client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=5000
)
shop_db = client['shop_db']
user_col = shop_db['user']

# Simple token storage (in production, use Redis or database)
token_store = {}

def generate_token(user_email):
    token = secrets.token_urlsafe(32)
    token_store[token] = {"email": user_email}
    return token

def decode_token(token):
    return token_store.get(token)

def get_next_customer_id(user):
    """Get next customer ID for auto-increment"""
    customers = user.get('customers', [])
    if not customers:
        return 1
    
    # Find the highest customer_id
    max_id = 0
    for customer in customers:
        customer_id = customer.get('customer_id', 0)
        if isinstance(customer_id, int) and customer_id > max_id:
            max_id = customer_id
    
    return max_id + 1

def get_next_order_id(user):
    """Get next order ID for auto-increment"""
    orders = user.get('orders', [])
    if not orders:
        return 1
    
    # Find the highest order_id
    max_id = 0
    for order in orders:
        order_id = order.get('order_id', 0)
        if isinstance(order_id, int) and order_id > max_id:
            max_id = order_id
    
    return max_id + 1

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "Missing or invalid token"}), 401
        token = auth_header.split(" ")[1]
        payload = decode_token(token)
        if not payload or "email" not in payload:
            return jsonify({"success": False, "message": "Invalid token"}), 401
        request.user_email = payload["email"]
        return f(*args, **kwargs)
    return decorated

# Auth Routes
@app.route('/api/auth/register', methods=['POST'])
def register_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', '')
    phone = data.get('phone', '')
    ownerName = data.get('ownerName', '')
    address = data.get('address', '')
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400
    
    if user_col.find_one({'email': email}):
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    user_doc = {
        'email': email,
        'password': hashed_password,
        'name': name,
        'phone': phone,
        'ownerName': ownerName,
        'address': address,
        'inventory': [],
        'orders': [],
        'customers': []
    }
    user_col.insert_one(user_doc)
    return jsonify({'success': True, 'message': 'User registered successfully'})

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    try:
        user = user_col.find_one({'email': email}, {'_id': 0})
        if not user:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if user['password'] != hashed_password:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        token = generate_token(email)
        user.pop('password', None)
        user['token'] = token
        return jsonify({'success': True, 'user': user, 'token': token})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Server error'}), 500

# Inventory Routes
@app.route('/api/inventory', methods=['POST'])
@login_required
def add_inventory():
    data = request.json
    email = request.user_email
    user = user_col.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    inventory = user.get('inventory', [])
    name = data.get('name', '').strip()
    
    for item in inventory:
        if item['name'].lower() == name.lower():
            item['quantity'] += int(data.get('quantity', 0))
            user_col.update_one({'email': email}, {'$set': {'inventory': inventory}})
            return jsonify({'success': True, 'data': item, 'warning': f"Item '{name}' already exists. Quantity updated instead of adding a new item."})
    
    new_item = {
        'name': name,
        'quantity': int(data.get('quantity', 0)),
        'price': float(data.get('price', 0)),
        'category': data.get('category', 'General'),
        'minStock': int(data.get('minStock', 5))
    }
    inventory.append(new_item)
    user_col.update_one({'email': email}, {'$set': {'inventory': inventory}})
    return jsonify({'success': True, 'data': new_item})

@app.route('/api/inventory', methods=['GET'])
@login_required
def get_inventory():
    email = request.user_email
    user = user_col.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    return jsonify({'success': True, 'data': user.get('inventory', [])})

@app.route('/api/inventory/<item_name>', methods=['PUT'])
@login_required
def update_inventory(item_name):
    data = request.json
    email = request.user_email
    user = user_col.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    inventory = user.get('inventory', [])
    updated = False
    for item in inventory:
        if item['name'].lower() == item_name.lower():
            for k in ['name', 'price', 'quantity', 'minStock', 'category']:
                if k in data:
                    item[k] = data[k]
            updated = True
            break
    
    if updated:
        user_col.update_one({'email': email}, {'$set': {'inventory': inventory}})
        return jsonify({'success': True, 'data': item})
    return jsonify({'success': False, 'message': 'Item not found'}), 404

@app.route('/api/inventory/<item_name>', methods=['DELETE'])
@login_required
def delete_inventory(item_name):
    email = request.user_email
    user = user_col.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    inventory = user.get('inventory', [])
    new_inventory = [item for item in inventory if item['name'].lower() != item_name.lower()]
    if len(new_inventory) == len(inventory):
        return jsonify({'success': False, 'message': 'Item not found'}), 404

    user_col.update_one({'email': email}, {'$set': {'inventory': new_inventory}})
    return jsonify({'success': True, 'message': 'Item deleted'})

# Inventory update for order processing (used by chatbot)
@app.route('/api/inventory/update-quantities', methods=['POST'])
@login_required
def update_inventory_quantities():
    data = request.json
    email = request.user_email
    user = user_col.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    inventory = user.get('inventory', [])
    updates = data.get('updates', [])  # List of {name, quantity} objects
    
    for update in updates:
        item_name = update.get('name', '').lower()
        quantity_change = update.get('quantity', 0)
        
        item_found = False
        for item in inventory:
            if item['name'].lower() == item_name:
                current_quantity = item.get('quantity', 0)
                new_quantity = current_quantity + quantity_change
                
                if new_quantity < 0:
                    return jsonify({'success': False, 'message': f'Insufficient stock for {item_name}'}), 400
                
                item['quantity'] = new_quantity
                item_found = True
                break
        
        if not item_found:
            return jsonify({'success': False, 'message': f'Item {item_name} not found'}), 404
    
    user_col.update_one({'email': email}, {'$set': {'inventory': inventory}})
    return jsonify({'success': True, 'message': 'Inventory quantities updated'})

# Orders Routes
@app.route('/api/orders', methods=['POST'])
@login_required
def create_order():
    data = request.json
    email = request.user_email
    user = user_col.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    orders = user.get('orders', [])
    customers = user.get('customers', [])
    
    # Handle both old and new data structures
    customer_phone = data.get('customerPhone', data.get('phone', ''))
    customer_name = data.get('customerName', data.get('name', ''))
    customer_address = data.get('address', '')
    
    # Find customer_id by phone
    customer_id = None
    for c in customers:
        if c.get('phone') == customer_phone:
            customer_id = c.get('customer_id')
            break
    
    # If customer not found, create new customer
    if customer_id is None and customer_phone:
        customer_id = get_next_customer_id(user)
        new_customer = {
            'customer_id': customer_id,
            'name': customer_name,
            'phone': customer_phone,
            'address': customer_address,
            'user_email': email
        }
        customers.append(new_customer)
        user_col.update_one({'email': email}, {'$set': {'customers': customers}})
    
    order_id = get_next_order_id(user)
    order = {
        'order_id': order_id,
        'customer_id': customer_id,
        'customer_phone': customer_phone,
        'customer_name': customer_name,
        'items': data.get('items', []),
        'total': data.get('total', data.get('total_price', 0)),
        'status': data.get('status', 'pending'),
        'timestamp': data.get('timestamp', datetime.utcnow().isoformat() + "Z"),
        'notes': data.get('notes', '')
    }
    orders.append(order)
    user_col.update_one({'email': email}, {'$set': {'orders': orders}})
    return jsonify({'success': True, 'data': order, 'message': f"Order placed successfully! Your order ID is {order_id}."})

@app.route('/api/orders', methods=['GET'])
@login_required
def get_orders():
    email = request.user_email
    user = user_col.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    return jsonify({'success': True, 'data': user.get('orders', [])})

@app.route('/api/orders/<order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    email = request.user_email
    user = user_col.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    for order in user.get('orders', []):
        if order['order_id'] == order_id:
            return jsonify({'success': True, 'data': order})
        return jsonify({'success': False, 'message': 'Order not found'}), 404

@app.route('/api/orders/<order_id>', methods=['PUT'])
@login_required
def update_order(order_id):
    data = request.json
    email = request.user_email
    user = user_col.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    orders = user.get('orders', [])
    updated = False
    for order in orders:
        if order['order_id'] == order_id:
            for k in ['items', 'total', 'status', 'timestamp', 'notes']:
                if k in data:
                    order[k] = data[k]
            updated = True
            break
    
    if updated:
        user_col.update_one({'email': email}, {'$set': {'orders': orders}})
        return jsonify({'success': True, 'data': order})
    return jsonify({'success': False, 'message': 'Order not found'}), 404

@app.route('/api/orders/<order_id>', methods=['DELETE'])
@login_required
def delete_order(order_id):
    email = request.user_email
    user = user_col.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    orders = user.get('orders', [])
    new_orders = [order for order in orders if order['order_id'] != order_id]
    if len(new_orders) == len(orders):
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    user_col.update_one({'email': email}, {'$set': {'orders': new_orders}})
    return jsonify({'success': True, 'message': 'Order deleted'})

# New endpoint for direct order creation (compatible with your new logic)
@app.route('/api/orders/direct', methods=['POST'])
@login_required
def create_direct_order():
    data = request.json
    email = request.user_email
    user = user_col.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    orders = user.get('orders', [])
    customers = user.get('customers', [])
    
    # Extract data from your new format
    customer_data = data.get('customer', {})
    order_data = data.get('order', {})
    
    # Handle customer
    customer_phone = customer_data.get('phone', '')
    customer_name = customer_data.get('name', '')
    customer_address = customer_data.get('address', '')
    customer_email = customer_data.get('user_email', email)
    
    # Find or create customer
    customer_id = None
    for c in customers:
        if c.get('phone') == customer_phone:
            customer_id = c.get('customer_id')
            # Update customer info if needed
            c.update({
                'name': customer_name or c.get('name', ''),
                'address': customer_address or c.get('address', ''),
                'user_email': customer_email
            })
            break
    
    if customer_id is None and customer_phone:
        customer_id = get_next_customer_id(user)
        new_customer = {
            'customer_id': customer_id,
            'name': customer_name,
            'phone': customer_phone,
            'address': customer_address,
            'user_email': customer_email
        }
        customers.append(new_customer)
    
    # Create order
    order_id = get_next_order_id(user)
    order = {
        'order_id': order_id,
        'customer_id': customer_id,
        'customer_phone': customer_phone,
        'customer_name': customer_name,
        'items': order_data.get('items', []),
        'total': order_data.get('total', 0),
        'status': 'pending',
        'timestamp': datetime.utcnow().isoformat() + "Z",
        'notes': order_data.get('notes', '')
    }
    
    orders.append(order)
    user_col.update_one({'email': email}, {'$set': {'orders': orders, 'customers': customers}})
    
    return jsonify({
        'success': True,
        'data': {
            'order_id': order_id,
            'customer_id': customer_id,
            'total': order['total']
        },
        'message': f"Order placed successfully! Order ID: {order_id}, Customer ID: {customer_id}"
    })

# Customers Routes
@app.route('/api/customers', methods=['GET'])
@login_required
def get_customers():
    email = request.user_email
    user = user_col.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    customers = [
        {k: v for k, v in customer.items() if k != 'password'}
        for customer in user.get('customers', [])
    ]
    return jsonify({'success': True, 'data': customers})

@app.route('/api/customers/add', methods=['POST'])
@login_required
def add_customer():
    data = request.json
    email = request.user_email
    user = user_col.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    customers = user.get('customers', [])
    
    # Check if customer already exists by phone
    phone = data.get('phone', '')
    for existing_customer in customers:
        if existing_customer.get('phone') == phone:
            # Update existing customer
            existing_customer.update({
                'name': data.get('name', existing_customer.get('name', '')),
                'address': data.get('address', existing_customer.get('address', '')),
                'user_email': data.get('user_email', email)
            })
            user_col.update_one({'email': email}, {'$set': {'customers': customers}})
            return jsonify({'success': True, 'data': existing_customer})
    
    # Create new customer
    customer_id = get_next_customer_id(user)
    new_customer = {
        'customer_id': customer_id,
        'name': data.get('name', ''),
        'phone': phone,
        'address': data.get('address', ''),
        'user_email': data.get('user_email', email)
    }
    customers.append(new_customer)
    user_col.update_one({'email': email}, {'$set': {'customers': customers}})
    return jsonify({'success': True, 'data': new_customer})

# Customer lookup by phone (used by chatbot)
@app.route('/api/customers/find-by-phone', methods=['POST'])
@login_required
def find_customer_by_phone():
    data = request.json
    phone = data.get('phone', '')
    email = request.user_email
    user = user_col.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    customers = user.get('customers', [])
    for customer in customers:
        if customer.get('phone') == phone:
            return jsonify({'success': True, 'data': customer})
    
    return jsonify({'success': False, 'message': 'Customer not found'}), 404

# Profile Routes
@app.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    email = request.user_email
    user = user_col.find_one({'email': email}, {'_id': 0})
    if user:
        return jsonify({'success': True, 'data': user})
    return jsonify({'success': False, 'message': 'User not found'}), 404

@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.json
    email = request.user_email
    update_fields = {k: v for k, v in data.items() if k in ['name', 'phone', 'address', 'ownerName']}
    result = user_col.update_one({'email': email}, {'$set': update_fields})
    if result.matched_count:
        updated = user_col.find_one({'email': email}, {'_id': 0})
        return jsonify({'success': True, 'data': updated})
    return jsonify({'success': False, 'message': 'User not found'}), 404

@app.route('/api/profile/password', methods=['PUT'])
@login_required
def update_password():
    data = request.json
    email = request.user_email
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')
    
    if not (email and current_password and new_password):
        return jsonify({'success': False, 'message': 'Email, current password, and new password are required'}), 400

    hashed_current = hashlib.sha256(current_password.encode()).hexdigest()
    user = user_col.find_one({'email': email, 'password': hashed_current})
    if not user:
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401

    hashed_new = hashlib.sha256(new_password.encode()).hexdigest()
    user_col.update_one({'email': email}, {'$set': {'password': hashed_new}})
    return jsonify({'success': True, 'message': 'Password updated successfully'})

# Dashboard Stats
@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def dashboard_stats():
    try:
        email = request.user_email
        user = user_col.find_one({'email': email})
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        orders = user.get('orders', [])
        inventory = user.get('inventory', [])
        
        total_orders = len(orders)
        pending_orders = sum(1 for order in orders if order.get('status') == 'pending')
        total_revenue = sum(order.get('total', 0) for order in orders)
        total_products = len(inventory)
        low_stock_items = sum(1 for item in inventory if item.get('quantity', 0) <= item.get('minStock', 0))
        
        stats = {
            'totalOrders': total_orders,
            'pendingOrders': pending_orders,
            'lowStockItems': low_stock_items,
            'totalRevenue': total_revenue,
            'totalProducts': total_products
        }
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Chatbot API
@app.route('/api/chatbot', methods=['POST'])
@login_required
def chatbot_api():
    data = request.json
    messages = data.get('messages', [])
    email = request.user_email
    
    user = user_col.find_one({'email': email})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    inventory = user.get('inventory', [])
    inventory_map = {item['name'].lower(): item for item in inventory}
    
    user_message = messages[-1] if messages else ''
    requested_items = [name for name in inventory_map if name in user_message.lower()]
    
    context = ""
    for name in requested_items:
        item = inventory_map[name]
        if item['quantity'] <= 0:
            context += f"No stock for {name}. "
        else:
            context += f"{name} in stock: {item['quantity']}. "
    
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    contents = []
    for i, m in enumerate(messages):
        role = "user" if i % 2 == 0 else "model"
        contents.append({"role": role, "parts": [{"text": m}]})
    gemini_data = {"contents": contents}
    if context:
        gemini_data["context"] = context
    
    resp = ext_requests.post(GEMINI_API_URL, headers=headers, params=params, json=gemini_data)
    resp.raise_for_status()
    gemini_reply = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return jsonify({"reply": gemini_reply, "context": context, "inventory": inventory})

# Extract all data for chatbot
@app.route('/api/chatbot/data', methods=['GET'])
@login_required
def get_chatbot_data():
    try:
        email = request.user_email
        user = user_col.find_one({'email': email})
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Extract inventory, customers, and orders
        inventory = user.get('inventory', [])
        customers = user.get('customers', [])
        orders = user.get('orders', [])
        
        # Create shop data structure
        shop_data = {
            "customers": customers,
            "orders": orders,  # Include actual orders
            "inventory": inventory,
            "current_customer": None,
            "current_order": None,
            "conversation_state": {
                "stage": "greeting",
                "customer_info": {},
                "order_items": [],
                "total_price": 0,
                "notes": "",
                "confirmations": {
                    "phone_confirmed": False,
                    "address_confirmed": False,
                    "order_complete": False,
                    "delivery_confirmed": False
                },
                "last_5_messages": [],
                "conversation_history": [],
                "chat_buffer": []
            }
        }
        
        return jsonify({
            'success': True, 
            'data': shop_data,
            'message': f'Extracted {len(inventory)} inventory items, {len(customers)} customers, and {len(orders)} orders'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def send_notification(order_id, customer_name, total_items):
    """Send notification after order creation"""
    try:
        print(f"🔔 Notification: New order {order_id} created for {customer_name} with {total_items} items")
        # In production, this could send email, SMS, or push notification
        return True
    except Exception as e:
        print(f"❌ Notification error: {e}")
        return False

def preprocess_image(image):
    """Basic image preprocessing for better OCR"""
    try:
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Resize if too large (OCR works better with reasonable sizes)
        max_size = 2000
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        return image
    except Exception as e:
        print(f"❌ Image preprocessing error: {e}")
        return image

def extract_items_from_ocr_text(ocr_text):
    """Use Gemini to extract structured items from OCR text"""
    try:
        prompt = f"""You are a smart assistant. Given messy handwritten shopping list text, extract a JSON list of items with names and quantities. If quantity is missing, assume 1. Example output: [{{"item": "Moong Dal", "quantity": 2}}]. Ignore headers like 'India Market'. Normalize spelling errors.

OCR Text: {ocr_text}

Return only valid JSON array with items and quantities:"""
        
        headers = {"Content-Type": "application/json"}
        params = {"key": GEMINI_API_KEY}
        
        gemini_data = {
            "contents": [{
                "role": "user",
                "parts": [{"text": prompt}]
            }]
        }
        
        response = ext_requests.post(GEMINI_API_URL, headers=headers, params=params, json=gemini_data)
        response.raise_for_status()
        
        gemini_reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        
        # Extract JSON from Gemini response
        try:
            # Find JSON array in the response
            start_idx = gemini_reply.find('[')
            end_idx = gemini_reply.rfind(']') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = gemini_reply[start_idx:end_idx]
                items = json.loads(json_str)
                return items
            else:
                print(f"❌ No JSON array found in Gemini response: {gemini_reply}")
                return []
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Gemini response: {gemini_reply}")
            return []
            
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return []

def fuzzy_match_items(requested_items, inventory_items):
    """Fuzzy match requested items with inventory items"""
    matched_items = []
    
    for requested_item in requested_items:
        item_name = requested_item.get('item', '').strip()
        requested_quantity = requested_item.get('quantity', 1)
        
        if not item_name:
            continue
        
        # Use RapidFuzz to find best match
        best_match = None
        best_score = 0
        
        for inventory_item in inventory_items:
            inventory_name = inventory_item.get('name', '').strip()
            
            # Calculate similarity score
            score = fuzz.ratio(item_name.lower(), inventory_name.lower())
            
            if score >= 85 and score > best_score:  # 85% similarity threshold
                best_match = inventory_item
                best_score = score
        
        if best_match:
            # Check stock availability
            available_quantity = best_match.get('quantity', 0)
            fulfilled_quantity = min(requested_quantity, available_quantity)
            
            if fulfilled_quantity > 0:
                matched_items.append({
                    'item_name': best_match['name'],
                    'requested_quantity': requested_quantity,
                    'fulfilled_quantity': fulfilled_quantity,
                    'price': best_match.get('price', 0),
                    'total_price': fulfilled_quantity * best_match.get('price', 0),
                    'match_score': best_score,
                    'available_stock': available_quantity
                })
            else:
                print(f"⚠️ Item '{item_name}' matched to '{best_match['name']}' but out of stock")
        else:
            print(f"❌ No match found for item: {item_name}")
    
    return matched_items

@app.route('/api/upload-image-order', methods=['POST'])
@login_required
def upload_image_order():
    """Image-to-order workflow endpoint"""
    try:
        email = request.user_email
        user = user_col.find_one({'email': email})
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Get customer info from request
        customer_phone = request.form.get('customer_phone', '')
        customer_name = request.form.get('customer_name', 'Unknown Customer')
        
        # Find or create customer
        customer_id = None
        customers = user.get('customers', [])
        
        if customer_phone:
            for customer in customers:
                if customer.get('phone') == customer_phone:
                    customer_id = customer.get('customer_id')
                    customer_name = customer.get('name', customer_name)
                    break
        
        if not customer_id:
            # Create new customer if not found
            customer_id = get_next_customer_id(user)
            new_customer = {
                'customer_id': customer_id,
                'name': customer_name,
                'phone': customer_phone,
                'address': '',
                'email': ''
            }
            customers.append(new_customer)
            user['customers'] = customers
            user_col.update_one({'email': email}, {'$set': {'customers': customers}})
        
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'No image file provided'}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'success': False, 'message': 'No image file selected'}), 400
        
        # Process the image
        try:
            # Read and preprocess image
            image = Image.open(image_file.stream)
            processed_image = preprocess_image(image)
            
            # Perform OCR
            ocr_text = pytesseract.image_to_string(processed_image)
            print(f"📝 OCR Text: {ocr_text}")
            
            if not ocr_text.strip():
                return jsonify({'success': False, 'message': 'No text found in image'}), 400
            
            # Extract items using Gemini
            requested_items = extract_items_from_ocr_text(ocr_text)
            print(f"🛒 Extracted items: {requested_items}")
            
            if not requested_items:
                return jsonify({'success': False, 'message': 'No items could be extracted from image'}), 400
            
            # Fuzzy match with inventory
            inventory_items = user.get('inventory', [])
            matched_items = fuzzy_match_items(requested_items, inventory_items)
            
            if not matched_items:
                return jsonify({'success': False, 'message': 'No items matched with inventory'}), 400
            
            # Calculate order total
            order_total = sum(item['total_price'] for item in matched_items)
            
            # Generate order ID
            next_order_id = get_next_order_id(user)
            order_id_str = f"{next_order_id:04d}"  # Format as "0001", "0002", etc.
            
            # Create order object
            order_items = []
            for item in matched_items:
                order_items.append({
                    'name': item['item_name'],
                    'quantity': item['fulfilled_quantity'],
                    'price': item['price'],
                    'total': item['total_price']
                })
            
            new_order = {
                'order_id': next_order_id,
                'customer_id': customer_id,
                'customerPhone': customer_phone,
                'customerName': customer_name,
                'items': order_items,
                'total': order_total,
                'status': 'pending',
                'timestamp': datetime.utcnow().isoformat() + "Z",
                'notes': f'Order created from image upload. OCR text: {ocr_text[:100]}...',
                'source': 'image_upload'
            }
            
            # Add order to user's orders
            orders = user.get('orders', [])
            orders.append(new_order)
            user['orders'] = orders
            user_col.update_one({'email': email}, {'$set': {'orders': orders}})
            
            # Update inventory quantities
            inventory_updates = []
            for item in matched_items:
                item_name = item['item_name']
                fulfilled_qty = item['fulfilled_quantity']
                
                for inv_item in inventory_items:
                    if inv_item['name'] == item_name:
                        inv_item['quantity'] = max(0, inv_item['quantity'] - fulfilled_qty)
                        inventory_updates.append({
                            'name': item_name,
                            'quantity': -fulfilled_qty
                        })
                        break
            
            # Update inventory in database
            user_col.update_one({'email': email}, {'$set': {'inventory': inventory_items}})
            
            # Send notification
            send_notification(order_id_str, customer_name, len(matched_items))
            
            # Prepare response
            response_data = {
                'order_id': order_id_str,
                'customer_name': customer_name,
                'customer_phone': customer_phone,
                'items': matched_items,
                'total_price': order_total,
                'status': 'pending',
                'timestamp': new_order['timestamp'],
                'ocr_text': ocr_text,
                'extracted_items': requested_items,
                'inventory_updates': inventory_updates
            }
            
            return jsonify({
                'success': True,
                'message': f'Order {order_id_str} created successfully from image',
                'data': response_data
            })
            
        except Exception as e:
            print(f"❌ Image processing error: {e}")
            return jsonify({'success': False, 'message': f'Image processing error: {str(e)}'}), 500
            
    except Exception as e:
        print(f"❌ Upload image order error: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use PORT from Render, default 5000 for local
    app.run(host="0.0.0.0", port=port, debug=False) 
