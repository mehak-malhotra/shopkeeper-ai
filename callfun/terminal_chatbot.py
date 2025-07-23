import re
import json
from pymongo import MongoClient
import random
from datetime import datetime
import google.generativeai as genai
import certifi
import requests
from difflib import get_close_matches

GEMINI_API_KEY = "AIzaSyDN6BSxkHUMru8-m51NmfU0SUKGFBbFYmk"
GEMINI_MODEL = "gemini-2.0-flash"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)
client = MongoClient(
    "mongodb+srv://dhallhimanshu1234:9914600112%40DHALLh@himanshudhall.huinsh2.mongodb.net/",
    tls=True,
    tlsCAFile=certifi.where()
)  
db = client['shop_db']
collection = db["inventory"]
orders_collection = db["orders"]
customers_collection = db["customers"]

fixed_inventory_email = "dhallhimanshu1234@gmail.com"

# Helper functions for backend API calls
def check_customer_backend(name, phone):
    url = "http://127.0.0.1:5000/api/customers/check"
    resp = requests.post(url, json={"customerName": name, "customerPhone": phone})
    return resp.json()

def add_customer_backend(name, phone, address, user_email):
    url = "http://127.0.0.1:5000/api/customers/add"
    resp = requests.post(url, json={"customerName": name, "customerPhone": phone, "address": address, "user_email": user_email})
    return resp.json()

def verify_address_backend(name, phone):
    url = "http://127.0.0.1:5000/api/customers/verify_address"
    resp = requests.post(url, json={"customerName": name, "customerPhone": phone})
    return resp.json()

# Helper to parse user input for item/quantity/inventory request
def parse_order_input(user_input, inventory_names):
    text = re.sub(r'[\?\.!]', '', user_input.lower())
    # Inventory request
    if any(word in text for word in ["inventory", "what do you have", "list", "show", "available"]):
        return "inventory_request", None, None
    # Done ordering
    if any(done_word in text for done_word in ["done", "no more", "that's all", "nothing else", "finish", "complete"]):
        return "done", None, None
    # Try to extract quantity and item
    match = re.search(r'(\d+)\s+([\w\s]+)', text)
    if match:
        qty = int(match.group(1))
        item = match.group(2).strip()
    else:
        qty = 1
        item = text.strip()
    # Fuzzy match item name
    item_match = get_close_matches(item, inventory_names, n=1, cutoff=0.7)
    if item_match:
        return "order", item_match[0], qty
    else:
        return "unknown", item, qty

# Helper to detect intent for casual conversation
def detect_intent(user_input):
    text = user_input.lower()
    if any(greet in text for greet in ["hello", "hi", "hey", "good morning", "good evening"]):
        return "greeting"
    if any(bye in text for bye in ["bye", "goodbye", "see you", "later"]):
        return "goodbye"
    if any(thank in text for thank in ["thank you", "thanks", "thx"]):
        return "thanks"
    if any(small in text for small in ["how are you", "what's up", "how's it going"]):
        return "smalltalk"
    return None

# State machine
state = "greeting"
order = {
    "customerName": "",
    "customerPhone": "",
    "address": "",
    "address_confirmed": False,
    "items": [],
    "items_confirmed": False,
    "total": 0,
    "status": "pending",
    "notes": ""
}
status = "in_progress"

print("Hi there! Welcome to Enterprises. How can I help you today?")

