import re
import requests
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Add parent directory to path to import enhanced_conversation_state
sys.path.insert(0, str(Path(__file__).parent.parent))
from enhanced_conversation_state import get_cached_token, get_cached_inventory


def parse_bulk_list(text: str) -> List[Dict]:
    """
    Parse bulk list text into structured items.
    Example input: "rajma 7 lb- 2 cases, aata- 10 cases"
    Output: [{"name": "rajma", "quantity": 2}, {"name": "aata", "quantity": 10}]
    Notes: If both a weight and cases are present, prefer cases as the orderable quantity.
    """
    if not text:
        return []

    items: List[Dict] = []
    # Split by commas for separate entries
    parts = [p.strip() for p in text.split(',') if p.strip()]
    case_pattern = re.compile(r"(?P<num>\d+)\s*(case|cases|cs)", re.IGNORECASE)
    weight_pattern = re.compile(r"(?P<num>\d+)\s*(lb|lbs|kg|g|gram|grams)", re.IGNORECASE)

    for part in parts:
        # Split name and trailing details by '-' if present
        if '-' in part:
            name_part, details_part = [s.strip() for s in part.split('-', 1)]
        else:
            name_part, details_part = part, part

        # Extract name: first word(s) until number/unit
        name_tokens = []
        for token in name_part.split():
            if re.match(r"^\d+", token):
                break
            name_tokens.append(token)
        item_name = ' '.join(name_tokens).strip() or name_part.strip()

        # Prefer cases if present
        qty = None
        m_case = case_pattern.search(part)
        if m_case:
            qty = int(m_case.group('num'))
        else:
            # Fallback: any number present without unit treated as quantity
            m_num = re.search(r"(\d+)", part)
            if m_num:
                qty = int(m_num.group(1))
            else:
                qty = 1

        items.append({
            'name': item_name.lower().strip(),
            'quantity': qty
        })

    return items


def _find_inventory_item(inventory: List[Dict], query_name: str) -> Dict:
    q = query_name.lower().strip()
    # exact
    for it in inventory:
        if it.get('name', '').lower() == q:
            return it
    # contains
    for it in inventory:
        if q in it.get('name', '').lower():
            return it
    # word match
    q_words = q.split()
    for it in inventory:
        words = it.get('name', '').lower().split()
        if any(w in words for w in q_words):
            return it
    return None


def match_items_with_inventory(parsed_items: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Return (matched_items, missing_items)
    matched_items entries include: name, quantity, price
    missing_items are original requests that could not be matched
    """
    inventory = get_cached_inventory() or []

    matched: List[Dict] = []
    missing: List[Dict] = []

    for req in parsed_items:
        inv = _find_inventory_item(inventory, req['name'])
        if inv:
            # Check stock
            available = inv.get('quantity', 0)
            req_qty = req.get('quantity', 1)
            if available <= 0:
                missing.append({**req, 'reason': 'out_of_stock'})
                continue
            qty = min(req_qty, available)
            matched.append({
                'name': inv.get('name'),
                'quantity': qty,
                'price': inv.get('price', 0)
            })
        else:
            missing.append({**req, 'reason': 'not_found'})

    return matched, missing


def create_order_via_api(customer_phone: str, customer_name: str, items: List[Dict]) -> Dict:
    """
    Create order using existing backend API.
    Expects items with name, quantity, price.
    Returns API response JSON.
    """
    token = get_cached_token()
    if not token:
        return {'success': False, 'message': 'Authentication failed'}

    total = sum((it.get('quantity', 0) * it.get('price', 0)) for it in items)
    order_data = {
        'customerPhone': customer_phone,
        'customerName': customer_name,
        'items': items,
        'total': total,
        'status': 'pending'
    }

    resp = requests.post(
        "http://localhost:5000/api/orders",
        headers={"Authorization": f"Bearer {token}"},
        json=order_data,
        timeout=10,
    )
    try:
        data = resp.json()
    except Exception:
        data = {'success': False, 'message': f'HTTP {resp.status_code}', 'raw': resp.text[:500]}
    return data


def process_bulk_order_input(raw_text: str, customer_phone: str, customer_name: str = "") -> Dict:
    """
    High-level entry: parse, match, create order, return summary with missing items.
    """
    parsed = parse_bulk_list(raw_text)
    matched, missing = match_items_with_inventory(parsed)
    result = {
        'parsed': parsed,
        'matched': matched,
        'missing': missing,
        'order': None,
    }
    if matched:
        order_resp = create_order_via_api(customer_phone, customer_name, matched)
        result['order'] = order_resp
    return result


