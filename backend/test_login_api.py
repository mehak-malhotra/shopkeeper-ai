import requests

# Test login with the new user we just created
BACKEND_URL = "http://localhost:5000/api/auth/login"

test_user = {
    "email": "test@shopkeeper.com",
    "password": "testpassword123"
}

def test_login_api():
    print("Testing login API endpoint...")
    print(f"Email: {test_user['email']}")
    print(f"Password: {test_user['password']}")
    
    try:
        response = requests.post(BACKEND_URL, json=test_user)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            data = response.json()
            if 'token' in data:
                print(f"✅ JWT Token received: {data['token'][:20]}...")
        else:
            print("❌ Login failed.")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error! Make sure your Flask backend is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_login_api() 