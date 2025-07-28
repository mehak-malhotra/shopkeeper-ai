import requests
import json
import certifi
from pymongo import MongoClient
import google.generativeai as genai
import random
from datetime import datetime
import re
from dotenv import load_dotenv
import os
import uuid

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# LLM setup (Gemini)
GEMINI_MODEL = "gemini-2.0-flash"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

# MongoDB setup (use shop_db, new structure)
client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
shop_db = client['shop_db']
user_col = shop_db['user']

# Prompt for user email at startup
user_email = input("Enter your email: ").strip()

# Helper to get current inventory for a user via API
def get_inventory():
    token = get_user_token(user_email)
    if not token:
        print("Error: Could not authenticate. Please check your email and try again.")
        return []
    
    resp = requests.get(f"http://localhost:5000/api/inventory", headers={
        'Authorization': f'Bearer {token}'
    })
    if resp.ok and resp.json().get("success"):
        return resp.json()["data"]
    else:
        print(f"Error fetching inventory: {resp.status_code} - {resp.text}")
    return []

# Helper to get user token
def get_user_token(email):
    # Get token from user document or generate a new one
    user = user_col.find_one({'email': email})
    if user and 'token' in user:
        return user['token']
    
    # If no token exists, we need to login via API
    login_response = requests.post("http://localhost:5000/api/auth/login", 
                                 json={'email': email, 'password': '1234567890'})  # Default password
    if login_response.ok:
        data = login_response.json()
        if data.get('success'):
            return data.get('token')
    
    print(f"Error: Could not get token for {email}")
    return None

# Helper to update inventory quantities via API
def update_inventory_quantities(updates):
    token = get_user_token(user_email)
    if not token:
        return False
    
    resp = requests.post(f"http://localhost:5000/api/inventory/update-quantities", 
                        headers={
                            'Authorization': f'Bearer {token}',
                            'Content-Type': 'application/json'
                        },
                        json={'updates': updates})
    return resp.ok and resp.json().get("success", False)

# Helper to find customer by phone via API
def find_customer_by_phone(phone):
    token = get_user_token(user_email)
    if not token:
        return None
    
    resp = requests.post(f"http://localhost:5000/api/customers/find-by-phone",
                        headers={
                            'Authorization': f'Bearer {token}',
                            'Content-Type': 'application/json'
                        },
                        json={'phone': phone})
    if resp.ok and resp.json().get("success"):
        return resp.json()["data"]
    return None

# Helper to get all customers for the user
def get_customers():
    token = get_user_token(user_email)
    if not token:
        return []
    
    resp = requests.get(f"http://localhost:5000/api/customers",
                        headers={
                            'Authorization': f'Bearer {token}',
                            'Content-Type': 'application/json'
                        })
    if resp.ok and resp.json().get("success"):
        return resp.json()["data"]
    return []

# Helper to get orders for a specific customer
def get_orders_for_customer(customer_id):
    token = get_user_token(user_email)
    if not token:
        return []
    
    # Get all orders and filter by customer_id
    resp = requests.get(f"http://localhost:5000/api/orders",
                        headers={
                            'Authorization': f'Bearer {token}',
                            'Content-Type': 'application/json'
                        })
    if resp.ok and resp.json().get("success"):
        all_orders = resp.json()["data"]
        # Filter orders by customer_id
        customer_orders = [order for order in all_orders if order.get('customer_id') == customer_id]
        return customer_orders
    return []

# Helper to add customer via API
def add_customer(customer_data):
    token = get_user_token(user_email)
    if not token:
        return None
    
    resp = requests.post(f"http://localhost:5000/api/customers/add",
                        headers={
                            'Authorization': f'Bearer {token}',
                            'Content-Type': 'application/json'
                        },
                        json=customer_data)
    if resp.ok and resp.json().get("success"):
        return resp.json()["data"]
    return None

