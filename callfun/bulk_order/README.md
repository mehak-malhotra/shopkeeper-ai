# Bulk Order Processor

This module processes bulk order lists, matches items with inventory, and creates orders via the backend API.

## Features

- Parses text input like "rajma 7 lb- 2 cases, aata- 10 cases"
- Matches items against inventory using existing APIs
- Creates orders in MongoDB via backend API
- Returns list of items not available in inventory

## Usage

### Method 1: Run the standalone script (Recommended)

```bash
cd callfun/bulk_order
python run_bulk_order.py
```

Then follow the prompts:
- Enter customer phone number
- Enter customer name (optional)
- Enter bulk list (e.g., "rajma 7 lb- 2 cases, aata- 10 cases")

### Method 2: Use as a module

```python
from bulk_order.processor import process_bulk_order_input

result = process_bulk_order_input(
    "rajma 7 lb- 2 cases, aata- 10 cases",
    customer_phone="9914600112",
    customer_name="John Doe"
)

print("Matched items:", result['matched'])
print("Missing items:", result['missing'])
print("Order:", result['order'])
```

### Method 3: Process a handwritten list image (OCR)

Dependencies:
- Install OCR libs: `pip install pytesseract pillow`
- Windows users may need Tesseract binary installed (e.g., https://github.com/UB-Mannheim/tesseract/wiki)

Run the image processor:
```bash
cd callfun/bulk_order
python run_image_order.py
```
Follow prompts to enter phone, name, and an image path.

Programmatically:
```python
from bulk_order.image_order import process_image_order

result = process_image_order(
    image_path="/path/to/handwritten_list.jpg",
    customer_phone="9914600112",
    customer_name="John Doe"
)
```

## Input Format

The parser understands various formats:
- `rajma 7 lb- 2 cases` → name: "rajma", quantity: 2
- `aata- 10 cases` → name: "aata", quantity: 10
- `rice 5 kg` → name: "rice", quantity: 5
- `sugar 2` → name: "sugar", quantity: 2

## Output

The processor returns a dictionary with:
- `parsed`: List of parsed items from input
- `matched`: Items successfully matched and added to order
- `missing`: Items not found or out of stock
- `order`: Order creation API response

## Requirements

- Backend API must be running on `http://localhost:5000`
- Authentication token must be available (uses `get_cached_token()`)
- Inventory must be accessible via `get_cached_inventory()`
- For OCR feature: `pytesseract` and `Pillow` installed; Tesseract executable available on PATH

