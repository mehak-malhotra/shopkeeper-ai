import os
from dotenv import load_dotenv
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

# Flask and CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000"]}}, supports_credentials=True)

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
GEMINI_API_KEY="AIzaSyDN6BSxkHUMru8-m51NmfU0SUKGFBbFYmk"
GEMINI_API_URL="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
BACKEND_URL="http://localhost:5000"
MONGO_URI="mongodb+srv://user:user%40123@himanshudhall.huinsh2.mongodb.net/"
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
                }
            }
        }
        
        return jsonify({
            'success': True, 
            'data': shop_data,
            'message': f'Extracted {len(inventory)} inventory items, {len(customers)} customers, and {len(orders)} orders'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
