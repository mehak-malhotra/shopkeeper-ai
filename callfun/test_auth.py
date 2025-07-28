import requests
import json

def test_auth():
    email = "dhallhimanshu1234@gmail.com"
    
    # Test different passwords
    passwords = ["1234567890", "password", "123456", "admin"]
    
    for password in passwords:
        print(f"Testing password: {password}")
        try:
            response = requests.post("http://localhost:5000/api/auth/login", 
                                   json={"email": email, "password": password})
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            print("-" * 50)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ SUCCESS with password: {password}")
                    return data.get('token')
        except Exception as e:
            print(f"Error: {e}")
    
    return None

if __name__ == "__main__":
    print("Testing authentication...")
    token = test_auth()
    if token:
        print(f"Token: {token}")
    else:
        print("❌ No working password found") 