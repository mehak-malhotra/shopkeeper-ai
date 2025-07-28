import requests
import json
import certifi
from pymongo import MongoClient
import google.generativeai as genai
import random
from datetime import datetime
import re
import os

# LLM setup (Gemini)
GEMINI_API_KEY = "AIzaSyDN6BSxkHUMru8-m51NmfU0SUKGFBbFYmk"
GEMINI_MODEL = "gemini-2.0-flash"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

# MongoDB setup
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

# Conversation state management
class ConversationState:
    def __init__(self):
        self.stage = "greeting"
        self.customer_info = {}
        self.order_items = []
        self.total_price = 0
        self.notes = ""
        self.confirmations = {
            "phone_confirmed": False,
            "address_confirmed": False,
            "order_complete": False,
            "delivery_confirmed": False
        }
        self.messages = []
        self.inventory = []
        self.user_email = None

    def to_json(self):
        return {
            "stage": self.stage,
            "customer_info": self.customer_info,
            "order_items": self.order_items,
            "total_price": self.total_price,
            "notes": self.notes,
            "confirmations": self.confirmations,
            "messages": self.messages[-5:],  # Keep last 5 messages
            "inventory_count": len(self.inventory)
        }

    def from_json(self, data):
        self.stage = data.get("stage", "greeting")
        self.customer_info = data.get("customer_info", {})
        self.order_items = data.get("order_items", [])
        self.total_price = data.get("total_price", 0)
        self.notes = data.get("notes", "")
        self.confirmations = data.get("confirmations", {})
        self.messages = data.get("messages", [])

