import requests
import json

def get_user_token(email):
    """Get authentication token"""
    try:
        # Try with the default password
        response = requests.post("http://localhost:5000/api/auth/login", 
                               json={"email": email, "password": "1234567890"})
        if response.status_code == 200:
            return response.json().get('token')
        
        # If that fails, try with "password"
        response = requests.post("http://localhost:5000/api/auth/login", 
                               json={"email": email, "password": "password"})
        if response.status_code == 200:
            return response.json().get('token')
        
        return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def extract_data_from_backend():
    """Extract all data from backend"""
    try:
        token = get_user_token("dhallhimanshu1234@gmail.com")
        if not token:
            print("❌ No authentication token available")
            return None
        
        response = requests.get("http://localhost:5000/api/chatbot/data", 
                              headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 200:
            data = response.json()
            return data.get('data', {})
        else:
            print(f"❌ Data extraction failed: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        print(f"❌ Data extraction error: {e}")
        return None

def create_shop_data():
    """Create shop_data.json with backend data"""
    print("📦 Extracting data from backend...")
    
    data = extract_data_from_backend()
    if not data:
        print("❌ Failed to extract data from backend")
        return
    
    # Create shop_data.json
    shop_data = {
        "customers": data.get("customers", []),
        "orders": data.get("orders", []),
        "inventory": data.get("inventory", []),
        "current_customer": None,
        "current_order": None,
        "conversation_state": {
            "stage": "greeting",
            "customer_info": {},
            "order_items": [],
            "total_price": 0,
            "notes": "",
            "confirmations": {
                "phone_confirmed": False,
                "address_confirmed": False,
                "order_complete": False,
                "delivery_confirmed": False
            }
        }
    }
    
    # Save to file
    with open("shop_data.json", "w") as f:
        json.dump(shop_data, f, indent=2)
    
    print(f"✅ Created shop_data.json with:")
    print(f"   - {len(shop_data['customers'])} customers")
    print(f"   - {len(shop_data['orders'])} orders")
    print(f"   - {len(shop_data['inventory'])} inventory items")

if __name__ == "__main__":
    create_shop_data() 