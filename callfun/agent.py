import json
from typing import Dict, Any

from enhanced_conversation_state import (
    handle_customer_call,
    get_or_create_conversation,
    get_cached_inventory,
    get_cached_token,
)

import requests

class OrderAgent:
    def __init__(self, customer_phone: str):
        self.customer_phone = customer_phone
        self.history = []
        
        # Initialize conversation and verify inventory connection
        state = get_or_create_conversation(self.customer_phone)
        self._verify_inventory_connection(state)
    
    def _verify_inventory_connection(self, state):
        """Verify inventory is loaded and connection is working"""
        print("\n" + "="*60)
        print("🔍 Checking Inventory Connection...")
        print("="*60)
        
        # Step 1: Check authentication token
        print("\n1️⃣ Checking Authentication Token...")
        token = get_cached_token()
        if token:
            print(f"   ✅ Token obtained: {token[:20]}...")
        else:
            print(f"   ❌ Failed to obtain authentication token!")
            print(f"   This is likely the root cause of the issue.")
            print(f"   Check if backend API is running on http://localhost:5000")
            print(f"   Check login credentials in enhanced_conversation_state.py")
            print("="*60 + "\n")
            return
        
        # Step 2: Test API connection
        print("\n2️⃣ Testing API Connection...")
        try:
            response = requests.get("http://localhost:5000/api/inventory", 
                                   headers={"Authorization": f"Bearer {token}"},
                                   timeout=5)
            if response.status_code == 200:
                api_data = response.json()
                api_items = api_data.get('data', [])
                print(f"   ✅ API connection successful!")
                print(f"   📦 API returned {len(api_items)} items")
                if len(api_items) > 0:
                    print(f"   Sample from API (first 3):")
                    for i, item in enumerate(api_items[:3], 1):
                        print(f"      {i}. {item.get('name', 'N/A')}")
            else:
                print(f"   ❌ API returned status code: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection Error: Cannot reach http://localhost:5000")
            print(f"   Make sure backend API is running!")
        except Exception as e:
            print(f"   ❌ API test error: {e}")
        
        # Step 3: Check global cache
        print("\n3️⃣ Checking Global Inventory Cache...")
        global_inventory = get_cached_inventory()
        print(f"   📦 Global inventory cache: {len(global_inventory)} items")
        
        # Step 4: Check state inventory
        print("\n4️⃣ Checking State Inventory Snapshot...")
        state_inventory = state.inventory_snapshot
        print(f"   📦 State inventory snapshot: {len(state_inventory)} items")
        
        if len(state_inventory) == 0:
            print("   ⚠️  WARNING: Inventory snapshot is empty!")
            print("   This means items cannot be found even if they exist in inventory.")
        else:
            print(f"   ✅ Inventory loaded successfully!")
            print(f"   Sample items (first 5):")
            for i, item in enumerate(state_inventory[:5], 1):
                print(f"      {i}. {item.get('name', 'N/A')} - Qty: {item.get('quantity', 0)}, Price: ₹{item.get('price', 0)}")
        
        # Step 5: Test item finding
        print("\n5️⃣ Testing Item Matching...")
        test_items = ["onion", "green chilli", "onions"]
        for test_item in test_items:
            found = state.find_item(test_item)
            if found:
                print(f"   ✅ '{test_item}' → Found: {found.get('name')}")
            else:
                print(f"   ❌ '{test_item}' → Not found")
                # Show what items are available for debugging
                if len(state_inventory) > 0:
                    matching_items = [item for item in state_inventory 
                                    if test_item.lower() in item.get('name', '').lower()]
                    if matching_items:
                        print(f"      (But items containing '{test_item}' exist: {[i.get('name') for i in matching_items[:3]]})")
        
        print("="*60 + "\n")

    def handle_message(self, user_message: str) -> Dict[str, Any]:
        state = get_or_create_conversation(self.customer_phone)
        
        # Debug: Check inventory before processing
        if len(state.inventory_snapshot) == 0:
            print(f"⚠️  WARNING: Processing message but inventory is empty!")
            print(f"   Attempting to refresh inventory...")
            state._refresh_inventory()
            if len(state.inventory_snapshot) == 0:
                print(f"   ❌ Inventory refresh failed!")
        
        reply_text = handle_customer_call(self.customer_phone, user_message)
        state = get_or_create_conversation(self.customer_phone)

        data: Dict[str, Any] = {
            "reply": reply_text,
            "stage": state.stage,
            "current_order": state.current_order,
        }

        self.history.append({"user": user_message, "agent": data["reply"]})
        return data


if __name__ == "__main__":
    phone = input("Enter customer phone: ").strip()
    if not phone:
        print("Missing phone number. Exiting.")
    else:
        agent = OrderAgent(phone)
        while True:
            msg = input("You: ")
            if msg.lower() in ["exit", "quit"]:
                break
            response = agent.handle_message(msg)
            print("Agent:", response["reply"])
            print("Stage:", response.get("stage"))
            print("Current order:", response.get("current_order"))
            print("-" * 60)
