import certifi
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://dhallhimanshu1234:9914600112%40DHALLh@himanshudhall.huinsh2.mongodb.net/")

client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
shop_db = client['shop_db']
user_col = shop_db['user']

def migrate_ids():
    print("Migrating existing customers and orders to have proper IDs...")
    
    # Get all users
    users = user_col.find({})
    
    for user in users:
        email = user.get('email')
        print(f"\nProcessing user: {email}")
        
        customers = user.get('customers', [])
        orders = user.get('orders', [])
        
        # Migrate customers
        if customers:
            print(f"  Found {len(customers)} customers")
            for i, customer in enumerate(customers):
                if 'customer_id' not in customer or not isinstance(customer['customer_id'], int):
                    customer['customer_id'] = i + 1
                    print(f"    Customer '{customer.get('name', 'Unknown')}' -> ID: {customer['customer_id']}")
        
        # Migrate orders
        if orders:
            print(f"  Found {len(orders)} orders")
            for i, order in enumerate(orders):
                if 'order_id' not in order or not isinstance(order['order_id'], int):
                    order['order_id'] = i + 1
                    print(f"    Order {order.get('order_id', 'Unknown')} -> ID: {order['order_id']}")
                
                # Link orders to customers by phone
                customer_phone = order.get('customer_phone', '')
                if customer_phone:
                    for customer in customers:
                        if customer.get('phone') == customer_phone:
                            order['customer_id'] = customer.get('customer_id')
                            print(f"      Linked to customer ID: {order['customer_id']}")
                            break
        
        # Update the user document
        if customers or orders:
            user_col.update_one(
                {'email': email},
                {'$set': {
                    'customers': customers,
                    'orders': orders
                }}
            )
            print(f"  ✅ Updated user document")
    
    print("\n✅ Migration completed!")

if __name__ == "__main__":
    migrate_ids() 