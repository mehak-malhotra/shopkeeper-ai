import requests
import json
import certifi
from pymongo import MongoClient
import google.generativeai as genai
from datetime import datetime, timedelta
import uuid
import os
import threading
import time
import signal
import sys
from typing import Dict, List, Optional, Any
from enhanced_conversation_state import (
    ConversationState, 
    get_or_create_conversation, 
    end_conversation, 
    get_active_conversations,
    cleanup_inactive_conversations
)

# LLM setup (Gemini)
GEMINI_API_KEY = "AIzaSyDN6BSxkHUMru8-m51NmfU0SUKGFBbFYmk"
GEMINI_MODEL = "gemini-2.0-flash"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

# MongoDB setup
client = MongoClient(
    "mongodb+srv://dhallhimanshu1234:9914600112%40DHALLh@himanshudhall.huinsh2.mongodb.net/",
    tls=True,
    tlsCAFile=certifi.where()
)
db = client['shop_db']
collection = db["inventory"]
customers_collection = db["customers"]
orders_collection = db["orders"]

fixed_inventory_email = "dhallhimanshu1234@gmail.com"

class DeploymentManager:
    """
    Manages deployment of AI grocery store assistant with multi-customer support
    """
    
    def __init__(self):
        self.is_running = False
        self.active_conversations = {}
        self.conversation_locks = {}
        self.cleanup_thread = None
        self.stats = {
            "total_conversations": 0,
            "active_conversations": 0,
            "completed_conversations": 0,
            "errors": 0,
            "start_time": datetime.utcnow()
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}. Shutting down gracefully...")
        self.shutdown()
        sys.exit(0)
    
    def start(self):
        """Start the deployment manager"""
        print("🚀 Starting AI Grocery Store Assistant Deployment Manager")
        print("=" * 60)
        print("Features:")
        print("- Multi-customer conversation support")
        print("- Real-time inventory management")
        print("- Automatic state cleanup")
        print("- Production-ready deployment")
        print("- Graceful shutdown handling")
        print("=" * 60)
        
        self.is_running = True
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        
        print("✅ Deployment manager started successfully")
        print("📊 Monitoring active conversations...")
        
        # Main monitoring loop
        while self.is_running:
            try:
                self._update_stats()
                self._display_status()
                time.sleep(30)  # Update every 30 seconds
                
            except KeyboardInterrupt:
                print("\n🛑 Shutdown requested...")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                self.stats["errors"] += 1
                time.sleep(5)
        
        self.shutdown()
    
    def _cleanup_worker(self):
        """Background worker for cleaning up inactive conversations"""
        while self.is_running:
            try:
                cleanup_inactive_conversations()
                
                # Clean up conversations older than 1 hour
                current_time = datetime.utcnow()
                phones_to_remove = []
                
                for phone, conv in get_active_conversations().items():
                    if conv.last_updated:
                        last_updated = datetime.fromisoformat(conv.last_updated.replace('Z', '+00:00'))
                        if current_time - last_updated > timedelta(hours=1):
                            phones_to_remove.append(phone)
                
                for phone in phones_to_remove:
                    end_conversation(phone)
                    print(f"🧹 Cleaned up inactive conversation: {phone}")
                
                time.sleep(60)  # Cleanup every minute
                
            except Exception as e:
                print(f"❌ Error in cleanup worker: {e}")
                time.sleep(30)
    
    def _update_stats(self):
        """Update deployment statistics"""
        active_convs = get_active_conversations()
        self.stats["active_conversations"] = len(active_convs)
        
        # Calculate completed conversations
        if self.stats["total_conversations"] > 0:
            self.stats["completed_conversations"] = (
                self.stats["total_conversations"] - self.stats["active_conversations"]
            )
    
    def _display_status(self):
        """Display current deployment status"""
        uptime = datetime.utcnow() - self.stats["start_time"]
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        
        print(f"\n📊 Deployment Status - Uptime: {hours}h {minutes}m")
        print(f"   Active Conversations: {self.stats['active_conversations']}")
        print(f"   Total Conversations: {self.stats['total_conversations']}")
        print(f"   Completed Conversations: {self.stats['completed_conversations']}")
        print(f"   Errors: {self.stats['errors']}")
        
        if self.stats['active_conversations'] > 0:
            active_convs = get_active_conversations()
            print("   Active Customers:")
            for phone in list(active_convs.keys())[:5]:  # Show first 5
                print(f"     - {phone}")
            if len(active_convs) > 5:
                print(f"     ... and {len(active_convs) - 5} more")
    
    def process_customer_request(self, customer_phone: str, user_input: str) -> str:
        """Process customer request with thread-safe conversation management"""
        
        # Get or create conversation with thread safety
        if customer_phone not in self.conversation_locks:
            self.conversation_locks[customer_phone] = threading.Lock()
        
        with self.conversation_locks[customer_phone]:
            try:
                # Track new conversations
                if customer_phone not in self.active_conversations:
                    self.stats["total_conversations"] += 1
                    self.active_conversations[customer_phone] = True
                
                # Process the request
                from enhanced_llm_chatbot import process_customer_interaction
                response = process_customer_interaction(customer_phone, user_input)
                
                # Check if conversation ended
                if any(word in user_input.lower() for word in ["bye", "goodbye", "exit", "quit", "end", "thank you", "thanks"]):
                    if customer_phone in self.active_conversations:
                        del self.active_conversations[customer_phone]
                
                return response
                
            except Exception as e:
                self.stats["errors"] += 1
                print(f"❌ Error processing request for {customer_phone}: {e}")
                return "I'm having technical difficulties. Please try again."
    
    def get_deployment_stats(self) -> dict:
        """Get deployment statistics for monitoring"""
        return {
            "status": "running" if self.is_running else "stopped",
            "uptime": str(datetime.utcnow() - self.stats["start_time"]),
            "stats": self.stats.copy(),
            "active_conversations": list(get_active_conversations().keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def shutdown(self):
        """Graceful shutdown of deployment manager"""
        print("🛑 Shutting down deployment manager...")
        
        self.is_running = False
        
        # End all active conversations
        active_convs = get_active_conversations()
        for phone in active_convs.keys():
            end_conversation(phone)
            print(f"✅ Ended conversation for {phone}")
        
        # Wait for cleanup thread to finish
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5)
        
        print("✅ Deployment manager shutdown complete")

# API endpoints for external integration
def create_api_endpoints():
    """Create Flask API endpoints for external integration"""
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    manager = DeploymentManager()
    
    @app.route('/api/chatbot/process', methods=['POST'])
    def process_chat():
        """Process chatbot request"""
        try:
            data = request.json
            customer_phone = data.get('customer_phone')
            user_input = data.get('user_input')
            
            if not customer_phone or not user_input:
                return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            
            response = manager.process_customer_request(customer_phone, user_input)
            return jsonify({'success': True, 'response': response})
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    @app.route('/api/deployment/stats', methods=['GET'])
    def get_stats():
        """Get deployment statistics"""
        try:
            stats = manager.get_deployment_stats()
            return jsonify({'success': True, 'data': stats})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    @app.route('/api/deployment/shutdown', methods=['POST'])
    def shutdown_deployment():
        """Shutdown deployment manager"""
        try:
            manager.shutdown()
            return jsonify({'success': True, 'message': 'Deployment shutdown initiated'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return app

def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Grocery Store Assistant Deployment Manager')
    parser.add_argument('--mode', choices=['standalone', 'api'], default='standalone',
                       help='Deployment mode: standalone or API server')
    parser.add_argument('--port', type=int, default=5001,
                       help='Port for API server (default: 5001)')
    
    args = parser.parse_args()
    
    if args.mode == 'api':
        # Start as API server
        app = create_api_endpoints()
        print(f"🌐 Starting API server on port {args.port}")
        app.run(host='0.0.0.0', port=args.port, debug=False)
    else:
        # Start as standalone deployment manager
        manager = DeploymentManager()
        manager.start()

if __name__ == "__main__":
    main() 