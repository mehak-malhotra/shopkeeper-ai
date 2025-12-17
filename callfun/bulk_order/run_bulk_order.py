#!/usr/bin/env python3
"""
Standalone script to run bulk order processing.
Usage: python run_bulk_order.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bulk_order.processor import process_bulk_order_input
import json


def main():
    print("=" * 60)
    print("Bulk Order Processor")
    print("=" * 60)
    
    # Get inputs
    phone = input("Customer phone: ").strip()
    if not phone:
        print("❌ Phone number is required!")
        return
    
    name = input("Customer name (optional): ").strip() or ""
    
    print("\nEnter bulk list (e.g., 'rajma 7 lb- 2 cases, aata- 10 cases')")
    print("Or type 'exit' to quit")
    raw = input("> ").strip()
    
    if raw.lower() in ['exit', 'quit', 'q']:
        print("Exiting...")
        return
    
    if not raw:
        print("❌ Bulk list is required!")
        return
    
    print("\n" + "=" * 60)
    print("Processing...")
    print("=" * 60)
    
    try:
        result = process_bulk_order_input(raw, phone, name)
        
        # Display results
        print("\n📋 PARSED ITEMS:")
        print(json.dumps(result['parsed'], indent=2))
        
        print("\n✅ MATCHED ITEMS (Added to Order):")
        if result['matched']:
            print(json.dumps(result['matched'], indent=2))
            total = sum(item.get('quantity', 0) * item.get('price', 0) for item in result['matched'])
            print(f"\n💰 Total: ₹{total:.2f}")
        else:
            print("   (None)")
        
        print("\n❌ MISSING ITEMS (Not in Inventory):")
        if result['missing']:
            for item in result['missing']:
                reason = item.get('reason', 'unknown')
                print(f"   - {item['name']} (qty: {item['quantity']}) - {reason}")
        else:
            print("   (None - all items found!)")
        
        print("\n📦 ORDER CREATION RESULT:")
        if result['order']:
            if result['order'].get('success'):
                print("✅ Order created successfully!")
                print(json.dumps(result['order'], indent=2))
            else:
                print("❌ Order creation failed!")
                print(json.dumps(result['order'], indent=2))
        else:
            print("   (No order created - no matched items)")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

