# Enhanced AI Grocery Store Assistant

## 🚀 Overview

This enhanced version of the AI grocery store assistant provides **improved conversation state management**, **better AI responses**, and **multi-customer support** with proper deployment handling.

## ✨ Key Improvements

### 1. **Enhanced Conversation State Management**
- **Per-customer state tracking**: Each customer has their own conversation state
- **Real-time inventory updates**: Inventory changes are tracked during conversations
- **Order state management**: Orders are managed with proper state transitions
- **Automatic cleanup**: Inactive conversations are automatically cleaned up

### 2. **Improved AI Responses**
- **Context-aware responses**: AI considers current conversation state
- **Inventory-aware processing**: Real-time stock checking and updates
- **Better conversation flow**: Structured conversation stages with boolean flags
- **Enhanced LLM prompts**: More comprehensive prompts for better responses

### 3. **Multi-Customer Support**
- **Concurrent conversations**: Support for multiple customers simultaneously
- **Thread-safe operations**: Thread-safe conversation management
- **Customer isolation**: Each customer's state is completely isolated
- **Deployment monitoring**: Real-time monitoring of active conversations

### 4. **Production-Ready Deployment**
- **Graceful shutdown**: Proper cleanup on system shutdown
- **Error handling**: Comprehensive error handling and recovery
- **Monitoring**: Real-time statistics and monitoring
- **API endpoints**: RESTful API for external integration

## 📁 File Structure

```
callfun/
├── enhanced_conversation_state.py    # Core state management system
├── enhanced_llm_chatbot.py          # Enhanced text-based chatbot
├── enhanced_voice_chatbot.py        # Enhanced voice-based chatbot
├── deployment_manager.py             # Production deployment manager
├── requirements_enhanced.txt         # Dependencies
└── README_ENHANCED.md              # This file
```

## 🔧 Installation

1. **Install dependencies**:
```bash
pip install -r requirements_enhanced.txt
```

2. **Set up environment variables** (optional):
```bash
export GEMINI_API_KEY="your_api_key"
export MONGO_URI="your_mongodb_uri"
```

## 🚀 Usage

### 1. **Text-Based Chatbot**
```bash
python enhanced_llm_chatbot.py
```

### 2. **Voice-Based Chatbot**
```bash
python enhanced_voice_chatbot.py
```

### 3. **Production Deployment**
```bash
# Standalone mode
python deployment_manager.py

# API server mode
python deployment_manager.py --mode api --port 5001
```

## 🏗️ Architecture

### Conversation State Management

```python
class ConversationState:
    def __init__(self, customer_phone: str):
        # Core state
        self.conversation_id = str(uuid.uuid4())
        self.customer_phone = customer_phone
        self.stage = "greeting"
        self.is_active = True
        
        # Customer information
        self.customer_info = {...}
        
        # Order management
        self.current_order = {...}
        
        # Inventory state
        self.inventory_snapshot = []
        self.inventory_updates = []
        
        # Flow control
        self.flow_flags = {
            "phone_collected": False,
            "customer_verified": False,
            "order_started": False,
            "order_complete": False,
            # ... more flags
        }
```

### Key Features

1. **State Persistence**: Each customer's state is maintained throughout their session
2. **Inventory Tracking**: Real-time inventory updates during conversations
3. **Order Management**: Complete order lifecycle management
4. **Flow Control**: Boolean flags control conversation flow
5. **Automatic Cleanup**: Inactive conversations are automatically cleaned up

## 🔄 Conversation Flow

### 1. **Initial Contact**
- Customer provides phone number
- System checks if customer exists
- Creates or loads customer state

### 2. **Customer Registration** (if new)
- Collects name and address
- Creates customer record
- Sets verification flags

### 3. **Menu Selection**
- Customer chooses action (order, check status, delete)
- System transitions to appropriate stage

### 4. **Order Processing**
- AI-driven conversation for order creation
- Real-time inventory updates
- Order finalization and backend storage

