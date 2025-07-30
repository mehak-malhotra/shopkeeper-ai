from enhanced_conversation_state import get_cached_inventory, find_item

def check_inventory():
    """Check what items are available in inventory"""
    print("🔍 Checking Inventory...")
    print("=" * 50)
    
    items = get_cached_inventory()
    print(f"Total items in inventory: {len(items)}")
    
    # Show all items with their names and quantities
    print("\n📦 All Inventory Items:")
    for item in items:
        print(f"- {item['name']}: {item['quantity']} in stock (₹{item['price']})")
    
    # Check for specific items mentioned in the test
    test_items = ["Milk", "Apple", "Garam Masala", "Aashirvaad Atta", "Sunflower Oil"]
    print(f"\n🔍 Checking for test items:")
    for test_item in test_items:
        found = False
        for item in items:
            if test_item.lower() in item['name'].lower():
                print(f"✅ Found '{item['name']}': {item['quantity']} in stock")
                found = True
                break
        if not found:
            print(f"❌ '{test_item}' not found in inventory")
    
    # Check for items with similar names
    print(f"\n🔍 Checking for similar item names:")
    for test_item in test_items:
        similar_items = []
        for item in items:
            if any(word in item['name'].lower() for word in test_item.lower().split()):
                similar_items.append(item)
        
        if similar_items:
            print(f"Items similar to '{test_item}':")
            for item in similar_items:
                print(f"  - {item['name']}: {item['quantity']} in stock")
        else:
            print(f"No items similar to '{test_item}' found")
    
    # Test the improved find_item function
    print(f"\n🧪 Testing improved find_item function:")
    test_cases = [
        "milk",
        "apple", 
        "garam masala",
        "atta",
        "oil",
        "Amul Taaza Milk",
        "Aashirvaad Atta"
    ]
    
    for test_case in test_cases:
        # Create a mock state to test find_item
        from enhanced_conversation_state import ConversationState
        mock_state = ConversationState("test_phone")
        mock_state.inventory_snapshot = items
        found_item = mock_state.find_item(test_case)
        
        if found_item:
            print(f"✅ '{test_case}' → Found: {found_item['name']} ({found_item['quantity']} in stock)")
        else:
            print(f"❌ '{test_case}' → Not found")

if __name__ == "__main__":
    check_inventory() 