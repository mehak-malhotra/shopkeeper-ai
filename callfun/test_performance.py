import time
from enhanced_conversation_state import handle_customer_call

def test_performance():
    """Test the performance of the chatbot"""
    print("🚀 Testing Chatbot Performance")
    print("=" * 50)
    
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
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n🔄 Test {i}: '{user_input}'")
        start_time = time.time()
        
        try:
            response = handle_customer_call(customer_phone, user_input)
            end_time = time.time()
            response_time = end_time - start_time
            total_time += response_time
            
            print(f"⏱️  Response time: {response_time:.2f} seconds")
            print(f"🤖 Response: {response[:100]}...")
            responses.append(response_time)
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Performance Summary:")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average response time: {total_time/len(test_inputs):.2f} seconds")
    print(f"Fastest response: {min(responses):.2f} seconds")
    print(f"Slowest response: {max(responses):.2f} seconds")
    
    if total_time < 30:  # Less than 30 seconds total
        print("✅ Performance is good!")
    elif total_time < 60:  # Less than 1 minute total
        print("⚠️  Performance is acceptable")
    else:
        print("❌ Performance needs improvement")

if __name__ == "__main__":
    test_performance() 