while status == "in_progress":
    if state == "greeting":
        print("May I have your name?")
        name = input("You: ").strip()
        order["customerName"] = name
        print("And your phone number?")
        phone = input("You: ").strip()
        order["customerPhone"] = phone
        # Check customer in backend
        check = check_customer_backend(name, phone)
        if check.get("exists"):
            customer = check["customer"]
            order["address"] = customer.get("address", "")
            if not customer.get("address_verified", False):
                print(f"I have your address as: {order['address']}. Is this correct? (yes/no)")
                confirm = input("You: ").strip().lower()
                if confirm in ["yes", "y", "correct"]:
                    verify_address_backend(name, phone)
                    order["address_confirmed"] = True
                else:
                    print("Please provide your correct address:")
                    address = input("You: ").strip()
                    order["address"] = address
                    add_customer_backend(name, phone, address, fixed_inventory_email)
                    order["address_confirmed"] = True
            else:
                order["address_confirmed"] = True
            state = "order"
        else:
            print("I couldn't find you in our records. Could you please provide your address?")
            address = input("You: ").strip()
            order["address"] = address
            add_customer_backend(name, phone, address, fixed_inventory_email)
            order["address_confirmed"] = True
            state = "order"
    elif state == "order":
        inventory_docs = list(collection.find({"user_email": fixed_inventory_email}))
        inventory_names = [doc["name"].lower() for doc in inventory_docs]
        # Create a temp inventory for this session
        temp_inventory = {doc["name"].lower(): doc["quantity"] for doc in inventory_docs}
        print("What would you like to order? (Type one item at a time, or 'done' when finished)")
        items = []
        while True:
            user_input = input("You: ").strip()
            # Casual conversation intent detection
            intent_type = detect_intent(user_input)
            if intent_type == "greeting":
                print("Bot: Hi! 😊 What would you like to order?")
                continue
            elif intent_type == "goodbye":
                print("Bot: Goodbye! Have a wonderful day!")
                break
            elif intent_type == "thanks":
                print("Bot: You're welcome! Anything else I can help with?")
                continue
            elif intent_type == "smalltalk":
                print("Bot: I'm just a bot, but I'm here to help you with your order!")
                continue
            intent, item, qty = parse_order_input(user_input, inventory_names)
            if intent == "done":
                break
            elif intent == "inventory_request":
                print("Here is what we have in inventory:")
                for doc in inventory_docs:
                    print(f"- {doc['name']} (in stock: {temp_inventory[doc['name'].lower()]}, price: {doc['price']})")
                continue
            elif intent == "order":
                item_lc = item.lower()
                if item_lc in temp_inventory:
                    if qty > temp_inventory[item_lc]:
                        print(f"Sorry, we only have {temp_inventory[item_lc]} {item} in stock.")
                        qty = temp_inventory[item_lc]
                    if qty <= 0:
                        print(f"Sorry, {item} is out of stock.")
                        continue
                    items.append({"name": item, "quantity": qty, "price": next(doc["price"] for doc in inventory_docs if doc["name"].lower() == item_lc)})
                    temp_inventory[item_lc] -= qty
                    print(f"Added {qty} {item}(s) to your order.")
                else:
                    print(f"Sorry, we don't have {item} in our inventory.")
            elif intent == "unknown":
                print("Sorry, I couldn't understand that item. Please try again or ask for the inventory list.")
        order["items"] = items
        order["items_confirmed"] = True
        state = "confirm_order"
    elif state == "confirm_order":
        print("Here is your order summary:")
        total = 0
        for it in order["items"]:
            print(f"- {it['name']} x{it['quantity']} @ {it['price']} each")
            total += it["quantity"] * it["price"]
        order["total"] = total
        print(f"Total price: {total}")
        print("Would you like to confirm this order? (yes/no)")
        confirm = input("You: ").strip().lower()
        if confirm in ["yes", "y", "confirm"]:
            # Atomic inventory check and update
            can_fulfill = True
            for it in order["items"]:
                db_item = collection.find_one({"user_email": fixed_inventory_email, "name": it["name"]})
                if not db_item or db_item["quantity"] < it["quantity"]:
                    print(f"Sorry, we only have {db_item['quantity'] if db_item else 0} {it['name']} left. Please adjust your order.")
                    can_fulfill = False
            if not can_fulfill:
                print("Please update your order to match available stock.")
                state = "order"
                continue
            # Atomic decrement
            for it in order["items"]:
                result = collection.update_one(
                    {"user_email": fixed_inventory_email, "name": it["name"], "quantity": {"$gte": it["quantity"]}},
                    {"$inc": {"quantity": -it["quantity"]}}
                )
                if result.modified_count == 0:
                    print(f"Sorry, {it['name']} just went out of stock. Please adjust your order.")
                    state = "order"
                    break
            else:
                status = "finalized"
                print("Thank you! Your order has been placed. Have a great day!")
        else:
            print("Order cancelled. If you want to start over, please run the assistant again.")
            break
# After loop, update DB with final order and inventory
if status == "finalized":
    if not order.get("items"):
        print("Order is empty. Exiting.")
    else:
        customer_name = order.get("customerName", "")
        customer_phone = order.get("customerPhone", "")
        address = order.get("address", "")
        notes = order.get("notes", "")
        # Upsert customer
        customers_collection.update_one(
            {"customerName": customer_name, "customerPhone": customer_phone},
            {"$set": {"user_email": fixed_inventory_email, "address": address, "address_verified": True}},
            upsert=True
        )
        # Save order
        order_id = f"ORDER{random.randint(100,999)}"
        order_doc = {
            "id": order_id,
            "customerPhone": customer_phone,
            "customerName": customer_name,
            "items": order.get("items", []),
            "total": order.get("total", 0),
            "status": order.get("status", "pending"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "notes": notes,
            "user_email": fixed_inventory_email,
            "address": address
        }
        orders_collection.insert_one(order_doc)
        # Update inventory in DB
        for it in order["items"]:
            collection.update_one(
                {"user_email": fixed_inventory_email, "name": it["name"]},
                {"$inc": {"quantity": -it["quantity"]}}
            )
        print(f"Order placed. ID: {order_id}")