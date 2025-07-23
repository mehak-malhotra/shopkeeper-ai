import requests
import json
import certifi
from pymongo import MongoClient
import google.generativeai as genai
import random
from datetime import datetime
import re
import speech_recognition as sr
import pyttsx3

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

# Voice engine setup
engine = pyttsx3.init()
def speak(text):
    print(f"Bot: {text}")
    engine.say(text)
    engine.runAndWait()

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio)
        print(f"You: {text}")
        return text
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that. Could you please repeat?")
        return listen()
    except sr.RequestError:
        speak("Sorry, there was a problem with the speech recognition service.")
        return ""

# Helper to get current inventory as a list of dicts
def get_inventory():
    docs = list(collection.find({"user_email": fixed_inventory_email}))
    return [{"name": doc["name"], "quantity": doc["quantity"], "price": doc["price"]} for doc in docs]

# Helper to call Gemini LLM for a conversational response
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

# Main chat loop (voice-to-voice)
speak("Hi! I'm your AI shop assistant. Let's get started with your order.")
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
        speak("May I have your name?")
        name = listen().strip()
        messages.append({"role": "user", "content": name})
    if not phone:
        speak("And your phone number?")
        phone = listen().strip()
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
    speak(f"Welcome back, {customer['name']}! I have your address as: {customer['address']}. Let's proceed with your order.")
    messages.append({"role": "assistant", "content": f"Welcome back, {customer['name']}! I have your address as: {customer['address']}."})
else:
    # Step 3: Ask for address and email
    speak("I couldn't find you in our records. May I have your address?")
    address = listen().strip()
    speak("And your email address?")
    user_email = listen().strip()
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
    response = llm_respond(messages, inventory, customer, ask_for_notes=ask_for_notes)
    speak(response)
    messages.append({"role": "assistant", "content": response})
    data = extract_json(response)
    if data and 'customer' in data and 'order' in data and not order_placed:
        customer = data['customer']
        order = data['order']
        can_fulfill = True
        for it in order.get('items', []):
            db_item = collection.find_one({"user_email": fixed_inventory_email, "name": it["name"]})
            if not db_item or db_item["quantity"] < it["quantity"]:
                speak(f"Sorry, we only have {db_item['quantity'] if db_item else 0} {it['name']} left. Please adjust your order.")
                can_fulfill = False
        if not can_fulfill:
            continue
        for it in order.get('items', []):
            result = collection.update_one(
                {"user_email": fixed_inventory_email, "name": it["name"], "quantity": {"$gte": it["quantity"]}},
                {"$inc": {"quantity": -it["quantity"]}}
            )
            if result.modified_count == 0:
                speak(f"Sorry, {it['name']} just went out of stock. Please adjust your order.")
                can_fulfill = False
                break
        if not can_fulfill:
            continue
        customers_collection.update_one(
            {"customerPhone": customer.get("phone", "")},
            {"$set": {"customerName": customer.get("name", ""), "address": customer.get("address", ""), "user_email": customer.get("user_email", user_email or fixed_inventory_email)}},
            upsert=True
        )
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
        speak("Your order has been placed! Thank you.")
        speak("It was great talking to you! Have a wonderful day!")
        order_placed = True
        break
    if not ask_for_notes:
        ask_for_notes = True
    user_input = listen().strip()
    messages.append({"role": "user", "content": user_input})
    if any(word in user_input.lower() for word in ["bye", "thank you", "thanks", "exit", "quit"]):
        speak("It was great talking to you! Have a wonderful day!")
        break 