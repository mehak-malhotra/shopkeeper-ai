import requests

# Test token authentication
BACKEND_URL = "http://localhost:5000/api/customers"

def test_token():
    print("Testing token authentication...")
    
    # Try to get customers without token
    try:
        response = requests.get(BACKEND_URL)
        print(f"Without token - Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Try with a fake token
    try:
        response = requests.get(BACKEND_URL, headers={
            'Authorization': 'Bearer fake-token',
            'Content-Type': 'application/json'
        })
        print(f"With fake token - Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_token() 