import requests
import json
import certifi
from pymongo import MongoClient
import google.generativeai as genai
from datetime import datetime
import uuid
import os
import speech_recognition as sr
import pyttsx3
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

# Voice engine setup
engine = pyttsx3.init()

def speak(text):
    """Convert text to speech"""
    print(f"Bot: {text}")
    engine.say(text)
    engine.runAndWait()

def listen():
    """Listen for voice input and convert to text"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            text = r.recognize_google(audio)
            print(f"👤 Customer: {text}")
            return text
        except sr.WaitTimeoutError:
            print("⏰ No speech detected within timeout")
            return ""
        except sr.UnknownValueError:
            print("❓ Could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
            return ""
        except Exception as e:
            print(f"❌ Error in speech recognition: {e}")
            return ""

def get_user_token(email):
    """Get authentication token - use cached version from enhanced_conversation_state"""
    try:
        from enhanced_conversation_state import get_cached_token
        return get_cached_token()
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

def get_customer_orders(customer_phone):
    """Get all orders for a specific customer - use cached version from enhanced_conversation_state"""
    try:
        from enhanced_conversation_state import get_cached_customer_orders
        return get_cached_customer_orders(customer_phone)
    except Exception as e:
        print(f"❌ Error getting customer orders: {e}")
        return []

def process_voice_customer_interaction(customer_phone: str, user_input: str) -> str:
    """Process customer interaction for the voice bot with enhanced state management"""
    # Handle empty input - end conversation gracefully
    if not user_input.strip():
        end_conversation(customer_phone)
        return "Thank you for calling INDIA MART GROCERY! Have a great day!"

    # Handle conversation end keywords - only end when customer explicitly indicates completion
    end_keywords = ["bye", "goodbye", "exit", "quit", "end", "thank you", "thanks", "thankyou", "done", "finish", "complete", "that's it", "that's all", "nothing else", "i'm done", "i'm finished", "that's everything", "that's all i need", "nothing more", "complete my order", "finalize my order"]
    if any(word in user_input.lower() for word in end_keywords):
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
    """Main voice conversation loop with enhanced state management"""
    print("🎤 Enhanced Voice AI Grocery Store Assistant")
    print("=" * 50)
    print("Features:")
    print("- Voice-based conversation")
    print("- Enhanced conversation state management")
    print("- Real-time inventory tracking")
    print("- Multi-customer support")
    print("- Automatic state cleanup")
    print("=" * 50)

    speak("Welcome to INDIA MART GROCERY Voice Assistant!")

    while True:
        try:
            print("\n📞 Enter customer phone number (or 'quit' to exit):")
            customer_phone = input("Phone: ").strip()

            if customer_phone.lower() in ["quit", "exit", "bye"]:
                break

            if not customer_phone:
                print("❌ Please enter a valid phone number")
                continue

            print(f"\n🎯 Starting voice conversation with customer: {customer_phone}")

            while True:
                try:
                    user_input = listen()

                    if not user_input:
                        speak("Thank you for calling INDIA MART GROCERY! Have a great day!")
                        end_conversation(customer_phone)
                        break

                    if user_input.lower() in ["quit", "exit", "bye"]:
                        speak("Thank you for calling INDIA MART GROCERY! Have a great day!")
                        end_conversation(customer_phone)
                        break

                    response = process_voice_customer_interaction(customer_phone, user_input)
                    speak(response)

                    if "Thank you for calling" in response or "Have a great day" in response:
                        break

                except KeyboardInterrupt:
                    print("\n\nBot: Thank you for calling INDIA MART GROCERY! Have a great day!")
                    speak("Thank you for calling INDIA MART GROCERY! Have a great day!")
                    end_conversation(customer_phone)
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    speak("I'm having technical difficulties. Please try again.")
                    continue

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
            speak("Goodbye! Thank you for using our voice assistant!")
            break
        except Exception as e:
            print(f"\n❌ System error: {e}")
            continue

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