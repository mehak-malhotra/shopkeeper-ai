import os, time
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from enhanced_llm_chatbot import (
    process_customer_interaction,
    get_customer_orders,
    get_inventory,
    find_customer,
    add_customer,
    update_customer_address,
    place_order,
    finalize_order,
    cancel_order
)

APP_ENV = os.getenv("APP_ENV", "dev")

app = FastAPI(title="Callbot Agent API", version="2.1", docs_url="/docs")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Middleware ----
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    dur = round((time.time()-start)*1000)
    print(f"{request.method} {request.url.path} → {response.status_code} ({dur}ms)")
    return response

# ---- Health ----
@app.get("/healthz")
def health():
    return {"response": "ok"}

@app.get("/readyz")
def ready():
    return {"response": "ready"}

# ========================
#  MAIN CHATBOT API
# ========================
@app.post("/callbot/message")
def handle_message(
    phone: str = Form(...),
    message: str = Form(...),
    session_id: Optional[str] = Form(None)
):
    response_text = process_customer_interaction(phone, message)
    return {"response": response_text}

@app.post("/callbot/omnidim")
def handle_message_for_omnidim(
    phone: str = Form(...),
    message: str = Form(...),
    session_id: Optional[str] = Form(None)
):
    response_text = process_customer_interaction(phone, message)
    return {"response": response_text}

# ========================
#  CUSTOMER APIs
# ========================
@app.post("/callbot/customer/find")
def api_find_customer(phone: str = Form(...)):
    customer = find_customer(phone)
    if not customer:
        return {"response": "Customer not found"}
    return {"response": f"Found customer {customer.get('name')} at {customer.get('address')}"}

@app.post("/callbot/customer/add")
def api_add_customer(
    phone: str = Form(...),
    name: str = Form(...),
    address: str = Form(...)
):
    customer = add_customer(phone, name, address)
    return {"response": f"Customer {name} added with address {address}"}

@app.post("/callbot/customer/update_address")
def api_update_address(
    phone: str = Form(...),
    address: str = Form(...)
):
    updated = update_customer_address(phone, address)
    if not updated:
        return {"response": "Customer not found"}
    return {"response": f"Customer {phone} address updated to {address}"}

# ========================
#  ORDER APIs
# ========================
@app.get("/callbot/orders/{phone}")
def api_get_orders(phone: str):
    orders = get_customer_orders(phone)
    if not orders:
        return {"response": "No orders found"}
    summaries = [f"Order {o.get('order_id', 'N/A')} with {len(o.get('items', []))} items" for o in orders]
    return {"response": "; ".join(summaries)}

@app.post("/callbot/order/place")
def api_place_order(
    phone: str = Form(...),
    items: str = Form(...)
):
    order = place_order(phone, {"items": items})  # simplified, Omnidim passes string like "2 breads, 1 milk"
    return {"response": f"Order placed for {phone}: {items}"}

@app.post("/callbot/order/finalize")
def api_finalize_order(phone: str = Form(...)):
    result = finalize_order(phone)
    return {"response": f"Order finalized for {phone}"}

@app.post("/callbot/order/cancel")
def api_cancel_order(phone: str = Form(...)):
    result = cancel_order(phone)
    return {"response": f"Order cancelled for {phone}"}

# ========================
#  INVENTORY
# ========================
@app.get("/callbot/inventory")
def api_inventory():
    items = get_inventory()
    if not items:
        return {"response": "No items in inventory"}
    item_list = ", ".join([f"{i['name']} ({i['quantity']} left)" for i in items])
    return {"response": f"Available items: {item_list}"}