### 5. **Conversation End**
- State cleanup
- Resource release
- Statistics update

## 📊 Monitoring and Statistics

The deployment manager provides real-time statistics:

```python
{
    "status": "running",
    "uptime": "2:30:15",
    "stats": {
        "total_conversations": 150,
        "active_conversations": 5,
        "completed_conversations": 145,
        "errors": 2
    },
    "active_conversations": ["1234567890", "9876543210"],
    "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🔌 API Integration

### Process Chat Request
```bash
curl -X POST http://localhost:5001/api/chatbot/process \
  -H "Content-Type: application/json" \
  -d '{
    "customer_phone": "1234567890",
    "user_input": "I want to order apples"
  }'
```

### Get Deployment Stats
```bash
curl http://localhost:5001/api/deployment/stats
```

## 🛡️ Error Handling

The system includes comprehensive error handling:

1. **Network errors**: Automatic retry with exponential backoff
2. **Authentication errors**: Token refresh and re-authentication
3. **Database errors**: Graceful degradation and error reporting
4. **LLM errors**: Fallback responses and error logging
5. **State corruption**: Automatic state recovery and cleanup

## 🔧 Configuration

### Environment Variables
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key
MONGO_URI=your_mongodb_connection_string

# Optional
BACKEND_URL=http://localhost:5000
LOG_LEVEL=INFO
CLEANUP_INTERVAL=60
MAX_CONVERSATION_AGE=3600
```

### Deployment Options
```bash
# Development mode
python enhanced_llm_chatbot.py

# Production standalone
python deployment_manager.py

# Production API server
python deployment_manager.py --mode api --port 5001
```

## 🧪 Testing

### Manual Testing
```bash
# Test text chatbot
python enhanced_llm_chatbot.py
# Enter phone number: 1234567890
# Test conversation flow

# Test voice chatbot
python enhanced_voice_chatbot.py
# Enter phone number: 1234567890
# Test voice interaction
```

### API Testing
```bash
# Start API server
python deployment_manager.py --mode api --port 5001

# Test API endpoints
curl http://localhost:5001/api/deployment/stats
```

## 📈 Performance Optimization

1. **Memory Management**: Automatic cleanup of inactive conversations
2. **Thread Safety**: Thread-safe conversation state management
3. **Connection Pooling**: Efficient database connection management
4. **Caching**: Inventory and customer data caching
5. **Async Processing**: Background cleanup and monitoring

## 🔒 Security Considerations

1. **Authentication**: Token-based authentication for API access
2. **Input Validation**: Comprehensive input validation and sanitization
3. **Error Logging**: Secure error logging without sensitive data exposure
4. **Rate Limiting**: API rate limiting for production deployment
5. **Data Encryption**: Sensitive data encryption in transit and at rest

## 🚀 Deployment Checklist

- [ ] Install all dependencies
- [ ] Set up environment variables
- [ ] Configure MongoDB connection
- [ ] Set up Gemini API key
- [ ] Test basic functionality
- [ ] Configure production settings
- [ ] Set up monitoring and logging
- [ ] Deploy with proper error handling
- [ ] Monitor performance and errors

## 📞 Support

For issues or questions:
1. Check the logs for error details
2. Verify environment variables are set correctly
3. Test with a simple conversation flow
4. Monitor the deployment statistics
5. Check MongoDB connection and permissions

## 🔄 Migration from Old System

To migrate from the old system:

1. **Backup existing data**:
```bash
# Export existing conversations
python -c "import json; print(json.dumps(conversation_state))"
```

2. **Update imports**:
```python
# Old
from llm_chatbot import process_conversation

# New
from enhanced_llm_chatbot import process_customer_interaction
```

3. **Update API calls**:
```python
# Old
response = process_conversation(user_input)

# New
response = process_customer_interaction(customer_phone, user_input)
```

4. **Test thoroughly** before production deployment

---

**🎉 The enhanced system provides a robust, scalable, and production-ready AI grocery store assistant with improved conversation management and multi-customer support!** 