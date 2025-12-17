import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bulk_order.processor import process_bulk_order_input


def run_cli():
    print("Bulk Order Processor")
    print("=" * 40)
    phone = input("Customer phone: ").strip()
    name = input("Customer name (optional): ").strip()
    raw = input("Enter bulk list (e.g., 'rajma 7 lb- 2 cases, aata- 10 cases'): \n> ")

    result = process_bulk_order_input(raw, phone, name)
    print("\nParsed:")
    print(result['parsed'])
    print("\nMatched:")
    print(result['matched'])
    print("\nMissing:")
    print(result['missing'])
    print("\nOrder API Response:")
    print(result['order'])


if __name__ == "__main__":
    run_cli()


