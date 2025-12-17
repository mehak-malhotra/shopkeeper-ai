#!/usr/bin/env python3
"""
Standalone script to process an uploaded image of a handwritten list.
Usage: python run_image_order.py
"""

import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bulk_order.image_order import process_image_order


def main():
    print("=" * 60)
    print("Handwritten Image Order Processor")
    print("=" * 60)

    phone = input("Customer phone: ").strip()
    if not phone:
        print("❌ Phone number is required!")
        return

    name = input("Customer name (optional): ").strip() or ""
    image_path = input("Path to image file: ").strip()

    if not image_path:
        print("❌ Image path is required!")
        return

    try:
        result = process_image_order(image_path, phone, name)
        print("\n📋 PARSED:")
        print(json.dumps(result['parsed'], indent=2))

        print("\n✅ MATCHED:")
        print(json.dumps(result['matched'], indent=2))

        print("\n❌ MISSING:")
        print(json.dumps(result['missing'], indent=2))

        print("\n📦 ORDER:")
        print(json.dumps(result['order'], indent=2))
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


