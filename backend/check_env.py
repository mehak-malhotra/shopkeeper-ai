import os
from dotenv import load_dotenv

load_dotenv()

print("Checking environment variables...")
print("=" * 40)

# Check MongoDB URI
mongo_uri = os.getenv("MONGO_URI")
if mongo_uri:
    print("✅ MONGO_URI: Found")
else:
    print("❌ MONGO_URI: Missing")

# Check JWT Secret
jwt_secret = os.getenv("JWT_SECRET")
if jwt_secret:
    print("✅ JWT_SECRET: Found")
else:
    print("❌ JWT_SECRET: Missing")

# Check Gemini API Key
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    print("✅ GEMINI_API_KEY: Found")
else:
    print("❌ GEMINI_API_KEY: Missing")

# Check Gemini API URL
gemini_url = os.getenv("GEMINI_API_URL")
if gemini_url:
    print("✅ GEMINI_API_URL: Found")
else:
    print("❌ GEMINI_API_URL: Missing")

print("=" * 40)

# Test JWT import
try:
    import jwt
    print("✅ PyJWT package: Installed")
except ImportError:
    print("❌ PyJWT package: Missing - Run: pip install PyJWT")

print("=" * 40) 