# Helper to create order via API
def create_order(order_data):
    token = get_user_token(user_email)
    if not token:
        return None
    
    resp = requests.post(f"http://localhost:5000/api/orders",
                        headers={
                            'Authorization': f'Bearer {token}',
                            'Content-Type': 'application/json'
                        },
                        json=order_data)
    if resp.ok and resp.json().get("success"):
        return resp.json()["data"]
    return None

# Helper to call Gemini LLM for a conversational response
# The LLM is responsible for all intent detection, fuzzy matching, and natural conversation

def llm_respond(messages, inventory, customer=None, ask_for_notes=False):
    prompt = (
    "You are a friendly, helpful shop assistant AI. Your job is to help customers place orders. "
    "Follow this exact process:\n\n"
    
    "1. FIRST: Ask for customer details (name, phone, address) if not provided\n"
    "2. SECOND: Ask what items they want to order\n"
    "3. THIRD: For each item, ask for quantity\n"
    "4. FOURTH: Show order summary and total price\n"
    "5. FIFTH: Ask for any special instructions or notes\n"
    "6. SIXTH: Confirm the order and place it\n\n"
    
    "IMPORTANT RULES:\n"
    "- Always ask for customer name, phone, and address if not provided\n"
    "- Always ask for quantity when customer mentions an item\n"
    "- Check if items are available in inventory before adding\n"
    "- Show running total as items are added\n"
    "- Ask for delivery notes before finalizing\n"
    "- Be conversational and friendly\n"
    "- Don't output JSON until the order is complete and confirmed\n\n"
    
    "Current inventory: " + json.dumps(inventory) + "\n"
    + (f"Customer info: {json.dumps(customer)}" if customer else "No customer info yet") + "\n"
    + "Conversation: " + json.dumps(messages) + "\n\n"
    
    "Respond naturally as a helpful shop assistant."
)
    response = model.generate_content(prompt)
    return response.text

# Helper to extract JSON block from LLM response
def extract_json(text):
    try:
        start = text.index('{')
        end = text.rindex('}') + 1
        json_str = text[start:end]
        return json.loads(json_str)
    except Exception:
        return None

# Main chat loop
print("Hi! I'm your AI shop assistant. Let's get started with your order.")

# Validate setup
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in environment variables")
    exit(1)

if not MONGO_URI:
    print("Error: MONGO_URI not found in environment variables")
    exit(1)

# Test connection to backend
try:
    test_response = requests.get("http://localhost:5000/api/auth/login")
    if test_response.status_code != 405:  # 405 is expected for GET on POST endpoint
        print("Error: Backend server is not running. Please start the Flask backend first.")
        exit(1)
except requests.exceptions.ConnectionError:
    print("Error: Cannot connect to backend server. Please start the Flask backend first.")
    exit(1)

print(f"✅ Connected to backend server")
print(f"✅ Using email: {user_email}")

messages = []
order_placed = False
customer = None
name = None
phone = None
address = None
ask_for_notes = False
collected_notes = None

# Use get_inventory() to fetch inventory
print("Fetching inventory...")
inventory = get_inventory()
if inventory:
    print(f"✅ Found {len(inventory)} items in inventory")
else:
    print("⚠️  No inventory items found")

# Efficient call-bot friendly order processing
customer_info = {}
order_items = []
total_price = 0
notes = ""

print("Bot: Hi! Welcome to our shop. How can I help you today?")

