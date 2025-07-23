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

# Flask and CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# MongoDB connection
client = MongoClient(
    "mongodb+srv://dhallhimanshu1234:9914600112%40DHALLh@himanshudhall.huinsh2.mongodb.net/",
    tls=True,
    tlsCAFile=certifi.where()
)  # Cloud MongoDB
db = client['shop_db']
inventory_col = db['inventory']
orders_col = db['orders']
customers_col = db['customers'] # Added customers collection

# Home route
@app.route('/')
def home():
    return "Shop Assistant Backend Running!"

# -----------------------------
# Inventory Routes (MongoDB CRUD)
# -----------------------------

# Get all inventory items
@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    user_email = request.args.get('user_email')
    items = list(inventory_col.find({'user_email': user_email}, {'_id': 0}))
    # Only return the required fields
    for item in items:
        for k in list(item.keys()):
            if k not in ['id', 'name', 'price', 'quantity', 'minStock', 'category', 'user_email']:
                del item[k]
    return jsonify({'success': True, 'data': items})

# Add a new inventory item
@app.route('/api/inventory', methods=['POST'])
def add_inventory():
    data = request.json
    name = data.get('name', '').strip()
    user_email = data.get('user_email', '')
    quantity = int(data.get('quantity', 0))
    # Check for duplicate name for this user
    existing = inventory_col.find_one({'name': name, 'user_email': user_email})
    if existing:
        # Update the quantity of the existing item
        new_quantity = int(existing.get('quantity', 0)) + quantity
        inventory_col.update_one({'_id': existing['_id']}, {'$set': {'quantity': new_quantity}})
        updated_item = inventory_col.find_one({'_id': existing['_id']}, {'_id': 0})
        return jsonify({'success': True, 'data': updated_item, 'warning': f"Item '{name}' already exists. Quantity updated instead of adding a new item."})
    else:
        item_id = str(uuid.uuid4())[:8].upper()
        item = {
            'id': item_id,
            'name': name,
            'price': float(data.get('price', 0)),
            'quantity': quantity,
            'minStock': int(data.get('minStock', 5)),
            'category': data.get('category', 'General'),
            'user_email': user_email,
        }
        inventory_col.insert_one(item)
        if '_id' in item:
            del item['_id']
        return jsonify({'success': True, 'data': item})

# Update an inventory item
@app.route('/api/inventory/<item_id>', methods=['PUT'])
def update_inventory(item_id):
    data = request.json
    user_email = data.get('user_email')
    update_fields = {k: v for k, v in data.items() if k in ['name', 'price', 'quantity', 'minStock', 'category']}
    # Coerce types
    if 'price' in update_fields:
        update_fields['price'] = float(update_fields['price'])
    if 'quantity' in update_fields:
        update_fields['quantity'] = int(update_fields['quantity'])
    if 'minStock' in update_fields:
        update_fields['minStock'] = int(update_fields['minStock'])
    result = inventory_col.update_one({'id': item_id, 'user_email': user_email}, {'$set': update_fields})
    if result.matched_count:
        updated = inventory_col.find_one({'id': item_id, 'user_email': user_email}, {'_id': 0})
        # Only return the required fields
        filtered = {k: updated[k] for k in ['id', 'name', 'price', 'quantity', 'minStock', 'category', 'user_email'] if k in updated}
        return jsonify({'success': True, 'data': filtered})
    return jsonify({'success': False, 'message': 'Item not found'}), 404

# Delete an inventory item
@app.route('/api/inventory/<item_id>', methods=['DELETE'])
def delete_inventory(item_id):
    user_email = request.args.get('user_email')
    result = inventory_col.delete_one({'id': item_id, 'user_email': user_email})
    if result.deleted_count:
        return jsonify({'success': True, 'message': 'Item deleted'})
    return jsonify({'success': False, 'message': 'Item not found'}), 404

# Get a specific inventory item
@app.route('/api/inventory/<item_id>', methods=['GET'])
def get_inventory_item(item_id):
    user_email = request.args.get('user_email')
    item = inventory_col.find_one({'id': item_id, 'user_email': user_email}, {'_id': 0})
    if item:
        filtered = {k: item[k] for k in ['id', 'name', 'price', 'quantity', 'minStock', 'category', 'user_email'] if k in item}
        return jsonify({'success': True, 'data': filtered})
    return jsonify({'success': False, 'message': 'Item not found'}), 404

