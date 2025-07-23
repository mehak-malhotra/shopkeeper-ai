import requests
import json
import certifi
from pymongo import MongoClient
import google.generativeai as genai
import random
from datetime import datetime
import re

# LLM setup (Gemini)
GEMINI_API_KEY = "AIzaSyDN6BSxkHUMru8-m51NmfU0SUKGFBbFYmk"
GEMINI_MODEL = "gemini-2.0-flash"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

# MongoDB setup (for inventory and customer lookups)
client = MongoClient(
    "mongodb+srv://dhallhimanshu1234:9914600112%40DHALLh@himanshudhall.huinsh2.mongodb.net/",
    tls=True,
    tlsCAFile=certifi.where()
)
db = client['shop_db']
collection = db["inventory"]
customers_collection = db["customers"]
orders_collection = db["orders"]

fixed_inventory_email = "dhallhimanshu1234@gmail.com"

# Helper to get current inventory as a list of dicts
def get_inventory():
    docs = list(collection.find({"user_email": fixed_inventory_email}))
    return [{"name": doc["name"], "quantity": doc["quantity"], "price": doc["price"]} for doc in docs]

# Helper to call Gemini LLM for a conversational response
# The LLM is responsible for all intent detection, fuzzy matching, and natural conversation

def llm_respond(messages, inventory, customer=None, ask_for_notes=False):
    prompt = (
        "You are a friendly, helpful shop assistant AI. "
        "First, always ask for the user's name and phone number. "
        "After receiving both, check if the customer exists in the database (the system will do this lookup). "
        "If the customer exists, confirm their details and proceed to order-taking. "
        "If not, ask for their address and email, and record them. "
        "Take the order as usual, matching items to inventory even if misspelled. "
        "At the end, before finalizing the order, always ask for any special instructions or delivery notes, and include them as 'notes' in the order JSON. "
        "When the user confirms the order, output a JSON block with the following structure: "
        "{ 'customer': { 'name': ..., 'phone': ..., 'address': ..., 'user_email': ... }, 'order': { 'items': [...], 'total': ..., 'notes': ... } } "
        "If the user provides any special instructions or delivery notes, include them as 'notes' in the order JSON. "
        "If any item in the order is out of stock, inform the user and ask them to adjust their order. "
        + (f"Here is the current customer info: {json.dumps(customer)}. " if customer else "")
        + ("Please ask for special instructions or notes now." if ask_for_notes else "")
        + "Here is the current inventory: " + json.dumps(inventory) + ". "
        + "Conversation so far: " + json.dumps(messages) + ". "
        "Respond as a real person would, in a friendly and natural way."
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
messages = []
inventory = get_inventory()
order_placed = False
customer = None
name = None
phone = None
address = None
user_email = None
ask_for_notes = False
collected_notes = None

# Step 1: Ask for name and phone number
while not (name and phone):
    if not name:
        name = input("Bot: May I have your name?\nYou: ").strip()
        messages.append({"role": "user", "content": name})
    if not phone:
        phone = input("Bot: And your phone number?\nYou: ").strip()
        messages.append({"role": "user", "content": phone})

# Step 2: Check database for customer
customer_db = customers_collection.find_one({"customerPhone": phone})
if customer_db:
    customer = {
        "name": customer_db.get("customerName", ""),
        "phone": customer_db.get("customerPhone", ""),
        "address": customer_db.get("address", ""),
        "user_email": customer_db.get("user_email", "")
    }
    print(f"Bot: Welcome back, {customer['name']}! I have your address as: {customer['address']}. Let's proceed with your order.")
    messages.append({"role": "assistant", "content": f"Welcome back, {customer['name']}! I have your address as: {customer['address']}."})
else:
    # Step 3: Ask for address and email
    address = input("Bot: I couldn't find you in our records. May I have your address?\nYou: ").strip()
    user_email = input("Bot: And your email address?\nYou: ").strip()
    customer = {
        "name": name,
        "phone": phone,
        "address": address,
        "user_email": user_email
    }
    messages.append({"role": "user", "content": address})
    messages.append({"role": "user", "content": user_email})

# Step 4: Order-taking and LLM-driven conversation
while True:
    # If we haven't asked for notes yet and the user is about to confirm, set ask_for_notes True
    response = llm_respond(messages, inventory, customer, ask_for_notes=ask_for_notes)
    print(f"Bot: {response}")
    messages.append({"role": "assistant", "content": response})
    # Try to extract order/customer JSON if present
    data = extract_json(response)
    if data and 'customer' in data and 'order' in data and not order_placed:
        # Place order in DB
        customer = data['customer']
        order = data['order']
        # Check inventory for each item before placing order
        can_fulfill = True
        for it in order.get('items', []):
            db_item = collection.find_one({"user_email": fixed_inventory_email, "name": it["name"]})
            if not db_item or db_item["quantity"] < it["quantity"]:
                print(f"Bot: Sorry, we only have {db_item['quantity'] if db_item else 0} {it['name']} left. Please adjust your order.")
                can_fulfill = False
        if not can_fulfill:
            continue
        # Atomic decrement
        for it in order.get('items', []):
            result = collection.update_one(
                {"user_email": fixed_inventory_email, "name": it["name"], "quantity": {"$gte": it["quantity"]}},
                {"$inc": {"quantity": -it["quantity"]}}
            )
            if result.modified_count == 0:
                print(f"Bot: Sorry, {it['name']} just went out of stock. Please adjust your order.")
                can_fulfill = False
                break
        if not can_fulfill:
            continue
        # Upsert customer
        customers_collection.update_one(
            {"customerPhone": customer.get("phone", "")},
            {"$set": {"customerName": customer.get("name", ""), "address": customer.get("address", ""), "user_email": customer.get("user_email", user_email or fixed_inventory_email)}},
            upsert=True
        )
        # Insert order with custom id, timestamp, and notes
        order_id = f"ORDER{random.randint(100,999)}"
        timestamp = datetime.utcnow().isoformat() + "Z"
        order_doc = {
            "id": order_id,
            "customerPhone": customer.get("phone", ""),
            "customerName": customer.get("name", ""),
            "items": order.get("items", []),
            "total": order.get("total", 0),
            "status": "pending",
            "timestamp": timestamp,
            "notes": order.get("notes", ""),
            "user_email": customer.get("user_email", user_email or fixed_inventory_email),
            "address": customer.get("address", "")
        }
        orders_collection.insert_one(order_doc)
        print("Bot: Your order has been placed! Thank you.")
        print("Bot: It was great talking to you! Have a wonderful day!")
        order_placed = True
        break
    # If we haven't asked for notes yet, do so before final confirmation
    if not ask_for_notes:
        ask_for_notes = True
    user_input = input("You: ")
    messages.append({"role": "user", "content": user_input})
    if any(word in user_input.lower() for word in ["bye", "thank you", "thanks", "exit", "quit"]):
        print("Bot: It was great talking to you! Have a wonderful day!")
        break 