while True:
    user_input = input("You: ")
    messages.append({"role": "user", "content": user_input})
    
    # Check for exit
    if any(word in user_input.lower() for word in ["bye", "thank you", "thanks", "exit", "quit"]):
        print("Bot: Thanks for calling! Have a great day!")
        break
    
    # If no customer info yet, get phone first (most efficient for call bot)
    if not customer_info.get('phone'):
        # Try to extract phone from user input
        phone_match = re.search(r'\d{10}', user_input)
        if phone_match:
            customer_info['phone'] = phone_match.group()
        else:
            print("Bot: Could you please share your phone number?")
            continue
        
        # Check if customer exists
        existing_customer = find_customer_by_phone(customer_info['phone'])
        if existing_customer:
            customer_info = existing_customer
            print(f"Bot: Welcome back, {customer_info['name']}! How can I help you today?")
        else:
            # New customer - get name and address
            print("Bot: I don't have your details yet. What's your name?")
            continue
    
    # Get name for new customers
    if not customer_info.get('name') and not customer_info.get('customer_id'):
        customer_info['name'] = user_input
        print("Bot: And your delivery address?")
        continue
    
    # Get address for new customers
    if not customer_info.get('address') and not customer_info.get('customer_id'):
        customer_info['address'] = user_input
        # Add new customer
        new_customer = add_customer(customer_info)
        if new_customer:
            customer_info = new_customer
            print("Bot: Perfect! Now, what would you like to order?")
        else:
            print("Bot: Let's continue with your order. What would you like?")
        continue
    
    # Process order items - casual conversation
    if any(word in user_input.lower() for word in ["done", "finish", "complete", "that's all", "that's it"]):
        if not order_items:
            print("Bot: You haven't added any items yet. What would you like to order?")
            continue
        
        print(f"Bot: Great! Let me summarize your order:")
        for item in order_items:
            print(f"  - {item['quantity']} {item['name']} = ₹{item['quantity'] * item['price']}")
        print(f"Total: ₹{total_price}")
        
        print("Bot: Any special delivery instructions?")
        notes = input("You: ")
        
        # Create the order
        print("Bot: Perfect! Let me place your order...")
        
        # Check inventory availability (silently)
        can_fulfill = True
        inventory_updates = []
        
        for item in order_items:
            db_item = next((i for i in inventory if i['name'].lower() == item['name'].lower()), None)
            if not db_item or db_item["quantity"] < item["quantity"]:
                print(f"Bot: I'm sorry, but {item['name']} is currently out of stock. Would you like to modify your order?")
                can_fulfill = False
                break
            else:
                inventory_updates.append({
                    'name': item['name'],
                    'quantity': -item['quantity']
                })
        
        if not can_fulfill:
            print("Bot: Please let me know what you'd like instead.")
            order_items = []
            total_price = 0
            continue
        
        # Update inventory
        if not update_inventory_quantities(inventory_updates):
            print("Bot: Sorry, there was a technical issue. Please try again.")
            continue
        
        # Create order
        order_data = {
            'customerPhone': customer_info['phone'],
            'items': order_items,
            'total': total_price,
            'status': 'pending',
            'timestamp': datetime.utcnow().isoformat() + "Z",
            'notes': notes
        }
        
        created_order = create_order(order_data)
        if created_order:
            order_id = created_order.get('order_id', 'Unknown')
            customer_id = created_order.get('customer_id', 'Unknown')
            print(f"Bot: ✅ Order placed successfully!")
            print(f"Bot: 📋 Order ID: {order_id}")
            print(f"Bot: 👤 Customer ID: {customer_id}")
            print(f"Bot: 💰 Total Amount: ₹{total_price}")
            print("Bot: Thank you for your order! Have a great day!")
        else:
            print("Bot: Sorry, there was an error creating the order. Please try again.")
        
        break
    
    # Process item addition - casual conversation
    item_found = False
    for item in inventory:
        if item['name'].lower() in user_input.lower():
            print(f"Bot: Sure! How many {item['name']} would you like?")
            quantity_input = input("You: ")
            try:
                quantity = int(quantity_input)
                if quantity > 0 and quantity <= item['quantity']:
                    order_items.append({
                        'name': item['name'],
                        'quantity': quantity,
                        'price': item['price']
                    })
                    total_price += quantity * item['price']
                    print(f"Bot: Added {quantity} {item['name']}. Total so far: ₹{total_price}")
                    item_found = True
                    break
                else:
                    print(f"Bot: I'm sorry, but we don't have that many {item['name']} available right now.")
                    item_found = True
                    break
            except ValueError:
                print("Bot: Could you please tell me the number?")
                item_found = True
                break
    
    if not item_found:
        print("Bot: I'm not sure about that item. Could you please tell me what you'd like to order?")