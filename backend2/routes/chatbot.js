const express = require('express');
const axios = require('axios');
const User = require('../models/User');
const { loginRequired } = require('../middleware/auth');

const router = express.Router();

// Chatbot API
router.post('/', loginRequired, async (req, res) => {
  try {
    const { messages } = req.body;
    const user = req.user;
    
    if (!messages || !Array.isArray(messages)) {
      return res.status(400).json({
        success: false,
        message: 'Messages array is required'
      });
    }
    
    const inventory = user.inventory || [];
    const inventoryMap = {};
    
    // Create inventory map for quick lookup
    inventory.forEach(item => {
      inventoryMap[item.name.toLowerCase()] = item;
    });
    
    // Get the last user message
    const userMessage = messages[messages.length - 1] || '';
    
    // Find requested items in the message
    const requestedItems = Object.keys(inventoryMap).filter(name => 
      userMessage.toLowerCase().includes(name)
    );
    
    // Build context from inventory
    let context = '';
    requestedItems.forEach(name => {
      const item = inventoryMap[name];
      if (item.quantity <= 0) {
        context += `No stock for ${name}. `;
      } else {
        context += `${name} in stock: ${item.quantity}. `;
      }
    });
    
    // Prepare Gemini API request
    const headers = {
      'Content-Type': 'application/json'
    };
    
    const params = {
      key: process.env.GEMINI_API_KEY
    };
    
    // Convert messages to Gemini format
    const contents = messages.map((message, index) => ({
      role: index % 2 === 0 ? 'user' : 'model',
      parts: [{ text: message }]
    }));
    
    const geminiData = {
      contents: contents
    };
    
    // Add context if available
    if (context) {
      geminiData.context = context;
    }
    
    // Call Gemini API
    const response = await axios.post(
      process.env.GEMINI_API_URL,
      geminiData,
      { headers, params }
    );
    
    const geminiReply = response.data.candidates[0].content.parts[0].text;
    
    res.json({
      reply: geminiReply,
      context: context,
      inventory: inventory
    });
    
  } catch (error) {
    console.error('Chatbot API error:', error);
    
    if (error.response) {
      console.error('Gemini API error:', error.response.data);
    }
    
    res.status(500).json({
      success: false,
      message: 'Server error while processing chatbot request'
    });
  }
});

// Get chatbot data
router.get('/data', loginRequired, async (req, res) => {
  try {
    const user = req.user;
    
    // Extract inventory, customers, and orders
    const inventory = user.inventory || [];
    const customers = user.customers || [];
    const orders = user.orders || [];
    
    // Create shop data structure
    const shopData = {
      customers: customers,
      orders: orders,
      inventory: inventory,
      current_customer: null,
      current_order: null,
      conversation_state: {
        stage: 'greeting',
        customer_info: {},
        order_items: [],
        total_price: 0,
        notes: '',
        confirmations: {
          phone_confirmed: false,
          address_confirmed: false,
          order_complete: false,
          delivery_confirmed: false
        },
        last_5_messages: [],
        conversation_history: [],
        chat_buffer: []
      }
    };
    
    res.json({
      success: true,
      data: shopData,
      message: `Extracted ${inventory.length} inventory items, ${customers.length} customers, and ${orders.length} orders`
    });
    
  } catch (error) {
    console.error('Get chatbot data error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while fetching chatbot data'
    });
  }
});

// Process call (for voice chatbot integration)
router.post('/process-call', loginRequired, async (req, res) => {
  try {
    const { audioData, customerPhone } = req.body;
    const user = req.user;
    
    // This endpoint would integrate with speech-to-text services
    // For now, we'll return a placeholder response
    
    res.json({
      success: true,
      message: 'Call processing endpoint - to be implemented with speech-to-text integration',
      data: {
        customerPhone: customerPhone,
        processed: false
      }
    });
    
  } catch (error) {
    console.error('Process call error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while processing call'
    });
  }
});

// Generate response (for AI integration)
router.post('/generate-response', loginRequired, async (req, res) => {
  try {
    const { prompt, context } = req.body;
    const user = req.user;
    
    if (!prompt) {
      return res.status(400).json({
        success: false,
        message: 'Prompt is required'
      });
    }
    
    // Prepare Gemini API request
    const headers = {
      'Content-Type': 'application/json'
    };
    
    const params = {
      key: process.env.GEMINI_API_KEY
    };
    
    const geminiData = {
      contents: [{
        role: 'user',
        parts: [{ text: prompt }]
      }]
    };
    
    // Add context if provided
    if (context) {
      geminiData.context = context;
    }
    
    // Call Gemini API
    const response = await axios.post(
      process.env.GEMINI_API_URL,
      geminiData,
      { headers, params }
    );
    
    const geminiReply = response.data.candidates[0].content.parts[0].text;
    
    res.json({
      success: true,
      response: geminiReply,
      context: context
    });
    
  } catch (error) {
    console.error('Generate response error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error while generating response'
    });
  }
});

module.exports = router;
