import requests
import json
import certifi
from pymongo import MongoClient
import google.generativeai as genai
from datetime import datetime
import uuid
import os
from typing import Dict, List, Optional, Any

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
            "conversation_history": []  # Full conversation history
        }
        
        # Initialize inventory
        self._refresh_inventory()
    
    def _refresh_inventory(self):
        """Get fresh inventory from backend"""
        try:
            token = self._get_user_token()
            if not token:
                return
            
            response = requests.get("http://localhost:5000/api/inventory", 
                                  headers={"Authorization": f"Bearer {token}"})
            if response.status_code == 200:
                data = response.json()
                self.inventory_snapshot = data.get('data', [])
            else:
                print(f"❌ Inventory fetch failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Inventory refresh error: {e}")
    
    def _get_user_token(self):
        """Get authentication token"""
        try:
            response = requests.post("http://localhost:5000/api/auth/login", 
                                   json={"email": self.user_email, "password": "1234567890"})
            if response.status_code == 200:
                return response.json().get('token')
            
            response = requests.post("http://localhost:5000/api/auth/login", 
                                   json={"email": self.user_email, "password": "password"})
            if response.status_code == 200:
                return response.json().get('token')
            
            return None
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return None
    
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
        """Find item by name (case-insensitive)"""
        for item in self.inventory_snapshot:
            if item['name'].lower() == item_name.lower():
                return item
        return None
    
    def add_item_to_order(self, item_name: str, quantity: int):
        """Add item to current order"""
        item = self.find_item(item_name)
        if not item:
            return False, f"Item '{item_name}' not found in inventory"
        
        if item['quantity'] < quantity:
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
    
    def get_recent_conversation(self, max_messages: int = 5):
        """Get recent conversation for LLM context"""
        return self.context["chat_buffer"][-max_messages:] if self.context["chat_buffer"] else []
    
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
    
    # Check for end keywords in user input
    end_keywords = ["bye", "goodbye", "exit", "quit", "end", "thank you", "thanks", "done", "finish", "complete", "yes", "perfect", "okay", "ok"]
    
    if any(word in user_input.lower() for word in end_keywords):
        # If we have items in order, finalize it
        if state.current_order.get('items'):
            return True
        else:
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