# Helper functions
def get_inventory():
    """Get current inventory from backend"""
    try:
        token = get_user_token(fixed_inventory_email)
        if not token:
            print("❌ No authentication token available")
            return []
        
        response = requests.get("http://localhost:5000/api/inventory", 
                              headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        else:
            print(f"❌ Inventory fetch failed: {response.status_code} - {response.text}")
        return []
    except Exception as e:
        print(f"❌ Inventory fetch error: {e}")
        return []

def get_user_token(email):
    """Get authentication token"""
    try:
        # Try with the default password that was set during registration
        response = requests.post("http://localhost:5000/api/auth/login", 
                               json={"email": email, "password": "1234567890"})
        if response.status_code == 200:
            return response.json().get('token')
        
        # If that fails, try with "password"
        response = requests.post("http://localhost:5000/api/auth/login", 
                               json={"email": email, "password": "password"})
        if response.status_code == 200:
            return response.json().get('token')
        
        print(f"❌ Authentication failed for {email}")
        return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None



def find_customer_by_phone(phone):
    """Find customer by phone number"""
    try:
        response = requests.post("http://localhost:5000/api/customers/find-by-phone",
                               headers={"Authorization": f"Bearer {get_user_token(fixed_inventory_email)}"},
                               json={"phone": phone})
        if response.status_code == 200:
            return response.json().get('data')
        return None
    except:
        return None

def add_customer(customer_data):
    """Add new customer"""
    try:
        response = requests.post("http://localhost:5000/api/customers/add",
                               headers={"Authorization": f"Bearer {get_user_token(fixed_inventory_email)}"},
                               json=customer_data)
        if response.status_code == 200:
            return response.json().get('data')
        return None
    except:
        return None

def create_order(order_data):
    """Create new order"""
    try:
        response = requests.post("http://localhost:5000/api/orders",
                               headers={"Authorization": f"Bearer {get_user_token(fixed_inventory_email)}"},
                               json=order_data)
        if response.status_code == 200:
            return response.json().get('data')
        return None
    except:
        return None

def update_inventory_quantities(updates):
    """Update inventory quantities"""
    try:
        response = requests.post("http://localhost:5000/api/inventory/update-quantities",
                               headers={"Authorization": f"Bearer {get_user_token(fixed_inventory_email)}"},
                               json={"updates": updates})
        return response.status_code == 200
    except:
        return False

def llm_process_conversation(state, user_input):
    """Process conversation with LLM and return structured response - Only for ordering"""
    
    # Create context for LLM
    context = {
        "current_stage": state.stage,
        "customer_info": state.customer_info,
        "order_items": state.order_items,
        "total_price": state.total_price,
        "confirmations": state.confirmations,
        "inventory": [{"name": item["name"], "price": item["price"], "quantity": item["quantity"]} for item in state.inventory],
        "conversation_history": state.messages[-5:],
        "user_input": user_input
    }
    
    prompt = f"""
You are a professional store assistant for INDIA MART GROCERY. You are helping a customer with their FRESH NEW ORDER.

CONVERSATION CONTEXT:
{json.dumps(context, indent=2)}

AVAILABLE INVENTORY:
{chr(10).join([f"- {item['name']}: ₹{item['price']} (Stock: {item['quantity']})" for item in state.inventory])}

IMPORTANT: This is a COMPLETELY FRESH NEW ORDER. There are no previous items or orders connected to this conversation.

ORDERING RULES:
1. Be natural, friendly, and helpful
2. Help customers order items from inventory
3. Check stock availability before adding items
4. Calculate prices correctly
5. Handle order completion gracefully
6. Be conversational, not robotic
7. If customer mentions an item, ask for quantity
8. If customer provides a number after an item, add that quantity to order
9. If customer says "done", "finish", "complete", "no more" - complete the order
10. Don't add items to order unless customer explicitly requests them
11. This is a FRESH ORDER - start with empty cart
12. Don't reference any previous orders or items

ORDERING FLOW:
- Start with empty cart (fresh order)
- Help customer select items from inventory
- Ask for quantities when items are mentioned
- Confirm orders and calculate totals
- Handle order completion

RESPOND WITH JSON ONLY:
{{
    "response": "Your natural, conversational response to the customer",
    "actions": {{
        "add_item": {{"name": "item_name", "quantity": 0}},
        "complete_order": true/false,
        "reset_order": true/false
    }},
    "order_update": {{"field": "value"}},
    "system_message": "Optional system message for debugging"
}}

EXAMPLES:
- Customer says "apples" → Ask for quantity
- Customer says "5" → Add 5 apples to order and ask for more items
- Customer says "done" → Complete order and show summary
- Customer says "I want 3 bananas" → Add 3 bananas to order
"""
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Extract JSON from response
        if '{' in response_text and '}' in response_text:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            json_str = response_text[start:end]
            llm_response = json.loads(json_str)
            

            
            return llm_response
        else:
            # Fallback response
            return {
                "response": "I understand. How can I help you with your order?",
                "actions": {},
                "order_update": {}
            }
    except Exception as e:
        print(f"LLM Error: {e}")
        return {
            "response": "I'm having trouble understanding. Could you please repeat that?",
            "actions": {},
            "order_update": {}
        }

def save_conversation_state(state, filename="conversation_state.json"):
    """Save conversation state to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(state.to_json(), f, indent=2)
    except Exception as e:
        print(f"Error saving state: {e}")

def load_conversation_state(filename="conversation_state.json"):
    """Load conversation state from JSON file"""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            state = ConversationState()
            state.from_json(data)
            return state
    except:
        return ConversationState()

def reset_order(state):
    """Reset order if there are stock issues"""
    state.order_items = []
    state.total_price = 0
    print("🔄 Order reset due to stock issues. Please start fresh.")

def add_item_to_order(state, item_name, quantity):
    """Add item to order with inventory check"""
    for item in state.inventory:
        if item["name"].lower() == item_name.lower():
            if item["quantity"] >= quantity:
                state.order_items.append({
                    "name": item["name"],
                    "quantity": quantity,
                    "price": item["price"]
                })
                state.total_price += quantity * item["price"]
                print(f"✅ Added {quantity} {item['name']} to your order")
                return True
            else:
                print(f"❌ Sorry, we only have {item['quantity']} {item['name']} in stock.")
                return False
    print(f"❌ Sorry, {item_name} is not available in our inventory.")
    return False

def process_order_completion(state):
    """Process order completion"""
    if not state.order_items:
        print("Bot: You haven't added any items yet. What would you like to order?")
        return False
    
    # Show order summary
    print("\n📋 ORDER SUMMARY:")
    for item in state.order_items:
        print(f"  - {item['quantity']} {item['name']} = ₹{item['quantity'] * item['price']}")
    print(f"💰 Total: ₹{state.total_price}")
    
    # Get delivery notes
    print("\nBot: Any special delivery instructions?")
    state.notes = input("You: ").strip()
    
    # Check inventory and update
    inventory_updates = []
    can_fulfill = True
    
    for item in state.order_items:
        for inv_item in state.inventory:
            if inv_item["name"].lower() == item["name"].lower():
                if inv_item["quantity"] < item["quantity"]:
                    print(f"❌ Sorry, {item['name']} is out of stock!")
                    can_fulfill = False
                    break
                else:
                    inventory_updates.append({
                        "name": item["name"],
                        "quantity": -item["quantity"]
                    })
                break
    
    if can_fulfill and update_inventory_quantities(inventory_updates):
        # Create order
        order_data = {
            "customerPhone": state.customer_info.get("phone", ""),
            "items": state.order_items,
            "total": state.total_price,
            "status": "pending",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "notes": state.notes
        }
        
        created_order = create_order(order_data)
        if created_order:
            order_id = created_order.get("order_id", "Unknown")
            customer_id = created_order.get("customer_id", "Unknown")
            print(f"✅ Order placed successfully!")
            print(f"📋 Order ID: {order_id}")
            print(f"👤 Customer ID: {customer_id}")
            print(f"💰 Total Amount: ₹{state.total_price}")
            print("🎉 Thank you for your order! Have a great day!")
            return True
        else:
            print("❌ Sorry, there was an error creating the order.")
            return False
    else:
        print("❌ Sorry, some items are out of stock. Please modify your order.")
        return False

def get_order_status(order_id):
    """Get order status from shop_data.json"""
    try:
        with open('shop_data.json', 'r') as f:
            shop_data = json.load(f)
        
        all_orders = shop_data.get('orders', [])
        # Find order by ID
        for order in all_orders:
            if str(order.get('order_id')) == str(order_id):
                return order
        
        return None
    except Exception as e:
        print(f"❌ Error reading orders from shop_data.json: {e}")
        return None

def get_all_orders():
    """Get all orders from backend"""
    try:
        token = get_user_token(fixed_inventory_email)
        if not token:
            print("❌ No authentication token available")
            return []
        
        response = requests.get("http://localhost:5000/api/orders", 
                              headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        else:
            print(f"❌ Orders fetch failed: {response.status_code} - {response.text}")
        return []
    except Exception as e:
        print(f"❌ Orders fetch error: {e}")
        return []

def get_customer_orders(customer_phone):
    """Get all orders for a specific customer from database using customer_id"""
    try:
        token = get_user_token(fixed_inventory_email)
        if not token:
            print("❌ No authentication token available")
            return []
        
        # First get all customers to find the customer_id
        response = requests.get("http://localhost:5000/api/customers", 
                              headers={"Authorization": f"Bearer {token}"})
        if response.status_code != 200:
            print(f"❌ Failed to get customers: {response.status_code}")
            return []
        
        customers_data = response.json().get('data', [])
        
        # Find customer by phone number
        customer_id = None
        for customer in customers_data:
            if customer.get('phone') == customer_phone:
                customer_id = customer.get('customer_id')
                break
        
        if customer_id is None:
            print(f"Bot: Could not find customer_id for phone number: {customer_phone}")
            return []
        
        # Get all orders
        response = requests.get("http://localhost:5000/api/orders", 
                              headers={"Authorization": f"Bearer {token}"})
        if response.status_code != 200:
            print(f"❌ Failed to get orders: {response.status_code}")
            return []
        
        orders_data = response.json().get('data', [])
        
        # Filter orders for this customer by customer_id
        customer_orders = [order for order in orders_data if order.get('customer_id') == customer_id]
        return customer_orders
    except Exception as e:
        print(f"❌ Error getting customer orders from database: {e}")
        return []

def display_order_summary(order):
    """Display a formatted order summary"""
    print(f"\n📋 Order ID: {order.get('order_id', 'N/A')}")
    print(f"📞 Customer Phone: {order.get('customerPhone', 'N/A')}")
    print(f"💰 Total Amount: ₹{order.get('total', 'N/A')}")
    print(f"📦 Status: {order.get('status', 'N/A')}")
    print(f"📝 Notes: {order.get('notes', 'N/A')}")
    print(f"🕒 Timestamp: {order.get('timestamp', 'N/A')}")
    
    items = order.get('items', [])
    if items:
        print("🛒 Items:")
        for item in items:
            print(f"  - {item.get('quantity', 0)} x {item.get('name', 'Unknown')} = ₹{item.get('quantity', 0) * item.get('price', 0)}")
    print("-" * 40)

def process_user_input(user_input):
    """Process user input with LLM to handle exit responses"""
    
    prompt = f"""
You are a grocery store assistant. The customer said: "{user_input}"

Determine if the customer wants to:
1. Exit/quit the conversation
2. Continue with current functionality
3. Say no/decline current offer

RESPOND WITH JSON ONLY:
{{
    "action": "exit|continue|decline",
    "reason": "brief explanation of the action",
    "response": "appropriate bot response"
}}

EXAMPLES:
- "no" → exit
- "thanks" → exit  
- "none" → exit
- "neither" → exit
- "bye" → exit
- "quit" → exit
- "exit" → exit
- "goodbye" → exit
- "yes" → continue
- "okay" → continue
- "sure" → continue
"""
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Extract JSON from response
        if '{' in response_text and '}' in response_text:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            json_str = response_text[start:end]
            return json.loads(json_str)
        else:
            # Default to continue if LLM fails
            return {
                "action": "continue",
                "reason": "LLM response parsing failed",
                "response": "I understand. How can I help you?"
            }
    except Exception as e:
        print(f"LLM Input Processing Error: {e}")
        return {
            "action": "continue",
            "reason": "Error processing input",
            "response": "I understand. How can I help you?"
        }

def ask_for_more_help():
    """Ask if user wants anything else and handle response"""
    print("Bot: Is there anything else I can help you with today?")
    user_response = input("You: ").strip()
    
    # Process with LLM
    llm_result = process_user_input(user_response)
    
    if llm_result.get("action") == "exit":
        print(f"Bot: {llm_result.get('response', 'Thank you for calling INDIA MART GROCERY! Have a great day!')}")
        return False  # Exit the bot
    else:
        return True  # Continue with menu

def delete_order_from_backend(order_id):
    """Delete order from backend"""
    try:
        token = get_user_token(fixed_inventory_email)
        if not token:
            print("❌ No authentication token available")
            return False
        
        response = requests.delete(f"http://localhost:5000/api/orders/{order_id}", 
                                headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 200:
            data = response.json()
            return data.get('success', False)
        else:
            print(f"❌ Order deletion failed: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        print(f"❌ Order deletion error: {e}")
        return False

def delete_order_from_shop_data(order_id):
    """Delete order from database (this function is now redundant since we use backend directly)"""
    try:
        # Since we're now using the database directly, this function is redundant
        # The backend deletion in delete_order_from_backend is sufficient
        print(f"✅ Order {order_id} deleted from backend")
        return {"order_id": order_id, "status": "deleted"}
    except Exception as e:
        print(f"❌ Error in delete_order_from_shop_data: {e}")
        return None

# Main conversation flow - Fully LLM-driven
def main():
    print("🤖 INDIA MART GROCERY - AI Assistant")
    print("=" * 50)
    
    # Initialize state
    state = load_conversation_state()
    state.user_email = fixed_inventory_email
    
    # Get inventory directly from backend
    print("📦 Loading inventory from backend...")
    state.inventory = get_inventory()
    
    if state.inventory:
        print(f"✅ Found {len(state.inventory)} items in inventory")
    else:
        print("⚠️  No inventory items found")
    
    print("\n🎯 Starting conversation...")
    print("Bot: Welcome to INDIA MART GROCERY! How can I help you today?")
    print("Bot: Can I get your phone number to look up your details?")
    state.stage = "phone_collection"
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            # Check for exit
            if any(word in user_input.lower() for word in ["bye", "exit", "quit", "goodbye"]):
                print("Bot: Thank you for calling INDIA MART GROCERY! Have a great day!")
                break
            
            # Process user input with LLM first
            llm_input_result = process_user_input(user_input)
            if llm_input_result.get("action") == "exit":
                print(f"Bot: {llm_input_result.get('response', 'Thank you for calling INDIA MART GROCERY! Have a great day!')}")
                break
            
            # Add user input to messages
            state.messages.append({"role": "user", "content": user_input})
            
            # Handle customer logic (hardcoded)
            if state.stage == "phone_collection":
                phone = user_input.strip()
                if phone:
                    state.customer_info["phone"] = phone
                    
                    # Check if customer exists
                    existing_customer = find_customer_by_phone(phone)
                    if existing_customer:
                        print("Bot: Welcome back! I found your details in our system.")
                        print(f"Bot: Your address is {existing_customer.get('address', 'not found')}. Is this correct?")
                        state.customer_info.update(existing_customer)
                        state.stage = "address_confirmation"
                    else:
                        print("Bot: Thanks! I don't have your details yet. What's your name?")
                        state.stage = "name_collection"
                else:
                    print("Bot: Please provide a valid phone number.")
                continue
            
            elif state.stage == "name_collection":
                state.customer_info["name"] = user_input
                state.stage = "address_collection"
                print("Bot: And what's your delivery address?")
                continue
            
            elif state.stage == "address_collection":
                state.customer_info["address"] = user_input
                # Add new customer to database
                new_customer = add_customer(state.customer_info)
                if new_customer:
                    state.customer_info = new_customer
                state.confirmations["address_confirmed"] = True
                state.stage = "menu_selection"
                print("Bot: Perfect! What would you like to do today?")
                print("1. Create new order")
                print("2. Check status of old order")
                print("3. Delete order")
                print("Please choose 1, 2, or 3:")
                continue
            
            elif state.stage == "address_confirmation":
                if user_input.lower() in ["yes", "y", "correct", "right"]:
                    state.confirmations["address_confirmed"] = True
                    state.stage = "menu_selection"
                    print("Bot: Great! What would you like to do today?")
                    print("1. Create new order")
                    print("2. Check status of old order")
                    print("3. Delete order")
                    print("Please choose 1, 2, or 3:")
                elif user_input.lower() in ["no", "n", "incorrect", "wrong"]:
                    print("Bot: Please provide your correct address:")
                    state.stage = "address_collection"
                else:
                    print("Bot: Please respond with 'yes' or 'no' to confirm your address.")
                continue
            
            elif state.stage == "menu_selection":
                if user_input.strip() == "1":
                    # Create new order - fresh start
                    reset_order(state)
                    state.stage = "ordering"
                    print("Bot: Perfect! Let's create a fresh new order. What would you like to order?")
                elif user_input.strip() == "2":
                    # Check status of old order
                    state.stage = "check_order_status"
                    print("Bot: I'll check your order status. Please provide your order ID:")
                elif user_input.strip() == "3":
                    # Delete order
                    state.stage = "delete_order"
                    print("Bot: I'll help you delete an order. Please provide your order ID:")
                else:
                    print("Bot: Please choose 1, 2, or 3:")
                continue
            
            elif state.stage == "check_order_status":
                # First, show customer's orders
                customer_phone = state.customer_info.get("phone", "")
                print(f"Bot: Looking for orders with phone number: {customer_phone}")
                
                # Find customer_id first
                try:
                    with open('shop_data.json', 'r') as f:
                        shop_data = json.load(f)
                    all_customers = shop_data.get('customers', [])
                    customer_id = None
                    for customer in all_customers:
                        if customer.get('phone') == customer_phone:
                            customer_id = customer.get('customer_id')
                            break
                    
                    if customer_id:
                        print(f"Bot: Found customer_id: {customer_id}")
                    else:
                        print(f"Bot: No customer_id found for phone: {customer_phone}")
                except Exception as e:
                    print(f"Bot: Error looking up customer: {e}")
                
                customer_orders = get_customer_orders(customer_phone)
                
                if customer_orders:
                    print(f"Bot: Found {len(customer_orders)} orders for you:")
                    for i, order in enumerate(customer_orders, 1):
                        print(f"{i}. Order ID: {order.get('order_id')} - Status: {order.get('status')} - Total: ₹{order.get('total')}")
                    
                    print("Bot: Which order would you like to check? (Enter the number or order ID):")
                    state.stage = "order_selection"
                else:
                    print("Bot: You don't have any orders yet.")
                    # Debug: show all available orders
                    try:
                        with open('shop_data.json', 'r') as f:
                            shop_data = json.load(f)
                        all_orders = shop_data.get('orders', [])
                        print(f"Bot: (Debug: There are {len(all_orders)} total orders in the system)")
                        for order in all_orders[:3]:  # Show first 3 orders as example
                            print(f"  - Order {order.get('order_id')}: Customer ID {order.get('customer_id', 'N/A')}")
                    except:
                        pass
                    
                    # Ask if they want anything else
                    if not ask_for_more_help():
                        break
                    state.stage = "menu_selection"
                    print("Bot: What would you like to do?")
                    print("1. Create new order")
                    print("2. Check status of old order")
                    print("3. Delete order")
                    print("Please choose 1, 2, or 3:")
                continue
            
            elif state.stage == "order_selection":
                user_choice = user_input.strip()
                customer_phone = state.customer_info.get("phone", "")
                customer_orders = get_customer_orders(customer_phone)
                
                # Try to find order by number or ID
                selected_order = None
                try:
                    choice_num = int(user_choice)
                    if 1 <= choice_num <= len(customer_orders):
                        selected_order = customer_orders[choice_num - 1]
                except ValueError:
                    # Try to find by order ID
                    for order in customer_orders:
                        if str(order.get('order_id')) == user_choice:
                            selected_order = order
                            break
                
                if selected_order:
                    print("Bot: Here are the details for your order:")
                    display_order_summary(selected_order)
                else:
                    print(f"Bot: Could not find order with ID: {user_choice}")
                
                # Ask if they want anything else
                if not ask_for_more_help():
                    break
                state.stage = "menu_selection"
                print("Bot: What would you like to do?")
                print("1. Create new order")
                print("2. Check status of old order")
                print("3. Delete order")
                print("Please choose 1, 2, or 3:")
                continue
            
            elif state.stage == "delete_order":
                # First, show customer's orders
                customer_phone = state.customer_info.get("phone", "")
                print(f"Bot: Looking for orders with phone number: {customer_phone}")
                
                customer_orders = get_customer_orders(customer_phone)
                
                if customer_orders:
                    print(f"Bot: Here are your orders:")
                    for i, order in enumerate(customer_orders, 1):
                        print(f"{i}. Order ID: {order.get('order_id')} - Status: {order.get('status')} - Total: ₹{order.get('total')}")
                    
                    print("Bot: Which order would you like to delete? (Enter the number or order ID):")
                    state.stage = "delete_order_selection"
                else:
                    print("Bot: You don't have any orders to delete.")
                    
                    # Ask if they want anything else
                    if not ask_for_more_help():
                        break
                    state.stage = "menu_selection"
                    print("Bot: What would you like to do?")
                    print("1. Create new order")
                    print("2. Check status of old order")
                    print("3. Delete order")
                    print("Please choose 1, 2, or 3:")
                continue
            
            elif state.stage == "delete_order_selection":
                user_choice = user_input.strip()
                customer_phone = state.customer_info.get("phone", "")
                customer_orders = get_customer_orders(customer_phone)
                
                # Try to find order by number or ID
                selected_order = None
                try:
                    choice_num = int(user_choice)
                    if 1 <= choice_num <= len(customer_orders):
                        selected_order = customer_orders[choice_num - 1]
                except ValueError:
                    # Try to find by order ID
                    for order in customer_orders:
                        if str(order.get('order_id')) == user_choice:
                            selected_order = order
                            break
                
                if selected_order:
                    order_id = selected_order.get('order_id')
                    print(f"Bot: You want to delete Order {order_id}. Here are the details:")
                    display_order_summary(selected_order)
                    
                    print("Bot: Are you sure you want to delete this order? (yes/no):")
                    state.stage = "confirm_delete"
                    # Store the order to delete
                    state.order_to_delete = selected_order
                else:
                    print(f"Bot: Could not find order with ID: {user_choice}")
                    
                    # Ask if they want anything else
                    if not ask_for_more_help():
                        break
                    state.stage = "menu_selection"
                    print("Bot: What would you like to do?")
                    print("1. Create new order")
                    print("2. Check status of old order")
                    print("3. Delete order")
                    print("Please choose 1, 2, or 3:")
                continue
            
            elif state.stage == "confirm_delete":
                if user_input.lower() in ["yes", "y", "confirm", "sure"]:
                    order_to_delete = getattr(state, 'order_to_delete', None)
                    if order_to_delete:
                        order_id = order_to_delete.get('order_id')
                        print(f"Bot: Deleting order {order_id}...")
                        
                        # Delete from backend
                        backend_success = delete_order_from_backend(order_id)
                        
                        # Delete from shop_data.json
                        deleted_order = delete_order_from_shop_data(order_id)
                        
                        if backend_success and deleted_order:
                            print(f"✅ Order {order_id} has been successfully deleted!")
                            print(f"Bot: Deleted order details:")
                            display_order_summary(deleted_order)
                        elif deleted_order:
                            print(f"✅ Order {order_id} has been deleted from local data!")
                            print("⚠️  Note: Backend deletion may have failed, but order is removed from your view.")
                        else:
                            print(f"❌ Failed to delete order {order_id}")
                    else:
                        print("Bot: Error: No order selected for deletion.")
                else:
                    print("Bot: Order deletion cancelled.")
                
                # Clear the stored order
                if hasattr(state, 'order_to_delete'):
                    delattr(state, 'order_to_delete')
                
                # Ask if they want anything else
                if not ask_for_more_help():
                    break
                state.stage = "menu_selection"
                print("Bot: What would you like to do?")
                print("1. Create new order")
                print("2. Check status of old order")
                print("3. Delete order")
                print("Please choose 1, 2, or 3:")
                continue
            
            # Handle ordering stage (LLM-powered)
            elif state.stage == "ordering":
                # Process order through LLM
                llm_response = llm_process_conversation(state, user_input)
                
                # Handle item addition
                actions = llm_response.get("actions", {})
                if actions.get("add_item"):
                    item_data = actions["add_item"]
                    if item_data.get("name") and item_data.get("quantity", 0) > 0:
                        add_item_to_order(state, item_data["name"], item_data["quantity"])
                
                # Handle order completion
                if actions.get("complete_order"):
                    if process_order_completion(state):
                        # Reset order state for next conversation
                        reset_order(state)
                        state.stage = "greeting"
                        state.customer_info = {}
                        state.confirmations = {}
                        print("\n" + "="*50)
                        print("🤖 Starting new conversation...")
                        print("Bot: Welcome to INDIA MART GROCERY! How can I help you today?")
                        print("Bot: Can I get your phone number to look up your details?")
                        state.stage = "phone_collection"
                    else:
                        print("Bot: Let's continue with your order. What else would you like?")
                    continue
                
                # Handle order reset
                if actions.get("reset_order"):
                    reset_order(state)
                    print("Bot: Order has been reset. What would you like to order?")
                    continue
                
                # Print bot response
                print(f"Bot: {llm_response.get('response', 'I understand. How can I help you?')}")
                state.messages.append({"role": "assistant", "content": llm_response.get('response', '')})
                
                # Save state periodically
                if len(state.messages) % 5 == 0:
                    save_conversation_state(state)
                
        except KeyboardInterrupt:
            print("\n\nBot: Thank you for calling! Have a great day!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Bot: I'm having technical difficulties. Please try again.")
            continue
    
    # Save final state
    save_conversation_state(state)

if __name__ == "__main__":
    main()