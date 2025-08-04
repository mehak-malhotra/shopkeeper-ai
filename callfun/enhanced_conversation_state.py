import requests
import json
import certifi
from pymongo import MongoClient
import google.generativeai as genai
from datetime import datetime, timedelta
import uuid
import os
from typing import Dict, List, Optional, Any
import re

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

# Global conversation states for multiple customers
ACTIVE_CONVERSATIONS: Dict[str, 'ConversationState'] = {}

# Performance optimization: Add caching
CACHED_TOKEN = None
CACHED_TOKEN_EXPIRY = None
INVENTORY_CACHE = None
INVENTORY_CACHE_EXPIRY = None
CUSTOMER_ORDERS_CACHE = {}
CUSTOMER_ORDERS_CACHE_EXPIRY = {}

def get_cached_token():
    """Get cached authentication token"""
    global CACHED_TOKEN, CACHED_TOKEN_EXPIRY
    
    # Check if token is still valid (cache for 1 hour)
    if CACHED_TOKEN and CACHED_TOKEN_EXPIRY and datetime.utcnow() < CACHED_TOKEN_EXPIRY:
        return CACHED_TOKEN
    
    # Get new token
    try:
        response = requests.post("http://localhost:5000/api/auth/login", 
                               json={"email": "dhallhimanshu1234@gmail.com", "password": "1234567890"})
        if response.status_code == 200:
            CACHED_TOKEN = response.json().get('token')
            CACHED_TOKEN_EXPIRY = datetime.utcnow() + timedelta(hours=1)
            return CACHED_TOKEN
        
        response = requests.post("http://localhost:5000/api/auth/login", 
                               json={"email": "dhallhimanshu1234@gmail.com", "password": "password"})
        if response.status_code == 200:
            CACHED_TOKEN = response.json().get('token')
            CACHED_TOKEN_EXPIRY = datetime.utcnow() + timedelta(hours=1)
            return CACHED_TOKEN
        
        return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def get_cached_inventory():
    """Get cached inventory data"""
    global INVENTORY_CACHE, INVENTORY_CACHE_EXPIRY
    
    # Check if cache is still valid (cache for 5 minutes)
    if INVENTORY_CACHE and INVENTORY_CACHE_EXPIRY and datetime.utcnow() < INVENTORY_CACHE_EXPIRY:
        return INVENTORY_CACHE
    
    # Get fresh inventory
    try:
        token = get_cached_token()
        if not token:
            return []
        
        response = requests.get("http://localhost:5000/api/inventory", 
                              headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 200:
            data = response.json()
            INVENTORY_CACHE = data.get('data', [])
            INVENTORY_CACHE_EXPIRY = datetime.utcnow() + timedelta(minutes=5)
            return INVENTORY_CACHE
        else:
            print(f"❌ Inventory fetch failed: {response.status_code}")
        return []
    except Exception as e:
        print(f"❌ Inventory refresh error: {e}")
        return []

def get_cached_customer_orders(customer_phone):
    """Get cached customer orders"""
    global CUSTOMER_ORDERS_CACHE, CUSTOMER_ORDERS_CACHE_EXPIRY
    
    # Check if cache is still valid (cache for 2 minutes)
    if (customer_phone in CUSTOMER_ORDERS_CACHE and 
        customer_phone in CUSTOMER_ORDERS_CACHE_EXPIRY and 
        datetime.utcnow() < CUSTOMER_ORDERS_CACHE_EXPIRY[customer_phone]):
        return CUSTOMER_ORDERS_CACHE[customer_phone]
    
    # Get fresh orders
    try:
        token = get_cached_token()
        if not token:
            return []
        
        # Get all customers to find the customer_id
        response = requests.get("http://localhost:5000/api/customers", 
                              headers={"Authorization": f"Bearer {token}"})
        if response.status_code != 200:
            return []
        
        customers_data = response.json().get('data', [])
        
        # Find customer by phone number
        customer_id = None
        for customer in customers_data:
            if customer.get('phone') == customer_phone:
                customer_id = customer.get('customer_id')
                break
        
        if customer_id is None:
            return []
        
        # Get all orders
        response = requests.get("http://localhost:5000/api/orders", 
                              headers={"Authorization": f"Bearer {token}"})
        if response.status_code != 200:
            return []
        
        orders_data = response.json().get('data', [])
        
        # Filter orders for this customer
        customer_orders = [order for order in orders_data if order.get('customer_id') == customer_id]
        
        # Cache the result
        CUSTOMER_ORDERS_CACHE[customer_phone] = customer_orders
        CUSTOMER_ORDERS_CACHE_EXPIRY[customer_phone] = datetime.utcnow() + timedelta(minutes=2)
        
        return customer_orders
    except Exception as e:
        print(f"❌ Error getting customer orders: {e}")
        return []

def parse_quantity_from_text(text: str) -> int:
    """Parse quantity from natural language text"""
    text = text.lower()
    
    # Common quantity mappings
    quantity_mappings = {
        'dozen': 12,
        'pack': 1,
        'packs': 1,
        'packet': 1,
        'packets': 1,
        'kg': 1,
        'kilo': 1,
        'kilogram': 1,
        'liter': 1,
        'litre': 1,
        'l': 1,
        'ml': 1,
        'gram': 1,
        'g': 1,
        'piece': 1,
        'pieces': 1,
        'bottle': 1,
        'bottles': 1,
        'bag': 1,
        'bags': 1,
        'box': 1,
        'boxes': 1,
        'can': 1,
        'cans': 1
    }
    
    # Extract number and unit
    numbers = re.findall(r'\d+', text)
    if not numbers:
        return 1  # Default to 1 if no number found
    
    quantity = int(numbers[0])
    
    # Check for units and multiply accordingly
    for unit, multiplier in quantity_mappings.items():
        if unit in text:
            return quantity * multiplier
    
    return quantity

def extract_items_from_text(text: str) -> list:
    """Extract items and quantities from natural language text"""
    items = []
    
    # Common patterns
    patterns = [
        r'(\d+)\s*(dozen|pack|packs|packet|packets|kg|kilo|kilogram|liter|litre|l|ml|gram|g|piece|pieces|bottle|bottles|bag|bags|box|boxes|can|cans)?\s+(\w+(?:\s+\w+)*)',
        r'(\w+(?:\s+\w+)*)\s+(\d+)\s*(dozen|pack|packs|packet|packets|kg|kilo|kilogram|liter|litre|l|ml|gram|g|piece|pieces|bottle|bottles|bag|bags|box|boxes|can|cans)?',
        r'(\d+)\s+(\w+(?:\s+\w+)*)',
        r'(\w+(?:\s+\w+)*)\s+(\d+)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        for match in matches:
            if len(match) >= 2:
                if match[0].isdigit():
                    quantity = parse_quantity_from_text(' '.join(match))
                    item_name = ' '.join(match[1:])
                else:
                    item_name = match[0]
                    quantity = parse_quantity_from_text(' '.join(match[1:]))
                
                if item_name.strip():
                    items.append({
                        'name': item_name.strip(),
                        'quantity': quantity
                    })
    
    return items

class ConversationState:
    """
    Enhanced conversation state management for AI grocery store assistant
    Maintains state per customer session with inventory and order tracking
    """
    
    def __init__(self, customer_phone: str, user_email: str = "dhallhimanshu1234@gmail.com"):
        self.conversation_id = str(uuid.uuid4())
        self.customer_phone = customer_phone
        self.user_email = user_email
        self.created_at = datetime.utcnow().isoformat()
        self.last_updated = datetime.utcnow().isoformat()
        
        # Conversation Flow Control
        self.stage = "greeting"
        self.is_active = True
        
        # Customer Information
        self.customer_info = {
            "name": "",
            "phone": customer_phone,
            "address": "",
            "customer_id": None,
            "is_existing_customer": False
        }
        
        # Order Management
        self.current_order = {
            "items": [],
            "total_price": 0.0,
            "notes": "",
            "order_id": None,
            "status": "draft"
        }
        
        # Inventory State (real-time)
        self.inventory_snapshot = []
        self.inventory_updates = []  # Track changes made during conversation
        
        # Conversation Flow Booleans
        self.flow_flags = {
            "phone_collected": False,
            "customer_verified": False,
            "address_confirmed": False,
            "order_started": False,
            "order_complete": False,
            "payment_discussed": False,
            "delivery_confirmed": False,
            "call_ending": False
        }
        
        # Enhanced Conversation Context with Chat Buffer
        self.context = {
            "last_user_input": "",
            "last_ai_response": "",
            "conversation_summary": "",
            "current_topic": "greeting",
            "chat_buffer": [],  # Store recent conversation history
            "conversation_history": [],  # Full conversation history
            "last_5_messages": []  # Store last 5 messages for model context
        }
        
        # Initialize inventory
        self._refresh_inventory()
    
    def _refresh_inventory(self):
        """Get fresh inventory from backend"""
        try:
            # Use cached inventory instead of making HTTP request
            self.inventory_snapshot = get_cached_inventory()
        except Exception as e:
            print(f"❌ Inventory refresh error: {e}")
    
    def _get_user_token(self):
        """Get authentication token"""
        return get_cached_token()
    
    def update_inventory_item(self, item_name: str, quantity_change: int):
        """Update inventory item quantity during conversation"""
        for item in self.inventory_snapshot:
            if item['name'].lower() == item_name.lower():
                new_quantity = item['quantity'] + quantity_change
                if new_quantity >= 0:
                    item['quantity'] = new_quantity
                    self.inventory_updates.append({
                        "item_name": item['name'],
                        "quantity_change": quantity_change,
                        "new_quantity": new_quantity,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    return True
        return False
    
    def get_available_items(self):
        """Get items with stock > 0"""
        return [item for item in self.inventory_snapshot if item['quantity'] > 0]
    
    def find_item(self, item_name: str):
        """Find item by name (case-insensitive) with improved matching"""
        # First try exact match
        for item in self.inventory_snapshot:
            if item['name'].lower() == item_name.lower():
                return item
        
        # Try partial match (item_name contains in item name)
        for item in self.inventory_snapshot:
            if item_name.lower() in item['name'].lower():
                return item
        
        # Try reverse partial match (item name contains item_name)
        for item in self.inventory_snapshot:
            if item['name'].lower() in item_name.lower():
                return item
        
        # Try word-by-word matching
        item_words = item_name.lower().split()
        for item in self.inventory_snapshot:
            item_name_words = item['name'].lower().split()
            if any(word in item_name_words for word in item_words):
                return item
        
        # Common item name mappings
        item_mappings = {
            'milk': ['amul', 'taaza', 'milk'],
            'apple': ['apple'],
            'garam masala': ['masala', 'spice'],
            'atta': ['aashirvaad', 'atta', 'wheat'],
            'oil': ['sunflower', 'oil', 'fortune'],
            'bread': ['bread'],
            'rice': ['rice'],
            'sugar': ['sugar'],
            'salt': ['salt'],
            'tea': ['tea'],
            'coffee': ['coffee']
        }
        
        # Check mappings
        for search_term, keywords in item_mappings.items():
            if search_term in item_name.lower():
                for item in self.inventory_snapshot:
                    if any(keyword in item['name'].lower() for keyword in keywords):
                        return item
        
        return None
    
    def add_item_to_order(self, item_name: str, quantity: int):
        """Add item to current order"""
        item = self.find_item(item_name)
        if not item:
            return False, f"Item '{item_name}' not found in inventory"
        
        if item['quantity'] < quantity and item['quantity'] > item['minStock']*0.2:
            return False, f"Only {item['quantity']} {item['name']} available"
        
        # Add to order
        order_item = {
            "name": item['name'],
            "quantity": quantity,
            "price": item['price'],
            "total": quantity * item['price']
        }
        
        self.current_order['items'].append(order_item)
        self.current_order['total_price'] += order_item['total']
        
        # Update inventory
        self.update_inventory_item(item['name'], -quantity)
        
        return True, f"Added {quantity} {item['name']} to order"
    
    def remove_item_from_order(self, item_name: str, quantity: int = None):
        """Remove item from current order"""
        for i, item in enumerate(self.current_order['items']):
            if item['name'].lower() == item_name.lower():
                if quantity is None or quantity >= item['quantity']:
                    # Remove entire item
                    removed_item = self.current_order['items'].pop(i)
                    self.current_order['total_price'] -= removed_item['total']
                    self.update_inventory_item(item['name'], removed_item['quantity'])
                    return True, f"Removed {removed_item['name']} from order"
                else:
                    # Remove partial quantity
                    item['quantity'] -= quantity
                    item['total'] = item['quantity'] * item['price']
                    self.current_order['total_price'] -= quantity * item['price']
                    self.update_inventory_item(item['name'], quantity)
                    return True, f"Removed {quantity} {item['name']} from order"
        
        return False, f"Item '{item_name}' not found in order"
    
    def clear_order(self):
        """Clear current order and restore inventory"""
        for item in self.current_order['items']:
            self.update_inventory_item(item['name'], item['quantity'])
        
        self.current_order = {
            "items": [],
            "total_price": 0.0,
            "notes": "",
            "order_id": None,
            "status": "draft"
        }
        self.flow_flags["order_started"] = False
        self.flow_flags["order_complete"] = False
    
    def finalize_order(self):
        """Finalize order and save to backend"""
        if not self.current_order['items']:
            return False, "No items in order"
        
        try:
            token = self._get_user_token()
            if not token:
                return False, "Authentication failed"
            
            # Prepare order data
            order_data = {
                "customerPhone": self.customer_info['phone'],
                "customerName": self.customer_info['name'],
                "items": self.current_order['items'],
                "total": self.current_order['total_price'],
                "status": "pending",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "notes": self.current_order['notes']
            }
            
            # Create order in backend
            response = requests.post("http://localhost:5000/api/orders", 
                                   headers={"Authorization": f"Bearer {token}"},
                                   json=order_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.current_order['order_id'] = data['data']['order_id']
                    self.current_order['status'] = 'pending'
                    self.flow_flags["order_complete"] = True
                    
                    # Apply inventory updates to backend
                    self._apply_inventory_updates()
                    
                    return True, f"Order placed successfully! Order ID: {self.current_order['order_id']}"
                else:
                    return False, data.get('message', 'Order creation failed')
            else:
                return False, f"Backend error: {response.status_code}"
                
        except Exception as e:
            return False, f"Error finalizing order: {str(e)}"
    
    def _apply_inventory_updates(self):
        """Apply inventory updates to backend"""
        if not self.inventory_updates:
            return
        
        try:
            token = self._get_user_token()
            if not token:
                return
            
            updates = []
            for update in self.inventory_updates:
                updates.append({
                    "name": update['item_name'],
                    "quantity": update['quantity_change']
                })
            
            response = requests.post("http://localhost:5000/api/inventory/update-quantities",
                                   headers={"Authorization": f"Bearer {token}"},
                                   json={"updates": updates})
            
            if response.status_code == 200:
                self.inventory_updates = []  # Clear updates after successful application
                print("✅ Inventory updates applied to backend")
            else:
                print(f"❌ Failed to apply inventory updates: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error applying inventory updates: {e}")
    
    def add_to_chat_buffer(self, role: str, content: str):
        """Add message to chat buffer for context"""
        message = {
            "role": role,  # "user" or "assistant"
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add to conversation history
        self.context["conversation_history"].append(message)
        
        # Keep only last 10 messages in buffer for LLM context
        self.context["chat_buffer"] = self.context["conversation_history"][-10:]
        
        # Update last 5 messages for model context
        self.context["last_5_messages"] = self.context["conversation_history"][-5:]
    
    def get_recent_conversation(self, max_messages: int = 5):
        """Get recent conversation for LLM context"""
        return self.context["chat_buffer"][-max_messages:] if self.context["chat_buffer"] else []
    
    def get_last_5_messages(self):
        """Get last 5 messages for model context"""
        return self.context.get("last_5_messages", [])
    
    def update_context(self, user_input: str, ai_response: str, topic: str = None):
        """Update conversation context with chat buffer"""
        self.context['last_user_input'] = user_input
        self.context['last_ai_response'] = ai_response
        if topic:
            self.context['current_topic'] = topic
        self.last_updated = datetime.utcnow().isoformat()
        
        # Add to chat buffer
        self.add_to_chat_buffer("user", user_input)
        self.add_to_chat_buffer("assistant", ai_response)
    
    def get_state_summary(self):
        """Get concise state summary for LLM"""
        return {
            "stage": self.stage,
            "customer_verified": self.flow_flags["customer_verified"],
            "order_started": self.flow_flags["order_started"],
            "order_complete": self.flow_flags["order_complete"],
            "current_order_items": len(self.current_order['items']),
            "current_order_total": self.current_order['total_price'],
            "available_items_count": len(self.get_available_items()),
            "last_topic": self.context['current_topic']
        }
    
    def to_json(self):
        """Convert state to JSON for storage"""
        return {
            "conversation_id": self.conversation_id,
            "customer_phone": self.customer_phone,
            "user_email": self.user_email,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "stage": self.stage,
            "is_active": self.is_active,
            "customer_info": self.customer_info,
            "current_order": self.current_order,
            "flow_flags": self.flow_flags,
            "context": self.context,
            "inventory_snapshot": self.inventory_snapshot,
            "inventory_updates": self.inventory_updates
        }
    
    def from_json(self, data: dict):
        """Load state from JSON"""
        self.conversation_id = data.get("conversation_id", str(uuid.uuid4()))
        self.customer_phone = data.get("customer_phone", "")
        self.user_email = data.get("user_email", "dhallhimanshu1234@gmail.com")
        self.created_at = data.get("created_at", datetime.utcnow().isoformat())
        self.last_updated = data.get("last_updated", datetime.utcnow().isoformat())
        self.stage = data.get("stage", "greeting")
        self.is_active = data.get("is_active", True)
        self.customer_info = data.get("customer_info", {})
        self.current_order = data.get("current_order", {})
        self.flow_flags = data.get("flow_flags", {})
        self.context = data.get("context", {})
        self.inventory_snapshot = data.get("inventory_snapshot", [])
        self.inventory_updates = data.get("inventory_updates", [])
        
        # Ensure chat buffer exists for backward compatibility
        if "chat_buffer" not in self.context:
            self.context["chat_buffer"] = []
        if "conversation_history" not in self.context:
            self.context["conversation_history"] = []
        if "last_5_messages" not in self.context:
            self.context["last_5_messages"] = []

    def end_conversation(self):
        """End conversation and cleanup"""
        self.is_active = False
        self.flow_flags["call_ending"] = True
        
        # Apply any pending inventory updates
        if self.inventory_updates:
            self._apply_inventory_updates()
        
        # Remove from active conversations
        if self.customer_phone in ACTIVE_CONVERSATIONS:
            del ACTIVE_CONVERSATIONS[self.customer_phone]
        
        print(f"✅ Conversation ended for {self.customer_phone}")

# Global conversation management functions
def get_or_create_conversation(customer_phone: str, user_email: str = "dhallhimanshu1234@gmail.com") -> ConversationState:
    """Get existing conversation or create new one"""
    if customer_phone in ACTIVE_CONVERSATIONS:
        return ACTIVE_CONVERSATIONS[customer_phone]
    
    conversation = ConversationState(customer_phone, user_email)
    ACTIVE_CONVERSATIONS[customer_phone] = conversation
    return conversation

def end_conversation(customer_phone: str):
    """End conversation for specific customer"""
    if customer_phone in ACTIVE_CONVERSATIONS:
        ACTIVE_CONVERSATIONS[customer_phone].end_conversation()

def get_active_conversations():
    """Get all active conversations"""
    return {phone: conv for phone, conv in ACTIVE_CONVERSATIONS.items() if conv.is_active}

def cleanup_inactive_conversations():
    """Clean up inactive conversations"""
    inactive_phones = []
    for phone, conv in ACTIVE_CONVERSATIONS.items():
        if not conv.is_active:
            inactive_phones.append(phone)
    
    for phone in inactive_phones:
        del ACTIVE_CONVERSATIONS[phone]
    
    if inactive_phones:
        print(f"🧹 Cleaned up {len(inactive_phones)} inactive conversations")

# Enhanced LLM processing with better state management
def process_conversation_with_llm(customer_phone: str, user_input: str) -> str:
    """Process conversation with enhanced state management"""
    
    # Get or create conversation state
    state = get_or_create_conversation(customer_phone)
    
    # Update context
    state.update_context(user_input, "", "processing")
    
    # Create LLM prompt with current state
    prompt = create_llm_prompt(state, user_input)
    
    try:
        response = model.generate_content(prompt)
        ai_response = response.text.strip()
        
        # Extract response text from JSON if needed
        response_text = extract_response_from_llm(ai_response)
        
        # Update context with AI response
        state.update_context(user_input, response_text, "ai_response")
        
        # Process any actions from AI response
        process_ai_actions(state, ai_response)
        
        # Check if this should end the conversation
        if should_end_conversation(user_input, response_text, state):
            success, message = state.finalize_order()
            if success:
                end_conversation(customer_phone)
                return f"Perfect! {message} Thank you for your order! Have a great day!"
            else:
                end_conversation(customer_phone)
                return f"Thank you for calling! {message} Have a great day!"
        
        return response_text
        
    except Exception as e:
        error_response = f"I'm having trouble understanding. Could you please repeat that? (Error: {str(e)})"
        state.update_context(user_input, error_response, "error")
        return error_response

def should_end_conversation(user_input: str, ai_response: str, state: ConversationState) -> bool:
    """Check if conversation should end based on user input and context"""
    
    # Check for end keywords in user input - only end when customer explicitly indicates completion
    end_keywords = ["bye", "goodbye", "exit", "quit", "end", "thank you", "thanks", "thankyou", "done", "finish", "complete", "that's it", "that's all", "nothing else", "i'm done", "i'm finished", "that's everything", "that's all i need", "nothing more", "complete my order", "finalize my order"]
    
    if any(word in user_input.lower() for word in end_keywords):
        # Always end when customer explicitly indicates completion
        return True
    
    # Check if AI response indicates order completion
    completion_phrases = [
        "order is complete", "order complete", "finalize", "proceed with order",
        "confirm your order", "everything for your order", "happy with"
    ]
    
    if any(phrase in ai_response.lower() for phrase in completion_phrases):
        # Check if user input is affirmative
        affirmative_words = ["yes", "perfect", "okay", "ok", "sure", "confirm", "proceed"]
        if any(word in user_input.lower() for word in affirmative_words):
            return True
    
    return False

def extract_response_from_llm(llm_output: str) -> str:
    """Extract natural response text from LLM output"""
    try:
        # Check if output contains JSON
        if '{' in llm_output and '}' in llm_output:
            start = llm_output.find('{')
            end = llm_output.rfind('}') + 1
            json_str = llm_output[start:end]
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Extract response text
            response_text = data.get('response', '')
            
            # If response is empty, try to extract from the original text
            if not response_text:
                # Look for text before the JSON
                before_json = llm_output[:start].strip()
                if before_json:
                    return before_json
                else:
                    return "I understand. How can I help you?"
            
            return response_text
        else:
            # No JSON found, return as is
            return llm_output.strip()
            
    except Exception as e:
        print(f"❌ Error extracting response: {e}")
        # Fallback: return the original text or a default response
        if llm_output.strip():
            return llm_output.strip()
        else:
            return "I understand. How can I help you?"

def process_user_input_for_items(user_input: str, state: ConversationState) -> list:
    """Process user input to extract items before sending to LLM"""
    extracted_items = extract_items_from_text(user_input)
    processed_items = []
    
    # Handle context references like "that" or "it"
    if any(word in user_input.lower() for word in ["that", "it", "this"]) and not extracted_items:
        # Look for recently mentioned items in conversation
        recent_context = state.get_recent_conversation(3)
        for msg in recent_context:
            if msg['role'] == 'assistant':
                # Extract items mentioned by assistant
                context_items = extract_items_from_text(msg['content'])
                for item_data in context_items:
                    found_item = state.find_item(item_data['name'])
                    if found_item:
                        processed_items.append({
                            'name': found_item['name'],
                            'quantity': item_data['quantity'],
                            'price': found_item['price']
                        })
                        break  # Use the first found item
    
    for item_data in extracted_items:
        item_name = item_data['name']
        quantity = item_data['quantity']
        
        # Try to find the item in inventory
        found_item = state.find_item(item_name)
        if found_item:
            processed_items.append({
                'name': found_item['name'],
                'quantity': quantity,
                'price': found_item['price']
            })
        else:
            # Item not found, but keep it for LLM to handle
            processed_items.append({
                'name': item_name,
                'quantity': quantity,
                'price': 0
            })
    
    return processed_items

def create_llm_prompt(state: ConversationState, user_input: str) -> str:
    """Create comprehensive LLM prompt with current state"""
    
    # Pre-process user input to extract items
    extracted_items = process_user_input_for_items(user_input, state)
    
    available_items = state.get_available_items()
    # Limit inventory display to reduce prompt size - only show first 20 items
    limited_items = available_items[:20]
    items_list = "\n".join([f"- {item['name']}: ₹{item['price']} (Stock: {item['quantity']})" for item in limited_items])
    if len(available_items) > 20:
        items_list += f"\n... and {len(available_items) - 20} more items"
    
    state_summary = state.get_state_summary()
    
    # Get recent conversation for context - limit to last 2 messages
    recent_conversation = state.get_recent_conversation(2)
    conversation_context = ""
    if recent_conversation:
        conversation_context = "\nRecent conversation:\n"
        for msg in recent_conversation:
            conversation_context += f"{msg['role']}: {msg['content']}\n"
    
    # Get last 5 messages for model context
    last_5_messages = state.get_last_5_messages()
    last_5_context = ""
    if last_5_messages:
        last_5_context = "\nLast 5 messages for context:\n"
        for msg in last_5_messages:
            last_5_context += f"{msg['role']}: {msg['content']}\n"
    
    # Customer details section
    customer_details = ""
    if state.customer_info.get("name"):
        customer_details = f"\nCUSTOMER DETAILS:\n- Name: {state.customer_info.get('name')}\n- Phone: {state.customer_info.get('phone')}\n- Address: {state.customer_info.get('address', 'Not provided')}\n- Customer ID: {state.customer_info.get('customer_id', 'New customer')}\n"
    
    # Get customer orders for context
    customer_orders = []
    try:
        # Use cached customer orders instead of making HTTP request
        customer_orders = get_cached_customer_orders(state.customer_info.get('phone', ''))
    except:
        pass
    
    orders_context = ""
    if customer_orders:
        orders_context = "\nCUSTOMER ORDERS:\n"
        # Only show last 3 orders to reduce prompt size
        for i, order in enumerate(customer_orders[-3:], 1):
            orders_context += f"{i}. Order ID: {order.get('order_id')} - Status: {order.get('status')} - Total: ₹{order.get('total')}\n"
            items = order.get('items', [])
            if items:
                orders_context += "   Items: "
                # Only show first 3 items to reduce prompt size
                for item in items[:3]:
                    orders_context += f"{item.get('quantity', 0)}x{item.get('name', 'Unknown')}, "
                orders_context = orders_context.rstrip(", ") + "\n"
    
    # Add extracted items context
    extracted_items_context = ""
    unavailable_items = []
    if extracted_items:
        extracted_items_context = "\nEXTRACTED ITEMS FROM USER INPUT:\n"
        for item in extracted_items:
            if item['price'] == 0:
                # Item not found in inventory
                unavailable_items.append(item['name'])
                extracted_items_context += f"- {item['name']}: {item['quantity']} (NOT AVAILABLE)\n"
            else:
                extracted_items_context += f"- {item['name']}: {item['quantity']} (₹{item['price']})\n"
    
    # Add unavailable items context
    unavailable_context = ""
    if unavailable_items:
        unavailable_context = f"\nUNAVAILABLE ITEMS: {', '.join(unavailable_items)}\n"
        unavailable_context += "For these items, apologize and suggest alternatives from inventory."
    
    prompt = f"""
You are a professional store assistant for INDIA MART GROCERY. You are helping a customer with their order.
you have complete knowledge of the store's inventory, customer orders, and conversation state.
if a person uses words like "that" or "it" referring to an item, you should check the recent conversation context to understand what they are referring to.
You are polite, friendly, and helpful. You can handle all requests naturally without rigid menus.
if person uses words like want to make , reicpe etc you can suggest recipes and ingredients from the inventory , also manage the conversation state accordingly.
if someone asks he need to make 2 pizzas or cake for 2 persons recommend the ingredients and quantity from the inventory.   
along with it you have a good domain knowledge , for example when i say ingredients for a dish you know what are the ingredients and you can suggest alternatives if the item is not available , you can ask crooss questions as per your requirement.
BEFORE EACH REPLY MAKE SURE YOU CHECK THE CONVERSATION STATE AND recent conversation context to provide accurate and relevant responses.
ALSO BE CONCISE JUST TAKE THE ORDER , because people right now are usually in hurry but make sure you are polite and helpful.
BEFORE REPLYING MAKE SURE YOU CHECK THE CONVERSATION STATE AND THE LAST 5 MESSAGES TO STAY IN CORRELATION WITH THE CONVERSATION FLOW.
CONVERSATION STATE:
{json.dumps(state_summary, indent=2)}

CUSTOMER INFO:
{json.dumps(state.customer_info, indent=2)}
{customer_details}

CURRENT ORDER:
{json.dumps(state.current_order, indent=2)}

AVAILABLE INVENTORY (INTERNAL USE - means do not disclose completeinventory to customer but you can disclose related items or suggested items or similar items):
{items_list}

CUSTOMER ORDERS:
{orders_context}

EXTRACTED ITEMS FROM USER INPUT:
{extracted_items_context}

UNAVAILABLE ITEMS:
{unavailable_context}

CONVERSATION FLOW FLAGS:
{json.dumps(state.flow_flags, indent=2)}

CURRENT STAGE: {state.stage}
{conversation_context}
{last_5_context}

USER INPUT: "{user_input}"

INSTRUCTIONS:
1. Be natural, friendly, and helpful
2. Use customer's name when available: {state.customer_info.get('name', '')}
3. Handle all requests naturally without rigid menus
4. When customer mentions items, extract them using the extract_items_from_text function
5. Use "add_items" array for multiple items
6. Parse quantities correctly: "2 dozen" = 24, "8 packs" = 8, "5kg bag" = 1
7. Only end when customer says he has completed the order in any textual forms,.
8. Continue after "yes" confirmations - don't end conversation
9. Never disclose full inventory to customers
10. If item not found or out of stock, apologize and suggest alternatives from inventory, dont give false promises
11. When customer says "that" or "it" referring to an item, check recent conversation context
12. Handle item modifications: "make onions 1 kg instead of 2", "remove harpic"
13. When customer asks about price, provide it and offer to add to order
14. If item is not available, say "Sorry, we don't have [item] in our inventory yet" and suggest similar items
15. Check inventory availability before adding items to order

CAPABILITIES:
- Add items: "I want apples", "add bananas", "need bread"
-Add recipes : "I want to make a cake, what ingredients do I need?"
- Add multiple items: "add 2 dozen apples, 8 packs garam masala, and 5kg atta"
- Modify quantities: "make onions 1 kg instead of 2", "change milk to 3 packs"
- Remove items: "remove harpic", "take out tomatoes"
- Complete order: "that's it", "that's all", "nothing else", "i'm done", "complete my order"

GREETING EXAMPLES:
- For existing customer: "Welcome back [Name]! How can I help you today?"
- For new customer: "Welcome to INDIA MART GROCERY! I don't have your details yet. What's your name?"
- For general greeting: "Hello! Welcome to INDIA MART GROCERY. How can I assist you?"

in case the item is a container - like milke may have a large number of items under it, like amul taaza milk, amul gold milk, amul cow milk, etc , in that case suggest all the similar items from inventory o the user and let him choose the one he wants to add to order.
in the cases like:
📦 Item 'chocolate' not found in inventory
❌ Failed to add chocolate: Item 'chocolate' not found in inventory
you should not add the item to order, just inform the customer that the item is not available and suggest alternatives from inventory.
RESPOND WITH JSON ONLY:
{{
    "response": "Your natural response to the customer",
    "actions": {{
        "add_item": {{"name": "item_name", "quantity": 0}},
        "add_items": [
            {{"name": "item_name", "quantity": 0}},
            {{"name": "item_name", "quantity": 0}}
        ],
        "modify_item": {{"name": "item_name", "new_quantity": 0}},
        "remove_item": {{"name": "item_name"}},
        "finalize_order": true/false,
        "end_conversation": true/false
    }}
}}

EXAMPLES:
- Customer says "apples" → Ask for quantity and add to order
- Customer says "add 2 dozen apples, 8 packs garam masala, and 5kg atta" → Add multiple items at once using add_items array
- Customer says "What is the price for Toor Dal?" → Provide price and offer to add
- Customer says "Okay, add one bag of that to my order" → Add Toor Dal (from context)
- Customer says "make onions 1 kg instead of 2" → Modify onion quantity to 1 kg
- Customer says "remove harpic" → Remove Harpic from order
- Customer says "yes" → Confirm and continue (don't end conversation)
- Customer says "that's it" or "that's all" → Complete order and end conversation
- Customer says "bye" → End conversation
- Customer says "bananas" (if not in inventory) → "Sorry, we don't have bananas in our inventory yet. Would you like to try apples or oranges instead?"
- Customer says "2 dozen bananas" (if not in inventory) → "Sorry, we don't have bananas in our inventory yet. We have apples, oranges, and other fruits available."
"""
    
    return prompt

def process_ai_actions(state: ConversationState, ai_response: str):
    """Process actions from AI response with proper error handling"""
    try:
        # Extract JSON from AI response
        if '{' in ai_response and '}' in ai_response:
            start = ai_response.find('{')
            end = ai_response.rfind('}') + 1
            json_str = ai_response[start:end]
            data = json.loads(json_str)
            actions = data.get('actions', {})
            
            # Process item addition
            if actions.get('add_item'):
                item_data = actions['add_item']
                if item_data and isinstance(item_data, dict):
                    item_name = item_data.get('name')
                    quantity = item_data.get('quantity', 0)
                    if item_name and quantity > 0:
                        success, message = state.add_item_to_order(item_name, quantity)
                        print(f"📦 {message}")
                        if not success:
                            # Item not found or out of stock - don't add to order
                            print(f"❌ Failed to add {item_name}: {message}")
            
            # Process multiple items addition
            if actions.get('add_items'):
                items_data = actions['add_items']
                if items_data and isinstance(items_data, list):
                    for item_data in items_data:
                        if isinstance(item_data, dict):
                            item_name = item_data.get('name')
                            quantity = item_data.get('quantity', 0)
                            if item_name and quantity > 0:
                                success, message = state.add_item_to_order(item_name, quantity)
                                print(f"📦 {message}")
                                if not success:
                                    # Item not found or out of stock - don't add to order
                                    print(f"❌ Failed to add {item_name}: {message}")
            
            # Process item modification (change quantity)
            if actions.get('modify_item'):
                item_data = actions['modify_item']
                if item_data and isinstance(item_data, dict):
                    item_name = item_data.get('name')
                    new_quantity = item_data.get('new_quantity', 0)
                    if item_name and new_quantity >= 0:
                        # First remove the item, then add with new quantity
                        state.remove_item_from_order(item_name)
                        if new_quantity > 0:
                            success, message = state.add_item_to_order(item_name, new_quantity)
                            print(f"📦 {message}")
                        else:
                            print(f"🗑️ Removed {item_name} from order")
            
            # Process item removal
            if actions.get('remove_item'):
                item_data = actions['remove_item']
                if item_data and isinstance(item_data, dict):
                    item_name = item_data.get('name')
                    if item_name:
                        state.remove_item_from_order(item_name)
                        print(f"🗑️ Removed {item_name} from order")
            
            # Process order finalization
            if actions.get('finalize_order'):
                success, message = state.finalize_order()
                print(f"✅ {message}")
            
            # Process conversation ending
            if actions.get('end_conversation'):
                state.end_conversation()
                print("👋 Conversation ended")
                
    except Exception as e:
        print(f"❌ Error processing AI actions: {e}")

# Main conversation handler
def handle_customer_call(customer_phone: str, user_input: str) -> str:
    """Handle customer call with enhanced LLM processing"""
    return process_conversation_with_llm(customer_phone, user_input)

if __name__ == "__main__":
    # Example usage
    print("🤖 Enhanced Conversation State Management System")
    print("=" * 50)
    
    # Test conversation
    customer_phone = "1234567890"
    
    responses = [
        "Hello, I want to order some groceries",
        "I need 2 apples",
        "And 1 bread",
        "That's all, please complete my order",
        "Thank you, goodbye"
    ]
    
    for user_input in responses:
        print(f"\n👤 Customer: {user_input}")
        response = handle_customer_call(customer_phone, user_input)
        print(f"🤖 Assistant: {response}")
    
    # Cleanup
    cleanup_inactive_conversations()
    print(f"\n📊 Active conversations: {len(get_active_conversations())}") 