def create_llm_prompt(state: ConversationState, user_input: str) -> str:
    """Create comprehensive LLM prompt with current state"""
    
    available_items = state.get_available_items()
    items_list = "\n".join([f"- {item['name']}: ₹{item['price']} (Stock: {item['quantity']})" for item in available_items])
    
    state_summary = state.get_state_summary()
    
    # Get recent conversation for context
    recent_conversation = state.get_recent_conversation(3)
    conversation_context = ""
    if recent_conversation:
        conversation_context = "\nRecent conversation:\n"
        for msg in recent_conversation:
            conversation_context += f"{msg['role']}: {msg['content']}\n"
    
    # Customer details section
    customer_details = ""
    if state.customer_info.get("name"):
        customer_details = f"\nCUSTOMER DETAILS:\n- Name: {state.customer_info.get('name')}\n- Phone: {state.customer_info.get('phone')}\n- Address: {state.customer_info.get('address', 'Not provided')}\n- Customer ID: {state.customer_info.get('customer_id', 'New customer')}\n"
    
    # Get customer orders for context
    customer_orders = []
    try:
        from enhanced_llm_chatbot import get_customer_orders
        customer_orders = get_customer_orders(state.customer_info.get('phone', ''))
    except:
        pass
    
    orders_context = ""
    if customer_orders:
        orders_context = "\nCUSTOMER ORDERS:\n"
        for i, order in enumerate(customer_orders, 1):
            orders_context += f"{i}. Order ID: {order.get('order_id')} - Status: {order.get('status')} - Total: ₹{order.get('total')}\n"
            items = order.get('items', [])
            if items:
                orders_context += "   Items: "
                for item in items:
                    orders_context += f"{item.get('quantity', 0)}x{item.get('name', 'Unknown')}, "
                orders_context = orders_context.rstrip(", ") + "\n"
    
    prompt = f"""
You are a professional grocery store assistant for INDIA MART GROCERY. You are helping a customer with their order.

CONVERSATION STATE:
{json.dumps(state_summary, indent=2)}

CUSTOMER INFO:
{json.dumps(state.customer_info, indent=2)}
{customer_details}

CURRENT ORDER:
{json.dumps(state.current_order, indent=2)}

AVAILABLE INVENTORY (INTERNAL USE ONLY - DO NOT DISCLOSE TO CUSTOMER):
{items_list}

CUSTOMER ORDERS:
{orders_context}

CONVERSATION FLOW FLAGS:
{json.dumps(state.flow_flags, indent=2)}

CURRENT STAGE: {state.stage}
{conversation_context}

USER INPUT: "{user_input}"

INSTRUCTIONS:
1. Be natural, friendly, and helpful
2. Use the customer's name when available: {state.customer_info.get('name', '')}
3. Handle all customer requests naturally without rigid menus
4. If customer wants to place an order, start the ordering process
5. If customer wants to check order status, show their orders
6. If customer wants to delete an order, help them delete it
7. If customer mentions specific items, add them to the order
8. Update inventory and order as needed
9. Use the flow flags to guide conversation
10. If customer wants to end call, set call_ending flag
11. Be conversational, not robotic
12. Respond naturally, not in JSON format
13. Always confirm customer details before finalizing orders
14. Ask for delivery address if not provided
15. NEVER disclose the full inventory list to customers
16. Only mention specific items when customer asks for them
17. For greetings, check if customer exists and greet appropriately

CAPABILITIES:
- Place new orders: "I want to order", "place an order", "buy groceries"
- Check order status: "check my orders", "order status", "my orders"
- Delete orders: "delete order", "cancel order", "remove order"
- Add items: "I want apples", "add bananas", "need bread"
- Complete order: "that's all", "done", "finish", "complete"

GREETING EXAMPLES:
- For existing customer: "Welcome back [Name]! How can I help you today?"
- For new customer: "Welcome to INDIA MART GROCERY! I don't have your details yet. What's your name?"
- For general greeting: "Hello! Welcome to INDIA MART GROCERY. How can I assist you?"

RESPOND WITH JSON ONLY:
{{
    "response": "Your natural response to the customer",
    "actions": {{
        "update_stage": "new_stage_or_null",
        "update_flags": {{"flag_name": true/false}},
        "add_item": {{"name": "item_name", "quantity": 0}},
        "remove_item": {{"name": "item_name", "quantity": 0}},
        "clear_order": true/false,
        "finalize_order": true/false,
        "end_conversation": true/false,
        "update_customer": {{"field": "value"}},
        "check_orders": true/false,
        "delete_order": {{"order_id": "id_or_index"}},
        "show_order_details": {{"order_id": "id_or_index"}}
    }},
    "system_message": "Optional system message for debugging"
}}

EXAMPLES:
- Customer says "I want to order" → Start ordering process
- Customer says "check my orders" → Show order list
- Customer says "delete order 123" → Delete specific order
- Customer says "apples" → Ask for quantity and add to order
- Customer says "done" → Complete order
- Customer says "bye" → End conversation
- If customer name is "John" → "Great John, I've added that to your order"
- For greeting: "Hello" → Check customer and greet appropriately
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
            
            # Process stage update
            if actions.get('update_stage'):
                state.stage = actions['update_stage']
            
            # Process flag updates
            if actions.get('update_flags'):
                for flag, value in actions['update_flags'].items():
                    if flag in state.flow_flags:
                        state.flow_flags[flag] = value
            
            # Process customer updates
            if actions.get('update_customer'):
                customer_updates = actions['update_customer']
                if isinstance(customer_updates, dict):
                    for field, value in customer_updates.items():
                        if field in state.customer_info:
                            state.customer_info[field] = value
            
            # Process item addition
            if actions.get('add_item'):
                item_data = actions['add_item']
                if item_data and isinstance(item_data, dict):
                    item_name = item_data.get('name')
                    quantity = item_data.get('quantity', 0)
                    if item_name and quantity > 0:
                        success, message = state.add_item_to_order(item_name, quantity)
                        print(f"📦 {message}")
            
            # Process item removal
            if actions.get('remove_item'):
                item_data = actions['remove_item']
                if item_data and isinstance(item_data, dict):
                    item_name = item_data.get('name')
                    quantity = item_data.get('quantity')
                    if item_name:
                        success, message = state.remove_item_from_order(item_name, quantity)
                        print(f"🗑️ {message}")
            
            # Process order clearing
            if actions.get('clear_order'):
                state.clear_order()
                print("🔄 Order cleared")
            
            # Process order finalization
            if actions.get('finalize_order'):
                success, message = state.finalize_order()
                print(f"✅ {message}")
            
            # Process order checking
            if actions.get('check_orders'):
                from enhanced_llm_chatbot import get_customer_orders, display_order_summary
                customer_orders = get_customer_orders(state.customer_info.get('phone', ''))
                if customer_orders:
                    print(f"📋 Found {len(customer_orders)} orders:")
                    for order in customer_orders:
                        display_order_summary(order)
                else:
                    print("📋 No orders found for this customer")
            
            # Process order deletion
            if actions.get('delete_order'):
                delete_data = actions['delete_order']
                if isinstance(delete_data, dict):
                    order_id = delete_data.get('order_id')
                    if order_id:
                        from enhanced_llm_chatbot import get_customer_orders
                        customer_orders = get_customer_orders(state.customer_info.get('phone', ''))
                        try:
                            # Try to find by index
                            index = int(order_id) - 1
                            if 0 <= index < len(customer_orders):
                                order_to_delete = customer_orders[index]
                            else:
                                # Try to find by order ID
                                order_to_delete = None
                                for order in customer_orders:
                                    if str(order.get('order_id')) == str(order_id):
                                        order_to_delete = order
                                        break
                        except ValueError:
                            # Try to find by order ID
                            order_to_delete = None
                            for order in customer_orders:
                                if str(order.get('order_id')) == str(order_id):
                                    order_to_delete = order
                                    break
                        
                        if order_to_delete:
                            try:
                                from enhanced_llm_chatbot import get_user_token, fixed_inventory_email
                                import requests
                                token = get_user_token(fixed_inventory_email)
                                if token:
                                    response = requests.delete(f"http://localhost:5000/api/orders/{order_to_delete.get('order_id')}", 
                                                            headers={"Authorization": f"Bearer {token}"})
                                    if response.status_code == 200:
                                        print(f"✅ Order {order_to_delete.get('order_id')} deleted successfully")
                                    else:
                                        print(f"❌ Failed to delete order {order_to_delete.get('order_id')}")
                                else:
                                    print("❌ Authentication failed")
                            except Exception as e:
                                print(f"❌ Error deleting order: {e}")
                        else:
                            print(f"❌ Order {order_id} not found")
            
            # Process order details display
            if actions.get('show_order_details'):
                show_data = actions['show_order_details']
                if isinstance(show_data, dict):
                    order_id = show_data.get('order_id')
                    if order_id:
                        from enhanced_llm_chatbot import get_customer_orders, display_order_summary
                        customer_orders = get_customer_orders(state.customer_info.get('phone', ''))
                        try:
                            # Try to find by index
                            index = int(order_id) - 1
                            if 0 <= index < len(customer_orders):
                                selected_order = customer_orders[index]
                                display_order_summary(selected_order)
                            else:
                                # Try to find by order ID
                                selected_order = None
                                for order in customer_orders:
                                    if str(order.get('order_id')) == str(order_id):
                                        selected_order = order
                                        break
                                if selected_order:
                                    display_order_summary(selected_order)
                                else:
                                    print(f"❌ Order {order_id} not found")
                        except ValueError:
                            # Try to find by order ID
                            selected_order = None
                            for order in customer_orders:
                                if str(order.get('order_id')) == str(order_id):
                                    selected_order = order
                                    break
                            if selected_order:
                                display_order_summary(selected_order)
                            else:
                                print(f"❌ Order {order_id} not found")
            
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