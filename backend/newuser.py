import requests

# Backend registration endpoint
BACKEND_URL = "http://localhost:5000/api/auth/register"

# Prompt for user details
email = input("Enter user email: ")
password = input("Enter user password: ")
shop_name = input("Enter shop name: ")
owner_name = input("Enter owner name: ")

payload = {
    "email": email,
    "password": password,
    "shopName": shop_name,
    "ownerName": owner_name
}

try:
    response = requests.post(BACKEND_URL, json=payload)
    if response.ok:
        print("User registered successfully!")
        print("Response:", response.json())
    else:
        print("Failed to register user.")
        print("Status code:", response.status_code)
        print("Response:", response.text)
except Exception as e:
    print("Error connecting to backend:", e)