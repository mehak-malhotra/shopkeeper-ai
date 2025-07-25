import certifi
from pymongo import MongoClient

# MongoDB connection URI (same as in main.py)
MONGO_URI = "mongodb+srv://dhallhimanshu1234:9914600112%40DHALLh@himanshudhall.huinsh2.mongodb.net/"

client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())

db = client['shop_0001']

try:
    # Test connection
    client.server_info()
    print("MongoDB connection successful!")
    # List collections in shop_0001
    collections = db.list_collection_names()
    print(f"Collections in shop_0001: {collections}")
except Exception as e:
    print(f"MongoDB connection failed: {e}") 