import requests
import json
import certifi
from pymongo import MongoClient
import google.generativeai as genai
from datetime import datetime
import uuid
import os
from typing import Dict, List, Optional, Any
from enhanced_conversation_state import (
    ConversationState, 
    get_or_create_conversation, 
    end_conversation, 
    get_active_conversations,
    cleanup_inactive_conversations,
    handle_customer_call
)

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

def get_user_token(email):
    """Get authentication token"""
    try:
        response = requests.post("http://localhost:5000/api/auth/login", 
                               json={"email": email, "password": "1234567890"})
        if response.status_code == 200:
            return response.json().get('token')
        
        response = requests.post("http://localhost:5000/api/auth/login", 
                               json={"email": email, "password": "password"})
        if response.status_code == 200:
            return response.json().get('token')
        
        return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def find_customer_by_phone(phone):
    """Find customer by phone number"""
    try:
        token = get_user_token(fixed_inventory_email)
        if not token:
            return None
        
        response = requests.post("http://localhost:5000/api/customers/find-by-phone",
                               headers={"Authorization": f"Bearer {token}"},
                               json={"phone": phone})
        if response.status_code == 200:
            return response.json().get('data')
        return None
    except:
        return None

def add_customer(customer_data):
    """Add new customer"""
    try:
        token = get_user_token(fixed_inventory_email)
        if not token:
            return None
        
        response = requests.post("http://localhost:5000/api/customers/add",
                               headers={"Authorization": f"Bearer {token}"},
                               json=customer_data)
        if response.status_code == 200:
            return response.json().get('data')
        return None
    except:
        return None

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

def get_customer_orders(customer_phone):
    """Get all orders for a specific customer"""
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

def process_customer_interaction(customer_phone: str, user_input: str) -> str:
    """Process customer interaction with enhanced state management"""
    
    # Handle empty input - end conversation gracefully
    if not user_input.strip():
        end_conversation(customer_phone)
        return "Thank you for calling INDIA MART GROCERY! Have a great day!"
    
    # Handle conversation end keywords
    if any(word in user_input.lower() for word in ["bye", "goodbye", "exit", "quit", "end", "thank you", "thanks", "done", "finish", "complete", "yes", "perfect", "okay", "ok"]):
        # Check if we're in ordering stage and have items
        state = get_or_create_conversation(customer_phone)
        if state.stage == "ordering" and state.current_order.get('items'):
            # Finalize the order before ending
            success, message = state.finalize_order()
            if success:
                end_conversation(customer_phone)
                return f"Perfect! {message} Thank you for your order! Have a great day!"
            else:
                end_conversation(customer_phone)
                return f"Thank you for calling! {message} Have a great day!"
        else:
            end_conversation(customer_phone)
            return "Thank you for calling INDIA MART GROCERY! Have a great day!"
    
    # Get or create conversation state
    state = get_or_create_conversation(customer_phone)
    
    # Handle initial customer setup if needed
    if not state.flow_flags["phone_collected"]:
        state.customer_info["phone"] = customer_phone
        state.flow_flags["phone_collected"] = True
        
        # Check if customer exists
        existing_customer = find_customer_by_phone(customer_phone)
        if existing_customer:
            state.customer_info.update({
                "name": existing_customer.get('name', ''),
                "address": existing_customer.get('address', ''),
                "customer_id": existing_customer.get('customer_id'),
                "is_existing_customer": True
            })
            state.flow_flags["customer_verified"] = True
            state.stage = "greeting"
        else:
            state.stage = "customer_registration"
        
        # Let LLM handle the greeting
        return handle_customer_call(customer_phone, user_input)
    
    # Handle customer registration
    if state.stage == "customer_registration" and not state.customer_info.get("name"):
        state.customer_info["name"] = user_input.strip()
        state.stage = "address_collection"
        return f"Nice to meet you {state.customer_info['name']}! And what's your delivery address?"
    
    elif state.stage == "address_collection" and not state.customer_info.get("address"):
        state.customer_info["address"] = user_input.strip()
        
        # Add new customer to database
        new_customer = add_customer(state.customer_info)
        if new_customer:
            state.customer_info.update(new_customer)
        
        state.flow_flags["customer_verified"] = True
        state.stage = "menu_selection"
        customer_name = state.customer_info.get('name', '')
        if customer_name:
            return f"Perfect {customer_name}! Your details have been saved. How can I help you today? You can place a new order, check your order status, or delete an order."
        else:
            return "Perfect! Your details have been saved. How can I help you today? You can place a new order, check your order status, or delete an order."
    
    # Let LLM handle all other interactions naturally
    return handle_customer_call(customer_phone, user_input)

def main():
    """Main conversation loop with enhanced state management"""
    print("🤖 Enhanced AI Grocery Store Assistant")
    print("=" * 50)
    print("Features:")
    print("- Enhanced conversation state management")
    print("- Real-time inventory tracking")
    print("- Multi-customer support")
    print("- Improved AI responses")
    print("- Automatic state cleanup")
    print("=" * 50)

    while True:
        try:
            print("\n📞 Enter customer phone number (or 'quit' to exit):")
            customer_phone = input("Phone: ").strip()

            if customer_phone.lower() in ["quit", "exit", "bye"]:
                break

            if not customer_phone:
                print("❌ Please enter a valid phone number")
                continue

            print(f"\n🎯 Starting conversation with customer: {customer_phone}")

            while True:
                try:
                    user_input = input("Customer: ").strip()

                    # Handle empty input or quit
                    if not user_input:
                        print("Bot: Thank you for calling INDIA MART GROCERY! Have a great day!")
                        end_conversation(customer_phone)
                        break

                    if user_input.lower() in ["quit", "exit", "bye"]:
                        print("Bot: Thank you for calling INDIA MART GROCERY! Have a great day!")
                        end_conversation(customer_phone)
                        break

                    response = process_customer_interaction(customer_phone, user_input)
                    print(f"Bot: {response}")

                    # Check if conversation should end
                    if "Thank you for calling" in response or "Have a great day" in response:
                        break

                except KeyboardInterrupt:
                    print("\n\nBot: Thank you for calling INDIA MART GROCERY! Have a great day!")
                    end_conversation(customer_phone)
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    print("Bot: I'm having technical difficulties. Please try again.")
                    continue

            # Clean up after each conversation
            try:
                cleanup_inactive_conversations()
                active_conversations = get_active_conversations()
                if active_conversations:
                    print(f"\n📊 Active conversations: {len(active_conversations)}")
                    for phone in active_conversations.keys():
                        print(f"  - {phone}")
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Cleaning up...")
            break
        except Exception as e:
            print(f"\n❌ System error: {e}")
            continue

    # Final cleanup
    try:
        print("🧹 Cleaning up all conversations...")
        active_conversations = get_active_conversations()
        for phone in list(active_conversations.keys()):
            try:
                end_conversation(phone)
            except Exception as e:
                print(f"⚠️  Error cleaning up {phone}: {e}")
        
        print("✅ All conversations cleaned up. Goodbye!")
    except Exception as e:
        print(f"⚠️  Final cleanup warning: {e}")

if __name__ == "__main__":
    main() 