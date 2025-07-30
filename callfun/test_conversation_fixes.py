import time
from enhanced_conversation_state import handle_customer_call, get_cached_inventory

def test_conversation_fixes():
    """Test the conversation fixes for item modification, removal, and proper ending"""
    print("🔧 Testing Conversation Fixes")
    print("=" * 60)
    
    # First, let's check what's in inventory
    print("📦 Checking Inventory...")
    inventory = get_cached_inventory()
    print(f"Total items in inventory: {len(inventory)}")
    print("Sample items:")
    for item in inventory[:5]:
        print(f"  - {item['name']}: {item['quantity']} in stock (₹{item['price']})")
    print()
    
    customer_phone = "9914600112"
    test_inputs = [
        "Hello",
        "I need 2 kg of onions and 1 bottle of Harpic",
        "What is the price for Toor Dal?",
        "Okay, add one bag of that to my order",
        "Actually, make the onions 1 kg instead of 2. And please remove the Harpic.",
        "Show me my cart",
        "no that's it"
    ]
    
    total_time = 0
    responses = []
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n🔄 Test {i}: '{user_input}'")
        start_time = time.time()
        
        try:
            response = handle_customer_call(customer_phone, user_input)
            end_time = time.time()
            response_time = end_time - start_time
            total_time += response_time
            
            print(f"⏱️  Response time: {response_time:.2f} seconds")
            print(f"🤖 Response: {response[:200]}...")
            responses.append(response_time)
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Performance Summary:")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average response time: {total_time/len(test_inputs):.2f} seconds")
    print(f"Fastest response: {min(responses):.2f} seconds")
    print(f"Slowest response: {max(responses):.2f} seconds")
    
    print(f"\n🔍 Functionality Analysis:")
    print("Expected behavior:")
    print("1. Should add onions (2kg) and Harpic initially")
    print("2. Should provide Toor Dal price when asked")
    print("3. Should add Toor Dal when customer says 'add one bag of that'")
    print("4. Should modify onions to 1kg and remove Harpic")
    print("5. Should show updated cart")
    print("6. Should end conversation when customer says 'no that's it'")
    
    print(f"\n💡 Key Fixes Applied:")
    print("- Added 'thankyou' to end keywords")
    print("- Added support for item modification (modify_item action)")
    print("- Added support for item removal (remove_item action)")
    print("- Improved context handling for 'that' and 'it' references")
    print("- Enhanced conversation ending logic")

if __name__ == "__main__":
    test_conversation_fixes() 