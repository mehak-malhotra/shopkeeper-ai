import requests
import json
import os
from PIL import Image, ImageDraw, ImageFont
import io

# Backend URL
BACKEND_URL = "http://localhost:5000/api/upload-image-order"

# Test credentials
TEST_EMAIL = "dhallhimanshu1234@gmail.com"
TEST_PASSWORD = "1234567890"

def create_test_image():
    """Create a test shopping list image"""
    # Create a white image
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add text to simulate a shopping list
    text_lines = [
        "Shopping List",
        "2 kg Rice",
        "1 pack Sugar",
        "3 dozen Eggs",
        "1 kg Onions",
        "2 packs Milk",
        "1 bottle Oil"
    ]
    
    y_position = 30
    for line in text_lines:
        draw.text((20, y_position), line, fill='black')
        y_position += 30
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

def test_image_order():
    """Test the image-to-order endpoint"""
    print("🧪 Testing Image-to-Order Functionality")
    print("=" * 50)
    
    # First, login to get token
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        login_response = requests.post("http://localhost:5000/api/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
        
        token = login_response.json().get('token')
        if not token:
            print("❌ No token received")
            return
        
        print(f"✅ Login successful, token: {token[:20]}...")
        
        # Create test image
        print("📸 Creating test shopping list image...")
        image_bytes = create_test_image()
        
        # Prepare form data
        files = {
            'image': ('shopping_list.png', image_bytes, 'image/png')
        }
        
        data = {
            'customer_phone': '+1234567890',
            'customer_name': 'Test Customer'
        }
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        print("📤 Uploading image to backend...")
        response = requests.post(BACKEND_URL, files=files, data=data, headers=headers)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Image-to-order successful!")
            print(f"📋 Order ID: {result['data']['order_id']}")
            print(f"👤 Customer: {result['data']['customer_name']}")
            print(f"💰 Total Price: ₹{result['data']['total_price']}")
            print(f"📦 Items: {len(result['data']['items'])}")
            
            print("\n📝 OCR Text:")
            print(result['data']['ocr_text'])
            
            print("\n🛒 Extracted Items:")
            for item in result['data']['extracted_items']:
                print(f"  - {item['item']}: {item['quantity']}")
            
            print("\n✅ Matched Items:")
            for item in result['data']['items']:
                print(f"  - {item['item_name']}: {item['fulfilled_quantity']}/{item['requested_quantity']} (Match: {item['match_score']}%)")
            
            print("\n📊 Inventory Updates:")
            for update in result['data']['inventory_updates']:
                print(f"  - {update['name']}: {update['quantity']}")
                
        else:
            print(f"❌ Image-to-order failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error! Make sure your Flask backend is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_with_real_image(image_path):
    """Test with a real image file"""
    print(f"🧪 Testing with real image: {image_path}")
    print("=" * 50)
    
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return
    
    # Login to get token
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        login_response = requests.post("http://localhost:5000/api/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return
        
        token = login_response.json().get('token')
        if not token:
            print("❌ No token received")
            return
        
        print(f"✅ Login successful, token: {token[:20]}...")
        
        # Upload real image
        with open(image_path, 'rb') as f:
            files = {
                'image': (os.path.basename(image_path), f, 'image/png')
            }
            
            data = {
                'customer_phone': '+9876543210',
                'customer_name': 'Real Customer'
            }
            
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            print("📤 Uploading real image to backend...")
            response = requests.post(BACKEND_URL, files=files, data=data, headers=headers)
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Real image-to-order successful!")
                print(f"📋 Order ID: {result['data']['order_id']}")
                print(f"👤 Customer: {result['data']['customer_name']}")
                print(f"💰 Total Price: ₹{result['data']['total_price']}")
                
                print("\n📝 OCR Text:")
                print(result['data']['ocr_text'])
                
                print("\n✅ Matched Items:")
                for item in result['data']['items']:
                    print(f"  - {item['item_name']}: {item['fulfilled_quantity']}/{item['requested_quantity']} (Match: {item['match_score']}%)")
                    
            else:
                print(f"❌ Real image-to-order failed: {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Image-to-Order Test Suite")
    print("=" * 50)
    
    # Test 1: Generated image
    print("\n1️⃣ Testing with generated shopping list image...")
    test_image_order()
    
    # Test 2: Real image (if provided)
    real_image_path = "test_shopping_list.png"  # Change this to your image path
    if os.path.exists(real_image_path):
        print(f"\n2️⃣ Testing with real image: {real_image_path}")
        test_with_real_image(real_image_path)
    else:
        print(f"\n2️⃣ Skipping real image test (file not found: {real_image_path})")
        print("💡 To test with a real image, place a shopping list image named 'test_shopping_list.png' in this directory")
    
    print("\n✅ Test suite completed!") 