# -----------------------------
# Order Routes (MongoDB CRUD)
# -----------------------------
orders_col = db['orders']

# Update order schema to match frontend expectations
# Fields: id, customerPhone, customerName, items, total, status, timestamp, notes, user_email

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json
    # Generate a unique order id
    order_id = str(uuid.uuid4())[:8].upper()
    order = {
        'id': order_id,
        'customerPhone': data.get('customerPhone', ''),
        'customerName': data.get('customerName', ''),
        'items': data.get('items', []),
        'total': data.get('total', 0),
        'status': data.get('status', 'pending'),
        'timestamp': data.get('timestamp', ''),
        'notes': data.get('notes', ''),
        'user_email': data.get('user_email', ''),
    }
    orders_col.insert_one(order)
    return jsonify({'success': True, 'data': order})

@app.route('/api/orders', methods=['GET'])
def get_orders():
    user_email = request.args.get('user_email')
    orders = list(orders_col.find({'user_email': user_email}, {'_id': 0}))
    return jsonify({'success': True, 'data': orders, 'total': len(orders)})

@app.route('/api/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    user_email = request.args.get('user_email')
    order = orders_col.find_one({'id': order_id, 'user_email': user_email}, {'_id': 0})
    if order:
        return jsonify({'success': True, 'data': order})
    return jsonify({'success': False, 'message': 'Order not found'}), 404

@app.route('/api/orders/<order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.json
    user_email = data.get('user_email')
    update_fields = {k: v for k, v in data.items() if k in ['customerPhone', 'customerName', 'items', 'total', 'status', 'timestamp', 'notes']}
    result = orders_col.update_one({'id': order_id, 'user_email': user_email}, {'$set': update_fields})
    if result.matched_count:
        updated = orders_col.find_one({'id': order_id, 'user_email': user_email}, {'_id': 0})
        return jsonify({'success': True, 'data': updated})
    return jsonify({'success': False, 'message': 'Order not found'}), 404

@app.route('/api/orders/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    user_email = request.args.get('user_email')
    result = orders_col.delete_one({'id': order_id, 'user_email': user_email})
    if result.deleted_count:
        return jsonify({'success': True, 'message': 'Order deleted'})
    return jsonify({'success': False, 'message': 'Order not found'}), 404

# -----------------------------
# Calls Routes (in-memory for now)
# -----------------------------
calls_db = []

@app.route('/api/calls', methods=['GET'])
def get_calls():
    return jsonify({
        'success': True,
        'data': calls_db,
        'total': len(calls_db)
    })

@app.route('/api/calls', methods=['POST'])
def create_call():
    data = request.json
    call_id = f"CALL-{str(uuid.uuid4())[:8].upper()}"
    call = {
        'id': call_id,
        **data,
        'timestamp': str(data.get('timestamp', '')),
    }
    calls_db.append(call)
    return jsonify({'success': True, 'data': call})

@app.route('/api/calls/<call_id>', methods=['GET'])
def get_call(call_id):
    for call in calls_db:
        if call['id'] == call_id:
            return jsonify({'success': True, 'data': call})
    return jsonify({'success': False, 'message': 'Call not found'}), 404

# -----------------------------
# AI Endpoints (mocked)
# -----------------------------
@app.route('/api/ai/process-call', methods=['POST'])
def ai_process_call():
    # Mock AI processing
    result = {
        'callId': f"CALL-{str(uuid.uuid4())[:8].upper()}",
        'transcript': "Hello, I would like to order 2 liters of milk and 1 loaf of bread.",
        'summary': "Customer ordered milk (2L) and bread (1 loaf)",
        'extractedOrder': {
            'items': [
                {'name': 'Milk', 'quantity': 2, 'unit': 'liters'},
                {'name': 'Bread', 'quantity': 1, 'unit': 'loaf'}
            ]
        },
        'sentiment': 'positive',
        'confidence': 0.95
    }
    return jsonify({'success': True, 'data': result})

@app.route('/api/ai/generate-response', methods=['POST'])
def ai_generate_response():
    response = {
        'message': "Thank you for your order! I have 2 liters of milk and 1 loaf of bread available. The total comes to ₹70. Would you like me to arrange delivery?",
        'actions': [
            {'type': 'create_order', 'data': {'items': ['milk', 'bread'], 'total': 70}},
            {'type': 'check_inventory', 'data': {'items': ['milk', 'bread']}}
        ],
        'confidence': 0.92
    }
    return jsonify({'success': True, 'data': response})

# -----------------------------
# Dashboard Stats (mocked)
# -----------------------------
@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    user_email = request.args.get('user_email')
    if not user_email:
        return jsonify({'success': False, 'message': 'user_email is required'}), 400
    # Orders
    total_orders = orders_col.count_documents({'user_email': user_email})
    pending_orders = orders_col.count_documents({'user_email': user_email, 'status': 'pending'})
    total_revenue = sum(order.get('total', 0) for order in orders_col.find({'user_email': user_email}))
    # Inventory
    total_products = inventory_col.count_documents({'user_email': user_email})
    low_stock_items = inventory_col.count_documents({'user_email': user_email, '$expr': {'$lte': ['$quantity', '$minStock']}})
    stats = {
        'totalOrders': total_orders,
        'pendingOrders': pending_orders,
        'lowStockItems': low_stock_items,
        'totalRevenue': total_revenue,
        'totalProducts': total_products
    }
    return jsonify({'success': True, 'data': stats})

# -----------------------------
# Reports (mocked)
# -----------------------------
@app.route('/api/reports/sales', methods=['GET'])
def report_sales():
    sales_data = {
        'period': 'week',
        'totalSales': 12450,
        'totalOrders': 156,
        'averageOrderValue': 79.8,
        'topProducts': [
            {'name': 'Milk', 'quantity': 45, 'revenue': 1125},
            {'name': 'Bread', 'quantity': 38, 'revenue': 760},
            {'name': 'Rice', 'quantity': 25, 'revenue': 2000}
        ],
        'dailyBreakdown': [
            {'date': '2024-01-01', 'sales': 1200, 'orders': 15},
            {'date': '2024-01-02', 'sales': 1800, 'orders': 22}
        ]
    }
    return jsonify({'success': True, 'data': sales_data})

@app.route('/api/reports/inventory', methods=['GET'])
def report_inventory():
    inventory_report = {
        'totalProducts': 45,
        'lowStockItems': 3,
        'outOfStockItems': 1,
        'totalValue': 25000,
        'categories': [
            {'name': 'Dairy', 'count': 8, 'value': 5000},
            {'name': 'Bakery', 'count': 12, 'value': 3000},
            {'name': 'Grains', 'count': 15, 'value': 12000}
        ],
        'reorderSuggestions': [
            {'name': 'Milk', 'currentStock': 2, 'suggestedOrder': 20},
            {'name': 'Bread', 'currentStock': 5, 'suggestedOrder': 25}
        ]
    }
    return jsonify({'success': True, 'data': inventory_report})

# -----------------------------
# Settings (mocked)
# -----------------------------
@app.route('/api/settings', methods=['GET'])
def get_settings():
    settings = {
        'notifications': {
            'orderAlerts': True,
            'lowStockAlerts': True,
            'callNotifications': True,
            'emailNotifications': False
        },
        'ai': {
            'autoProcessCalls': True,
            'responseDelay': 2,
            'confidenceThreshold': 0.8
        },
        'business': {
            'operatingHours': {
                'start': '09:00',
                'end': '21:00'
            },
            'deliveryRadius': 5,
            'minimumOrderValue': 50
        }
    }
    return jsonify({'success': True, 'data': settings})

# -----------------------------
# Profile (mocked)
# -----------------------------
@app.route('/api/profile', methods=['GET'])
def get_profile():
    email = request.args.get('email')
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400
    user = db['users'].find_one({'email': email}, {'_id': 0})
    if user:
        return jsonify({'success': True, 'data': user})
    return jsonify({'success': False, 'message': 'User not found'}), 404

@app.route('/api/profile', methods=['PUT'])
def update_profile():
    data = request.json
    email = data.get('email')
    update_fields = {k: v for k, v in data.items() if k in ['shopName', 'phone', 'address', 'ownerName']}
    result = db['users'].update_one({'email': email}, {'$set': update_fields})
    if result.matched_count:
        updated = db['users'].find_one({'email': email}, {'_id': 0})
        return jsonify({'success': True, 'data': updated})
    return jsonify({'success': False, 'message': 'User not found'}), 404

@app.route('/api/profile/password', methods=['PUT'])
def update_password():
    data = request.json
    email = data.get('email')
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')
    if not (email and current_password and new_password):
        return jsonify({'success': False, 'message': 'Email, current password, and new password are required'}), 400
    user = db['users'].find_one({'email': email, 'password': current_password})
    if not user:
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401
    db['users'].update_one({'email': email}, {'$set': {'password': new_password}})
    return jsonify({'success': True, 'message': 'Password updated successfully'})

# -----------------------------
# Auth (simple email/password)
# -----------------------------
@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    print(f"Raw request data: {request.data}")
    data = request.json
    print(f"Parsed JSON: {data}")
    email = data.get('email')
    password = data.get('password')
    print(f"Login attempt: email={email}, password={password}")
    user = db['users'].find_one({'email': email, 'password': password}, {'_id': 0})
    print(f"User found: {user}")
    if user:
        user['token'] = 'mock-jwt-token'
        return jsonify({'success': True, 'user': user, 'token': user['token']})
    print("Returning invalid credentials error.")
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

# -----------------------------
# Customers Endpoints (CRUD and helpers)
# -----------------------------

@app.route('/api/customers/check', methods=['POST'])
def check_customer():
    data = request.json
    if not data or 'customerName' not in data or 'customerPhone' not in data:
        return jsonify({'error': 'Missing customerName or customerPhone'}), 400
    name = data.get('customerName', '').strip()
    phone = data.get('customerPhone', '').strip()
    customer = customers_col.find_one({'customerName': name, 'customerPhone': phone})
    if customer:
        # Ensure address_verified field exists
        if 'address_verified' not in customer:
            customers_col.update_one({'_id': customer['_id']}, {'$set': {'address_verified': False}})
            customer['address_verified'] = False
        customer['_id'] = str(customer['_id'])
        return jsonify({'exists': True, 'customer': customer})
    return jsonify({'exists': False})

@app.route('/api/customers', methods=['GET'])
def customers_health():
    return jsonify({'status': 'ok'})

@app.route('/api/customers/add', methods=['POST'])
def add_customer():
    data = request.json
    name = data.get('customerName', '').strip()
    phone = data.get('customerPhone', '').strip()
    address = data.get('address', '').strip()
    user_email = data.get('user_email', '').strip()
    customer = {
        'customerName': name,
        'customerPhone': phone,
        'address': address,
        'user_email': user_email,
        'address_verified': True
    }
    customers_col.insert_one(customer)
    customer['_id'] = str(customer['_id']) if '_id' in customer else None
    return jsonify({'success': True, 'customer': customer})

@app.route('/api/customers/verify_address', methods=['POST'])
def verify_address():
    data = request.json
    name = data.get('customerName', '').strip()
    phone = data.get('customerPhone', '').strip()
    result = customers_col.update_one({'customerName': name, 'customerPhone': phone}, {'$set': {'address_verified': True}})
    if result.matched_count:
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Customer not found'}), 404

@app.route('/api/customers/ensure_address_verified', methods=['POST'])
def ensure_address_verified():
    updated = 0
    for customer in customers_col.find({"address_verified": {"$exists": False}}):
        customers_col.update_one({"_id": customer["_id"]}, {"$set": {"address_verified": False}})
        updated += 1
    return jsonify({"updated": updated})

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "YOUR_GEMINI_API_URL_HERE")

@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    data = request.json
    messages = data.get('messages', [])
    user_email = data.get('user_email')
    # Fetch inventory for this user
    items = list(inventory_col.find({'user_email': user_email}, {'_id': 0}))
    inventory_map = {item['name'].lower(): item for item in items}
    # Check if user requested any item in the last message
    user_message = messages[-1] if messages else ''
    requested_items = [name for name in inventory_map if name in user_message.lower()]
    context = ""
    for name in requested_items:
        item = inventory_map[name]
        if item['quantity'] <= 0:
            context += f"No stock for {name}. ";
        else:
            context += f"{name} in stock: {item['quantity']}. ";
    # Build Gemini API payload
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
    return jsonify({"reply": gemini_reply, "context": context, "inventory": items})
