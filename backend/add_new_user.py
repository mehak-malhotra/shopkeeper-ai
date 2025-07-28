import requests
import hashlib

# Backend registration endpoint
BACKEND_URL = "http://localhost:5000/api/auth/register"

# Mock user data
mock_user = {
    "email": "test@shopkeeper.com",
    "password": "testpassword123",
    "name": "Test Shop",
    "phone": "+1234567890",
    "ownerName": "John Doe",
    "address": "123 Test Street, Test City"
}

def add_new_user():
    print("Adding new user to backend...")
    print(f"Email: {mock_user['email']}")
    print(f"Password: {mock_user['password']}")
    print(f"Shop Name: {mock_user['name']}")
    print(f"Owner: {mock_user['ownerName']}")
    
    try:
        response = requests.post(BACKEND_URL, json=mock_user)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ User registered successfully!")
            print("You can now login with:")
            print(f"Email: {mock_user['email']}")
            print(f"Password: {mock_user['password']}")
        else:
            print("❌ Failed to register user.")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error! Make sure your Flask backend is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_new_user() 