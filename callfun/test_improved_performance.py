import time
from enhanced_conversation_state import handle_customer_call, get_cached_inventory

def test_improved_performance():
    """Test the performance and functionality of the chatbot"""
    print("🚀 Testing Improved Chatbot Performance & Functionality")
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
        "I need 10 packs of milk",
        "yes",
        "add 2 dozen apples, 8 packs garam masala, and also a 5kg bag of Aashirvaad Atta",
        "Yes, that sounds correct. By the way, what kind of cooking oil do you have? I need a 1-litre bottle of sunflower oil.",
        "what is my current order?",
        "no that's it"
    ]
    
    total_time = 0
    responses = []
    order_items = []
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n🔄 Test {i}: '{user_input}'")
        start_time = time.time()
        
        try:
            response = handle_customer_call(customer_phone, user_input)
            end_time = time.time()
            response_time = end_time - start_time
            total_time += response_time
            
            print(f"⏱️  Response time: {response_time:.2f} seconds")
            print(f"🤖 Response: {response[:150]}...")
            responses.append(response_time)
            
            # Track order items if this is an item addition
            if any(word in user_input.lower() for word in ['milk', 'apple', 'garam', 'atta', 'oil']):
                print(f"📦 Expected items to be added from this input")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Performance Summary:")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average response time: {total_time/len(test_inputs):.2f} seconds")
    print(f"Fastest response: {min(responses):.2f} seconds")
    print(f"Slowest response: {max(responses):.2f} seconds")
    
    if total_time < 30:
        print("✅ Performance is good!")
    elif total_time < 60:
        print("⚠️  Performance is acceptable")
    else:
        print("❌ Performance needs improvement")
    
    print(f"\n🔍 Functionality Analysis:")
    print("Expected items to be added:")
    print("- Milk (10 packs)")
    print("- Apples (2 dozen = 24)")
    print("- Garam Masala (8 packs)")
    print("- Aashirvaad Atta (5kg bag)")
    print("- Sunflower Oil (1 litre)")
    
    print(f"\n💡 Issues to check:")
    print("- Are items being found in inventory?")
    print("- Are quantities being parsed correctly?")
    print("- Are items being added to the order?")
    print("- Is the conversation ending properly?")

if __name__ == "__main__":
    test_improved_performance() 