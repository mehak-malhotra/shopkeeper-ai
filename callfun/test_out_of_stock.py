import time
from enhanced_conversation_state import handle_customer_call, get_cached_inventory

def test_out_of_stock_functionality():
    """Test the chatbot's handling of out-of-stock and unavailable items"""
    print("🔧 Testing Out-of-Stock Functionality")
    print("=" * 60)
    
    # First, let's check what's in inventory
    print("📦 Checking Inventory...")
    inventory = get_cached_inventory()
    print(f"Total items in inventory: {len(inventory)}")
    print("Sample items:")
    for item in inventory[:5]:
        print(f"  - {item['name']}: {item['quantity']} in stock (₹{item['price']})")
    print()
    
    # Check if bananas exist in inventory
    banana_found = any('banana' in item['name'].lower() for item in inventory)
    print(f"🍌 Bananas in inventory: {'Yes' if banana_found else 'No'}")
    
    customer_phone = "9914600112"
    test_inputs = [
        "Hello",
        "I need 2 dozen bananas",  # This should fail if bananas not in inventory
        "What about apples?",  # This should work if apples are available
        "Add 5 kg of mangoes",  # This should fail if mangoes not in inventory
        "Show me my cart",
        "that's it"
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
            print(f"🤖 Response: {response[:300]}...")
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
    print("1. Should greet customer properly")
    print("2. Should apologize for bananas if not in inventory")
    print("3. Should suggest alternatives for unavailable items")
    print("4. Should add available items (like apples) to order")
    print("5. Should apologize for mangoes if not in inventory")
    print("6. Should show cart with only available items")
    print("7. Should end conversation when customer says 'that's it'")
    
    print(f"\n💡 Key Fixes Applied:")
    print("- Enhanced process_ai_actions to check add_item_to_order return value")
    print("- Added unavailable items context to LLM prompt")
    print("- Updated LLM instructions for out-of-stock scenarios")
    print("- Added examples for handling unavailable items")
    print("- Enhanced error handling in item addition process")

if __name__ == "__main__":
    test_out_of_stock_functionality() 