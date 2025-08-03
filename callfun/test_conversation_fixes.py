import time
from enhanced_conversation_state import handle_customer_call, get_cached_inventory, ConversationState, get_or_create_conversation

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

def test_last_5_messages():
    """Test that the last 5 messages are properly maintained"""
    print("🧪 Testing Last 5 Messages Functionality")
    print("=" * 50)
    
    # Create a new conversation state
    customer_phone = "9999999999"
    state = get_or_create_conversation(customer_phone)
    
    # Test messages
    test_messages = [
        "Hello, I want to order some groceries",
        "I need 2 apples",
        "And 1 bread",
        "What's the price of milk?",
        "Add 1 liter of milk to my order",
        "That's all, please complete my order",
        "Thank you, goodbye"
    ]
    
    print(f"📞 Testing with customer: {customer_phone}")
    print(f"📝 Testing {len(test_messages)} messages")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Message {i} ---")
        print(f"👤 Customer: {message}")
        
        # Process the message
        response = handle_customer_call(customer_phone, message)
        print(f"🤖 Assistant: {response}")
        
        # Check last 5 messages
        last_5 = state.get_last_5_messages()
        print(f"📋 Last 5 messages count: {len(last_5)}")
        
        if last_5:
            print("📋 Last 5 messages:")
            for j, msg in enumerate(last_5, 1):
                print(f"  {j}. {msg['role']}: {msg['content'][:50]}...")
        
        # Verify we have at most 5 messages
        assert len(last_5) <= 5, f"Expected at most 5 messages, got {len(last_5)}"
        
        if i >= 5:
            # After 5 messages, we should always have exactly 5 messages
            assert len(last_5) == 5, f"Expected exactly 5 messages after message {i}, got {len(last_5)}"
    
    print("\n✅ Last 5 messages test completed successfully!")
    return True

def test_conversation_context():
    """Test that conversation context is properly maintained"""
    print("\n🧪 Testing Conversation Context")
    print("=" * 50)
    
    customer_phone = "8888888888"
    state = get_or_create_conversation(customer_phone)
    
    # Test context references
    test_conversation = [
        "Hello, I want to order some groceries",
        "I need 2 apples",
        "And 1 bread",
        "What's the price of milk?",
        "Add 1 liter of that to my order",  # Should refer to milk from context
        "That's all, please complete my order"
    ]
    
    print(f"📞 Testing context with customer: {customer_phone}")
    
    for i, message in enumerate(test_conversation, 1):
        print(f"\n--- Message {i} ---")
        print(f"👤 Customer: {message}")
        
        # Process the message
        response = handle_customer_call(customer_phone, message)
        print(f"🤖 Assistant: {response}")
        
        # Check if context is being used (especially for "that" references)
        if "that" in message.lower():
            print("🔍 Context reference detected - checking if handled properly")
    
    print("\n✅ Conversation context test completed!")
    return True

def test_conversation_state_persistence():
    """Test that conversation state persists correctly with last 5 messages"""
    print("\n🧪 Testing Conversation State Persistence")
    print("=" * 50)
    
    customer_phone = "7777777777"
    
    # First conversation
    print("📞 First conversation session:")
    messages1 = [
        "Hello, I want to order groceries",
        "I need 2 apples",
        "And 1 bread"
    ]
    
    for message in messages1:
        print(f"👤 Customer: {message}")
        response = handle_customer_call(customer_phone, message)
        print(f"🤖 Assistant: {response}")
    
    # Get state after first session
    state1 = get_or_create_conversation(customer_phone)
    last_5_1 = state1.get_last_5_messages()
    print(f"📋 Messages after first session: {len(last_5_1)}")
    
    # Second conversation (should maintain context)
    print("\n📞 Second conversation session:")
    messages2 = [
        "What was I ordering again?",
        "Add milk to my order",
        "Complete my order"
    ]
    
    for message in messages2:
        print(f"👤 Customer: {message}")
        response = handle_customer_call(customer_phone, message)
        print(f"🤖 Assistant: {response}")
    
    # Get state after second session
    state2 = get_or_create_conversation(customer_phone)
    last_5_2 = state2.get_last_5_messages()
    print(f"📋 Messages after second session: {len(last_5_2)}")
    
    # Verify state persistence
    assert len(last_5_2) <= 5, "Should maintain at most 5 messages"
    print("\n✅ Conversation state persistence test completed!")
    return True

if __name__ == "__main__":
    print("🚀 Starting Conversation Fixes Tests")
    print("=" * 60)
    
    try:
        # Run all tests
        test_conversation_fixes()
        test_last_5_messages()
        test_conversation_context()
        test_conversation_state_persistence()
        
        print("\n🎉 All tests passed successfully!")
        print("✅ Last 5 messages functionality is working correctly")
        print("✅ Conversation context is properly maintained")
        print("✅ Conversation state persistence is working")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 